import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto max-w-3xl p-6">
      <h1 className="text-3xl font-semibold mb-2">PSA Pokémon Grade Guess</h1>
      <p className="mb-6">
        We’ll fetch a random PSA Pokémon certificates (front & back). Guess the card’s grade (1–10).
      </p>
      <Link href="/game" className="btn">Start Game</Link>
    </main>
  );
}
