import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteer.use(StealthPlugin());

export async function ocrCertFromEbay(itemId: string) {
  if (!itemId) throw new Error('No itemId provided');

  function findUniqueImage(urls: string[]): string | null {
    const keys = urls.map(url => {
      const match = url.match(/\/g\/([^/]+)\/s/);
      return match ? match[1] : null;
    });
    const uniqueKey = keys.find(key => key && keys.filter(k => k === key).length === 1);
    const idx = uniqueKey ? keys.indexOf(uniqueKey) : -1;
    return idx >= 0 ? urls[idx] : null;
  }

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
    const largeImgSrcs = Array.from(document.querySelectorAll('img'))
      .filter(img => img.width > 200 && img.height > 200)
      .map(img => img.src);
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
  const targetImgFront = largeImgSrcs.find(src => src && src.includes('1600')) || null;
  const uniqueImg = findUniqueImage(largeImgSrcs);
  const targetImgBack = uniqueImg ? uniqueImg.replace(/\/[^/]*$/, '/s-l1600.webp') : null;

  try {
    if (!targetImgFront || !targetImgBack) {
      await browser.close();
      return { imgUrlFront: 'No Image', imgUrlBack: 'No Image' };
    }
    if (!grade) {
      await browser.close();
      return { grade: 'Null Grade' };
    }
    await browser.close();
    return { grade, imgUrlFront: targetImgFront, imgUrlBack: targetImgBack, price };
  } catch (err) {
    await browser.close();
    return { ocrText: err };
  }
}
