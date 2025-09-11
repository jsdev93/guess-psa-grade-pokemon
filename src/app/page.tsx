import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto max-w-3xl p-6">
      <h1 className="text-3xl font-semibold mb-2">Guess The PSA Grade - Pokémon Edition</h1>
      <h1 className="mb-8 mt-6">
        We’ll fetch a random PSA Pokémon certificate (front & back). Guess the card’s grade (1–10). See how many you can get with 10 tries. You can use a hint (see price) but only once per game.
      </h1>
      <Link href="/game" className="bg-white hover:bg-gray-100 text-gray-800 font-semibold py-2 px-4 border border-gray-400 rounded shadow">Start Game</Link>
    </main>
  );
}
