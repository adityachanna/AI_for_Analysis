"""
graph_service.py — SentinelAI graph persistence layer (Neo4j-backed).

All graph data (nodes + relationships) is stored in Neo4j Aura.
SQLite is no longer used for graph data; the `graph_nodes` /
`graph_edges` tables in db.py are kept for schema-migration safety but
are no longer read or written by this service.
"""

import json
import logging
from typing import Any

from ..models import GraphResponse
from . import neo4j_service

logger = logging.getLogger(__name__)


def upsert_graph_for_violation(db, asset: dict, violation: dict) -> None:
    """
    Persist nodes and relationships for a detected violation to Neo4j.

    Parameters
    ----------
    db      : SQLite connection (kept for API compatibility; not used for graph).
    asset   : Asset row dict (must contain at least 'id', 'title').
    violation : Violation row dict.
    """
    driver = neo4j_service.get_driver()

    asset_id = asset["id"]
    suspect_id = violation["suspect_id"]
    platform = violation["platform"]
    confidence = float(violation.get("confidence_overall", 0.0))
    mutation_type = violation.get("mutation_type", "unknown")

    platform_slug = platform.lower().replace(" ", "-")
    domain_id = f"domain-{platform_slug}"

    # ------------------------------------------------------------------ nodes
    try:
        neo4j_service.upsert_node(
            driver, asset_id, asset_id,
            label=asset.get("title", "Registered Asset"),
            node_type="ASSET",
            metadata={
                "source_hash": asset.get("source_hash", ""),
                "owner_uid":   asset.get("owner_uid", ""),
                "gcs_uri":     asset.get("gcs_uri", ""),
            },
        )

        neo4j_service.upsert_node(
            driver, asset_id, suspect_id,
            label=violation.get("title", "Pirated Clip"),
            node_type="SUSPECT",
            metadata={
                "platform":           platform,
                "url":                violation.get("url", ""),
                "mutation_type":      mutation_type,
                "confidence_overall": confidence,
                "stage":              violation.get("stage", "A"),
                "status":             violation.get("status", "probable"),
            },
        )

        neo4j_service.upsert_node(
            driver, asset_id, domain_id,
            label=platform,
            node_type="DOMAIN",
            metadata={
                "platform": platform,
                "slug":     platform_slug,
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Neo4j node upsert failed for asset %s: %s", asset_id, exc)

    # --------------------------------------------------------------- edges
    try:
        # ASSET → SUSPECT: DETECTED_IN
        neo4j_service.upsert_relationship(
            driver, asset_id,
            source_id=asset_id,
            target_id=suspect_id,
            relation="DETECTED_IN",
            weight=confidence,
        )

        # SUSPECT → DOMAIN: HOSTED_ON
        neo4j_service.upsert_relationship(
            driver, asset_id,
            source_id=suspect_id,
            target_id=domain_id,
            relation="HOSTED_ON",
            weight=1.0,
        )

        # ASSET → DOMAIN: RIGHTS_INFRINGEMENT (high-confidence only)
        if confidence > 0.85:
            neo4j_service.upsert_relationship(
                driver, asset_id,
                source_id=asset_id,
                target_id=domain_id,
                relation="RIGHTS_INFRINGEMENT",
                weight=confidence,
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Neo4j edge upsert failed for asset %s: %s", asset_id, exc)

    # ------------------------------------------------- evidence from AI metadata
    graph_metadata = violation.get("graph_metadata") or {}
    if isinstance(graph_metadata, str):
        try:
            graph_metadata = json.loads(graph_metadata)
        except Exception:
            graph_metadata = {}

    ai_summary = graph_metadata.get("ai_summary", "")
    observable_entities = graph_metadata.get("observable_entities", [])
    semantic_tags = graph_metadata.get("semantic_tags", [])

    if ai_summary or observable_entities or semantic_tags:
        evidence_id = f"evidence-{suspect_id}"
        try:
            neo4j_service.upsert_node(
                driver, asset_id, evidence_id,
                label=f"AI Evidence: {mutation_type}",
                node_type="EVIDENCE",
                metadata={
                    "ai_summary":    ai_summary,
                    "entities":      observable_entities,
                    "semantic_tags": semantic_tags,
                    "mutation_type": mutation_type,
                },
            )
            neo4j_service.upsert_relationship(
                driver, asset_id,
                source_id=suspect_id,
                target_id=evidence_id,
                relation="SUPPORTED_BY",
                weight=confidence,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Neo4j evidence upsert failed for suspect %s: %s", suspect_id, exc)


def read_graph(db, asset_id: str) -> GraphResponse:
    """
    Return the provenance graph for an asset.

    Reads from Neo4j. If Neo4j is unavailable or returns nothing,
    returns an empty graph (SQLite graph tables are no longer populated).
    """
    driver = neo4j_service.get_driver()
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    try:
        nodes, edges = neo4j_service.query_asset_graph(driver, asset_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Neo4j read_graph failed for asset %s: %s", asset_id, exc)

    gemini_analysis: dict[str, Any] = {}
    try:
        from .gemini_service import analyze_graph_with_gemini
        gemini_analysis = analyze_graph_with_gemini(nodes, edges)
    except Exception as exc:
        logger.warning("Graph Gemini analysis failed: %s", exc)

    return GraphResponse(
        asset_id=asset_id,
        nodes=nodes,
        edges=edges,
        gemini_analysis=gemini_analysis,
    )
