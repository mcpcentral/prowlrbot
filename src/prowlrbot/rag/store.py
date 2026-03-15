# -*- coding: utf-8 -*-
"""SQLite-backed storage for RAG documents and chunks."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from .models import Chunk, Document, DocumentStatus


class RAGStore:
    """Persists RAG documents and chunks in SQLite."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        if db_path is None:
            from prowlrbot.constant import WORKING_DIR

            db_path = WORKING_DIR / "rag.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_db()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id           TEXT PRIMARY KEY,
                title        TEXT NOT NULL,
                source       TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                chunk_count  INTEGER NOT NULL DEFAULT 0,
                status       TEXT NOT NULL DEFAULT 'pending',
                created_at   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id          TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                content     TEXT NOT NULL,
                metadata    TEXT NOT NULL DEFAULT '{}',
                embedding   TEXT,
                position    INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_chunks_document_id
                ON chunks(document_id);
            """,
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Document operations
    # ------------------------------------------------------------------

    def add_document(self, doc: Document) -> Document:
        """Insert a document record."""
        self._conn.execute(
            """
            INSERT INTO documents (id, title, source, content_hash, chunk_count, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc.id,
                doc.title,
                doc.source,
                doc.content_hash,
                doc.chunk_count,
                doc.status,
                doc.created_at,
            ),
        )
        self._conn.commit()
        return doc

    def get_document(self, document_id: str) -> Optional[Document]:
        """Fetch a document by ID, or *None* if not found."""
        row = self._conn.execute(
            "SELECT id, title, source, content_hash, chunk_count, status, created_at "
            "FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
        if row is None:
            return None
        return Document(
            id=row[0],
            title=row[1],
            source=row[2],
            content_hash=row[3],
            chunk_count=row[4],
            status=DocumentStatus(row[5]),
            created_at=row[6],
        )

    def list_documents(self) -> list[Document]:
        """Return all documents ordered by creation time (newest first)."""
        rows = self._conn.execute(
            "SELECT id, title, source, content_hash, chunk_count, status, created_at "
            "FROM documents ORDER BY created_at DESC",
        ).fetchall()
        return [
            Document(
                id=r[0],
                title=r[1],
                source=r[2],
                content_hash=r[3],
                chunk_count=r[4],
                status=DocumentStatus(r[5]),
                created_at=r[6],
            )
            for r in rows
        ]

    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its chunks. Returns *True* if a row was deleted."""
        self._conn.execute(
            "DELETE FROM chunks WHERE document_id = ?",
            (document_id,),
        )
        cur = self._conn.execute(
            "DELETE FROM documents WHERE id = ?",
            (document_id,),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def update_document_status(
        self,
        document_id: str,
        status: DocumentStatus,
        chunk_count: int = 0,
    ) -> None:
        """Update the status (and optionally chunk count) of a document."""
        self._conn.execute(
            "UPDATE documents SET status = ?, chunk_count = ? WHERE id = ?",
            (status, chunk_count, document_id),
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Chunk operations
    # ------------------------------------------------------------------

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """Bulk-insert chunks."""
        self._conn.executemany(
            """
            INSERT INTO chunks (id, document_id, content, metadata, embedding, position)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    c.id,
                    c.document_id,
                    c.content,
                    json.dumps(c.metadata, ensure_ascii=False),
                    json.dumps(c.embedding) if c.embedding else None,
                    c.position,
                )
                for c in chunks
            ],
        )
        self._conn.commit()

    def get_chunks_for_document(self, document_id: str) -> list[Chunk]:
        """Return all chunks for a document, ordered by position."""
        rows = self._conn.execute(
            "SELECT id, document_id, content, metadata, embedding, position "
            "FROM chunks WHERE document_id = ? ORDER BY position",
            (document_id,),
        ).fetchall()
        return [self._row_to_chunk(r) for r in rows]

    def search_chunks(self, query: str, limit: int = 5) -> list[Chunk]:
        """Simple text search using SQL LIKE.

        Searches for each word in *query* (AND logic — all words must appear).
        """
        words = query.strip().split()
        if not words:
            return []

        where_clauses = ["content LIKE ?"] * len(words)
        params = [f"%{w}%" for w in words]

        sql = (
            "SELECT id, document_id, content, metadata, embedding, position "
            f"FROM chunks WHERE {' AND '.join(where_clauses)} "
            "ORDER BY position LIMIT ?"
        )
        params.append(limit)  # type: ignore[arg-type]

        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_chunk(r) for r in rows]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        """Return summary statistics about the RAG store."""
        doc_count = self._conn.execute(
            "SELECT COUNT(*) FROM documents",
        ).fetchone()[0]
        chunk_count = self._conn.execute(
            "SELECT COUNT(*) FROM chunks",
        ).fetchone()[0]
        status_rows = self._conn.execute(
            "SELECT status, COUNT(*) FROM documents GROUP BY status",
        ).fetchall()
        by_status = {row[0]: row[1] for row in status_rows}
        return {
            "document_count": doc_count,
            "chunk_count": chunk_count,
            "documents_by_status": by_status,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_chunk(row: tuple) -> Chunk:
        embedding = json.loads(row[4]) if row[4] else None
        return Chunk(
            id=row[0],
            document_id=row[1],
            content=row[2],
            metadata=json.loads(row[3]),
            embedding=embedding,
            position=row[5],
        )

    def close(self) -> None:
        self._conn.close()
