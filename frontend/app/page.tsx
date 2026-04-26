import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <div className="scanline"></div>
      <div className="page">
        <section className="hero">
          <div className="hero-bg-glow"></div>
          <div>
            <h1>The Apex of Media Rights Protection</h1>
            <p>
              SentinelAI utilizes synthetic ID continuity modeling and advanced Gemini semantic analysis to identify illicit reproductions of official sports broadcasting with unparalleled accuracy. Stop piracy at the root of distribution.
            </p>
            <div style={{ display: 'flex', gap: '20px', marginTop: '40px' }}>
              <Link href="/login" className="button">
                System Access
              </Link>
              <Link href="https://github.com" className="button secondary">
                Documentation
              </Link>
            </div>
          </div>
          
          <div className="grid three" style={{ marginTop: '80px' }}>
            <div className="panel">
              <h3 style={{ color: 'var(--accent)', marginBottom: '1rem', fontSize: '0.875rem' }}>// STAGE 01</h3>
              <h2>Kinematic Fingerprinting</h2>
              <p style={{ fontSize: '0.875rem' }}>Extracting deterministic keyframes to instantly detect exact reposts and cropped anomalies.</p>
            </div>
            <div className="panel">
              <h3 style={{ color: 'var(--accent-2)', marginBottom: '1rem', fontSize: '0.875rem' }}>// STAGE 02</h3>
              <h2>Semantic Isolation</h2>
              <p style={{ fontSize: '0.875rem' }}>Deep Gemini abstraction mapping protects against complex, edited, and meme-format media.</p>
            </div>
            <div className="panel">
              <h3 style={{ color: 'var(--alert)', marginBottom: '1rem', fontSize: '0.875rem' }}>// STAGE 03</h3>
              <h2>Propagation Graph</h2>
              <p style={{ fontSize: '0.875rem' }}>Mapping illicit distribution networks and visualizing mutation trees through graph intelligence.</p>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}
