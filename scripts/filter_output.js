// This script filters output.json to only include entries with a valid numeric grade.
// Usage: node filter_output.js

import fs from "fs";
import path from "path";

const __dirname = path.dirname(new URL(import.meta.url).pathname);
const inputPath = path.join(__dirname, "ml", "output.json");
const outputPath = path.join(__dirname, "ml", "output.filtered.json");

const data = JSON.parse(fs.readFileSync(inputPath, "utf8"));

const filtered = data.filter(
  (item) => typeof item.grade === "number" && !isNaN(item.grade)
);

fs.writeFileSync(outputPath, JSON.stringify(filtered, null, 2));

console.log(
  `Filtered ${
    data.length - filtered.length
  } invalid entries. Output: ${outputPath}`
);
