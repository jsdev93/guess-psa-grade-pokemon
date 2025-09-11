# Guess PSA Grade

A web app game where you guess the PSA grade of a Pokémon card based on its image.

## Features

- Random Pokémon card images
- Guess the PSA grade (1-10)
- Score tracking
- Built with Next.js and Tailwind CSS

## Getting Started

### Generating PSA Item IDs

To play the PSA game with real cert numbers, you need to generate a list of item IDs from eBay:

1. Run the scraping script to fetch item IDs:

   ```bash
   node scripts/generate_item_ids.js
   ```

   This will create or update `scripts/item-ids.json` with a list of 12-digit eBay item IDs.

2. The game API will use a random ID from this file for each round. If the file is empty or missing, it will fall back to a random cert number.

### Prerequisites

- Node.js (v18 or higher recommended)
- npm or yarn

### Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd guess-psa-grade
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

```

Open [http://localhost:3000](http://localhost:3000) to view the app.

## Project Structure

- `src/app/` - Main application code
- `src/app/game/` - Game page
- `src/app/api/random-pokemon/` - API route for random Pokémon
- `public/` - Static assets
- `scripts/generate_item_ids.js` - Script to scrape eBay and generate item-ids.json
- `scripts/item-ids.json` - List of eBay item IDs used for the PSA game

## Technologies Used

- [Next.js](https://nextjs.org/)
- [React](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

## License

MIT
