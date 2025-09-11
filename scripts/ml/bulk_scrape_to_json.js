// bulk_scrape_to_json.js
// Usage: node scripts/bulk_scrape_to_json.js <itemIdsFile> <outputFile>
// <itemIdsFile>: text file with one eBay item ID per line
// <outputFile>: JSON file to write array of {id, cert, grade, imgUrlFront, imgUrlBack}


import fs from 'fs';
import { exec } from 'child_process';


const [,, itemIdsFileOrJson, outputFile] = process.argv;
if (!outputFile) {
  console.error('Usage: node scripts/bulk_scrape_to_json.js <itemIdsFile|item-ids.json> <outputFile>');
  process.exit(1);
}

let itemIds = [];
if (!itemIdsFileOrJson) {
  // Default to scripts/item-ids.json
  const ids = JSON.parse(fs.readFileSync('scripts/item-ids.json', 'utf-8'));
  if (!Array.isArray(ids) || ids.length === 0) {
    console.error('No item IDs found in scripts/item-ids.json');
    process.exit(1);
  }
  itemIds = ids;
} else if (itemIdsFileOrJson.endsWith('.json')) {
  // Use provided JSON file
  const ids = JSON.parse(fs.readFileSync(itemIdsFileOrJson, 'utf-8'));
  if (!Array.isArray(ids) || ids.length === 0) {
    console.error('No item IDs found in', itemIdsFileOrJson);
    process.exit(1);
  }
  itemIds = ids;
} else {
  // Use text file (one ID per line)
  itemIds = fs.readFileSync(itemIdsFileOrJson, 'utf-8').split(/\r?\n/).filter(Boolean);
}

async function runOcrScript(itemId) {
  return new Promise((resolve) => {
    exec(`node scripts/ocr_cert_from_ebay.js ${itemId}`, { cwd: process.cwd() }, (error, stdout) => {
      if (error) {
        resolve({ id: itemId, error: error.message });
        return;
      }
      try {
        const parsed = JSON.parse(stdout);
        resolve({ id: itemId, ...parsed });
      } catch {
        resolve({ id: itemId, error: 'Failed to parse OCR output' });
      }
    });
  });
}

(async () => {
  const results = [];
  for (const id of itemIds) {
    console.log(`Processing ${id}...`);
    const result = await runOcrScript(id);
    results.push(result);
  }
  fs.writeFileSync(outputFile, JSON.stringify(results, null, 2));
  console.log(`Done. Wrote ${results.length} results to ${outputFile}`);
})();
