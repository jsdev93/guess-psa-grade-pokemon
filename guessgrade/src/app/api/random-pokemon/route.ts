import { NextResponse } from "next/server";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type CardItem = {
  cert: string;
  title: string;
  grade: number;         // 1..10
  frontUrl: string;
  backUrl: string;
  certUrl: string;
};

const CLOUDFRONT_RE = /https:\/\/[\w.\-]*cloudfront\.net[\w.\-/%?=&]+/i;

function rndInt(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}
function randomCertNumber() {
  return String(rndInt(110_000_000, 120_000_000));
}

function stubItems(n: number): CardItem[] {
  // using public Pokémon TCG images as placeholders; not PSA slabs
  const demo = [
    "https://images.pokemontcg.io/base1/4_hires.png",
    "https://images.pokemontcg.io/swsh45/1_hires.png",
    "https://images.pokemontcg.io/sv2/1_hires.png",
    "https://images.pokemontcg.io/sv1/3_hires.png",
    "https://images.pokemontcg.io/bw11/9_hires.png",
  ];
  return Array.from({ length: n }).map((_, i) => {
    const img = demo[i % demo.length];
    return {
      cert: `STUB-${i + 1}`,
      title: "Pokémon (stub)",
      grade: rndInt(1, 10),
      frontUrl: img,
      backUrl: img, // just duplicate in stub mode
      certUrl: "https://www.psacard.com/",
    };
  });
}

async function tryImportPlaywright() {
  try { return await import("playwright"); }
  catch (e: any) { return { __err: `PLAYWRIGHT_IMPORT_FAILED: ${e?.message || String(e)}` }; }
}

async function fetchOnePokemonCert(playwright: any): Promise<CardItem | null> {
  if ((playwright as any).__err) return null;
  const { chromium } = playwright;

  // Hard caps to avoid hangs
  const NAV_TIMEOUT = 8_000;

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    locale: "en-US",
  });

  const cert = randomCertNumber();
  const certUrl = `https://www.psacard.com/cert/${cert}/psa`;
  console.log('certUrl', certUrl);
  const page = await context.newPage();

  const cloud = new Set<string>();
  page.on("response", async (resp: any) => {
    try {
      const u = resp.url();
      if (!u.includes("cloudfront.net")) return;
      const ct = (resp.headers()["content-type"] || "").toLowerCase();
      if (ct.includes("image") || CLOUDFRONT_RE.test(u)) cloud.add(u);
    } catch { }
  });

  const watchdog = new Promise<null>((res) => setTimeout(() => res(null), NAV_TIMEOUT));

  const task = (async () => {
    try {
      const resp = await page.goto(certUrl, { waitUntil: "domcontentloaded", timeout: 10_000 });
      if (!resp || resp.status() >= 400) return null;

      await page.waitForTimeout(800);

      // Title & Pokémon check
      let title = (await page.title()) || "";
      const h = await page.$("h1,h2,.cert-title,.page-title");
      if (h) {
        const t = (await h.innerText()).trim();
        if (t.length > 5) title = t;
      }
      const body = await page.evaluate(() => document.body.innerText || "");

      const isPokemon = /(pokemon|pokémon|yu-?gi-?oh|one\s*piece)/i.test(title)
      if (!isPokemon) return null;

      // Grade extraction
      const all = `${title}\n${body}`;
      const m = all.match(/Grade[^0-9]*(10|[1-9])\b/i) || all.match(/\bPSA[^0-9]*(10|[1-9])\b/i);
      const grade = m ? parseInt(m[1], 10) : 0;
      if (!(grade >= 1 && grade <= 10)) return null;

      // Collect DOM <img> too
      const imgSrcs: string[] = await page.$$eval("img", (els: any) =>
        els.flatMap((e: any) => {
          const out: string[] = [];
          const s = (e as HTMLImageElement).src || "";
          if (s) out.push(s);
          const ss = (e as HTMLImageElement).srcset || "";
          if (ss) ss.split(",").forEach((piece) => {
            const u = piece.trim().split(" ")[0];
            if (u) out.push(u);
          });
          return out;
        })
      );
      for (const s of imgSrcs) if (s.includes("cloudfront.net")) cloud.add(s);

      const urls = Array.from(cloud);
      if (urls.length === 0) return null;

      // Try to pick front/back heuristically; fallback to first two
      const front = urls.find((u) => /front/i.test(u)) || urls[0];
      const backCandidates = urls.filter((u) => u !== front);
      const back = backCandidates.find((u) => /back/i.test(u)) || backCandidates[0] || front;
      console.log(front);

      return { cert, title, grade, frontUrl: front.replace('/small', ''), backUrl: back.replace('/small', ''), certUrl };
    } catch {
      return null;
    } finally {
      try { await page.close(); } catch { }
      try { await context.close(); } catch { }
      try { await browser.close(); } catch { }
    }
  })();

  return Promise.race([task, watchdog]);
}

export async function GET() {
  try {
    const pw = await tryImportPlaywright();
    if ((pw as any).__err) {
      return NextResponse.json({ ok: true, items: stubItems(1), fallback: (pw as any).__err });
    }

    const items: CardItem[] = [];

    const one = await fetchOnePokemonCert(pw);
    if (one && !items.some((x) => x.cert === one.cert)) items.push(one);
    await new Promise((r) => setTimeout(r, 250 + Math.random() * 350));

    if (items.length < 1) {
      const fill = stubItems(1 - items.length);
      return NextResponse.json({
        ok: true,
        partial: true,
        message: `Found ${items.length}/${1} from PSA; filled ${fill.length} stubs.`,
        items: [...items, ...fill],
      });
    }
    return NextResponse.json({ ok: true, items });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: String(e?.message ?? e) }, { status: 500 });
  }
}
