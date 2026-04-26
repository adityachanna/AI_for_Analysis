"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/firebase";
import { signInWithPopup, GoogleAuthProvider, onAuthStateChanged } from "firebase/auth";

export default function LoginPage() {
  const router = useRouter();

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (user) => {
      if (user) {
        router.push("/dashboard");
      }
    });
    return () => unsub();
  }, [router]);

  const handleAuth = async () => {
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
      // Let the onAuthStateChanged push them to dashboard
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <>
      <div className="scanline"></div>
      <div className="auth-container">
        <div className="auth-box">
          <div style={{ marginBottom: '2rem' }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', color: 'var(--accent)' }}>System Authentication Required</h2>
            <p style={{ margin: '0 auto', fontSize: '0.875rem' }}>Verify identity to access the SentinelAI core network.</p>
          </div>
          
          <button className="button" style={{ width: '100%', padding: '1.25rem', fontSize: '1rem' }} onClick={handleAuth}>
            VERIFY VIA GOOGLE IDENTITY
          </button>
          
          <div style={{ marginTop: '3rem', fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.2)', textTransform: 'uppercase', letterSpacing: '0.2em' }}>
            Connection SECURE // PORT 3001
          </div>
        </div>
      </div>
    </>
  );
}
