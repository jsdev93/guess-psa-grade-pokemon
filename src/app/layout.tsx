import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Guess The PSA Grade - Pokémon Edition",
  description: "Guess the grades (1–10) of PSA Pokémon slabs from cert images",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[url(/pkmbg.jpg)] bg-repeat text-neutral-900">{children}</body>
    </html>
  );
}
