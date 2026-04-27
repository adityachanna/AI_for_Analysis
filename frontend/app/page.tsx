import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <div className="scanline"></div>
      <div className="page">

        {/* Hero */}
        <section className="hero">
          <div className="hero-bg-glow"></div>
          <div>
            <p className="section-label">// Digital Asset Protection — Powered by Google AI</p>
            <h1>Sports IP Piracy Stops Here.</h1>
            <p style={{ fontSize: '1.125rem', maxWidth: '660px' }}>
              Every second, stolen sports footage is re-uploaded, re-encoded, and monetized without
              rights holders ever knowing. SentinelAI generates cryptographic DNA for every asset
              and runs a continuous AI cascade to detect every mutation — exact reposts, crops, overlays,
              screen captures — before they go viral.
            </p>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '2.5rem', flexWrap: 'wrap' }}>
              <Link href="/login" className="button">Protect Your Content →</Link>
              <Link href="/dashboard" className="button secondary">Live Demo</Link>
            </div>
          </div>
        </section>

        {/* Problem Statement */}
        <section style={{ marginTop: '5rem' }}>
          <p className="section-label">// The Problem</p>
          <div className="grid two" style={{ alignItems: 'start', gap: '3rem' }}>
            <div>
              <h2 style={{ marginBottom: '1rem' }}>Piracy Moves at Machine Speed</h2>
              <p>
                Sports broadcasters lose an estimated <strong style={{ color: 'var(--alert)' }}>$28 billion annually</strong> to
                digital piracy. A final highlight lands online and within minutes it exists on a dozen platforms
                in mutated forms — cropped, re-encoded, screen-captured with watermarks burned off.
                Traditional takedown workflows are manual, slow, and always one step behind.
              </p>
              <p>
                Rights holders need detection that matches the speed of infringement.
                SentinelAI matches it — and exceeds it.
              </p>
            </div>
            <div className="panel" style={{ padding: '1.5rem' }}>
              <p className="section-label" style={{ margin: 0, marginBottom: '1rem' }}>// Piracy Mutations SentinelAI Catches</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
                {([
                  ['exact_repost',           '1:1 re-upload, identical bytes'],
                  ['cropped_or_reencoded',   'Resolution, bitrate, aspect ratio changes'],
                  ['overlay_or_meme_edit',   'Captions, stickers, watermarks burned in'],
                  ['screen_recorded_recapture', 'Screen capture with glare artifacts'],
                  ['audio_or_semantic_reuse','Same commentary, different visual encoding'],
                ] as [string, string][]).map(([type, desc]) => (
                  <div key={type} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <span className={`mutation-badge ${type}`}>{type.replace(/_/g, ' ')}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>{desc}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Registration Pipeline */}
        <section style={{ marginTop: '5rem' }}>
          <p className="section-label">// Step 1 — Asset Registration</p>
          <h2 style={{ marginBottom: '0.5rem' }}>Digital DNA in Four Stages</h2>
          <p>
            Upload a video. SentinelAI builds a multi-layer fingerprint before the clip ever goes public —
            so any future copy can be matched against an immutable record.
          </p>
          <div className="pipeline">
            <div className="pipeline-step">
              <div className="pipeline-num">01 // SHA-256</div>
              <h4>Source Hash</h4>
              <p>Cryptographic fingerprint of raw bytes — the immutable ground-truth anchor for every scan.</p>
            </div>
            <div className="pipeline-step">
              <div className="pipeline-num">02 // SynthID</div>
              <h4>AI Watermark Token</h4>
              <p>Google SynthID-style token bound to asset identity — survives compression and re-encoding.</p>
            </div>
            <div className="pipeline-step">
              <div className="pipeline-num">03 // dHash + Gemini</div>
              <h4>Keyframes + Scene Context</h4>
              <p>Keyframes extracted at scene changes, perceptually hashed via dHash, then Gemini annotates each shot — entities, actions, visual context — for rich frame-level intelligence.</p>
            </div>
            <div className="pipeline-step">
              <div className="pipeline-num">04 // Gemini + Audio</div>
              <h4>Semantic Passport</h4>
              <p>Gemini generates the full content passport: scene-by-scene transcript, audio analysis, and semantic tags — all embedded into Pinecone for cross-mutation search.</p>
            </div>
          </div>
        </section>

        {/* Detection Cascade */}
        <section style={{ marginTop: '4rem' }}>
          <p className="section-label">// Step 2 — Continuous Detection</p>
          <h2 style={{ marginBottom: '0.5rem' }}>Three-Stage Cascade — Fast to Deep</h2>
          <p>
            Ordered pipeline — lightweight checks run first, Gemini is called only when needed.
            Every decision is logged with confidence scores and a full audit trail.
          </p>
          <div className="grid three" style={{ marginTop: '1.5rem' }}>
            <div className="panel">
              <h3 style={{ color: 'var(--accent)', marginBottom: '0.5rem', fontSize: '0.875rem' }}>// STAGE A — INSTANT</h3>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>dHash + SynthID</h2>
              <p style={{ fontSize: '0.875rem' }}>
                Hamming distance under 10 bits → instant confirmed match.
                SynthID token lookup catches exact reposts in milliseconds.
              </p>
            </div>
            <div className="panel">
              <h3 style={{ color: 'var(--accent-2)', marginBottom: '0.5rem', fontSize: '0.875rem' }}>// STAGE B — SEMANTIC</h3>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Semantic Embeddings</h2>
              <p style={{ fontSize: '0.875rem' }}>
                Gemini Embedding 2 (3072-dim) + Pinecone cosine similarity.
                Catches cropped, re-encoded, and overlay mutations that fool perceptual hashes.
              </p>
            </div>
            <div className="panel">
              <h3 style={{ color: 'var(--alert)', marginBottom: '0.5rem', fontSize: '0.875rem' }}>// STAGE C — AI REASONING</h3>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Gemini Reasoning</h2>
              <p style={{ fontSize: '0.875rem' }}>
                Gemini Flash describes the suspect clip and compares it to the content passport.
                Handles screen captures, audio-only reuse, and adversarial edits.
              </p>
            </div>
          </div>
        </section>

        {/* Graph Intelligence */}
        <section style={{ marginTop: '4rem', marginBottom: '5rem' }}>
          <p className="section-label">// Step 3 — Intelligence Layer</p>
          <div className="grid two" style={{ alignItems: 'start' }}>
            <div>
              <h2 style={{ marginBottom: '0.75rem' }}>Provenance Graph</h2>
              <p>
                Every confirmed match writes to a Neo4j Aura cloud graph. Nodes represent original assets,
                pirated clips, and platforms. Edges carry confidence scores and mutation labels —
                exposing the full distribution tree of illegal republishing.
              </p>
              <p>
                Gemini analyzes each graph cluster for risk level and recommends automated action:
                DMCA notice, escalation, or monitoring. One click generates a pre-filled takedown email.
              </p>
              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginTop: '1rem' }}>
                <span className="pill good">Asset Node</span>
                <span className="pill bad">Pirated Clip Node</span>
                <span className="pill warn">Platform Domain Node</span>
                <span className="pill">Confidence Edge</span>
              </div>
            </div>
            <div className="panel" style={{ padding: '1.5rem' }}>
              <p className="section-label" style={{ margin: 0, marginBottom: '1rem' }}>// Google AI Stack</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                {([
                  ['Gemini Flash',          'Content Passport generation, Stage C reasoning, graph risk analysis'],
                  ['Gemini Embedding 2',    '3072-dimensional semantic vectors for cross-mutation similarity search'],
                  ['Google SynthID',        'AI watermarking for provenance chain — survives re-encoding'],
                  ['Pinecone on GCP',       'Vector index for sub-second semantic search at scale'],
                  ['Cloud Run + GCS',       'Serverless deployment; all video assets stored in Firebase Storage'],
                  ['Neo4j Aura',            'Cloud graph DB for violation relationship mapping'],
                ] as [string, string][]).map(([tech, desc]) => (
                  <div key={tech} style={{ display: 'flex', gap: '0.75rem' }}>
                    <span style={{ fontSize: '0.65rem', fontFamily: 'Syncopate', color: 'var(--accent)', flexShrink: 0, paddingTop: '2px' }}>▸</span>
                    <div>
                      <strong style={{ fontSize: '0.8rem', color: 'var(--ink)' }}>{tech}</strong>
                      <p style={{ fontSize: '0.75rem', margin: '0.1rem 0 0', color: 'var(--muted)' }}>{desc}</p>
                    </div>
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
