import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';


// Usage: node src/app/utils/ocr_cert_from_ebay.js <itemId>

puppeteer.use(StealthPlugin());

const itemId = process.argv[2];
if (!itemId) {
  console.error('Usage: node src/app/utils/ocr_cert_from_ebay.js <itemId>');
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

  await page.goto(itemUrl, { waitUntil: 'domcontentloaded'});
  await new Promise(resolve => setTimeout(resolve, 3000));

  const { largeImgSrcs, grade, price } = await page.evaluate(() => {
    // Large image URLs
    const largeImgSrcs = Array.from(document.querySelectorAll('img'))
      .filter(img => img.width > 200 && img.height > 200)
      .map(img => img.src);

    // Grade extraction
    let grade = null;
    const insights = document.getElementById('vi_psa_card_insights');
    if (insights) {
      const valEl = insights.querySelector('.elevated-info__item__value');
      if (valEl) {
        const g = valEl.textContent?.trim();
        const match = g && g.match(/psa\s*(\d+)/i);
        if (match) {
          grade = parseInt(match[1], 10);
        } else if (g && /^\d+$/.test(g)) {
          grade = parseInt(g, 10);
        }
      }
    }
    // Price extraction
    let price = null;
    const priceDiv = document.querySelector('div.x-price-primary');
    if (priceDiv) {
      const priceSpan = priceDiv.querySelector('span.ux-textspans');
      let priceText = priceSpan?.textContent?.trim();
      if (priceText) {
        priceText = priceText.replace(/^US\s*/i, '');
        price = priceText;
      }
    }
    return { largeImgSrcs, grade, price };
  });
  // Find the highest resolution images for front and back
  const targetImgFront = largeImgSrcs.find(src => src && src.includes('1600')) || null;
  // Find the unique image by /g/.../s and force the filename to s-l1600.webp
  const uniqueImg = findUniqueImage(largeImgSrcs);
  const targetImgBack = uniqueImg ? uniqueImg.replace(/\/[^/]*$/, '/s-l1600.webp') : null;

  try {
    if (!targetImgFront || !targetImgBack) {
      await browser.close();
      process.stdout.write(JSON.stringify({ imgUrlFront: 'No Image', imgUrlBack: 'No Image' }));
      process.exit(0);
    }
    if (!grade) {
      await browser.close();
      process.stdout.write(JSON.stringify({ grade: 'Null Grade' }));
      process.exit(0);
    }
    await browser.close();
    // Output only pure JSON, no trailing newline or extra characters on Success
    const jsonOut = JSON.stringify({ grade, imgUrlFront: targetImgFront, imgUrlBack: targetImgBack, price });
    process.stdout.write(jsonOut);
  } catch (err) {
    await browser.close();
    // Output only pure JSON, no trailing newline or extra characters
    const jsonOut = JSON.stringify({ ocrText: err });
    process.stdout.write(jsonOut);
  }
})();
