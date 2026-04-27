import type { Metadata } from "next";
import { Topbar } from "@/components/Topbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "SentinelAI — Sports IP Protection at Machine Scale",
  description: "AI-powered video rights protection. Detects pirated sports footage across platforms using Gemini, SynthID, and semantic fingerprinting — before it goes viral.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Topbar />
        <main>{children}</main>
      </body>
    </html>
  );
}
