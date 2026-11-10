import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DataForge",
  description: "Guided data engineering labs in the browser",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
