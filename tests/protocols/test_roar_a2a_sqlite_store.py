# -*- coding: utf-8 -*-
"""Tests for SQLite-backed A2A task store."""

from __future__ import annotations

import os
import tempfile
import unittest

from prowlrbot.protocols.a2a_server import (
    A2ATask,
    Artifact,
    Message,
    Part,
    TaskStatus,
)
from prowlrbot.protocols.a2a_store_sqlite import SQLiteA2ATaskStore


class TestSQLiteA2ATaskStore(unittest.TestCase):
    """Tests for SQLiteA2ATaskStore full lifecycle."""

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmpfile.close()
        self.db_path = self._tmpfile.name
        self.store = SQLiteA2ATaskStore(db_path=self.db_path)

    def tearDown(self):
        self.store.close()
        os.unlink(self.db_path)

    def _make_task(self, **kwargs) -> A2ATask:
        defaults = {
            "from_agent": "agent-a",
            "to_agent": "agent-b",
            "messages": [Message(role="user", parts=[Part(text="Hello")])],
        }
        defaults.update(kwargs)
        return A2ATask(**defaults)

    def test_create_and_get(self):
        task = self._make_task()
        created = self.store.create(task)
        assert created.id == task.id
        assert len(created.history) == 1
        assert created.history[0].status == TaskStatus.SUBMITTED

        found = self.store.get(task.id)
        assert found is not None
        assert found.id == task.id
        assert found.from_agent == "agent-a"
        assert found.to_agent == "agent-b"
        assert len(found.messages) == 1
        assert found.messages[0].parts[0].text == "Hello"

    def test_get_missing(self):
        assert self.store.get("nonexistent") is None

    def test_update_status(self):
        task = self.store.create(self._make_task())
        updated = self.store.update_status(
            task.id,
            TaskStatus.WORKING,
            "Processing",
        )
        assert updated is not None
        assert updated.status == TaskStatus.WORKING
        assert len(updated.history) == 2
        assert updated.history[1].status == TaskStatus.WORKING
        assert updated.history[1].message == "Processing"

    def test_update_status_missing(self):
        result = self.store.update_status("nope", TaskStatus.WORKING)
        assert result is None

    def test_append_message(self):
        task = self.store.create(self._make_task())
        new_msg = Message(role="agent", parts=[Part(text="Working on it")])
        updated = self.store.append_message(task.id, new_msg)
        assert updated is not None
        assert len(updated.messages) == 2
        assert updated.messages[1].role == "agent"
        assert updated.messages[1].parts[0].text == "Working on it"

    def test_append_message_missing(self):
        msg = Message(role="agent", parts=[Part(text="lost")])
        assert self.store.append_message("nope", msg) is None

    def test_append_artifact(self):
        task = self.store.create(self._make_task())
        artifact = Artifact(
            name="result.txt",
            description="Output file",
            parts=[Part(text="file contents")],
            metadata={"size": 100},
        )
        updated = self.store.append_artifact(task.id, artifact)
        assert updated is not None
        assert len(updated.artifacts) == 1
        assert updated.artifacts[0].name == "result.txt"
        assert updated.artifacts[0].description == "Output file"
        assert updated.artifacts[0].parts[0].text == "file contents"
        assert updated.artifacts[0].metadata == {"size": 100}

    def test_append_artifact_missing(self):
        artifact = Artifact(name="lost.txt")
        assert self.store.append_artifact("nope", artifact) is None

    def test_list_tasks_all(self):
        self.store.create(self._make_task())
        self.store.create(self._make_task())
        tasks = self.store.list_tasks()
        assert len(tasks) == 2

    def test_list_tasks_filtered(self):
        t1 = self.store.create(self._make_task())
        t2 = self.store.create(self._make_task())
        self.store.update_status(t1.id, TaskStatus.WORKING)

        working = self.store.list_tasks(status=TaskStatus.WORKING)
        assert len(working) == 1
        assert working[0].id == t1.id

        submitted = self.store.list_tasks(status=TaskStatus.SUBMITTED)
        assert len(submitted) == 1
        assert submitted[0].id == t2.id

    def test_list_tasks_empty(self):
        assert len(self.store.list_tasks()) == 0

    def test_full_lifecycle(self):
        """Full task lifecycle: create -> working -> completed with artifacts."""
        task = self.store.create(self._make_task())
        self.store.update_status(task.id, TaskStatus.WORKING)
        self.store.append_message(
            task.id,
            Message(role="agent", parts=[Part(text="Analyzing...")]),
        )
        self.store.append_artifact(
            task.id,
            Artifact(
                name="output.json",
                parts=[Part(text='{"result": true}')],
            ),
        )
        self.store.update_status(task.id, TaskStatus.COMPLETED, "Done!")

        final = self.store.get(task.id)
        assert final is not None
        assert final.status == TaskStatus.COMPLETED
        assert len(final.messages) == 2
        assert len(final.artifacts) == 1
        assert len(final.history) == 3  # submitted, working, completed

    def test_persistence_across_connections(self):
        """Data survives closing and reopening the database."""
        task = self.store.create(self._make_task())
        self.store.update_status(task.id, TaskStatus.WORKING)
        task_id = task.id
        self.store.close()

        store2 = SQLiteA2ATaskStore(db_path=self.db_path)
        found = store2.get(task_id)
        assert found is not None
        assert found.status == TaskStatus.WORKING
        assert len(found.history) == 2
        store2.close()

    def test_metadata_preserved(self):
        task = self._make_task(
            metadata={"priority": "high", "tags": ["urgent"]},
        )
        self.store.create(task)
        found = self.store.get(task.id)
        assert found is not None
        assert found.metadata == {"priority": "high", "tags": ["urgent"]}

    def test_message_metadata_preserved(self):
        msg = Message(
            role="user",
            parts=[Part(text="test")],
            metadata={"source": "cli"},
        )
        task = self._make_task(messages=[msg])
        self.store.create(task)
        found = self.store.get(task.id)
        assert found is not None
        assert found.messages[0].metadata == {"source": "cli"}


if __name__ == "__main__":
    unittest.main()
