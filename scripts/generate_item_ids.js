

import puppeteer from 'puppeteer';
import fs from 'fs';

const EBAY_URL = "https://www.ebay.com/sch/183454/i.html?%5C_dkr=1&_fsrp=1&_blrs=recall%5C_filtering&_ssn=psa&_ipg=240&iconV2Request=true&store%5C_name=psa&_sop=10&_oac=1&Grade=1%7C2%7C3%7C4%7C5%7C6%7C7%7C8%7C9%7C10&_dmd=1&Professional%2520Grader=Professional%2520Sports%2520Authenticator%2520%2528PSA%2529&Game=Pok%25C3%25A9mon%2520TCG&_dcat=183454&LH_BIN=1&_pgn=21&rt=nc";

async function refreshItemIds() {
  // Clear the file before populating
  fs.writeFileSync('scripts/item-ids.json', '[]');
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  // Set a realistic user agent and browser-like headers
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

  await page.goto(EBAY_URL, { waitUntil: 'domcontentloaded' });
  // Wait a bit to allow dynamic content to load
  await new Promise(resolve => setTimeout(resolve, 3000));
  // Take a screenshot for debugging
  const html = await page.content();

  await browser.close();

  // Find all 12-digit numbers in the HTML
  const all12DigitNumbers = Array.from(html.matchAll(/\b\d{12}\b/g)).map(m => m[0]);
  const uniqueItemIds = Array.from(new Set(all12DigitNumbers));
  fs.writeFileSync('scripts/item-ids.json', JSON.stringify(uniqueItemIds, null, 2));
  console.log(`Refreshed and saved ${uniqueItemIds.length} item IDs to scripts/item-ids.json`);
}

// CLI flag logic
// CLI logic: only generate if scripts/item-ids.json does not exist
if (require.main === module) {
  if (fs.existsSync('scripts/item-ids.json')) {
    console.log('scripts/item-ids.json already exists. No action taken.');
    process.exit(0);
  }
  refreshItemIds();
}
