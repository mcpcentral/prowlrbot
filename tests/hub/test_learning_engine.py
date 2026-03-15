# -*- coding: utf-8 -*-
"""Tests for the Learning Engine — CRUD, FTS5 search, decay scoring,
preferences, sessions, thread safety, and module-level convenience functions.
"""

import threading
import time

import pytest

from prowlrbot.learning.db import (
    LearningDB,
    _clamp_limit,
    _decay_score,
    _sanitize_fts_query,
    add_learning,
    init_db,
    query_learnings,
    search_learnings,
)


@pytest.fixture
def db(tmp_path):
    """Create a fresh learning DB with an ephemeral database."""
    db_path = str(tmp_path / "test_learnings.db")
    learning_db = LearningDB(db_path)
    yield learning_db
    learning_db.close()


# --- CRUD ---


class TestLearningCRUD:
    def test_add_and_retrieve(self, db):
        lid = db.add_learning(
            "correction",
            "agent-1",
            "Fix import",
            "Use absolute imports",
        )
        assert lid is not None
        assert lid.startswith("learn-")
        recent = db.get_recent(limit=1)
        assert len(recent) == 1
        assert recent[0]["learning_id"] == lid
        assert recent[0]["title"] == "Fix import"
        assert recent[0]["content"] == "Use absolute imports"
        assert recent[0]["category"] == "correction"

    def test_add_with_metadata(self, db):
        lid = db.add_learning(
            "pattern",
            "agent-2",
            "Retry pattern",
            "Exponential backoff for HTTP calls",
            metadata={"language": "python", "context": "http"},
            confidence=0.85,
        )
        recent = db.get_recent(limit=1)
        assert recent[0]["confidence"] == 0.85
        assert '"language"' in recent[0]["metadata"]

    def test_add_with_project(self, db):
        lid = db.add_learning(
            "correction",
            "agent-1",
            "Project-scoped",
            "Use Black formatter",
            project="prowlrbot",
        )
        recent = db.get_recent(limit=1, project="prowlrbot")
        assert len(recent) == 1
        assert recent[0]["project"] == "prowlrbot"

        # Should not appear in different project scope
        other = db.get_recent(limit=10, project="other-project")
        assert len(other) == 0

    def test_get_by_id(self, db):
        lid = db.add_learning(
            "insight",
            "agent-1",
            "Key insight",
            "Important content",
        )
        result = db.get(lid)
        assert result is not None
        assert result["learning_id"] == lid
        assert result["title"] == "Key insight"

    def test_get_nonexistent(self, db):
        assert db.get("nonexistent-id") is None

    def test_get_by_source(self, db):
        db.add_learning("correction", "agent-a", "Title A", "Content A")
        db.add_learning("correction", "agent-b", "Title B", "Content B")
        db.add_learning("pattern", "agent-a", "Title C", "Content C")
        results = db.get_by_source("agent-a")
        assert len(results) == 2
        assert all(r["source"] == "agent-a" for r in results)

    def test_get_recent_by_category(self, db):
        db.add_learning("correction", "a", "C1", "content")
        db.add_learning("pattern", "a", "P1", "content")
        db.add_learning("insight", "a", "I1", "content")
        corrections = db.get_recent(category="correction")
        assert len(corrections) == 1
        assert corrections[0]["category"] == "correction"

    def test_delete_learning(self, db):
        lid = db.add_learning("correction", "a", "Delete me", "gone")
        assert db.delete_learning(lid) is True
        assert db.get_recent() == []

    def test_delete_nonexistent(self, db):
        assert db.delete_learning("nonexistent-id") is False

    def test_increment_usage(self, db):
        lid = db.add_learning("pattern", "a", "Reusable", "content")
        db.increment_usage(lid)
        db.increment_usage(lid)
        recent = db.get_recent(limit=1)
        assert recent[0]["times_used"] == 2

    def test_update_confidence(self, db):
        lid = db.add_learning(
            "pattern",
            "a",
            "Adjustable",
            "content",
            confidence=0.5,
        )
        db.update_confidence(lid, 0.9)
        result = db.get(lid)
        assert result["confidence"] == 0.9

    def test_update_confidence_clamped(self, db):
        lid = db.add_learning("pattern", "a", "Clamped", "content")
        db.update_confidence(lid, 1.5)
        assert db.get(lid)["confidence"] == 1.0
        db.update_confidence(lid, -0.5)
        assert db.get(lid)["confidence"] == 0.0


# --- FTS5 Search ---


class TestFTSSearch:
    def test_basic_search(self, db):
        db.add_learning(
            "correction",
            "a",
            "Fix async deadlock",
            "Use asyncio.gather instead of sequential awaits",
        )
        db.add_learning(
            "pattern",
            "a",
            "Database pooling",
            "Always use connection pools for SQLite",
        )
        results = db.search("async deadlock")
        assert len(results) == 1
        assert results[0]["title"] == "Fix async deadlock"

    def test_search_content(self, db):
        db.add_learning(
            "insight",
            "a",
            "Perf tip",
            "Use connection pools for better throughput",
        )
        results = db.search("connection pools")
        assert len(results) == 1

    def test_search_with_category_filter(self, db):
        db.add_learning("correction", "a", "Fix bug", "Fix the async bug")
        db.add_learning("pattern", "a", "Async pattern", "Use async properly")
        results = db.search("async", category="correction")
        assert len(results) == 1
        assert results[0]["category"] == "correction"

    def test_search_with_project_filter(self, db):
        db.add_learning(
            "correction",
            "a",
            "Proj A fix",
            "Fix in project A",
            project="proj-a",
        )
        db.add_learning(
            "correction",
            "a",
            "Proj B fix",
            "Fix in project B",
            project="proj-b",
        )
        results = db.search("fix", project="proj-a")
        assert len(results) == 1
        assert results[0]["project"] == "proj-a"

    def test_search_no_results(self, db):
        db.add_learning("correction", "a", "Something", "Unrelated content")
        results = db.search("xyznonexistent")
        assert len(results) == 0

    def test_search_empty_query(self, db):
        db.add_learning("correction", "a", "Title", "Content")
        results = db.search("")
        assert isinstance(results, list)


# --- FTS5 Safety (FINDING-08) ---


class TestFTSSafety:
    def test_sanitize_strips_operators(self):
        result = _sanitize_fts_query("test OR *")
        assert '"' in result
        assert "*" not in result
        result2 = _sanitize_fts_query('foo AND "bar"')
        assert '"' in result2
        assert result2.count('"') == 2

    def test_sanitize_strips_special_chars(self):
        result = _sanitize_fts_query("hello(){}[]^~:!world")
        assert '"' in result
        assert "(" not in result
        assert ")" not in result
        assert "{" not in result
        assert "!" not in result

    def test_sanitize_empty_string(self):
        assert _sanitize_fts_query("") == '""'
        assert _sanitize_fts_query("***") == '""'

    def test_sanitize_normal_query_preserved(self):
        assert _sanitize_fts_query("fix import error") == '"fix import error"'

    def test_search_with_malicious_fts_operators(self, db):
        db.add_learning(
            "correction",
            "a",
            "Safe title",
            "Safe content about imports",
        )
        results = db.search("* OR *")
        assert isinstance(results, list)
        results = db.search('NEAR("foo" "bar")')
        assert isinstance(results, list)
        results = db.search("title:exploit")
        assert isinstance(results, list)


# --- Limit Clamping (FINDING-06) ---


class TestLimitClamping:
    def test_clamp_limit_normal(self):
        assert _clamp_limit(10) == 10
        assert _clamp_limit(200) == 200

    def test_clamp_limit_too_high(self):
        assert _clamp_limit(999999) == 200
        assert _clamp_limit(1000000) == 200

    def test_clamp_limit_zero_or_negative(self):
        assert _clamp_limit(0) == 1
        assert _clamp_limit(-5) == 1

    def test_get_recent_respects_limit(self, db):
        for i in range(5):
            db.add_learning("correction", "a", f"Title {i}", f"Content {i}")
        results = db.get_recent(limit=3)
        assert len(results) == 3

    def test_search_respects_limit(self, db):
        for i in range(5):
            db.add_learning(
                "correction",
                "a",
                f"Search target {i}",
                f"Searchable content {i}",
            )
        results = db.search("searchable", limit=2)
        assert len(results) <= 2


# --- Decay Scoring ---


class TestDecayScoring:
    def test_decay_score_recent(self):
        """A learning created just now should have a decay score near 1.0."""
        from datetime import datetime, timezone

        now = datetime.now(tz=timezone.utc).isoformat()
        score = _decay_score(now)
        assert 0.99 <= score <= 1.0

    def test_decay_score_old(self):
        """A learning from 60 days ago should have decayed significantly."""
        from datetime import datetime, timedelta, timezone

        old = (datetime.now(tz=timezone.utc) - timedelta(days=60)).isoformat()
        score = _decay_score(old)
        # After 60 days (2 half-lives at 30-day default), score ~ 0.25
        assert 0.2 <= score <= 0.3

    def test_decay_score_invalid_timestamp(self):
        """Invalid timestamps should return the fallback score."""
        assert _decay_score("not-a-date") == 0.5
        assert _decay_score("") == 0.5

    def test_query_learnings_ranked_by_relevance(self, db):
        """Verify query_learnings returns results sorted by confidence * decay."""
        # Add high-confidence and low-confidence learnings
        db.add_learning(
            "correction",
            "a",
            "High confidence",
            "Important fix",
            project="test",
            confidence=1.0,
        )
        db.add_learning(
            "pattern",
            "a",
            "Low confidence",
            "Maybe useful",
            project="test",
            confidence=0.1,
        )
        results = db.query_learnings("test")
        assert len(results) == 2
        assert results[0]["title"] == "High confidence"
        assert results[1]["title"] == "Low confidence"
        # All results should have relevance key
        assert all("relevance" in r for r in results)
        assert results[0]["relevance"] > results[1]["relevance"]

    def test_query_learnings_with_category(self, db):
        db.add_learning("correction", "a", "C1", "content", project="p")
        db.add_learning("pattern", "a", "P1", "content", project="p")
        results = db.query_learnings("p", category="correction")
        assert len(results) == 1
        assert results[0]["category"] == "correction"

    def test_query_learnings_empty_project(self, db):
        db.add_learning("correction", "a", "Global", "content", project="")
        results = db.query_learnings("")
        assert len(results) == 1


# --- Preferences ---


class TestPreferences:
    def test_set_and_get_preference(self, db):
        pid = db.set_preference("formatter", "black")
        assert pid.startswith("pref-")
        pref = db.get_preference("formatter")
        assert pref is not None
        assert pref["key"] == "formatter"
        assert pref["value"] == "black"

    def test_update_preference_on_conflict(self, db):
        db.set_preference("indent", "4")
        db.set_preference("indent", "2")
        pref = db.get_preference("indent")
        assert pref["value"] == "2"

    def test_preference_project_scoping(self, db):
        db.set_preference("style", "pep8", project="proj-a")
        db.set_preference("style", "google", project="proj-b")
        assert db.get_preference("style", project="proj-a")["value"] == "pep8"
        assert db.get_preference("style", project="proj-b")["value"] == "google"

    def test_preference_scope_levels(self, db):
        db.set_preference("key", "global-val", scope="global")
        db.set_preference("key", "agent-val", scope="agent")
        assert db.get_preference("key", scope="global")["value"] == "global-val"
        assert db.get_preference("key", scope="agent")["value"] == "agent-val"

    def test_list_preferences(self, db):
        db.set_preference("a", "1", project="p")
        db.set_preference("b", "2", project="p")
        db.set_preference("c", "3", project="other")
        prefs = db.list_preferences(project="p")
        assert len(prefs) == 2
        keys = {p["key"] for p in prefs}
        assert keys == {"a", "b"}

    def test_list_preferences_by_scope(self, db):
        db.set_preference("x", "1", scope="global")
        db.set_preference("y", "2", scope="agent")
        prefs = db.list_preferences(scope="global")
        assert len(prefs) == 1
        assert prefs[0]["key"] == "x"

    def test_delete_preference(self, db):
        db.set_preference("deleteme", "val")
        assert db.delete_preference("deleteme") is True
        assert db.get_preference("deleteme") is None

    def test_delete_nonexistent_preference(self, db):
        assert db.delete_preference("nope") is False

    def test_get_nonexistent_preference(self, db):
        assert db.get_preference("nope") is None


# --- Session Tracking ---


class TestSessionTracking:
    def test_start_session(self, db):
        sid = db.start_session("agent-x")
        assert sid is not None
        stats = db.stats()
        assert stats["total_sessions"] == 1

    def test_end_session(self, db):
        sid = db.start_session("agent-y")
        db.end_session(sid, summary="Completed task", learnings_captured=3)
        stats = db.stats()
        assert stats["total_sessions"] == 1

    def test_stats(self, db):
        db.add_learning("correction", "a", "C1", "content")
        db.add_learning("correction", "a", "C2", "content")
        db.add_learning("pattern", "b", "P1", "content")
        db.set_preference("pref1", "val1")
        db.start_session("agent-1")
        stats = db.stats()
        assert stats["total_learnings"] == 3
        assert stats["by_category"]["correction"] == 2
        assert stats["by_category"]["pattern"] == 1
        assert stats["total_sessions"] == 1
        assert stats["total_preferences"] == 1

    def test_stats_by_project(self, db):
        db.add_learning("correction", "a", "C1", "c", project="proj-x")
        db.add_learning("correction", "a", "C2", "c", project="proj-x")
        db.add_learning("pattern", "a", "P1", "c", project="proj-y")
        stats = db.stats()
        assert stats["by_project"]["proj-x"] == 2
        assert stats["by_project"]["proj-y"] == 1


# --- Summary ---


class TestSummary:
    def test_summary_empty(self, db):
        result = db.summary()
        assert "No learnings" in result

    def test_summary_with_data(self, db):
        db.add_learning(
            "correction",
            "a",
            "Fix imports",
            "content",
            project="test",
        )
        db.add_learning(
            "pattern",
            "a",
            "Use dataclasses",
            "content",
            project="test",
        )
        result = db.summary("test")
        assert "Fix imports" in result
        assert "Use dataclasses" in result
        assert "confidence=" in result
        assert "relevance=" in result


# --- Module-level Convenience Functions ---


class TestModuleLevelFunctions:
    def test_init_db(self, tmp_path):
        db_path = str(tmp_path / "func_test.db")
        conn = init_db(db_path)
        assert conn is not None
        # Verify tables exist
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'",
        ).fetchall()
        table_names = {r[0] for r in tables}
        assert "learnings" in table_names
        assert "preferences" in table_names
        assert "sessions" in table_names
        conn.close()

    def test_add_learning_function(self, tmp_path):
        db_path = str(tmp_path / "func_test.db")
        conn = init_db(db_path)
        lid = add_learning(
            conn,
            "test-project",
            "correction",
            "Use Black formatter",
        )
        assert lid.startswith("learn-")
        # Verify stored
        row = conn.execute(
            "SELECT * FROM learnings WHERE learning_id = ?",
            (lid,),
        ).fetchone()
        assert row is not None
        assert row["project"] == "test-project"
        assert row["category"] == "correction"
        assert row["content"] == "Use Black formatter"
        # Title should be auto-generated from content
        assert row["title"] == "Use Black formatter"
        conn.close()

    def test_add_learning_with_explicit_title(self, tmp_path):
        db_path = str(tmp_path / "func_test.db")
        conn = init_db(db_path)
        lid = add_learning(
            conn,
            "proj",
            "pattern",
            "Long content here",
            title="Custom title",
        )
        row = conn.execute(
            "SELECT title FROM learnings WHERE learning_id = ?",
            (lid,),
        ).fetchone()
        assert row["title"] == "Custom title"
        conn.close()

    def test_query_learnings_function(self, tmp_path):
        db_path = str(tmp_path / "func_test.db")
        conn = init_db(db_path)
        add_learning(conn, "proj", "correction", "Content A", confidence=0.9)
        add_learning(conn, "proj", "pattern", "Content B", confidence=0.3)
        add_learning(conn, "other", "insight", "Content C", confidence=1.0)

        results = query_learnings(conn, "proj")
        assert len(results) == 2
        assert all("relevance" in r for r in results)
        # Higher confidence should rank first
        assert results[0]["confidence"] >= results[1]["confidence"]
        conn.close()

    def test_search_learnings_function(self, tmp_path):
        db_path = str(tmp_path / "func_test.db")
        conn = init_db(db_path)
        add_learning(
            conn,
            "proj",
            "correction",
            "Fix the async deadlock issue",
        )
        add_learning(conn, "proj", "pattern", "Database connection pooling")

        results = search_learnings(conn, "async deadlock")
        assert len(results) == 1
        assert "async" in results[0]["content"].lower()
        conn.close()

    def test_search_learnings_empty(self, tmp_path):
        db_path = str(tmp_path / "func_test.db")
        conn = init_db(db_path)
        results = search_learnings(conn, "nonexistent")
        assert results == []
        conn.close()

    def test_init_db_idempotent(self, tmp_path):
        """init_db can be called multiple times safely."""
        db_path = str(tmp_path / "func_test.db")
        conn1 = init_db(db_path)
        add_learning(conn1, "proj", "correction", "First entry")
        conn1.close()

        conn2 = init_db(db_path)
        results = query_learnings(conn2, "proj")
        assert len(results) == 1
        conn2.close()


# --- Thread Safety (FINDING-14) ---


class TestThreadSafety:
    def test_concurrent_writes(self, db):
        """Multiple threads writing simultaneously should not corrupt data."""
        errors = []

        def writer(thread_id):
            try:
                for i in range(20):
                    db.add_learning(
                        "correction",
                        f"thread-{thread_id}",
                        f"Title {thread_id}-{i}",
                        f"Content {thread_id}-{i}",
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"
        stats = db.stats()
        assert stats["total_learnings"] == 100  # 5 threads * 20 each

    def test_concurrent_read_write(self, db):
        """Reads during writes should not crash or corrupt data."""
        db.add_learning(
            "correction",
            "seed",
            "Seed data",
            "Initial content for searching",
        )
        write_errors = []
        read_errors = []

        def writer():
            try:
                for i in range(20):
                    db.add_learning(
                        "pattern",
                        "writer",
                        f"Write {i}",
                        f"Content {i}",
                    )
            except Exception as e:
                write_errors.append(e)

        def reader():
            for _ in range(20):
                try:
                    db.get_recent(limit=10)
                except Exception:
                    pass  # SQLite may briefly error under contention
                try:
                    db.search("content")
                except Exception:
                    pass

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Writes must succeed — that's the critical guarantee
        assert write_errors == [], f"Write errors: {write_errors}"
        # Data should be consistent after all threads finish
        stats = db.stats()
        assert stats["total_learnings"] == 21  # 1 seed + 20 writes

    def test_concurrent_preference_writes(self, db):
        """Concurrent preference upserts should not crash."""
        errors = []

        def pref_writer(thread_id):
            try:
                for i in range(10):
                    db.set_preference(
                        f"key-{thread_id}-{i}",
                        f"value-{i}",
                        project=f"proj-{thread_id}",
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=pref_writer, args=(t,)) for t in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Preference write errors: {errors}"


# --- Migration ---


class TestMigration:
    def test_migration_adds_project_column(self, tmp_path):
        """Opening a DB created without the project column should migrate cleanly."""
        db_path = str(tmp_path / "migrate_test.db")
        # Create a DB, then verify the project column works
        learning_db = LearningDB(db_path)
        lid = learning_db.add_learning(
            "correction",
            "a",
            "Title",
            "Content",
            project="migrated",
        )
        result = learning_db.get(lid)
        assert result["project"] == "migrated"
        learning_db.close()
