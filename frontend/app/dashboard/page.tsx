"use client";

import Link from "next/link";
import { useEffect, useState, FormEvent } from "react";
import { api, Asset, AuditSummary } from "@/lib/api";

export default function DashboardPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [audit, setAudit] = useState<AuditSummary | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = () => {
    Promise.all([api.assets(), api.audit()])
      .then(([assetData, auditData]) => {
        setAssets(assetData);
        setAudit(auditData);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load dashboard"));
  };

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      await api.register(form);
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ marginBottom: '0.5rem', fontSize: '3rem' }}>SYSTEM DEMO</h1>
          <p style={{ margin: 0 }}>Active detection matrix and asset registration.</p>
        </div>
      </div>
      
      {error && <div className="panel" style={{ borderColor: 'var(--alert)', backgroundColor: 'rgba(255, 0, 85, 0.05)', color: 'var(--alert)' }}>[ERROR]: {error}</div>}
      
      <div className="grid" style={{ gridTemplateColumns: '350px 1fr', alignItems: 'start', marginTop: '2rem' }}>
        {/* Upload Form */}
        <section className="panel" style={{ position: 'sticky', top: '100px' }}>
          <h3 style={{ color: 'var(--accent)', marginBottom: '1.5rem', fontSize: '1rem' }}>// REGISTER NEW ASSET</h3>
          <form style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }} onSubmit={onSubmit}>
            <label>
              Entity Title
              <input name="title" required placeholder="e.g. UFC 294 Highlight" />
            </label>
            <label>
              Category Designator
              <input name="sport" placeholder="Martial Arts" />
            </label>
            <label>
              Rights Holder ID
              <input name="owner" placeholder="UFC Inc." />
            </label>
            <label>
              Media Source
              <input name="file" required type="file" accept="video/mp4,video/webm,video/quicktime,.m4v" style={{ padding: '0.5rem', fontSize: '0.8rem' }} />
            </label>
            <button disabled={loading} type="submit" style={{ marginTop: '1rem' }}>
              {loading ? "PROCESSING..." : "REGISTER FOR SCAN"}
            </button>
          </form>
        </section>

        {/* Dashboard Matrix */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <section className="grid two">
            <div className="metric">
              <span>Indexed Assets</span>
              <strong>{assets.length}</strong>
            </div>
            <div className="metric">
              <span>Resolutions</span>
              <strong>{audit?.total_decisions || 0}</strong>
            </div>
          </section>
          
          <section style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <h3 style={{ fontSize: '1.5rem', color: 'var(--muted)', letterSpacing: '0.1em' }}><span style={{ color: 'var(--ink)' }}>[DATA]</span> REGISTERED ASSETS</h3>
            <div className="grid two">
              {assets.map((asset) => (
                <article className="card" key={asset.id} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div>
                    <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>{asset.title}</h3>
                    <p style={{ fontSize: '0.875rem', margin: 0, opacity: 0.8 }}>{asset.ai_summary || "Awaiting semantic analysis..."}</p>
                  </div>
                  
                  <div className="meta-row">
                    <span className="pill">{asset.keyframe_count} FRAMES</span>
                    <span className={asset.violation_count ? "pill bad" : "pill"}>
                      {asset.violation_count} INFRINGEMENTS
                    </span>
                  </div>
                  
                  <Link className="button secondary" href={`/assets/${asset.id}`} style={{ width: '100%', marginTop: 'auto' }}>
                    Access Terminals
                  </Link>
                </article>
              ))}
            </div>
            {!assets.length && (
              <div className="panel" style={{ textAlign: 'center', opacity: 0.5, borderStyle: 'dashed' }}>
                <p style={{ margin: 0 }}>NO DATA IN REGISTRY. AWAITING UPLOAD.</p>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
