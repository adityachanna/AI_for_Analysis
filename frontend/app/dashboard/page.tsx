"use client";

import Link from "next/link";
import { useEffect, useState, FormEvent } from "react";
import { api, Asset, AuditSummary } from "@/lib/api";

export default function DashboardPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [audit, setAudit] = useState<AuditSummary | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  useEffect(() => { loadData(); }, []);

  const loadData = () => {
    Promise.all([api.assets(), api.audit()])
      .then(([assetData, auditData]) => { setAssets(assetData); setAudit(auditData); })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load dashboard"));
  };

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true); setError(""); setUploadSuccess(false);
    const form = new FormData(event.currentTarget);
    try {
      await api.register(form);
      setUploadSuccess(true);
      loadData();
      (event.target as HTMLFormElement).reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally { setLoading(false); }
  }

  const totalViolations = assets.reduce((sum, a) => sum + (a.violation_count || 0), 0);

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2.5rem' }}>
        <div>
          <p className="section-label" style={{ margin: 0, marginBottom: '0.5rem' }}>// Demo Control Terminal</p>
          <h1 style={{ marginBottom: '0.5rem', fontSize: '2.5rem' }}>Asset Registry</h1>
          <p style={{ margin: 0 }}>Upload a sports video, generate Digital DNA, and launch the detection pipeline.</p>
        </div>
      </div>

      {error && (
        <div className="panel" style={{ borderColor: 'var(--alert)', background: 'rgba(255,0,85,0.05)', color: 'var(--alert)', marginBottom: '1.5rem', padding: '1rem' }}>
          [ERROR]: {error}
        </div>
      )}
      {uploadSuccess && (
        <div className="panel" style={{ borderColor: 'var(--good)', background: 'rgba(0,255,136,0.05)', color: 'var(--good)', marginBottom: '1.5rem', padding: '1rem' }}>
          [SUCCESS]: Asset registered — Digital DNA generated and 5 demo suspect clips created.
        </div>
      )}

      <div className="grid" style={{ gridTemplateColumns: '360px 1fr', alignItems: 'start', gap: '2rem' }}>

        {/* Upload Panel */}
        <section className="panel" style={{ position: 'sticky', top: '90px' }}>
          <p className="section-label" style={{ margin: 0, marginBottom: '1.25rem' }}>// Register New Asset</p>
          <form style={{ display: 'flex', flexDirection: 'column' }} onSubmit={onSubmit}>
            <label>
              Asset Title
              <input name="title" required placeholder="e.g. Match Highlights Q4" />
            </label>
            <label>
              Sport Category
              <input name="sport" placeholder="Cricket, Football, MMA..." />
            </label>
            <label>
              Rights Holder
              <input name="owner" placeholder="Rights Holder Organization" />
            </label>
            <label>
              Video File (MP4 / MOV — max 50MB)
              <input name="file" required type="file" accept="video/mp4,video/webm,video/quicktime,.m4v" />
            </label>
            <button disabled={loading} type="submit" style={{ marginTop: '0.5rem' }}>
              {loading ? "Generating Digital DNA..." : "Register + Create Suspect Clips"}
            </button>
          </form>

          {/* Pipeline Steps */}
          <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {[
              ['01', 'SHA-256 Source Hash'],
              ['02', 'SynthID Watermark Token'],
              ['03', 'Keyframe dHash Fingerprints'],
              ['04', 'Gemini Semantic Passport'],
              ['05', '5x Suspect Clip Generation'],
            ].map(([num, label]) => (
              <div key={num} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', opacity: 0.6 }}>
                <span style={{ fontFamily: 'Syncopate', fontSize: '0.6rem', color: 'var(--accent)', flexShrink: 0 }}>{num}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Right Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Metrics */}
          <section className="grid three">
            <div className="metric">
              <span>Registered Assets</span>
              <strong>{assets.length}</strong>
            </div>
            <div className="metric" style={{ borderLeftColor: 'var(--alert)' }}>
              <span>Total Violations</span>
              <strong style={{ color: totalViolations > 0 ? 'var(--alert)' : 'inherit' }}>{totalViolations}</strong>
            </div>
            <div className="metric">
              <span>Scan Decisions</span>
              <strong>{audit?.total_decisions || 0}</strong>
            </div>
          </section>

          {/* Asset Cards */}
          <section>
            <p className="section-label">// Registered Assets — Click to Run Detection</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {assets.map((asset) => (
                <article className="card" key={asset.id}>
                  <div className="card-header">
                    <div style={{ flex: 1 }}>
                      <h3>{asset.title}</h3>
                      <p style={{ fontSize: '0.875rem', margin: '0.375rem 0 0', opacity: 0.8 }}>
                        {asset.ai_summary || "Awaiting semantic analysis..."}
                      </p>
                      <div className="meta-row">
                        <span className="pill">{asset.keyframe_count || 0} KEYFRAMES</span>
                        <span className="pill">{asset.sport || "SPORT"}</span>
                        <span className={asset.violation_count ? "pill bad" : "pill good"}>
                          {asset.violation_count || 0} VIOLATIONS
                        </span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-end' }}>
                      <Link className="button" href={`/assets/${asset.id}`}>
                        Detection Console →
                      </Link>
                    </div>
                  </div>
                </article>
              ))}
              {!assets.length && (
                <div className="empty">No assets in registry. Upload a video to begin.</div>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
