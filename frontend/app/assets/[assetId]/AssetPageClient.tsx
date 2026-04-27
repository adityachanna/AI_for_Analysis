"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Asset, AuditSummary, DemoClip, GraphData, GraphEdge, GraphNode, ScanResult, Violation } from "@/lib/api";
import { ConfidenceBars } from "@/components/ConfidenceBars";
import { PropagationGraph } from "@/components/PropagationGraph";

const MUTATION_LABELS: Record<string, string> = {
  exact_repost: "Exact Repost",
  cropped_or_reencoded: "Cropped / Re-encoded",
  overlay_or_meme_edit: "Overlay / Meme Edit",
  screen_recorded_recapture: "Screen Recapture",
  audio_or_semantic_reuse: "Audio / Semantic Reuse",
};

function PipelineStep({ num, label, done }: { num: string; label: string; done?: boolean }) {
  return (
    <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
      <span style={{
        fontFamily: 'Syncopate, sans-serif', fontSize: '0.55rem',
        color: done ? 'var(--good)' : 'var(--accent)', flexShrink: 0, letterSpacing: '0.1em'
      }}>{done ? '✓' : num}</span>
      <span style={{
        fontSize: '0.7rem', color: done ? 'var(--ink)' : 'var(--muted)',
        textTransform: 'uppercase', letterSpacing: '0.06em',
        textDecoration: done ? 'none' : 'none'
      }}>{label}</span>
    </div>
  );
}

export default function AssetPage({ params }: { params: { assetId: string } }) {
  const [asset, setAsset] = useState<Asset | null>(null);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [audit, setAudit] = useState<AuditSummary | null>(null);
  const [scan, setScan] = useState<ScanResult | null>(null);
  const [demoClips, setDemoClips] = useState<DemoClip[]>([]);
  const [loading, setLoading] = useState(false);
  const [scanStep, setScanStep] = useState(0);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<'scan' | 'clips' | 'passport' | 'graph'>('clips');

  useEffect(() => {
    Promise.all([
      api.asset(params.assetId),
      api.violations(params.assetId),
      api.graph(params.assetId),
      api.audit(params.assetId),
    ])
      .then(([assetData, violationData, graphData, auditData]) => {
        setAsset(assetData);
        setViolations(violationData);
        setGraph(graphData);
        setAudit(auditData);
        setDemoClips(assetData.demo_clips || []);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load asset"));
  }, [params.assetId]);

  const SCAN_STEPS = [
    "Stage A — dHash Hamming Distance",
    "Stage B — Semantic Embedding Search",
    "Stage C — Gemini AI Reasoning",
    "Persisting violations to graph…",
  ];

  async function runScan() {
    setLoading(true); setScanStep(0); setError("");
    const stepInterval = setInterval(() => {
      setScanStep((s) => (s < SCAN_STEPS.length - 1 ? s + 1 : s));
    }, 2200);
    try {
      const result = await api.scan(params.assetId);
      clearInterval(stepInterval);
      setScan(result);
      const [newViolations, newGraph, newAudit] = await Promise.all([
        api.violations(params.assetId),
        api.graph(params.assetId),
        api.audit(params.assetId),
      ]);
      setViolations(newViolations);
      setGraph(newGraph);
      setAudit(newAudit);
      setActiveTab('scan');
    } catch (err) {
      clearInterval(stepInterval);
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally { setLoading(false); setScanStep(0); }
  }

  function handleDMCA(violation: Violation) {
    const subject = encodeURIComponent(`DMCA Takedown Notice — ${violation.title}`);
    const body = encodeURIComponent(
      `Dear Platform Abuse Team,\n\nWe are the rights holder of the content identified at:\n${violation.url}\n\n` +
      `This content is an unauthorized copy of our registered asset.\n` +
      `Mutation type: ${violation.mutation_type}\nConfidence: ${Math.round(violation.confidence_overall * 100)}%\n\n` +
      `We request immediate removal under DMCA § 512(c).\n\nSentinelAI Violation ID: ${violation.id}\n`
    );
    window.open(`mailto:abuse@${violation.platform.toLowerCase().replace(/\s+/g, '')}.com?subject=${subject}&body=${body}`);
  }

  if (!asset) {
    return (
      <div className="page">
        {error
          ? <div className="panel" style={{ color: 'var(--alert)' }}>[ERROR]: {error}</div>
          : <p style={{ color: 'var(--muted)' }}>Loading asset data...</p>
        }
      </div>
    );
  }

  const pipelineDone = {
    hash: !!asset.source_hash,
    synthid: !!asset.synthid_token,
    keyframes: (asset.keyframes?.length || 0) > 0,
    gemini: !!(asset.structured_analysis?.passport_text),
    clips: demoClips.length > 0,
  };

  const tabs: Array<{ id: 'scan' | 'clips' | 'passport' | 'graph'; label: string }> = [
    { id: 'clips', label: `Suspect Clips (${demoClips.length})` },
    { id: 'scan', label: `Detection Results${scan ? ` (${scan.stages.length})` : ''}` },
    { id: 'passport', label: 'Semantic Passport' },
    { id: 'graph', label: 'Propagation Graph' },
  ];

  return (
    <div className="page">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', gap: '1rem' }}>
        <div>
          <p className="section-label" style={{ margin: 0, marginBottom: '0.5rem' }}>// Detection Console</p>
          <h1 style={{ fontSize: 'clamp(1.5rem, 3vw, 2.5rem)', marginBottom: '0.5rem' }}>{asset.title}</h1>
          <p style={{ margin: 0, fontSize: '0.9rem' }}>{asset.ai_summary}</p>
          <div className="meta-row">
            {asset.sport && <span className="pill">{asset.sport}</span>}
            <span className="pill">{asset.keyframes?.length || 0} KEYFRAMES</span>
            <span className="pill warn" style={{ fontFamily: 'monospace', fontSize: '0.65rem' }}>{asset.synthid_token?.slice(0, 24)}...</span>
            <span className={violations.length > 0 ? "pill bad" : "pill good"}>{violations.length} VIOLATIONS</span>
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-end', flexShrink: 0 }}>
          <button onClick={runScan} disabled={loading} style={{ minWidth: '220px' }}>
            {loading ? `⟳ ${SCAN_STEPS[scanStep]}` : "Run Detection Pipeline"}
          </button>
          <Link href="/dashboard" className="button secondary" style={{ minWidth: '200px' }}>
            ← Back to Registry
          </Link>
        </div>
      </div>

      {error && (
        <div className="panel" style={{ borderColor: 'var(--alert)', background: 'rgba(255,0,85,0.05)', color: 'var(--alert)', marginBottom: '1.5rem', padding: '1rem' }}>
          [ERROR]: {error}
        </div>
      )}

      <div className="grid" style={{ gridTemplateColumns: '220px 1fr', gap: '2rem', alignItems: 'start' }}>

        {/* Left Sidebar: pipeline status */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', position: 'sticky', top: '90px' }}>
          <div className="panel" style={{ padding: '1.25rem' }}>
            <p className="section-label" style={{ margin: 0, marginBottom: '1rem' }}>// Digital DNA</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
              <PipelineStep num="01" label="Source Hash" done={pipelineDone.hash} />
              <PipelineStep num="02" label="SynthID Token" done={pipelineDone.synthid} />
              <PipelineStep num="03" label="dHash Frames" done={pipelineDone.keyframes} />
              <PipelineStep num="04" label="Gemini Passport" done={pipelineDone.gemini} />
              <PipelineStep num="05" label="Suspect Clips" done={pipelineDone.clips} />
            </div>
          </div>

          <div className="panel" style={{ padding: '1.25rem' }}>
            <p className="section-label" style={{ margin: 0, marginBottom: '1rem' }}>// Registry Stats</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div>
                <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.2rem' }}>Scan Decisions</div>
                <div style={{ fontFamily: 'Syncopate, sans-serif', fontSize: '1.5rem', color: 'var(--ink)' }}>{audit?.total_decisions || 0}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.2rem' }}>Graph Nodes</div>
                <div style={{ fontFamily: 'Syncopate, sans-serif', fontSize: '1.5rem', color: 'var(--ink)' }}>{graph?.nodes.length || 0}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.2rem' }}>Graph Edges</div>
                <div style={{ fontFamily: 'Syncopate, sans-serif', fontSize: '1.5rem', color: 'var(--ink)' }}>{graph?.edges.length || 0}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div>
          {/* Tabs */}
          <div style={{ display: 'flex', gap: '0', marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  background: 'transparent', border: 'none', color: activeTab === tab.id ? 'var(--ink)' : 'var(--muted)',
                  borderBottom: activeTab === tab.id ? '2px solid var(--accent)' : '2px solid transparent',
                  padding: '0.75rem 1.25rem', cursor: 'pointer', fontFamily: 'Syncopate, sans-serif',
                  fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em',
                  transition: 'all 0.2s', transform: 'none', boxShadow: 'none',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab: Suspect Clips */}
          {activeTab === 'clips' && (
            <div>
              <p className="section-label">// Auto-generated Suspect Clips — Different Mutation Applied to Each</p>
              {demoClips.length === 0 && <div className="empty">No suspect clips generated yet.</div>}
              <div className="grid two">
                {demoClips.map((clip) => (
                  <div className="clip-card" key={clip.id}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem' }}>
                      <div>
                        <span className={`mutation-badge ${clip.mutation_type}`}>
                          {MUTATION_LABELS[clip.mutation_type] || clip.mutation_type}
                        </span>
                        <h3 style={{ marginTop: '0.625rem', fontSize: '0.9rem' }}>{clip.title}</h3>
                        <p style={{ fontSize: '0.75rem', margin: '0.3rem 0 0', color: 'var(--muted)' }}>{clip.platform}</p>
                      </div>
                      <div className="distance-ring" title="dHash Hamming Distance">
                        {clip.actual_distance ?? '—'}
                      </div>
                    </div>
                    <div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--muted)', margin: 0 }}>
                        {clip.ai_details?.description?.slice(0, 160)}...
                      </p>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                        Filters applied:
                      </span>
                      {(clip.transform_manifest?.filters as string[] || []).map((f: string) => (
                        <span key={f} className="pill" style={{ fontSize: '0.6rem', padding: '0.15rem 0.5rem' }}>{f}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab: Detection Results */}
          {activeTab === 'scan' && (
            <div>
              <p className="section-label">// Cascade Detection Pipeline Results</p>
              {!scan && (
                <div className="empty" style={{ marginBottom: '1.5rem' }}>
                  Click "Run Detection Pipeline" to scan all 5 suspect clips through the A → B → C cascade.
                </div>
              )}
              {scan && (
                <div className="timeline">
                  {scan.stages.map((stage, i) => {
                    const status = String(stage.status);
                    const overall = Number(stage.overall_confidence);
                    const stageLabel = `Stage ${String(stage.stage)} — ${String(stage.stage) === 'A' ? 'dHash' : String(stage.stage) === 'B' ? 'Embedding' : 'Gemini'}`;
                    return (
                      <div className={`timeline-item ${status}`} key={i}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                          <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.4rem' }}>
                              <span className="stage-badge">{stageLabel}</span>
                              <strong style={{ textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                                {String(stage.title)}
                              </strong>
                            </div>
                            <p style={{ margin: 0, fontSize: '0.8rem' }}>
                              Platform: <strong style={{ color: 'var(--ink)' }}>{String(stage.platform)}</strong>
                              {' · '}dHash distance: <strong style={{ color: 'var(--ink)' }}>{String(stage.dhash_distance)}/64</strong>
                              {' · '}Visual: <strong style={{ color: 'var(--ink)' }}>{Math.round(Number(stage.visual_confidence) * 100)}%</strong>
                              {' · '}Mutation: <strong style={{ color: 'var(--ink)' }}>
                                {MUTATION_LABELS[String(stage.mutation_type)] || String(stage.mutation_type)}
                              </strong>
                            </p>
                          </div>
                          <div style={{ textAlign: 'right', flexShrink: 0 }}>
                            <div style={{
                              fontFamily: 'Syncopate, sans-serif', fontSize: '1.25rem',
                              color: status === 'confirmed' ? 'var(--alert)' : status === 'probable' ? 'var(--warn)' : 'var(--muted)'
                            }}>
                              {Math.round(overall * 100)}%
                            </div>
                            <span className={`pill ${status === 'confirmed' ? 'bad' : status === 'probable' ? 'warn' : ''}`}>
                              {status.toUpperCase()}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {violations.length > 0 && (
                <div style={{ marginTop: '2rem' }}>
                  <p className="section-label">// Confirmed / Probable Violations</p>
                  <div className="list">
                    {violations.map((violation) => (
                      <article className="card" key={violation.id}>
                        <div className="card-header">
                          <div style={{ flex: 1 }}>
                            <h3 style={{ fontSize: '0.95rem' }}>{violation.title}</h3>
                            <p style={{ fontSize: '0.8rem', margin: '0.3rem 0 0' }}>{violation.explanation}</p>
                            <div className="meta-row">
                              <span className={violation.status === "confirmed" ? "pill bad" : "pill warn"}>
                                {violation.status.toUpperCase()}
                              </span>
                              <span className="pill">STAGE {violation.stage}</span>
                              <span className={`mutation-badge ${violation.mutation_type}`} style={{ borderRadius: '999px', padding: '0.2rem 0.6rem' }}>
                                {MUTATION_LABELS[violation.mutation_type] || violation.mutation_type}
                              </span>
                            </div>
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-end', flexShrink: 0 }}>
                            <div style={{ fontFamily: 'Syncopate, sans-serif', fontSize: '1.75rem', color: violation.status === 'confirmed' ? 'var(--alert)' : 'var(--warn)' }}>
                              {Math.round(violation.confidence_overall * 100)}%
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                              <button className="danger" onClick={() => handleDMCA(violation)} style={{ padding: '0.5rem 1rem', fontSize: '0.65rem' }}>
                                ⚡ DMCA
                              </button>
                              <Link className="button secondary" href={`/violations/${violation.id}`} style={{ padding: '0.5rem 0.875rem', fontSize: '0.65rem' }}>
                                Full Report
                              </Link>
                            </div>
                          </div>
                        </div>
                        <ConfidenceBars violation={violation} />
                      </article>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tab: Semantic Passport */}
          {activeTab === 'passport' && (
            <div>
              <p className="section-label">// Gemini Content Passport — AI-Generated Semantic Fingerprint</p>
              <div className="panel" style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ marginBottom: '0.75rem' }}>Passport Text</h3>
                <p style={{ fontStyle: 'italic', fontSize: '0.9rem' }}>
                  {String(asset.structured_analysis?.passport_text || "No passport generated yet.")}
                </p>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '1rem' }}>
                  {(asset.structured_analysis?.semantic_tags as string[] || []).map((tag: string) => (
                    <span key={tag} className="pill" style={{ fontSize: '0.65rem' }}>{tag}</span>
                  ))}
                </div>
              </div>
              <p className="section-label">// Keyframe Shot-by-Shot Analysis</p>
              <div className="passport-list">
                {asset.content_passport?.slice(0, 8).map((shot) => (
                  <div className="passport-shot" key={`${shot.shot}-${shot.timestamp_ms}`}>
                    <strong>Shot {shot.shot}</strong>
                    <span>@ {(shot.timestamp_ms / 1000).toFixed(1)}s</span>
                    <p>{shot.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab: Graph */}
          {activeTab === 'graph' && (
            <div>
              <p className="section-label">// Provenance Propagation Graph — Neo4j Compatible Data Model</p>
              <div className="panel">
              {graph && graph.nodes.length > 0 && graph.gemini_analysis?.risk_level && (
                <div style={{ marginBottom: '1.5rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <p className="section-label" style={{ margin: 0, marginBottom: '0.75rem' }}>// Gemini Graph Risk Analysis</p>
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                    <span className={`pill ${
                      graph.gemini_analysis.risk_level === 'CRITICAL' ? 'bad' :
                      graph.gemini_analysis.risk_level === 'HIGH' ? 'bad' :
                      graph.gemini_analysis.risk_level === 'MEDIUM' ? 'warn' : 'good'
                    }`} style={{ fontSize: '0.7rem' }}>RISK: {graph.gemini_analysis.risk_level}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--ink)' }}>{graph.gemini_analysis.recommended_action}</span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--muted)', margin: '0 0 0.5rem' }}>{graph.gemini_analysis.distribution_fingerprint}</p>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {(graph.gemini_analysis.patterns || []).map((p, i) => (
                      <span key={i} className="pill" style={{ fontSize: '0.65rem' }}>{p}</span>
                    ))}
                  </div>
                </div>
              )}
              {graph && <PropagationGraph graph={graph} />}
                {(!graph || !graph.nodes.length) && (
                  <div className="empty">Run the detection pipeline to generate graph data.</div>
                )}
              </div>
              {graph && graph.nodes.length > 0 && (
                <div style={{ marginTop: '1.5rem' }}>
                  <p className="section-label">// Graph Node Inventory</p>
                  <div className="grid three">
                    {graph.nodes.map((node: GraphNode) => (
                      <div key={node.id} style={{
                        background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.07)',
                        padding: '0.875rem', display: 'flex', flexDirection: 'column', gap: '0.35rem'
                      }}>
                        <span className={`pill ${
                          node.type === 'ASSET' ? 'good' :
                          node.type === 'SUSPECT' ? 'bad' :
                          node.type === 'DOMAIN' ? 'warn' : ''
                        }`} style={{ alignSelf: 'flex-start', fontSize: '0.6rem' }}>
                          {node.type}
                        </span>
                        <strong style={{ fontSize: '0.875rem' }}>{node.label}</strong>
                      </div>
                    ))}
                  </div>
                  {graph.edges.length > 0 && (
                    <div style={{ marginTop: '1rem' }}>
                      <p className="section-label">// Graph Edges (Relationships)</p>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {graph.edges.map((edge: GraphEdge) => (
                          <div key={edge.id} style={{
                            display: 'flex', gap: '0.75rem', alignItems: 'center',
                            fontSize: '0.8rem', padding: '0.5rem 0.75rem',
                            background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)'
                          }}>
                            <span style={{ color: 'var(--muted)' }}>{edge.source.slice(0, 16)}...</span>
                            <span style={{ color: 'var(--accent)' }}>—[ {edge.relation} ]→</span>
                            <span style={{ color: 'var(--muted)' }}>{edge.target.slice(0, 16)}...</span>
                            <span className={`pill ${edge.weight > 0.7 ? 'bad' : edge.weight > 0.4 ? 'warn' : ''}`} style={{ marginLeft: 'auto' }}>
                              {Math.round(edge.weight * 100)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
