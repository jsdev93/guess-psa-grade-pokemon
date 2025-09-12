// Utility to load item IDs from the generated JSON file
import fs from "fs";

export function getRandomItemId() {
  try {
    const data = fs.readFileSync("scripts/ml/output.filtered.json", "utf-8");
    const ids = JSON.parse(data);
    if (!Array.isArray(ids) || ids.length === 0) return null;
    const idx = Math.floor(Math.random() * ids.length);
    return ids[idx];
  } catch (e) {
    return e;
  }
}
