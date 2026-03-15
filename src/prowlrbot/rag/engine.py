# -*- coding: utf-8 -*-
"""RAG engine — ingest, search, and retrieve context for LLM queries."""

from __future__ import annotations

import hashlib
import logging
from typing import Optional

from .chunker import TextChunker
from .models import (
    Chunk,
    Document,
    DocumentStatus,
    RAGConfig,
    SearchResult,
)
from .store import RAGStore

logger = logging.getLogger(__name__)


class RAGEngine:
    """High-level interface for the RAG pipeline.

    Combines :class:`RAGStore` (persistence) and :class:`TextChunker`
    (splitting) to ingest documents, search for relevant chunks, and
    format context strings for downstream LLM consumption.
    """

    def __init__(
        self,
        store: Optional[RAGStore] = None,
        config: Optional[RAGConfig] = None,
    ) -> None:
        self.store = store or RAGStore()
        self.config = config or RAGConfig()
        self._chunker = TextChunker()

    # ------------------------------------------------------------------
    # Ingest
    # ------------------------------------------------------------------

    def ingest(self, title: str, source: str, content: str) -> Document:
        """Chunk *content*, persist the document and its chunks.

        Returns the created :class:`Document` with status ``indexed``.
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        doc = Document(
            title=title,
            source=source,
            content_hash=content_hash,
            status=DocumentStatus.processing,
        )
        self.store.add_document(doc)

        try:
            texts = self._chunker.chunk_text(
                text=content,
                strategy=self.config.strategy,
                chunk_size=self.config.chunk_size,
                overlap=self.config.chunk_overlap,
            )

            chunks = [
                Chunk(
                    document_id=doc.id,
                    content=text,
                    metadata={"title": title, "source": source},
                    position=idx,
                )
                for idx, text in enumerate(texts)
            ]

            self.store.add_chunks(chunks)
            self.store.update_document_status(
                doc.id,
                DocumentStatus.indexed,
                chunk_count=len(chunks),
            )
            doc.status = DocumentStatus.indexed
            doc.chunk_count = len(chunks)

            logger.info(
                "Ingested document %r (%s) — %d chunks",
                title,
                doc.id,
                len(chunks),
            )
        except Exception:
            self.store.update_document_status(doc.id, DocumentStatus.failed)
            doc.status = DocumentStatus.failed
            logger.exception(
                "Failed to ingest document %r (%s)",
                title,
                doc.id,
            )
            raise

        return doc

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
    ) -> list[SearchResult]:
        """Search chunks by keyword overlap and return ranked results.

        Scoring is based on the fraction of query terms found in each chunk
        (case-insensitive).  Only results meeting the configured
        ``similarity_threshold`` are returned.
        """
        limit = max_results or self.config.max_results
        query_terms = [t.lower() for t in query.strip().split() if t]
        if not query_terms:
            return []

        # Retrieve candidate chunks via text search (broader, OR-style).
        # We fetch more than needed so we can re-rank.
        candidates = self.store.search_chunks(query, limit=limit * 5)

        results: list[SearchResult] = []
        for chunk in candidates:
            score = self._keyword_score(chunk.content, query_terms)
            if score < self.config.similarity_threshold:
                continue
            doc = self.store.get_document(chunk.document_id)
            if doc is None:
                continue
            results.append(
                SearchResult(chunk=chunk, score=score, document=doc),
            )

        # Sort descending by score, then truncate.
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, document_id: str) -> bool:
        """Remove a document and all its chunks."""
        return self.store.delete_document(document_id)

    # ------------------------------------------------------------------
    # Context helper
    # ------------------------------------------------------------------

    def get_context(
        self,
        query: str,
        max_results: Optional[int] = None,
    ) -> str:
        """Search for relevant chunks and format them as an LLM context block.

        Returns a string suitable for injection into a system/user prompt.
        """
        results = self.search(query, max_results=max_results)
        if not results:
            return ""

        parts: list[str] = []
        for idx, result in enumerate(results, 1):
            header = f"[{idx}] {result.document.title} " f"(score: {result.score:.2f})"
            parts.append(f"{header}\n{result.chunk.content}")

        return "\n\n---\n\n".join(parts)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _keyword_score(text: str, query_terms: list[str]) -> float:
        """Fraction of *query_terms* found in *text* (case-insensitive)."""
        if not query_terms:
            return 0.0
        text_lower = text.lower()
        hits = sum(1 for term in query_terms if term in text_lower)
        return hits / len(query_terms)
