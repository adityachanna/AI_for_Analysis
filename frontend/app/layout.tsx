import type { Metadata } from "next";
import { Topbar } from "@/components/Topbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "SentinelAI",
  description: "Rights protection MVP for sports media.",
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
