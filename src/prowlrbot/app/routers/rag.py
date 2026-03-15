# -*- coding: utf-8 -*-
"""API routes for the RAG (Retrieval-Augmented Generation) module."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...rag.engine import RAGEngine
from ...rag.models import Document, SearchResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])

# Lazy-initialised singleton so the DB file is created only when first needed.
_engine: Optional[RAGEngine] = None


def _get_engine() -> RAGEngine:
    global _engine  # noqa: PLW0603
    if _engine is None:
        _engine = RAGEngine()
    return _engine


# ------------------------------------------------------------------
# Request / response schemas
# ------------------------------------------------------------------


class IngestRequest(BaseModel):
    title: str = Field(..., description="Document title")
    source: str = Field(..., description="File path or URL of the source")
    content: str = Field(..., description="Full document text to ingest")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: Optional[int] = Field(
        None,
        description="Maximum results to return",
    )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.post("/documents", status_code=201)
async def ingest_document(request: IngestRequest) -> Document:
    """Ingest a new document into the RAG store."""
    try:
        doc = _get_engine().ingest(
            title=request.title,
            source=request.source,
            content=request.content,
        )
    except Exception as exc:
        logger.exception("RAG ingest failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return doc


@router.get("/documents")
async def list_documents() -> list[Document]:
    """List all indexed documents."""
    return _get_engine().store.list_documents()


@router.get("/documents/{document_id}")
async def get_document(document_id: str) -> Document:
    """Get a single document by ID."""
    doc = _get_engine().store.get_document(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks."""
    deleted = _get_engine().delete(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": True}


@router.post("/search")
async def search(request: SearchRequest) -> list[SearchResult]:
    """Search the RAG index for relevant chunks."""
    return _get_engine().search(
        query=request.query,
        max_results=request.max_results,
    )


@router.get("/stats")
async def get_stats() -> dict:
    """Return summary statistics about the RAG store."""
    return _get_engine().store.get_stats()
