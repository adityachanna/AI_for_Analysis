import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <div className="scanline"></div>
      <div className="page">
        <section className="hero">
          <div className="hero-bg-glow"></div>
          <div>
            <p className="section-label">// Aditya — SentinelAI Demo Platform</p>
            <h1>Sports IP Protection at Machine Scale</h1>
            <p style={{ fontSize: '1.125rem', maxWidth: '620px' }}>
              When official sports footage is published, SentinelAI immediately generates a cryptographic SynthID,
              extracts perceptual fingerprints, and builds a Gemini-powered semantic passport — then continuously
              hunts every corner of the web for unauthorized copies.
            </p>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '2.5rem', flexWrap: 'wrap' }}>
              <Link href="/login" className="button">Initialize System Access</Link>
              <Link href="/dashboard" className="button secondary">Demo Dashboard →</Link>
            </div>
          </div>
        </section>

        {/* Registration Pipeline */}
        <section style={{ marginTop: '5rem' }}>
          <p className="section-label">// Digital DNA Generation Pipeline</p>
          <h2 style={{ marginBottom: '0.5rem' }}>How the Shield Works</h2>
          <p>Every registered asset passes through a four-stage protection pipeline before any clip is ever scanned.</p>
          <div className="pipeline">
            <div className="pipeline-step">
              <div className="pipeline-num">01 // SHA-256</div>
              <h4>Source Hash</h4>
              <p>Cryptographic fingerprint of the raw file bytes — the ground truth anchor.</p>
            </div>
            <div className="pipeline-step">
              <div className="pipeline-num">02 // SynthID</div>
              <h4>Watermark Token</h4>
              <p>Simulated SynthID marker bound to asset ID + source hash for provenance chain.</p>
            </div>
            <div className="pipeline-step">
              <div className="pipeline-num">03 // dHash</div>
              <h4>Keyframe Fingerprints</h4>
              <p>Up to 12 perceptual hashes extracted from video keyframes — survive crop &amp; re-encode.</p>
            </div>
            <div className="pipeline-step">
              <div className="pipeline-num">04 // Gemini</div>
              <h4>Semantic Passport</h4>
              <p>AI-generated content passport: entities, actions, transcript, and scene-level embeddings.</p>
            </div>
          </div>
        </section>

        {/* Detection Pipeline */}
        <section style={{ marginTop: '4rem' }}>
          <p className="section-label">// The Sentry — Detection Cascade</p>
          <h2 style={{ marginBottom: '0.5rem' }}>Three-Stage Detection</h2>
          <p>Cost-ordered cascade — cheaper checks run first, AI only when needed.</p>
          <div className="grid three" style={{ marginTop: '1.5rem' }}>
            <div className="panel">
              <h3 style={{ color: 'var(--accent)', marginBottom: '0.5rem', fontSize: '0.875rem' }}>// STAGE A — FAST</h3>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>SynthID + dHash</h2>
              <p style={{ fontSize: '0.875rem' }}>Hamming distance &lt;10: instant confirmed match. SynthID token lookup for exact reposts.</p>
            </div>
            <div className="panel">
              <h3 style={{ color: 'var(--accent-2)', marginBottom: '0.5rem', fontSize: '0.875rem' }}>// STAGE B — DEEP</h3>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Semantic Embeddings</h2>
              <p style={{ fontSize: '0.875rem' }}>Cosine similarity on Gemini embeddings catches cropped, reencoded, and overlay mutations.</p>
            </div>
            <div className="panel">
              <h3 style={{ color: 'var(--alert)', marginBottom: '0.5rem', fontSize: '0.875rem' }}>// STAGE C — AI</h3>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Gemini Reasoning</h2>
              <p style={{ fontSize: '0.875rem' }}>Gemini 2.5 Pro describes the suspect and compares to semantic passport for uncertain cases.</p>
            </div>
          </div>
        </section>

        {/* Graph Intelligence */}
        <section style={{ marginTop: '4rem', marginBottom: '5rem' }}>
          <p className="section-label">// The Intelligence — Graph Analysis</p>
          <div className="grid two" style={{ alignItems: 'start' }}>
            <div>
              <h2 style={{ marginBottom: '0.5rem' }}>Provenance Graph</h2>
              <p>Every confirmed match populates a Neo4j-compatible graph. Nodes represent original assets, pirated clips, platforms, and domains. Edges carry confidence scores and mutation labels — exposing the full distribution tree of illegal republishing at a glance.</p>
              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginTop: '1.25rem' }}>
                <span className="pill good">Asset Node</span>
                <span className="pill warn">Pirated Clip Node</span>
                <span className="pill bad">Source Domain Node</span>
                <span className="pill">Confidence Edge</span>
              </div>
            </div>
            <div className="panel" style={{ padding: '1.5rem' }}>
              <p className="section-label" style={{ margin: 0, marginBottom: '1rem' }}>// Mutation Labels Detected</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
                {[
                  ['exact_repost', 'Identical re-upload — Stage A hit'],
                  ['cropped_or_reencoded', 'Scale/bitrate mutation — Stage B hit'],
                  ['overlay_or_meme_edit', 'Caption/sticker overlay — Stage B hit'],
                  ['screen_recorded_recapture', 'Screen capture with glare — Stage C'],
                  ['audio_or_semantic_reuse', 'Same commentary, different pixels — Stage C'],
                ].map(([type, desc]) => (
                  <div key={type} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <span className={`mutation-badge ${type}`}>{type.replace(/_/g, ' ')}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>{desc}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}
