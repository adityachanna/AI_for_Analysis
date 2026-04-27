"""
pinecone_service.py — Pinecone vector search for SentinelAI.

Replaces the old FAISS-based local vector index.

All embedding vectors (asset passports + demo/suspect clips) are
upserted into the "radiant-alder" Pinecone serverless index.
Similarity search is used during scanning to rank suspect clips
against the registered asset embedding.

Exports:
    get_index()           – singleton Pinecone Index, or None if unavailable
    upsert_vector(...)    – upsert a single embedding with metadata
    query_similar(...)    – ANN search; returns list of {id, score, metadata}
    delete_asset(...)     – delete all vectors belonging to an asset_id
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

_index = None
_initialized = False


# ---------------------------------------------------------------------------
# Singleton index
# ---------------------------------------------------------------------------

def get_index():
    """Return a connected Pinecone Index singleton, or None if unavailable."""
    global _index, _initialized
    if _initialized:
        return _index

    _initialized = True
    try:
        from ..config import settings

        if not settings.pinecone_enabled:
            logger.info("Pinecone disabled (PINECONE_ENABLED=false).")
            return None

        if not settings.pinecone_api_key:
            logger.warning("PINECONE_API_KEY is not set — vector search unavailable.")
            return None

        from pinecone import Pinecone  # type: ignore

        pc = Pinecone(api_key=settings.pinecone_api_key)
        _index = pc.Index(settings.pinecone_index_name)
        # Quick connectivity check
        _index.describe_index_stats()
        logger.info("Pinecone connected to index '%s'.", settings.pinecone_index_name)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Pinecone connection failed — vector search disabled. Reason: %s", exc)
        _index = None

    return _index


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def upsert_vector(
    index,
    vector_id: str,
    embedding: list[float],
    metadata: dict[str, Any] | None = None,
    namespace: str = "sentinelai",
) -> None:
    """
    Upsert a single embedding vector into Pinecone.

    Parameters
    ----------
    index      : Pinecone Index object (from get_index()).
    vector_id  : Unique string ID for this vector.
    embedding  : List of floats (must match the index dimension).
    metadata   : Optional dict of filterable metadata fields.
    namespace  : Pinecone namespace to write into (default: 'sentinelai').
    """
    if index is None:
        return
    try:
        index.upsert(
            vectors=[
                {
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata or {},
                }
            ],
            namespace=namespace,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Pinecone upsert failed for vector '%s': %s", vector_id, exc)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def query_similar(
    index,
    embedding: list[float],
    top_k: int = 10,
    filter_dict: dict | None = None,
    namespace: str = "sentinelai",
    include_metadata: bool = True,
) -> list[dict[str, Any]]:
    """
    Find the top-k most similar vectors to the given embedding.

    Returns
    -------
    List of dicts, each with keys: id, score, metadata.
    """
    if index is None:
        return []
    try:
        kwargs: dict[str, Any] = {
            "vector": embedding,
            "top_k": top_k,
            "namespace": namespace,
            "include_metadata": include_metadata,
        }
        if filter_dict:
            kwargs["filter"] = filter_dict

        result = index.query(**kwargs)
        matches = result.get("matches") or []
        return [
            {
                "id": m["id"],
                "score": float(m.get("score", 0.0)),
                "metadata": m.get("metadata") or {},
            }
            for m in matches
        ]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Pinecone query failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def delete_asset(index, asset_id: str, namespace: str = "sentinelai") -> None:
    """Delete all vectors tagged with asset_id from the index."""
    if index is None:
        return
    try:
        index.delete(filter={"asset_id": {"$eq": asset_id}}, namespace=namespace)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Pinecone delete for asset '%s' failed: %s", asset_id, exc)
