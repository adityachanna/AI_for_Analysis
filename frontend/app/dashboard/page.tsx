"use client";

import Link from "next/link";
import { useEffect, useRef, useState, FormEvent, DragEvent } from "react";
import { api, Asset, AuditSummary } from "@/lib/api";

export default function DashboardPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [audit, setAudit] = useState<AuditSummary | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = () => {
    Promise.all([api.assets(), api.audit()])
      .then(([assetData, auditData]) => { setAssets(assetData); setAudit(auditData); })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load dashboard"));
  };

  function pickFile(file: File) {
    if (file.size > 50 * 1024 * 1024) {
      setError(`File too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum is 50 MB.`);
      return;
    }
    setError("");
    setSelectedFile(file);
  }

  function onDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(true);
  }

  function onDragLeave() { setDragging(false); }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) pickFile(file);
  }

  function onFileInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) pickFile(file);
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile) { setError("Please select a video file."); return; }
    setLoading(true); setError(""); setUploadSuccess(false);
    const form = new FormData(event.currentTarget);
    form.set("file", selectedFile);
    try {
      await api.register(form);
      setUploadSuccess(true);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
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

            {/* Custom file drop zone */}
            <div style={{ marginBottom: '1rem' }}>
              <span style={{
                display: 'block', fontSize: '0.7rem', textTransform: 'uppercase',
                letterSpacing: '0.1em', color: 'var(--muted)', marginBottom: '0.5rem'
              }}>
                Video File (MP4 / MOV — max 50 MB)
              </span>
              <div
                onClick={() => fileInputRef.current?.click()}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
                style={{
                  border: `1px dashed ${dragging ? 'var(--accent)' : selectedFile ? 'var(--good)' : 'rgba(255,255,255,0.18)'}`,
                  background: dragging
                    ? 'rgba(136,255,255,0.05)'
                    : selectedFile
                      ? 'rgba(0,255,136,0.04)'
                      : 'rgba(255,255,255,0.02)',
                  borderRadius: '4px',
                  padding: '1.25rem 1rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}
              >
                {selectedFile ? (
                  <>
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--good)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    <span style={{ fontSize: '0.8rem', color: 'var(--good)', fontWeight: 600 }}>{selectedFile.name}</span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--muted)' }}>{(selectedFile.size / 1024 / 1024).toFixed(1)} MB · click to change</span>
                  </>
                ) : (
                  <>
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="16 16 12 12 8 16" />
                      <line x1="12" y1="12" x2="12" y2="21" />
                      <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
                    </svg>
                    <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                      {dragging ? 'Drop to select' : 'Drag & drop or click to browse'}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'rgba(139,139,155,0.6)' }}>MP4 · MOV · WebM — max 50 MB</span>
                  </>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="video/mp4,video/webm,video/quicktime,.m4v"
                style={{ display: 'none' }}
                onChange={onFileInputChange}
              />
            </div>

            <button
              disabled={loading || !selectedFile}
              type="submit"
              style={{ marginTop: '0.25rem', whiteSpace: 'normal', lineHeight: 1.4, padding: '0.875rem 1rem' }}
            >
              {loading ? "Generating Digital DNA…" : "Register Asset + Generate Suspect Clips"}
            </button>
          </form>

          {/* Pipeline Steps */}
          <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {[
              ['01', 'SHA-256 Source Hash'],
              ['02', 'SynthID Watermark Token'],
              ['03', 'Keyframe Extraction + dHash'],
              ['04', 'Gemini Context per Keyframe'],
              ['05', 'Semantic Passport + Audio'],
              ['06', '5x Suspect Clip Generation'],
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
