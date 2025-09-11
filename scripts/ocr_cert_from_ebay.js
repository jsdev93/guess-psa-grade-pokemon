import puppeteer from 'puppeteer';
import fetch from 'node-fetch';
import Tesseract from 'tesseract.js';

// Usage: node scripts/ocr_cert_from_ebay.js <itemId>
const itemId = process.argv[2];
if (!itemId) {
  console.error('Usage: node scripts/ocr_cert_from_ebay.js <itemId>');
  process.exit(1);
}

function findUniqueImage(urls) {
  // Extract the substring between /g/ and /s for each URL
  const keys = urls.map(url => {
    const match = url.match(/\/g\/([^/]+)\/s/);
    return match ? match[1] : null;
  });
  // Find the unique key
  const uniqueKey = keys.find(key => keys.filter(k => k === key).length === 1);
  // Return the corresponding URL
  return urls[keys.indexOf(uniqueKey)];
}

(async () => {
  const itemUrl = `https://www.ebay.com/itm/${itemId}`;
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36');
  await page.setExtraHTTPHeaders({
    'accept-language': 'en-US,en;q=0.9',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'sec-fetch-site': 'none',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-user': '?1',
    'sec-fetch-dest': 'document',
    'upgrade-insecure-requests': '1'
  });
  await page.goto(itemUrl, { waitUntil: 'domcontentloaded' });
  await new Promise(resolve => setTimeout(resolve, 3000));
  // Get all large image URLs on the page
  const largeImgSrcs = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('img'))
      .filter(img => img.width > 200 && img.height > 200)
      .map(img => img.src);
  });

  // Find the highest resolution images for front and back
  const targetImgFront = largeImgSrcs.find(src => src && src.includes('1600')) || null;
  // Find the unique image by /g/.../s and force the filename to s-l1600.webp
  const uniqueImg = findUniqueImage(largeImgSrcs);
  const targetImgBack = uniqueImg ? uniqueImg.replace(/\/[^/]*$/, '/s-l1600.webp') : null;

  if (!targetImgFront || !targetImgBack) {
    await browser.close();
    process.stdout.write(JSON.stringify({ cert: null, imgUrlFront: null, imgUrlBack: null, ocrText: largeImgSrcs }));
    process.exit(0);
  }
  try {
    const response = await fetch(targetImgFront);
  if (!response.ok) throw new Error('Failed to fetch image');
    const arrayBuffer = await response.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    const { data: { text } } = await Tesseract.recognize(buffer, 'eng', {
      logger: () => {},
      langPath: 'https://tessdata.projectnaptha.com/4.0.0_best',
    });
  const certMatches = text.match(/\b\d{8,9}\b/g);
  // Try to find a grade by keyword mapping
  let grade = null;
  const gradeMap = [
    { re: /GEM/i, val: 10 },
    { re: /MINT/i, val: 9 },
    { re: /NM[-\s]*MT/i, val: 8 }, // NM-MT or NM MT
    { re: /\bNM\b/i, val: 7 },
    { re: /EX\s*-\b/i, val: 6 },
    { re: /\bEX\b/i, val: 5 },
    { re: /VG\s*-\b/i, val: 4 },
    { re: /\bVG\b/i, val: 3 },
    { re: /GOOD/i, val: 2 },
    { re: /\bPR\b/i, val: 1 },
  ];
  for (const { re, val } of gradeMap) {
    if (re.test(text)) {
      grade = val;
      break;
    }
  }
  if (grade === null) {
    process.stdout.write(JSON.stringify({ cert: null, imgUrlFront: null, imgUrlBack: null, ocrText: 'Null Grade' }));
    process.exit(0);
  }
  await browser.close();
  // Output only pure JSON, no trailing newline or extra characters
  const jsonOut = JSON.stringify({ cert: certMatches && certMatches.length ? certMatches[0] : null, grade, imgUrlFront: targetImgFront, imgUrlBack: targetImgBack, ocrText: text });
  process.stdout.write(jsonOut);
  } catch (err) {
  await browser.close();
  // Output only pure JSON, no trailing newline or extra characters
  const jsonOut = JSON.stringify({ cert: null, imgUrlFront: targetImgFront, imgUrlBack: targetImgBack, ocrText: null });
  process.stdout.write(jsonOut);
  }
})();
