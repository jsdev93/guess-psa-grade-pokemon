/* eslint-disable @next/next/no-img-element */
"use client";

import { useCallback, useEffect, useState, useRef } from "react";

type CardItem = {
  cert: string;
  title: string;
  grade: number;     // hidden from user
  frontUrl: string;
  backUrl: string;
  certUrl: string;
};

type GameItem = CardItem & {
  guessed?: number;
  solved?: boolean;
  distance?: number;
};

const LS_SOLVED = "psa_session_solved";
const LS_TRIES = "psa_session_tries";

function cx(...a: (string | false | null | undefined)[]) {
  return a.filter(Boolean).join(" ");
}

export default function GamePage() {
  const [card, setCard] = useState<GameItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [tries, setTries] = useState(0); // tries for current card
  const [error, setError] = useState<string | null>(null);
  const [zoomUrl, setZoomUrl] = useState<string | null>(null);

  const [sessionSolved, setSessionSolved] = useState<number>(0);
  const [sessionTries, setSessionTries] = useState<number>(0);

  const [cooldown, setCooldown] = useState(0);

  // tick down the cooldown once per second
  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setInterval(() => setCooldown((c) => Math.max(0, c - 1)), 1000);
    return () => clearInterval(t);
  }, [cooldown]);

  // wrap your load() function
  async function handleNewCard() {
    if (cooldown > 0) return;
    await load();              // your existing load() logic
    setCooldown(8);            // start cooldown timer
  }


  // load session stats from localStorage
  useEffect(() => {
    const s = parseInt(localStorage.getItem(LS_SOLVED) || "0", 10);
    const t = parseInt(localStorage.getItem(LS_TRIES) || "0", 10);
    setSessionSolved(Number.isFinite(s) ? s : 0);
    setSessionTries(Number.isFinite(t) ? t : 0);
  }, []);
  useEffect(() => { localStorage.setItem(LS_SOLVED, String(sessionSolved)); }, [sessionSolved]);
  useEffect(() => { localStorage.setItem(LS_TRIES, String(sessionTries)); }, [sessionTries]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setCard(null);
    setTries(0);

    try {
      const r = await fetch("/api/random-pokemon?count=1", { cache: "no-store" });
      const ct = r.headers.get("content-type") || "";
      if (!ct.includes("application/json")) throw new Error("Non-JSON response");
      const data = await r.json();
      if (!r.ok || !data.ok) throw new Error(data?.error || "Fetch failed");
      const arr: CardItem[] = data.items;
      if (!Array.isArray(arr) || arr.length === 0) throw new Error("No items");
      setCard({ ...arr[0] });
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  function overlayClass(distance?: number, solved?: boolean) {
    if (solved) return "bg-emerald-400/25";
    if (distance == null) return "";
    if (distance <= 1) return "bg-amber-400/25";
    return "bg-rose-400/25";
  }

  function onSelect(value: number) {
    if (!card) return;
    setCard({ ...card, guessed: value });
  }

  function onGuess() {
    if (!card || card.solved || card.guessed == null) return;
    const dist = Math.abs(card.guessed - card.grade);
    const solved = dist === 0;

    setTries((t) => t + 1);
    setSessionTries((t) => t + 1);

    const next = { ...card, distance: dist, solved: solved || card.solved };
    setCard(next);

    if (solved && !card.solved) setSessionSolved((s) => s + 1);
  }

  function resetStats() {
    setSessionSolved(0);
    setSessionTries(0);
    localStorage.setItem(LS_SOLVED, "0");
    localStorage.setItem(LS_TRIES, "0");
  }

  return (
    <main className="mx-auto max-w-4xl p-4">
      {/* Session stats */}
      <div className="mb-4 rounded-2xl border border-slate-200 bg-white shadow p-4">
        <h1 className="text-2xl font-semibold mb-2">PSA Pokémon Grade Guess</h1>
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <span className="rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-800 px-3 py-1.5">
            Session Solved: <b>{sessionSolved}</b>
          </span>
          <span className="rounded-xl border border-indigo-200 bg-indigo-50 text-indigo-800 px-3 py-1.5">
            Session Tries: <b>{sessionTries}</b>
          </span>
          <span className="rounded-xl border border-slate-200 bg-slate-50 text-slate-800 px-3 py-1.5">
            This Card Tries: <b>{tries}</b>
          </span>
          <div className="ml-auto flex gap-2">
            <button onClick={resetStats} className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50">
              Reset Stats
            </button>
            <button
              onClick={handleNewCard}
              disabled={loading || cooldown > 0}
              className="rounded-lg bg-slate-900 text-white px-3 py-1.5 text-sm disabled:opacity-60"
            >
              {loading
                ? "Loading…"
                : cooldown > 0
                  ? `Wait ${cooldown}s`
                  : "New Card"}
            </button>
          </div>
        </div>
      </div>

      {error && <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-800 px-4 py-3">{error}</div>}

      {card && (
        <div className="rounded-2xl border border-slate-200 bg-white shadow">
          <div className={cx("p-3 rounded-t-2xl transition-colors", overlayClass(card.distance, card.solved))}>
            {/* Side-by-side images */}
            <div className="flex gap-3">
              <ImageWithMask src={card.frontUrl} alt={`${card.title} (front)`} onZoom={() => setZoomUrl(card.frontUrl)} />
              <ImageWithMask src={card.backUrl} alt={`${card.title} (back)`} onZoom={() => setZoomUrl(card.backUrl)} />
            </div>
          </div>

          <div className="px-3 pt-2 pb-3">
            <div className="text-sm text-slate-700 mb-2" title={card.title}>{card.title}</div>

            <div className="flex items-center gap-2">
              <SelectGrade value={card.guessed} disabled={card.solved} onChange={(val) => onSelect(val)} />
              <button
                className="ml-auto rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-60"
                onClick={onGuess}
                disabled={card.solved || card.guessed == null}
              >
                Guess
              </button>
            </div>

            <div className="mt-2 text-xs">
              {card.solved ? (
                <span className="text-emerald-700 font-medium">Correct!</span>
              ) : card.distance != null ? (
                card.distance <= 1 ? <span className="text-amber-700">Close (within 1)</span> :
                  <span className="text-rose-700">Off by {card.distance}</span>
              ) : (
                <span className="text-slate-500">Pick a grade and press Guess</span>
              )}
            </div>

            {card.solved && (
              <div className="mt-4">
                <button onClick={load} className="w-full rounded bg-emerald-600 text-white py-2 hover:bg-emerald-700">
                  Next Card
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {zoomUrl && (
        <ZoomModal src={zoomUrl} onClose={() => setZoomUrl(null)} />
      )}
    </main>
  );
}

function ZoomModal({ src, onClose }: { src: string; onClose: () => void }) {
  // viewport size (smaller than full screen)
  // tweak these to your taste
  const VIEW_W = Math.min(window.innerWidth * 0.9, 900);
  const VIEW_H = Math.min(window.innerHeight * 0.8, 600);

  // pan state
  const [dragging, setDragging] = useState(false);
  const [offset, setOffset] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const startRef = useRef<{ x: number; y: number } | null>(null);

  // optional: small scale so it appears “smaller”
  // increase IMG_SCALE (e.g., 1.2–1.6) if you want it larger
  const IMG_SCALE = 1.0;

  // Close on ESC
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  // Pointer handlers for drag-to-pan
  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    (e.currentTarget as HTMLDivElement).setPointerCapture(e.pointerId);
    setDragging(true);
    startRef.current = { x: e.clientX - offset.x, y: e.clientY - offset.y };
  };

  const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragging || !startRef.current) return;
    const { x, y } = startRef.current;
    setOffset({ x: e.clientX - x, y: e.clientY - y });
  };

  const onPointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    try { (e.currentTarget as HTMLDivElement).releasePointerCapture(e.pointerId); } catch { }
    setDragging(false);
    startRef.current = null;
  };

  // Prevent wheel from scrolling page while over modal
  const stopWheel = (e: React.WheelEvent) => { e.preventDefault(); };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="relative rounded-xl bg-black/40 shadow-xl ring-1 ring-white/10"
        style={{ width: VIEW_W, height: VIEW_H, overflow: "hidden" }}
        onClick={(e) => e.stopPropagation()} // don’t close when clicking inside
        onWheel={stopWheel}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-2 top-2 z-10 rounded-md bg-black/60 px-2 py-1 text-white text-xs hover:bg-black/80"
        >
          Close (Esc)
        </button>

        {/* Pan surface */}
        <div
          className={`w-full h-full cursor-${dragging ? "grabbing" : "grab"} touch-none`}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        >
          {/* The image itself */}
          <img
            src={src}
            alt="zoomed"
            draggable={false}
            className="select-none"
            style={{
              transform: `translate(${offset.x}px, ${offset.y}px) scale(${IMG_SCALE})`,
              transformOrigin: "center center",
              // Make the image larger than viewport so panning is meaningful
              // If your source images are huge already, you can remove these max sizes.
              maxWidth: "unset",
              maxHeight: "unset",
              width: "auto",
              height: "100%", // start by fitting height; you can switch to "width: 100%" if you prefer
            }}
          />
        </div>
      </div>
    </div>
  );
}


/* --- UI Subcomponents --- */

function ImageWithMask({ src, alt, onZoom }: { src: string; alt: string; onZoom: () => void }) {
  return (
    <div className="relative flex-1 rounded-xl overflow-hidden shadow-sm ring-1 ring-slate-200">
      <img
        src={src}
        alt={alt}
        className="w-full h-auto cursor-zoom-in transition-transform duration-200 hover:scale-[1.01]"
        onClick={onZoom}
      />
      <div className="pointer-events-none absolute left-0 right-0 top-0 h-[18%] bg-black/100" title="Label hidden" />
    </div>
  );
}

function SelectGrade({
  value,
  onChange,
  disabled,
}: {
  value?: number;
  onChange: (v: number) => void;
  disabled?: boolean;
}) {
  return (
    <select
      className="rounded border border-slate-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 disabled:opacity-60"
      value={value ?? ""}
      onChange={(e) => onChange(parseInt(e.target.value, 10))}
      disabled={disabled}
    >
      <option value="" disabled>Grade…</option>
      {Array.from({ length: 10 }, (_, i) => i + 1).map((g) => (
        <option key={g} value={g}>{g}</option>
      ))}
    </select>
  );
}
