"""
neo4j_service.py — Neo4j Aura integration for SentinelAI graph data.

Exports:
    get_driver()          – singleton Driver or None when Neo4j is disabled/unavailable
    upsert_node(...)      – MERGE a SentinelNode into Neo4j
    upsert_relationship(...)  – MERGE a typed relationship
    query_asset_graph(...)    – return (nodes, edges) dicts for an asset
    ensure_indexes(...)   – idempotent index creation on startup
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton driver
# ---------------------------------------------------------------------------
_driver = None
_driver_initialised = False


def get_driver():
    """Return a connected Neo4j Driver singleton, or None if unavailable."""
    global _driver, _driver_initialised
    if _driver_initialised:
        return _driver

    _driver_initialised = True
    try:
        from ..config import settings

        if not settings.neo4j_enabled:
            logger.info("Neo4j disabled (NEO4J_ENABLED=false) — graph will not be persisted to Neo4j.")
            return None

        if not settings.neo4j_password:
            logger.warning("NEO4J_PASSWORD is not set — Neo4j unavailable.")
            return None

        from neo4j import GraphDatabase  # type: ignore

        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        driver.verify_connectivity()
        logger.info("Neo4j driver connected to %s", settings.neo4j_uri)
        _driver = driver
    except Exception as exc:  # noqa: BLE001
        logger.warning("Neo4j connection failed — graph writes will be skipped. Reason: %s", exc)
        _driver = None

    return _driver


# ---------------------------------------------------------------------------
# Index management
# ---------------------------------------------------------------------------

_INDEXES = [
    "CREATE INDEX sentinel_node_id IF NOT EXISTS FOR (n:SentinelNode) ON (n.id)",
    "CREATE INDEX sentinel_node_asset IF NOT EXISTS FOR (n:SentinelNode) ON (n.asset_id)",
]


def ensure_indexes(driver=None) -> None:
    """Create required indexes on Neo4j (idempotent — safe to call on every startup)."""
    if driver is None:
        driver = get_driver()
    if driver is None:
        return
    try:
        from ..config import settings

        with driver.session(database=settings.neo4j_database) as session:
            for cypher in _INDEXES:
                session.run(cypher)
        logger.info("Neo4j indexes ensured.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Neo4j ensure_indexes failed: %s", exc)


# ---------------------------------------------------------------------------
# Node type → label mapping
# ---------------------------------------------------------------------------

_TYPE_LABEL: dict[str, str] = {
    "ASSET": "Asset",
    "SUSPECT": "Suspect",
    "DOMAIN": "Domain",
    "EVIDENCE": "Evidence",
}

# Relationship types that are valid
_VALID_RELATIONS = {"DETECTED_IN", "HOSTED_ON", "RIGHTS_INFRINGEMENT", "SUPPORTED_BY"}


# ---------------------------------------------------------------------------
# Cypher helpers
# ---------------------------------------------------------------------------

def _node_merge_cypher(node_type: str) -> str:
    """Return the MERGE cypher for a specific node type label."""
    type_label = _TYPE_LABEL.get(node_type, node_type.capitalize())
    return f"""
        MERGE (n:SentinelNode:{type_label} {{id: $id}})
        SET n.asset_id     = $asset_id,
            n.label        = $label,
            n.node_type    = $node_type,
            n.metadata_json = $metadata_json
    """


def _rel_merge_cypher(relation: str) -> str:
    """Return the MERGE cypher for a relationship type."""
    return f"""
        MATCH (s:SentinelNode {{id: $source_id}}), (t:SentinelNode {{id: $target_id}})
        MERGE (s)-[r:{relation} {{asset_id: $asset_id}}]->(t)
        SET r.weight = $weight
    """


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def upsert_node(
    driver,
    asset_id: str,
    node_id: str,
    label: str,
    node_type: str,
    metadata: dict,
) -> None:
    """MERGE a SentinelNode into Neo4j with the appropriate type label."""
    if driver is None:
        return
    try:
        from ..config import settings

        cypher = _node_merge_cypher(node_type)
        with driver.session(database=settings.neo4j_database) as session:
            session.run(
                cypher,
                id=node_id,
                asset_id=asset_id,
                label=label,
                node_type=node_type,
                metadata_json=json.dumps(metadata),
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Neo4j upsert_node failed for %s: %s", node_id, exc)


def upsert_relationship(
    driver,
    asset_id: str,
    source_id: str,
    target_id: str,
    relation: str,
    weight: float,
) -> None:
    """MERGE a typed relationship between two SentinelNodes."""
    if driver is None:
        return
    if relation not in _VALID_RELATIONS:
        logger.warning("Unknown relation type '%s' — skipping Neo4j edge.", relation)
        return
    try:
        from ..config import settings

        cypher = _rel_merge_cypher(relation)
        with driver.session(database=settings.neo4j_database) as session:
            session.run(
                cypher,
                source_id=source_id,
                target_id=target_id,
                asset_id=asset_id,
                weight=weight,
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Neo4j upsert_relationship failed (%s -[%s]-> %s): %s",
            source_id, relation, target_id, exc,
        )


def query_asset_graph(driver, asset_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Fetch all nodes and relationships for an asset from Neo4j.

    Returns:
        (nodes, edges) — each item is a plain dict matching the shape
        returned by the old SQLite graph queries so the API contract
        stays identical.
    """
    if driver is None:
        return [], []

    try:
        from ..config import settings

        cypher = """
            MATCH (n:SentinelNode {asset_id: $asset_id})
            OPTIONAL MATCH (n)-[r]->(m:SentinelNode {asset_id: $asset_id})
            RETURN n, r, m
        """
        nodes_by_id: dict[str, dict] = {}
        edges: list[dict] = {}  # type: ignore[assignment]
        edge_list: list[dict] = []

        with driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, asset_id=asset_id)
            for record in result:
                n = record["n"]
                r = record["r"]
                m = record["m"]

                # Collect source node
                if n is not None:
                    nid = n["id"]
                    if nid not in nodes_by_id:
                        nodes_by_id[nid] = _neo4j_node_to_dict(n)

                # Collect target node
                if m is not None:
                    mid = m["id"]
                    if mid not in nodes_by_id:
                        nodes_by_id[mid] = _neo4j_node_to_dict(m)

                # Collect relationship
                if r is not None:
                    edge = _neo4j_rel_to_dict(r, asset_id)
                    edge_key = f"{edge['source']}-{edge['relation']}-{edge['target']}"
                    if edge_key not in edges:
                        edges[edge_key] = edge  # type: ignore[index]
                        edge_list.append(edge)

        return list(nodes_by_id.values()), edge_list

    except Exception as exc:  # noqa: BLE001
        logger.warning("Neo4j query_asset_graph failed for asset %s: %s", asset_id, exc)
        return [], []


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _neo4j_node_to_dict(node) -> dict[str, Any]:
    """Convert a Neo4j Node object to the dict shape the API expects."""
    metadata: Any = {}
    raw_meta = node.get("metadata_json", "{}")
    try:
        metadata = json.loads(raw_meta) if raw_meta else {}
    except Exception:
        metadata = {}

    return {
        "id": node["id"],
        "asset_id": node["asset_id"],
        "label": node.get("label", ""),
        "type": node.get("node_type", ""),
        "metadata": metadata,
    }


def _neo4j_rel_to_dict(rel, asset_id: str) -> dict[str, Any]:
    """Convert a Neo4j Relationship object to the dict shape the API expects."""
    # neo4j-python-driver: rel.start_node, rel.end_node, rel.type, rel.items()
    props = dict(rel.items()) if hasattr(rel, "items") else {}
    source_id = rel.start_node["id"] if rel.start_node else ""
    target_id = rel.end_node["id"] if rel.end_node else ""
    relation = rel.type if hasattr(rel, "type") else props.get("relation", "")

    edge_id = f"edge-{source_id[:16]}-{relation}-{target_id[:16]}"
    return {
        "id": edge_id,
        "asset_id": asset_id,
        "source": source_id,
        "target": target_id,
        "relation": relation,
        "weight": float(props.get("weight", 0.0)),
    }
