import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DataForge",
  description: "Guided data engineering labs in the browser",
};

// Read at request time, so one image runs in each environment with no rebuild.
export const dynamic = "force-dynamic";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const config = {
    supabaseUrl: process.env.SUPABASE_URL ?? "",
    supabasePublishableKey: process.env.SUPABASE_PUBLISHABLE_KEY ?? "",
  };
  // Public values only. `<` is escaped so that a value cannot close the script.
  const script = `window.__DATAFORGE__=${JSON.stringify(config).replace(/</g, "\\u003c")};`;
  return (
    <html lang="en">
      <body>
        <script dangerouslySetInnerHTML={{ __html: script }} />
        {children}
      </body>
    </html>
  );
}
