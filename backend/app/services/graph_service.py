import json
from uuid import uuid4


def upsert_graph_for_violation(db, asset: dict, violation: dict) -> None:
    asset_node = f"asset:{asset['id']}"
    platform_node = f"platform:{violation['platform'].lower().replace(' ', '-')}"
    suspect_node = f"suspect:{violation['suspect_id']}"
    domain = violation["url"].split("/")[2] if "://" in violation["url"] else "mock.platform"
    domain_node = f"domain:{domain}"

    nodes = [
        (asset_node, asset["id"], asset["title"], "asset", {"owner": asset.get("owner")}),
        (platform_node, asset["id"], violation["platform"], "platform", {}),
        (domain_node, asset["id"], domain, "domain", {}),
        (suspect_node, asset["id"], violation["title"], "suspect_content", {"url": violation["url"]}),
    ]
    for node in nodes:
        db.execute(
            """
            INSERT OR REPLACE INTO graph_nodes(id, asset_id, label, type, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (node[0], node[1], node[2], node[3], json.dumps(node[4])),
        )

    edges = [
        (asset_node, suspect_node, "MATCHED_AS", violation["confidence_overall"]),
        (suspect_node, platform_node, "PUBLISHED_ON", 1.0),
        (platform_node, domain_node, "HOSTED_BY", 1.0),
    ]
    for source, target, relation, weight in edges:
        edge_id = f"{source}->{relation}->{target}"
        db.execute(
            """
            INSERT OR REPLACE INTO graph_edges(id, asset_id, source, target, relation, weight)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (edge_id, asset["id"], source, target, relation, weight),
        )


def read_graph(db, asset_id: str) -> dict:
    nodes = [
        {**dict(row), "metadata": json.loads(row["metadata"])}
        for row in db.execute("SELECT * FROM graph_nodes WHERE asset_id = ?", (asset_id,))
    ]
    edges = [dict(row) for row in db.execute("SELECT * FROM graph_edges WHERE asset_id = ?", (asset_id,))]
    return {"asset_id": asset_id, "nodes": nodes, "edges": edges}
