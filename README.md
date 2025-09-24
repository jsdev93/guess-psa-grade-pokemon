# Guess PSA Grade

A web app game and dataset pipeline for guessing the PSA grade of Pokémon cards using real eBay images and prices.

## Features

- Real eBay Pokémon card slab images (front and back)
- Guess the PSA grade (1-10)
- Toggleable price hint (hidden by default)
- Score tracking and session stats
- Bulk scraping and dataset creation for ML
- Fast, robust DOM-based extraction (no OCR)
- Built with Next.js, React, and Tailwind CSS

## Getting Started

### Prerequisites

- Node.js (v18 or higher recommended)
- npm or yarn
- Python 3 (for dataset image download)

### Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd guess-psa-grade-pokemon
   ```
2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

### Running the Development Server

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) to view the app.

## Data Pipeline & Scripts

### 1. Generate eBay Item IDs

Fetches a list of eBay item IDs for PSA Pokémon cards: (delete item-ids.json)

```bash
node scripts/generate_item_ids.js
```

Creates/updates `scripts/item-ids.json` with 12-digit eBay item IDs.

### 2. Scrape Card Data (Grade, Price, Images)

Scrape a single eBay item for grade, price, and high-res images (testing purposes):

```bash
node scripts/ocr_cert_from_ebay.js <itemId>
```

Outputs JSON: `{ grade, imgUrlFront, imgUrlBack, price }`

### 3. Bulk Scrape Many Items

Scrape 5K eBay items and save to a JSON file (run this every 3 months as eBay will remove hosted imgs):

```bash
node scripts/ml/bulk_scrape_to_json.js scripts/item-ids.json scripts/ml/output.json
```

Each entry: `{ id, grade, imgUrlFront, imgUrlBack, price, certNumber }`

### 4. Filter Out Invalid Entries

Removes entries without a valid numeric grade from the scraped output:

```bash
node scripts/filter_output.js
```

Creates `scripts/ml/output.filtered.json` containing only valid graded entries.

<!-- ### 4. Download Images by Grade (for ML, ignore mostly)

Download all images from a JSON dataset, organized by grade:

```bash
python3 scripts/download_images_by_grade.py output.json dataset/
```

Images are saved as `dataset/<grade>/<id>_imgUrlFront_...` and `dataset/<grade>/<id>_imgUrlBack_...` -->

## Game & API

- `src/app/game/` - Game UI (guess grade, toggle price, zoom images)
- `src/app/api/random-pokemon/` - API route for random eBay card (uses the scraping pipeline)
- `public/` - Static assets
- `scripts/` - All scraping and dataset scripts

## Technologies Used

- [Next.js](https://nextjs.org/)
- [React](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Puppeteer](https://pptr.dev/) (scraping)
- [Python 3](https://www.python.org/) (image download)

## Notes

- The scraping pipeline is fast and robust: it blocks unnecessary resources, extracts grade and price directly from the DOM, and outputs only the needed fields.
- The game UI shows a price hint (from eBay) that is hidden by default and can be toggled.
- All scripts output pure JSON for easy ML dataset creation.

## License

MIT
