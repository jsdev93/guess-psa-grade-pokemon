"use client";
// CardGuessControls: handles price hint, grade select, and guess button
type CardGuessControlsProps = {
  card: GameItem;
  priceHintUsed: boolean;
  showPrice: boolean;
  onPriceHint: () => void;
  onSelect: (val: number) => void;
  onGuess: () => void;
  disabled?: boolean;
};
function CardGuessControls({ card, priceHintUsed, showPrice, onPriceHint, onSelect, onGuess, disabled }: CardGuessControlsProps) {
  return (
  <div className="bg-[#e2f4f8] rounded-2xl border-2 border-[#8e9388] shadow-[0_0_16px_#8e9388] p-4 sm:p-6 flex flex-col gap-3 sm:gap-4 my-2 text-white">
      {card.price && !priceHintUsed && !showPrice && (
        <button
          className="mb-2 px-4 py-2 rounded-lg border-2 border-[#b1a886] bg-[#f4e37f] text-[#6a7678] text-lg font-bold shadow-[0_0_8px_#b1a886] hover:bg-[#b1a886] hover:text-white focus:outline-none focus:ring-2 focus:ring-[#b1a886] transition-colors"
          onClick={onPriceHint}
          type="button"
          disabled={disabled}
        >
          Show Price Hint
        </button>
      )}
      {card.price && (showPrice || card.solved) && (
  <div className="text-lg text-white mb-2 drop-shadow-[0_0_6px_#f4e37f]">Price: <span className="font-mono">{card.price}</span></div>
      )}
      <SelectGrade value={card.guessed} disabled={card.solved || disabled} onChange={onSelect} />
      <button
        className={cx(
          "w-full rounded-lg border-2 border-[#b1a886] px-6 py-4 text-3xl font-extrabold shadow-[0_0_8px_#b1a886] text-white transition-all",
          card.solved
            ? "bg-[#f4e37f] text-[#6a7678] hover:bg-[#b1a886] hover:text-white"
            : "bg-[#8e9388] text-white hover:bg-[#f4e37f] hover:text-[#6a7678] disabled:opacity-60"
        )}
        onClick={onGuess}
        disabled={card.solved || card.guessed == null || disabled}
        style={{fontFamily: 'Roboto, Arial, Helvetica, \"Segoe UI\", sans-serif'}}>
        Guess
      </button>
    </div>
  );
}
// CardImageCard: visually distinct card for the image/toggle UI
function CardImageCard({ children }: { children: React.ReactNode }) {
  return (
  <div className="w-[30rem] !important bg-[#e2f4f8] rounded-2xl border-2 border-[#6a7678] shadow-[0_0_16px_#6a7678] p-4 sm:p-6 m-2 sm:m-4 flex flex-col items-center justify-center text-white">
      {children}
    </div>
  );
}

type CardImagesSectionProps = {
  card: CardItem | GameItem;
  overlayClass?: string;
  zoomIntensity?: number;
};
function CardImagesSection({ card, overlayClass, zoomIntensity }: CardImagesSectionProps) {
  const solved = 'solved' in card ? card.solved : undefined;
  const [showFront, setShowFront] = useState(true);
  const handleToggle = () => setShowFront((v) => !v);
  return (
  <div className={cx("transition-colors duration-300 flex flex-col items-center justify-center bg-[#e2f4f8] border-2 border-[#f4e37f] shadow-[0_0_12px_#f4e37f] text-white", overlayClass)} style={{ minWidth: 0 }}>
      <CardImageCard>
        <div className="relative flex flex-col items-center justify-center w-full sm:max-w-xs md:max-w-2xl">
          <button
            aria-label={showFront ? "Show back of card" : "Show front of card"}
            onClick={handleToggle}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 border-2 bg-[#6a7678] rounded-full shadow-[0_0_8px_#f4e37f] p-2 w-12 h-12 flex items-center justify-center hover:bg-[#f4e37f] hover:text-[#6a7678] focus:outline-none focus:ring-2 focus:ring-[#f4e37f] transition-all duration-150"
            style={{ left: 0 }}
          >
            <span className="text-3xl text-white font-extrabold drop-shadow">&#8592;</span>
          </button>
          <div className="flex-1 flex justify-center w-full">
            {showFront ? (
              <ImageWithMask src={card.frontUrl} alt={`${card.title} (front)`} solved={solved} zoomIntensity={zoomIntensity} />
            ) : (
              <ImageWithMask src={card.backUrl} alt={`${card.title} (back)`} solved={solved} zoomIntensity={zoomIntensity} />
            )}
          </div>
          <button
            aria-label={showFront ? "Show back of card" : "Show front of card"}
            onClick={handleToggle}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-10 border-2 border-[#f4e37f] bg-[#6a7678] rounded-full shadow-[0_0_8px_#f4e37f] p-2 w-12 h-12 flex items-center justify-center hover:bg-[#f4e37f] hover:text-[#6a7678] focus:outline-none focus:ring-2 focus:ring-[#f4e37f] transition-all duration-150"
            style={{ right: 0 }}
          >
            <span className="text-3xl text-white font-extrabold drop-shadow">&#8594;</span>
          </button>
          <div className="mt-2 text-center text-xs text-white font-semibold drop-shadow-[0_0_4px_#003A6B]">
            {showFront ? "Front" : "Back"}
          </div>
        </div>
      </CardImageCard>
    </div>
  );
}
/* eslint-disable @next/next/no-img-element */

import { useCallback, useEffect, useState, useRef } from "react";

type CardItem = {
  title: string;
  grade: number;     // hidden from user
  frontUrl: string;
  backUrl: string;
  price?: string | null;
  id?: string | number;
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
  // Zoom intensity state (default 2.2)
  const [zoomIntensity, setZoomIntensity] = useState(2);
  const [showPrice, setShowPrice] = useState(false);
  const [priceHintUsed, setPriceHintUsed] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('psa_price_hint_used') === '1';
    }
    return false;
  });
  const [card, setCard] = useState<GameItem | null>(null);
  // Always reset showPrice to false on new card
  useEffect(() => {
    setShowPrice(false);
  }, [card]);
  const [loading, setLoading] = useState(false);
  const [tries, setTries] = useState(0); // tries for current card
  const [error, setError] = useState<string | null>(null);
  const [zoomUrl, setZoomUrl] = useState<string | null>(null);

  const [sessionSolved, setSessionSolved] = useState<number>(0);
  const [sessionTries, setSessionTries] = useState<number>(0);

  const [cooldown, setCooldown] = useState(0);
  const gameOver = tries >= 10;
  // ...existing code...
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
  // ...existing code...
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
    if (!card || gameOver) return;
    setCard({ ...card, guessed: value });
  }

  function onGuess() {
    if (!card || card.solved || card.guessed == null || gameOver) return;
    const dist = Math.abs(card.guessed - card.grade);
    const solved = dist === 0;

    setTries((t) => t + 1);
    setSessionTries((t) => t + 1);

    const next = { ...card, distance: dist, solved: solved || card.solved };
    setCard(next);

    if (solved && !card.solved) setSessionSolved((s) => s + 1);
  }

  function resetStatsAndNewGame() {
    setSessionSolved(0);
    setSessionTries(0);
    setShowPrice(false);
    setPriceHintUsed(false);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('psa_price_hint_used');
    }
    localStorage.setItem(LS_SOLVED, "0");
    localStorage.setItem(LS_TRIES, "0");
    load();
  }

  // When price hint is used, persist in localStorage for session
  const usePriceHint = () => {
    if (gameOver) return;
    setShowPrice(true);
    setPriceHintUsed(true);
    if (typeof window !== 'undefined') {
      localStorage.setItem('psa_price_hint_used', '1');
    }
  };

  return (
  <main
    className="mx-auto max-w-5xl min-h-screen font-sans flex flex-col items-center justify-start bg-[url(/pkmbg.jpg)] bg-repeat text-white"
    style={{
      fontFamily: 'Roboto, Arial, Helvetica, "Segoe UI", sans-serif',
      color: '#fff',
      minHeight: '100dvh',
      boxSizing: 'border-box',
      textShadow: '0 0 8px #f4e37f, 0 0 16px #8e9388',
    }}
  >
      {/* Session stats */}
  <div className="mb-4 sm:mb-6 rounded-2xl border-4 border-[#8e9388] bg-[#f4e37f] shadow-[0_0_24px_#8e9388] p-3 sm:p-4 md:p-6 w-full max-w-3xl mx-auto text-white">
    <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold mb-2 sm:mb-4 tracking-tight text-[#e2f4f8] text-center drop-shadow-[0_0_10px_#f4e37f]">Pokémon PSA SlabGuessr</h1>
  </div>

      {error && <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-800 px-4 py-3">{error}</div>}

      {card && (
  <div className="rounded-2xl border-2 border-[#b1a886] bg-[#f4e37f] shadow transition-shadow duration-300 hover:shadow-lg w-full max-w-3xl mx-auto flex flex-col sm:flex-row">
          {/* Left: Card Images */}
          <CardImagesSection card={card} overlayClass={overlayClass(card.distance, card.solved)} zoomIntensity={zoomIntensity} />
          {/* Right: Card Details and Controls */}
          <div className="flex-1 px-2 sm:px-3 pt-2 pb-3 flex flex-col gap-2 justify-center">
            {card.solved && card.id && (
              <a
                color="white"
                href={`https://www.ebay.com/itm/${card.id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block mb-3 px-4 py-2 rounded bg-[#6a7678] text-white text-xl font-bold hover:bg-[#8e9388] transition-colors"
              >
                View Listing on eBay
              </a>
            )}
            <div className="text-lg text-[#6a7678] mb-2 font-semibold tracking-wide" title={card.title}>{card.title}</div>
            {/* Counters */}
            <div className="mb-2 flex flex-wrap items-center justify-center gap-2 sm:gap-4 text-base sm:text-xl">
              <span className="shrink-0 rounded-xl border-2 border-[#8e9388] bg-[#e2f4f8] text-[#6a7678] px-4 py-2 font-bold shadow-[0_0_8px_#8e9388]">
                Cards Solved: <b>{sessionSolved}</b>
              </span>
              <span className="shrink-0 rounded-xl border-2 border-[#f4e37f] bg-[#e2f4f8] text-[#6a7678] px-4 py-2 font-bold shadow-[0_0_8px_#f4e37f]">
                Number of Tries: <b>{sessionTries}</b>
              </span>
              <span className="shrink-0 rounded-xl border-2 border-[#6a7678] bg-[#e2f4f8] text-[#6a7678] px-4 py-2 font-bold shadow-[0_0_8px_#6a7678]">
                This Card Tries: <b>{tries}</b>
              </span>
            </div>
            {/* New Game and New Card buttons */}
            <div className="mb-2 flex gap-3 w-full flex-col items-center text-center sm:w-auto sm:flex-row sm:items-center sm:justify-start">
              <button onClick={resetStatsAndNewGame} className="rounded-lg border-2 border-[#b1a886] bg-[#f4e37f] text-[#6a7678] px-5 py-2 text-xl font-bold shadow-[0_0_8px_#b1a886] hover:bg-[#b1a886] hover:text-white transition-colors">
                New Game
              </button>
              <button
                onClick={handleNewCard}
                disabled={loading || cooldown > 0 || sessionTries >= 10 || (!!card && !card.solved) || tries >= 10}
                className="rounded-lg border-2 border-[#f4e37f] bg-[#8e9388] text-white px-5 py-2 text-xl font-bold shadow-[0_0_8px_#f4e37f] hover:bg-[#e2f4f8] hover:text-[#6a7678] disabled:opacity-60 transition-colors"
              >
                {loading
                  ? "Loading…"
                  : cooldown > 0
                    ? `Wait ${cooldown}s`
                    : sessionTries >= 10
                      ? "Limit Reached"
                      : "New Card"}
              </button>
            </div>
            {/* Zoom intensity slider */}
            <div className="mb-2 flex gap-3 w-full flex-col items-center text-center sm:w-auto sm:flex-row sm:items-center sm:justify-start">
              <label htmlFor="zoom-slider" className="text-[#b1a886] font-semibold">Zoom Intensity</label>
              <input
                id="zoom-slider"
                type="range"
                min={1}
                max={5}
                step={0.5}
                value={zoomIntensity}
                onChange={e => setZoomIntensity(Number(e.target.value))}
                className="w-32 accent-[#8e9388]"
              />
              <span className="font-mono text-[#b1a886]">{zoomIntensity.toFixed(2)}x</span>
            </div>
            <CardGuessControls
              card={card}
              priceHintUsed={priceHintUsed}
              showPrice={showPrice}
              onPriceHint={usePriceHint}
              onSelect={onSelect}
              onGuess={onGuess}
              disabled={gameOver}
            />

            <div className="mt-2 text-lg min-h-[1.5em]">
              {gameOver ? (
                <span className="text-[#6a7678] font-bold">Game Over! Out of tries.</span>
              ) : card.solved ? (
                <span className="text-[#b1a886] font-bold">Correct!</span>
              ) : card.distance != null ? (
                <span className="text-[#fff] font-bold">Guess Again!</span>
              ) : (
                null
              )}
            </div>

            {card.solved && (
              <div className="mt-4">
                <button
                  onClick={load}
                  className="w-full rounded bg-emerald-600 text-white py-2 font-semibold shadow-md hover:bg-emerald-700 active:shadow-lg transition-all duration-200"
                  disabled={sessionTries === 10}
                >
                  {sessionTries >= 10 ? "Limit Reached" : "Next Card"}
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
// ...existing code...
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
        className="relative rounded-xl bg-[#e2f4f8]/90 shadow-xl ring-1 ring-[#f4e37f]/20"
        style={{ width: VIEW_W, height: VIEW_H, overflow: "hidden" }}
        onClick={(e) => e.stopPropagation()} // don’t close when clicking inside
        onWheel={stopWheel}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-2 top-2 z-10 rounded-md bg-black/60 px-2 py-1 text-white text-lg hover:bg-black/80"
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



function ImageWithMask({ src, alt, solved, zoomIntensity = 2.2 }: { src: string; alt: string; solved?: boolean; zoomIntensity?: number }) {
  const [hovering, setHovering] = useState(false);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [touchScale, setTouchScale] = useState(1);
  const [touchOrigin, setTouchOrigin] = useState({ x: 50, y: 50 });
  const [touching, setTouching] = useState(false);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [lastPan, setLastPan] = useState<{ x: number; y: number } | null>(null);
  const lastScale = useRef(1);
  const rafRef = useRef<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const lastDist = useRef<number | null>(null);
  if (!src) return null;
  const ZOOM = zoomIntensity; // zoom factor on hover
  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const relY = (e.clientY - rect.top) / rect.height;
    if (relY < 0.25) return; // Prevent pan in top 25%
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = relY * 100;
    setPos({ x, y });
  }

  function handleTouchStart(e: React.TouchEvent<HTMLDivElement>) {
    if (e.touches.length === 2) {
      setTouching(true);
      const rect = containerRef.current?.getBoundingClientRect();
      if (!rect) return;
      const x = ((e.touches[0].clientX + e.touches[1].clientX) / 2 - rect.left) / rect.width * 100;
      const y = ((e.touches[0].clientY + e.touches[1].clientY) / 2 - rect.top) / rect.height * 100;
      setTouchOrigin({ x, y });
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      lastDist.current = Math.sqrt(dx * dx + dy * dy);
      lastScale.current = touchScale;
      setLastPan(null);
    } else if (e.touches.length === 1 && touchScale > 1) {
      setLastPan({ x: e.touches[0].clientX - offset.x, y: e.touches[0].clientY - offset.y });
    }
  }
  function handleTouchMove(e: React.TouchEvent<HTMLDivElement>) {
    if (e.touches.length === 2 && lastDist.current) {
      // Pinch zoom
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      const dist = Math.sqrt(dx * dx + dy * dy);
      let scale = (dist / lastDist.current) * lastScale.current;
      // Use zoomIntensity as the max pinch zoom
      scale = Math.max(1, Math.min(scale, zoomIntensity));
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => setTouchScale(scale));
      // If user zooms out to 1x, reset pan/zoom state immediately
      if (scale === 1) {
        setTouchScale(1);
        setOffset({ x: 0, y: 0 });
        setLastPan(null);
        setTouching(false);
        lastDist.current = null;
        lastScale.current = 1;
      }
      e.preventDefault();
    } else if (e.touches.length === 1 && lastPan && touchScale > 1) {
      // Drag/pan
      const x = e.touches[0].clientX - lastPan.x;
      const y = e.touches[0].clientY - lastPan.y;
      setOffset({ x, y });
      e.preventDefault();
    }
  }
  function handleTouchEnd(e: React.TouchEvent<HTMLDivElement>) {
    if (e.touches.length < 2) {
      setTouching(false);
      setTouchScale(1);
      setOffset({ x: 0, y: 0 });
      setLastPan(null);
      lastDist.current = null;
      lastScale.current = 1;
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    }
  }
  return (
    <div
      ref={containerRef}
      className="relative flex-1 rounded-xl overflow-hidden shadow-sm ring-1 ring-slate-200 touch-none cursor-default"
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
      onMouseMove={handleMouseMove}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      <img
        src={src}
        alt={alt}
        draggable={false}
        className="select-none w-full h-full object-contain transition-transform duration-300"
        style={
          touching || touchScale > 1
            ? {
                transform: `scale(${touchScale}) translate(${offset.x / touchScale}px, ${offset.y / touchScale}px)` ,
                transformOrigin: `${touchOrigin.x}% ${touchOrigin.y}%`,
                zIndex: 2,
              }
            : hovering
            ? {
                transform: `scale(${ZOOM})`,
                transformOrigin: `${pos.x}% ${pos.y}%`,
                zIndex: 2,
              }
            : {}
        }
      />
      {/* Hide black overlay if solved */}
      {!solved && (
        <div className="pointer-events-none absolute left-0 right-0 top-0 h-[20%] bg-black/100" title="Label hidden" />
      )}
    </div>
  );
}

function SelectGrade({ value, onChange, disabled }: { value?: number; onChange: (v: number) => void; disabled?: boolean; }) {
  const [open, setOpen] = useState(false);
  const grades = Array.from({ length: 10 }, (_, i) => 10 - i);
  const selectRef = useRef<HTMLDivElement>(null);
  const handleSelect = (g: number) => {
    if (!disabled) {
      onChange(g);
      setOpen(false);
    }
  };
  useEffect(() => {
    if (!open) return;
    function handle(e: MouseEvent) {
      if (selectRef.current && !selectRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, [open]);
  return (
    <div ref={selectRef} className="relative w-full select-none z-50 text-white" tabIndex={-1}>
        {open && !disabled && (
          <ul
            className="absolute z-50 bottom-full mb-2 w-full rounded-lg border-2 border-[#8e9388] bg-[#f4e37f] shadow-[0_0_12px_#8e9388] max-h-60 overflow-auto animate-fade-in text-white"
            role="listbox"
          >
            <li
              className="px-5 py-3 text-xl text-[#6a7678] font-semibold cursor-default select-none text-center drop-shadow-[0_0_4px_#f4e37f]"
            >Grade…</li>
            {grades.map((g) => (
              <li
                key={g}
                role="option"
                aria-selected={value === g}
                className={cx(
                  "px-5 py-3 text-2xl font-bold cursor-pointer transition-colors text-center text-white",
                  value === g ? "bg-[#b1a886] text-white" : "text-white hover:bg-[#8e9388] hover:text-white"
                )}
                onClick={() => handleSelect(g)}
                tabIndex={0}
                onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && handleSelect(g)}
              >
                {g}
              </li>
            ))}
          </ul>
        )}
        <button
          type="button"
          className={cx(
            "w-full flex items-center justify-center gap-2 rounded-lg border-2 border-[#8e9388] px-5 py-3 text-2xl font-bold bg-[#f4e37f] text-[#6a7678] shadow-[0_0_8px_#8e9388] transition-all focus:outline-none focus:ring-4 focus:ring-[#8e9388]/30 text-center",
            disabled && "opacity-60 cursor-not-allowed"
          )}
          onClick={() => !disabled && setOpen((v) => !v)}
          disabled={disabled}
          aria-haspopup="listbox"
          aria-expanded={open}
          style={{ minWidth: 120 }}
        >
          <span className={cx("flex-1 text-center", !value && "text-[#6a7678] font-semibold text-xl drop-shadow-[0_0_4px_#f4e37f]")}>{value ?? "Grade…"}</span>
          <span className="text-[#6a7678] text-2xl">▼</span>
        </button>
      </div>
    );
}
