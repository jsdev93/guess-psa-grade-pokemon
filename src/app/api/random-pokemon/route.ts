import { NextResponse } from "next/server";
import { getRandomItemId } from '../../../../scripts/item-id-util.js';
import { exec } from 'child_process';

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



function stubItems(n: number): CardItem[] {
  // using public Pokémon TCG images as placeholders; not PSA slabs
  // To use cheerio, run: npm install cheerio
function rndInt(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}
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


export async function GET() {
  try {
    // Try up to 5 times to get a valid cert
    for (let attempt = 0; attempt < 5; attempt++) {
      const id = getRandomItemId?.();
      if (!id) break;
      const ocrResult = await new Promise((resolve) => {
        exec(`node scripts/ocr_cert_from_ebay.js ${id}`, { cwd: process.cwd() }, (error, stdout) => {
          if (error) {
            resolve({ cert: null, imgUrl: null, ocrText: null, error: error.message });
            return;
          }
          try {
            const parsed = JSON.parse(stdout);
            resolve(parsed);
          } catch {
            resolve({ cert: null, imgUrl: null, ocrText: null, error: 'Failed to parse OCR output' });
          }
        });
      });
      console.log('OCR result:', ocrResult);
      const { cert, grade, imgUrlFront, imgUrlBack, ocrText, error } = ocrResult as any;
      if (cert) {
        return NextResponse.json({
          ok: true,
          items: [{
            cert,
            title: 'Pokémon',
            grade,
            frontUrl: imgUrlFront,
            backUrl: imgUrlBack,
            certUrl: cert ? `https://www.psacard.com/cert/${cert}/psa` : '',
            ocrText,
          }],
        });
      }
      // If error is not 'Failed to parse OCR output', break and fallback
      if (error !== 'Failed to parse OCR output') break;
    }
    // fallback to stub if no cert found after attempts
    return NextResponse.json({ ok: true, items: stubItems(1), fallback: 'No cert found from OCR.' });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: String(e?.message ?? e) }, { status: 500 });
  }
}
