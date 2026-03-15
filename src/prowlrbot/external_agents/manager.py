# -*- coding: utf-8 -*-
"""External agent manager — dispatches tasks to external AI agents."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    AgentBackendType,
    ExternalAgentConfig,
    ExternalAgentStatus,
    ExternalTask,
    TaskStatus,
)


class ExternalAgentManager:
    """Manages external agent backends and task dispatching."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS external_agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                backend_type TEXT NOT NULL,
                command TEXT DEFAULT '',
                api_url TEXT DEFAULT '',
                api_key TEXT DEFAULT '',
                timeout_seconds INTEGER DEFAULT 300,
                working_dir TEXT DEFAULT '',
                environment TEXT DEFAULT '{}',
                enabled INTEGER DEFAULT 1,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS external_tasks (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                context TEXT DEFAULT '{}',
                status TEXT DEFAULT 'queued',
                result TEXT DEFAULT '',
                error TEXT DEFAULT '',
                started_at REAL DEFAULT 0,
                completed_at REAL DEFAULT 0,
                created_at REAL NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES external_agents(id)
            );
            CREATE INDEX IF NOT EXISTS idx_tasks_agent ON external_tasks(agent_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON external_tasks(status);
        """,
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Agent CRUD
    # ------------------------------------------------------------------

    def register_agent(
        self,
        config: ExternalAgentConfig,
    ) -> ExternalAgentConfig:
        config.created_at = time.time()
        self._conn.execute(
            "INSERT OR REPLACE INTO external_agents "
            "(id, name, backend_type, command, api_url, api_key, timeout_seconds, "
            "working_dir, environment, enabled, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                config.id,
                config.name,
                config.backend_type,
                config.command,
                config.api_url,
                config.api_key,
                config.timeout_seconds,
                config.working_dir,
                json.dumps(config.environment),
                1 if config.enabled else 0,
                config.created_at,
            ),
        )
        self._conn.commit()
        return config

    def get_agent(self, agent_id: str) -> Optional[ExternalAgentConfig]:
        row = self._conn.execute(
            "SELECT * FROM external_agents WHERE id = ?",
            (agent_id,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_config(row)

    def list_agents(
        self,
        enabled_only: bool = False,
    ) -> List[ExternalAgentConfig]:
        query = "SELECT * FROM external_agents"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY created_at DESC"
        rows = self._conn.execute(query).fetchall()
        return [self._row_to_config(r) for r in rows]

    def delete_agent(self, agent_id: str) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM external_agents WHERE id = ?",
            (agent_id,),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    def create_task(self, task: ExternalTask) -> ExternalTask:
        task.created_at = time.time()
        self._conn.execute(
            "INSERT INTO external_tasks "
            "(id, agent_id, prompt, context, status, result, error, "
            "started_at, completed_at, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                task.id,
                task.agent_id,
                task.prompt,
                json.dumps(task.context),
                task.status,
                task.result,
                task.error,
                task.started_at,
                task.completed_at,
                task.created_at,
            ),
        )
        self._conn.commit()
        return task

    def get_task(self, task_id: str) -> Optional[ExternalTask]:
        row = self._conn.execute(
            "SELECT * FROM external_tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_task(row)

    def list_tasks(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ExternalTask]:
        query = "SELECT * FROM external_tasks WHERE 1=1"
        params: list = []
        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_task(r) for r in rows]

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: str = "",
        error: str = "",
    ) -> bool:
        now = time.time()
        updates = ["status = ?"]
        params: list = [status]
        if status == TaskStatus.RUNNING:
            updates.append("started_at = ?")
            params.append(now)
        if status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ):
            updates.append("completed_at = ?")
            params.append(now)
        if result:
            updates.append("result = ?")
            params.append(result)
        if error:
            updates.append("error = ?")
            params.append(error)
        params.append(task_id)
        cursor = self._conn.execute(
            f"UPDATE external_tasks SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def cancel_task(self, task_id: str) -> bool:
        return self.update_task_status(task_id, TaskStatus.CANCELLED)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def execute_task(self, task_id: str) -> ExternalTask:
        """Execute a task using its assigned external agent."""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        agent = self.get_agent(task.agent_id)
        if not agent:
            self.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error="Agent not found",
            )
            task.status = TaskStatus.FAILED
            task.error = "Agent not found"
            return task

        self.update_task_status(task_id, TaskStatus.RUNNING)

        try:
            if agent.backend_type == AgentBackendType.CUSTOM_CLI:
                result = await self._run_cli(agent, task)
            elif agent.backend_type == AgentBackendType.DOCKER:
                result = await self._run_docker(agent, task)
            elif agent.backend_type == AgentBackendType.CLAUDE_CODE:
                result = await self._run_claude_code(agent, task)
            else:
                result = f"Backend {agent.backend_type} execution not yet implemented"

            self.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                result=result,
            )
            task.status = TaskStatus.COMPLETED
            task.result = result
        except asyncio.TimeoutError:
            self.update_task_status(
                task_id,
                TaskStatus.TIMEOUT,
                error="Task timed out",
            )
            task.status = TaskStatus.TIMEOUT
            task.error = "Task timed out"
        except Exception as e:
            self.update_task_status(task_id, TaskStatus.FAILED, error=str(e))
            task.status = TaskStatus.FAILED
            task.error = str(e)

        return task

    async def _run_cli(
        self,
        agent: ExternalAgentConfig,
        task: ExternalTask,
    ) -> str:
        """Run a CLI-based external agent."""
        env = {**agent.environment}
        cmd = f"{agent.command} {task.prompt}"
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=agent.working_dir or None,
            env=env if env else None,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=agent.timeout_seconds,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"CLI exited with code {proc.returncode}: {stderr.decode()}",
            )
        return stdout.decode()

    async def _run_docker(
        self,
        agent: ExternalAgentConfig,
        task: ExternalTask,
    ) -> str:
        """Run a Docker-based external agent."""
        env_flags = " ".join(f"-e {k}={v}" for k, v in agent.environment.items())
        cmd = f"docker run --rm {env_flags} {agent.command} {task.prompt}"
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=agent.timeout_seconds,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"Docker exited with code {proc.returncode}: {stderr.decode()}",
            )
        return stdout.decode()

    async def _run_claude_code(
        self,
        agent: ExternalAgentConfig,
        task: ExternalTask,
    ) -> str:
        """Run Claude Code as an external agent."""
        cmd = f"claude -p '{task.prompt}'"
        if agent.working_dir:
            cmd = f"cd {agent.working_dir} && {cmd}"
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**agent.environment} if agent.environment else None,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=agent.timeout_seconds,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"Claude Code exited with code {proc.returncode}: {stderr.decode()}",
            )
        return stdout.decode()

    async def check_agent_health(self, agent_id: str) -> ExternalAgentStatus:
        """Check if an external agent is available."""
        agent = self.get_agent(agent_id)
        if not agent:
            return ExternalAgentStatus(
                agent_id=agent_id,
                name="unknown",
                backend_type=AgentBackendType.CUSTOM_CLI,
                available=False,
                error="Agent not found",
            )

        status = ExternalAgentStatus(
            agent_id=agent.id,
            name=agent.name,
            backend_type=agent.backend_type,
            last_check=time.time(),
        )

        try:
            if agent.backend_type == AgentBackendType.CLAUDE_CODE:
                proc = await asyncio.create_subprocess_shell(
                    "claude --version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(proc.communicate(), timeout=10)
                status.available = proc.returncode == 0
            elif agent.backend_type == AgentBackendType.DOCKER:
                proc = await asyncio.create_subprocess_shell(
                    f"docker image inspect {agent.command.split()[0]}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(proc.communicate(), timeout=10)
                status.available = proc.returncode == 0
            elif agent.backend_type == AgentBackendType.CUSTOM_CLI:
                binary = agent.command.split()[0] if agent.command else ""
                if binary:
                    proc = await asyncio.create_subprocess_shell(
                        f"which {binary}",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await asyncio.wait_for(proc.communicate(), timeout=5)
                    status.available = proc.returncode == 0
            else:
                status.available = True  # Assume available for HTTP
        except Exception as e:
            status.error = str(e)

        return status

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_config(row: sqlite3.Row) -> ExternalAgentConfig:
        return ExternalAgentConfig(
            id=row["id"],
            name=row["name"],
            backend_type=AgentBackendType(row["backend_type"]),
            command=row["command"],
            api_url=row["api_url"],
            api_key=row["api_key"],
            timeout_seconds=row["timeout_seconds"],
            working_dir=row["working_dir"],
            environment=json.loads(row["environment"]) if row["environment"] else {},
            enabled=bool(row["enabled"]),
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> ExternalTask:
        return ExternalTask(
            id=row["id"],
            agent_id=row["agent_id"],
            prompt=row["prompt"],
            context=json.loads(row["context"]) if row["context"] else {},
            status=TaskStatus(row["status"]),
            result=row["result"],
            error=row["error"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            created_at=row["created_at"],
        )

    def close(self) -> None:
        self._conn.close()
