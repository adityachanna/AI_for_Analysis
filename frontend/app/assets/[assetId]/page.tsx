"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Asset, AuditSummary, GraphData, ScanResult, Violation } from "@/lib/api";
import { ConfidenceBars } from "@/components/ConfidenceBars";
import { PropagationGraph } from "@/components/PropagationGraph";

export default function AssetPage({ params }: { params: { assetId: string } }) {
  const [asset, setAsset] = useState<Asset | null>(null);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [audit, setAudit] = useState<AuditSummary | null>(null);
  const [scan, setScan] = useState<ScanResult | null>(null);
  const [suspectUrl, setSuspectUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.asset(params.assetId), api.violations(params.assetId), api.graph(params.assetId), api.audit(params.assetId)])
      .then(([assetData, violationData, graphData, auditData]) => {
        setAsset(assetData);
        setViolations(violationData);
        setGraph(graphData);
        setAudit(auditData);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load asset"));
  }, [params.assetId]);

  async function runScan() {
    setLoading(true);
    setError("");
    try {
      const result = await api.scan(params.assetId, suspectUrl);
      setScan(result);
      setViolations(await api.violations(params.assetId));
      setGraph(await api.graph(params.assetId));
      setAudit(await api.audit(params.assetId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setLoading(false);
    }
  }

  if (!asset) {
    return <div className="page">{error ? <p className="pill bad">{error}</p> : <p>Loading asset...</p>}</div>;
  }

  return (
    <div className="page">
      <section className="panel">
        <div className="card-header">
          <div>
            <h1>{asset.title}</h1>
            <p>{asset.ai_summary}</p>
            <div className="meta-row">
              <span className="pill">{asset.keyframes?.length || 0} fingerprints</span>
              <span className="pill warn">{asset.synthid_token}</span>
              <span className="pill">{String(asset.structured_analysis.provider || "fallback")}</span>
            </div>
          </div>
          <Link className="button secondary" href="/dashboard">
            Dashboard
          </Link>
        </div>
      </section>

      <section className="grid two" style={{ marginTop: 18 }}>
        <div className="metric">
          <span>Audit decisions</span>
          <strong>{audit?.total_decisions || 0}</strong>
        </div>
        <div className="metric">
          <span>Passport vector dims</span>
          <strong>{asset.passport_embedding?.length || 0}</strong>
        </div>
      </section>

      <section className="grid two" style={{ marginTop: 18 }}>
        <div className="panel">
          <h2>Scan mock platforms</h2>
          <label>
            Optional suspect URL
            <input value={suspectUrl} onChange={(event) => setSuspectUrl(event.target.value)} placeholder="https://example.com/suspect-clip" />
          </label>
          <button disabled={loading} onClick={runScan} style={{ marginTop: 14 }}>
            {loading ? "Scanning..." : "Run cascade scan"}
          </button>
          {error && <p className="pill bad">{error}</p>}
          {scan && (
            <div className="timeline" style={{ marginTop: 18 }}>
              {scan.stages.map((stage) => (
                <div className={`timeline-item ${stage.status}`} key={String(stage.suspect_id)}>
                  <strong>
                    Stage {stage.stage}: {stage.title}
                  </strong>
                  <p>
                    {stage.platform} - {stage.status} - dHash {stage.dhash_distance}/64 - visual {Math.round(Number(stage.visual_confidence) * 100)}% -
                    overall {Math.round(Number(stage.overall_confidence) * 100)}%
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="panel">
          <h2>Propagation graph</h2>
          {graph && <PropagationGraph graph={graph} />}
        </div>
      </section>

      <section className="panel" style={{ marginTop: 18 }}>
        <h2>Gemini Content Passport</h2>
        <p>{String(asset.structured_analysis.passport_text || "")}</p>
        <div className="passport-list">
          {asset.content_passport?.slice(0, 6).map((shot) => (
            <div className="passport-shot" key={`${shot.shot}-${shot.timestamp_ms}`}>
              <strong>Shot {shot.shot}</strong>
              <span>{Math.round(shot.timestamp_ms / 1000)}s</span>
              <p>{shot.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="panel" style={{ marginTop: 18 }}>
        <h2>Violations</h2>
        <div className="list">
          {violations.map((violation) => (
            <article className="card" key={violation.id}>
              <div className="card-header">
                <div>
                  <h3>{violation.title}</h3>
                  <p>{violation.explanation}</p>
                  <div className="meta-row">
                    <span className={violation.status === "confirmed" ? "pill bad" : "pill warn"}>{violation.status}</span>
                    <span className="pill">Stage {violation.stage}</span>
                    <span className="pill">{violation.mutation_type}</span>
                  </div>
                </div>
                <Link className="button" href={`/violations/${violation.id}`}>
                  Report
                </Link>
              </div>
              <ConfidenceBars violation={violation} />
            </article>
          ))}
          {!violations.length && <div className="empty">No violations yet. Run the cascade scan.</div>}
        </div>
      </section>
    </div>
  );
}
