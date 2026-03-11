# -*- coding: utf-8 -*-
"""Data models for the RAG module."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from prowlrbot.compat import StrEnum
from typing import Optional

from pydantic import BaseModel, Field


class ChunkingStrategy(StrEnum):
    """Strategy used to split documents into chunks."""

    fixed_size = "fixed_size"
    sentence = "sentence"
    paragraph = "paragraph"
    semantic = "semantic"


class DocumentStatus(StrEnum):
    """Processing status of a document."""

    pending = "pending"
    processing = "processing"
    indexed = "indexed"
    failed = "failed"


class Document(BaseModel):
    """A document ingested into the RAG store."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    title: str
    source: str  # file path or URL
    content_hash: str  # SHA-256 of original content
    chunk_count: int = 0
    status: DocumentStatus = DocumentStatus.pending
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


class Chunk(BaseModel):
    """A chunk of text belonging to a document."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    document_id: str
    content: str
    metadata: dict = Field(default_factory=dict)
    embedding: Optional[list[float]] = None
    position: int = 0


class SearchResult(BaseModel):
    """A search result pairing a chunk with its relevance score and parent document."""

    chunk: Chunk
    score: float
    document: Document


class RAGConfig(BaseModel):
    """Configuration for the RAG engine."""

    chunk_size: int = 512
    chunk_overlap: int = 64
    strategy: ChunkingStrategy = ChunkingStrategy.paragraph
    similarity_threshold: float = 0.7
    max_results: int = 5
