"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ConfidenceBars } from "@/components/ConfidenceBars";
import { api, GraphData, Violation } from "@/lib/api";
import { PropagationGraph } from "@/components/PropagationGraph";

const MUTATION_LABELS: Record<string, string> = {
  exact_repost: "Exact Repost",
  cropped_or_reencoded: "Cropped / Re-encoded",
  overlay_or_meme_edit: "Overlay / Meme Edit",
  screen_recorded_recapture: "Screen Recapture",
  audio_or_semantic_reuse: "Audio / Semantic Reuse",
};

export default function ViolationPage({ params }: { params: { violationId: string } }) {
  const [violation, setViolation] = useState<Violation | null>(null);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [error, setError] = useState("");
  const [dmcaFired, setDmcaFired] = useState(false);

  useEffect(() => {
    api.violation(params.violationId)
      .then(async (data) => {
        setViolation(data);
        setGraph(await api.graph(data.asset_id));
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load violation"));
  }, [params.violationId]);

  function handleDMCA() {
    if (!violation) return;
    const subject = encodeURIComponent(`DMCA Takedown Notice — ${violation.title}`);
    const body = encodeURIComponent(
      `Dear Platform Abuse Team,\n\nWe are the rights holder of the content identified at:\n${violation.url}\n\n` +
      `This content is an unauthorized copy of our registered asset.\n` +
      `Mutation type: ${violation.mutation_type}\nConfidence: ${Math.round(violation.confidence_overall * 100)}%\n\n` +
      `We request immediate removal under DMCA § 512(c).\n\nSentinelAI Violation ID: ${violation.id}\n`
    );
    window.open(`mailto:abuse@${violation.platform.toLowerCase().replace(/\s+/g, '')}.com?subject=${subject}&body=${body}`);
    setDmcaFired(true);
  }

  if (!violation) {
    return (
      <div className="page">
        {error
          ? <div className="panel" style={{ color: 'var(--alert)' }}>[ERROR]: {error}</div>
          : <p style={{ color: 'var(--muted)' }}>Loading violation report...</p>
        }
      </div>
    );
  }

  const isConfirmed = violation.status === "confirmed";
  const confidencePct = Math.round(violation.confidence_overall * 100);

  return (
    <div className="page">
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <p className="section-label" style={{ margin: 0, marginBottom: '0.5rem' }}>// Violation Report</p>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', flexWrap: 'wrap' }}>
          <div>
            <h1 style={{ fontSize: 'clamp(1.5rem, 2.5vw, 2.25rem)', marginBottom: '0.5rem' }}>{violation.title}</h1>
            <div className="meta-row">
              <span className={isConfirmed ? "pill bad" : "pill warn"}>
                {violation.status.toUpperCase()}
              </span>
              <span className="pill">STAGE {violation.stage}</span>
              <span className="pill">{violation.platform}</span>
              <span className={`mutation-badge ${violation.mutation_type}`}>
                {MUTATION_LABELS[violation.mutation_type] || violation.mutation_type}
              </span>
            </div>
          </div>
          <div style={{ fontFamily: 'Syncopate, sans-serif', fontSize: '3.5rem', lineHeight: 1, color: isConfirmed ? 'var(--alert)' : 'var(--warn)', flexShrink: 0 }}>
            {confidencePct}%
          </div>
        </div>
      </div>

      {/* DMCA Alert Banner */}
      {isConfirmed && (
        <div className="panel" style={{
          borderColor: 'var(--alert)', background: 'rgba(255,0,85,0.06)',
          padding: '1.25rem', marginBottom: '1.5rem',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem'
        }}>
          <div>
            <strong style={{ color: 'var(--alert)', fontFamily: 'Syncopate, sans-serif', fontSize: '0.8rem', letterSpacing: '0.08em' }}>
              CONFIRMED INFRINGEMENT DETECTED
            </strong>
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.8rem' }}>
              Rights violation confirmed with {confidencePct}% confidence. Immediate takedown action recommended.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button className="danger" onClick={handleDMCA} style={{ gap: '0.5rem' }}>
              ⚡ Send DMCA Takedown
            </button>
            {dmcaFired && <span className="pill good">DMCA NOTICE DRAFTED</span>}
          </div>
        </div>
      )}

      {/* Evidence & Confidence */}
      <div className="grid two" style={{ marginBottom: '1.5rem' }}>
        <div className="panel">
          <p className="section-label" style={{ margin: 0, marginBottom: '1rem' }}>// Infringement Evidence</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div>
              <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>Infringing URL</div>
              <a href={violation.url} style={{ color: 'var(--accent)', fontSize: '0.875rem', wordBreak: 'break-all' }}>{violation.url}</a>
            </div>
            <div>
              <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>Platform</div>
              <strong style={{ fontSize: '0.95rem' }}>{violation.platform}</strong>
            </div>
            <div>
              <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>dHash Distance</div>
              <strong style={{ fontFamily: 'Syncopate, sans-serif', color: violation.dhash_distance < 10 ? 'var(--alert)' : violation.dhash_distance < 20 ? 'var(--warn)' : 'var(--muted)' }}>
                {violation.dhash_distance}/64
              </strong>
            </div>
            <div>
              <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>SynthID Match</div>
              <span className={violation.synthid_match ? "pill bad" : "pill"}>
                {violation.synthid_match ? "TOKEN FOUND" : "Not Detected"}
              </span>
            </div>
            <div>
              <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>AI Explanation</div>
              <p style={{ fontSize: '0.8rem', margin: 0 }}>{violation.explanation}</p>
            </div>
          </div>
        </div>

        <div className="panel">
          <p className="section-label" style={{ margin: 0, marginBottom: '1rem' }}>// Confidence Breakdown</p>
          <ConfidenceBars violation={violation} />

          <div className="action-row" style={{ marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid rgba(255,255,255,0.07)' }}>
            {isConfirmed && (
              <button className="danger" onClick={handleDMCA} style={{ fontSize: '0.7rem', padding: '0.625rem 1.25rem' }}>
                ⚡ DMCA Takedown
              </button>
            )}
            <Link className="button secondary" href={`/assets/${violation.asset_id}`} style={{ fontSize: '0.7rem', padding: '0.625rem 1.25rem' }}>
              Asset Console
            </Link>
            <button className="good" onClick={() => window.print()} style={{ fontSize: '0.7rem', padding: '0.625rem 1.25rem' }}>
              Export Report
            </button>
          </div>
        </div>
      </div>

      {/* Propagation Graph */}
      <div className="panel">
        <p className="section-label" style={{ margin: 0, marginBottom: '1rem' }}>// Propagation Graph — Distribution Network</p>
        {graph && <PropagationGraph graph={graph} />}
        {(!graph || !graph.nodes.length) && (
          <div className="empty">No graph data yet. Graph is built from confirmed violations.</div>
        )}
      </div>
    </div>
  );
}
