"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { auth } from "@/lib/firebase";
import { onAuthStateChanged, User } from "firebase/auth";

export function Topbar() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
    });
    return () => unsubscribe();
  }, []);

  return (
    <header className="topbar">
      <Link href="/" className="brand">
        SentinelAI
      </Link>
      <nav style={{ display: 'flex', gap: '30px', alignItems: 'center' }}>
        {user ? (
          <>
            <Link href="/dashboard" style={{ fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700 }}>Demo</Link>
            <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.1em' }} title={user.email || ''}>
                {user.displayName || user.email?.split('@')[0]} [AUTH: ON]
              </span>
            </div>
          </>
        ) : (
          <Link href="/login" className="button" style={{ padding: '0.5rem 1.5rem', fontSize: '0.75rem' }}>
            Initialize Access
          </Link>
        )}
      </nav>
    </header>
  );
}
