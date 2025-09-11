import { NextResponse } from "next/server";

// Import the filtered data directly so it works on Vercel
import items from '../../../../scripts/ml/output.filtered.json';

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    // Pick a random item from the imported array
    for (let attempt = 0; attempt < 5; attempt++) {
      const idx = Math.floor(Math.random() * items.length);
      const item = items[idx];
      if (!item) continue;
      const { id, grade, imgUrlFront, imgUrlBack, price } = item;
      if (grade && imgUrlFront && imgUrlBack) {
        return NextResponse.json({
          ok: true,
          items: [{
            id,
            grade,
            frontUrl: imgUrlFront,
            backUrl: imgUrlBack,
            price,
          }],
        });
      }
    }
    // fallback to stub if no cert found after attempts
    return NextResponse.json({ ok: true, fallback: 'No cert found.' });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: String(e?.message ?? e) }, { status: 500 });
  }
}
