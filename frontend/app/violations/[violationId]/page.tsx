"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ConfidenceBars } from "@/components/ConfidenceBars";
import { api, GraphData, Violation } from "@/lib/api";
import { PropagationGraph } from "@/components/PropagationGraph";

export default function ViolationPage({ params }: { params: { violationId: string } }) {
  const [violation, setViolation] = useState<Violation | null>(null);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .violation(params.violationId)
      .then(async (data) => {
        setViolation(data);
        setGraph(await api.graph(data.asset_id));
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load violation"));
  }, [params.violationId]);

  if (!violation) {
    return <div className="page">{error ? <p className="pill bad">{error}</p> : <p>Loading report...</p>}</div>;
  }

  return (
    <div className="page">
      <section className="panel">
        <div className="card-header">
          <div>
            <h1>{violation.title}</h1>
            <p>{violation.explanation}</p>
            <div className="meta-row">
              <span className={violation.status === "confirmed" ? "pill bad" : "pill warn"}>{violation.status}</span>
              <span className="pill">Stage {violation.stage}</span>
              <span className="pill">{violation.platform}</span>
              <span className="pill">{violation.mutation_type}</span>
            </div>
          </div>
          <Link className="button secondary" href={`/assets/${violation.asset_id}`}>
            Asset
          </Link>
        </div>
      </section>

      <section className="grid two" style={{ marginTop: 18 }}>
        <div className="panel">
          <h2>Evidence</h2>
          <p>
            Suspect URL: <a href={violation.url}>{violation.url}</a>
          </p>
          <p>Registered asset: {violation.asset?.title || violation.asset_id}</p>
          <ConfidenceBars violation={violation} />
        </div>
        <div className="panel">
          <h2>Propagation</h2>
          {graph && <PropagationGraph graph={graph} />}
        </div>
      </section>
    </div>
  );
}
