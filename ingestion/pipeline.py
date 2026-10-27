"""
CareerOS — Resume ingestion pipeline.

Orchestrates: load → split → embed → store in Chroma.
Resolves all paths relative to the repository root for Windows compatibility.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document

from core.config import get_settings
from ingestion.embeddings import get_embeddings
from ingestion.loaders import load_resume
from ingestion.splitter import split_documents

logger = logging.getLogger(__name__)

# Chroma collection dedicated to resumes
_RESUME_COLLECTION = "resume_collection"


def _get_chroma(collection_name: str = _RESUME_COLLECTION) -> Chroma:
    """Return the Chroma vector store for the given collection."""
    settings = get_settings()
    embeddings = get_embeddings()
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(settings.chroma_dir),
    )


def ingest_resume(
    file_path: str | Path,
    *,
    clear_existing: bool = True,
    collection_name: str = _RESUME_COLLECTION,
) -> dict:
    """
    Full ingestion pipeline for a single resume file.

    Parameters
    ----------
    file_path:
        Absolute or relative path to the resume (PDF or image).
    clear_existing:
        When True (default), delete any existing documents in the collection
        before adding the new resume, preventing accidental mixing.
    collection_name:
        Chroma collection to use. Override in tests to avoid polluting the
        production collection.

    Returns
    -------
    dict with keys: ``chunks_stored``, ``source``, ``pages``
    """
    path = Path(file_path).resolve()

    # 1. Load
    logger.info("Loading resume: %s", path)
    documents: list[Document] = load_resume(str(path))

    # 2. Split
    chunks: list[Document] = split_documents(documents)
    logger.info("Split into %d chunks", len(chunks))

    if not chunks:
        raise ValueError(
            f"Resume produced 0 chunks after splitting: {path}"
        )

    # 3. Get vector store
    store = _get_chroma(collection_name)

    # 4. Optionally clear existing data
    if clear_existing:
        try:
            existing = store.get()
            if existing and existing.get("ids"):
                store.delete(ids=existing["ids"])
                logger.info("Cleared %d existing chunks from collection", len(existing["ids"]))
        except Exception as exc:
            logger.warning("Could not clear existing chunks: %s", exc)

    # 5. Add new chunks
    store.add_documents(chunks)
    logger.info("Stored %d chunks in Chroma collection '%s'", len(chunks), collection_name)

    return {
        "chunks_stored": len(chunks),
        "source": str(path),
        "pages": len(documents),
    }


def get_retriever(collection_name: str = _RESUME_COLLECTION, k: int = 6):
    """
    Return a Chroma-backed retriever for the resume collection.

    Parameters
    ----------
    k : int
        Number of chunks to return per query.
    """
    store = _get_chroma(collection_name)
    return store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )


def get_resume_text(collection_name: str = _RESUME_COLLECTION) -> str:
    """
    Retrieve all stored resume text as a single concatenated string.
    Useful for semantic matching without a targeted query.
    """
    store = _get_chroma(collection_name)
    try:
        data = store.get()
        docs = data.get("documents", []) or []
        return " ".join(d for d in docs if d)
    except Exception as exc:
        logger.warning("Could not retrieve resume text: %s", exc)
        return ""


def has_resume(collection_name: str = _RESUME_COLLECTION) -> bool:
    """Return True if the Chroma collection contains at least one chunk."""
    store = _get_chroma(collection_name)
    try:
        data = store.get()
        return bool(data and data.get("ids"))
    except Exception:
        return False
