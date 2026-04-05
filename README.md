# Guess PSA Grade

A web app game and dataset pipeline for guessing the PSA grade of Pokémon cards using real eBay images and prices.

## Features

- Real eBay Pokémon card slab images (front and back)
- Guess the PSA grade (1-10)
- Toggleable price hint (hidden by default)
- Score tracking and session stats
- **🎯 Advanced ML Pipeline**: PSA grade prediction with 9/10 optimization
- **Professional-grade Training**: Transfer learning, custom loss functions, early stopping
- **Complete Card Assessment**: Front+back image analysis like real PSA graders
- **High-value Focus**: 5x weighting for PSA 9/10 classification accuracy
- Bulk scraping and dataset creation for ML
- Fast, robust DOM-based extraction (no OCR)
- Built with Next.js, React, and Tailwind CSS

## Getting Started

### Prerequisites

- Node.js (v18 or higher recommended)
- npm or yarn
- **Python 3.8+** (for ML pipeline)
- **PyTorch & Dependencies** (auto-installed via requirements.txt)
- GPU recommended for faster training (CUDA-compatible)

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

## Quick Start: ML Pipeline

To train your own PSA grade prediction model:

```bash
# 1. Navigate to ML directory
cd scripts/ml

# 2. Auto-setup and train (recommended)
./setup_and_train.sh

# 3. Or manual setup:
pip3 install -r requirements.txt
python3 prepare_dataset.py
python3 ml_starter.py --combined
```

**Requirements:** Pre-existing `output.filtered.json` with scraped card data.

See **Data Pipeline & Scripts** section below for complete data collection process.

## Data Pipeline & Scripts

### 1. Generate eBay Item IDs

Fetches a list of eBay item IDs for PSA Pokémon cards: (delete item-ids.json to refresh)

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

Scrape thousands of eBay items and save to a JSON file (run every 3 months as eBay removes hosted images):

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

### 5. Machine Learning Pipeline

#### 5a. Prepare Dataset (Download Images)

Downloads and organizes card images from JSON data by PSA grade:

```bash
cd scripts/ml
python3 prepare_dataset.py
```

Options:

- `--input output.filtered.json` - Input JSON file (default)
- `--output dataset` - Output directory (default)
- `--max-per-grade 50` - Limit images per grade for testing

Creates folder structure: `dataset/1/`, `dataset/2/`, ..., `dataset/10/`
Downloads both front and back images for comprehensive PSA evaluation.

#### 5b. Combine Front+Back Images (Optional)

Creates side-by-side front+back image pairs for complete card assessment:

```bash
python3 combine_images.py --dataset dataset --output dataset_combined
```

Produces 448x224 combined images showing both card sides, essential for accurate PSA grading.

#### 5c. Train PSA Grade Prediction Model

Train a deep learning model optimized for PSA grade classification:

```bash
# Train on front images only (faster)
python3 ml_starter.py

# Train on combined front+back images (more accurate)
python3 ml_starter.py --combined
```

**Features:**

- **🎯 PSA 9/10 Optimization**: 5x class weighting for premium grades
- **Custom Loss Function**: 10x penalty for 9/10 misclassification errors
- **Transfer Learning**: ResNet50 pre-trained on ImageNet
- **Early Stopping**: Prevents overfitting with patience-based stopping
- **Comprehensive Evaluation**: Specialized metrics for high-value card accuracy
- **Data Augmentation**: Rotation, flipping, color jitter for robust training

**Output:**

- `models/best_psa_grade_model.pth` - Trained model
- `logs/evaluation_results.json` - Performance metrics including PSA 9/10 analysis
- `logs/confusion_matrix.png` - Confusion matrix with highlighted premium region
- `logs/training_history.png` - Training progress with PSA 9/10 tracking

#### 5d. Automated Setup (Recommended)

Complete pipeline automation with user prompts:

```bash
./setup_and_train.sh
```

This script:

- ✅ Installs Python dependencies
- ✅ Prepares dataset with front+back images
- ✅ Offers training mode selection (single vs combined)
- ✅ Handles the complete ML pipeline automatically
- ✅ Provides dataset statistics and warnings

### 6. Model Prediction

Use the trained model to predict PSA grades on new card images:

```python
from ml_starter import predict_image, PSAGradeConfig

# For single card images
config = PSAGradeConfig()
grade, confidence = predict_image('models/best_psa_grade_model.pth', 'card.jpg', config)

# For combined front+back images
config = PSAGradeConfig(use_combined_images=True)
grade, confidence = predict_image('models/best_psa_grade_model.pth', 'combined_card.jpg', config)

print(f'Predicted PSA Grade: {grade} (Confidence: {confidence:.2f})')
```

## Game & API

- `src/app/game/` - Game UI (guess grade, toggle price, zoom images)
- `src/app/api/random-pokemon/` - API route for random eBay card (uses the scraping pipeline)
- `scripts/ml/` - **Complete ML pipeline** for PSA grade prediction training and inference
- `public/` - Static assets
- `scripts/` - All scraping and dataset scripts

**ML Integration Potential:**

- Trained models can be integrated into the API for automated PSA grade suggestions
- Compare human predictions vs AI predictions for educational gameplay
- Use model confidence scores to highlight challenging cards

## Technologies Used

**Frontend & Game:**

- [Next.js](https://nextjs.org/) - React framework
- [React](https://react.dev/) - UI framework
- [Tailwind CSS](https://tailwindcss.com/) - Styling

**Data Collection:**

- [Puppeteer](https://pptr.dev/) - Web scraping
- [JavaScript](https://developer.mozilla.org/en-US/JavaScript) - Scraping automation

**Machine Learning:**

- [PyTorch](https://pytorch.org/) - Deep learning framework
- [torchvision](https://pytorch.org/vision/) - Computer vision models
- [ResNet50](https://pytorch.org/vision/main/models/resnet.html) - Transfer learning backbone
- [scikit-learn](https://scikit-learn.org/) - Evaluation metrics
- [matplotlib](https://matplotlib.org/) + [seaborn](https://seaborn.pydata.org/) - Visualization
- [Pillow (PIL)](https://pillow.readthedocs.io/) - Image processing
- [NumPy](https://numpy.org/) - Numerical computing

**Development:**

- [Python 3](https://www.python.org/) - ML pipeline
- [Node.js](https://nodejs.org/) - Scraping pipeline

## Notes

**Data Collection:**

- The scraping pipeline is fast and robust: blocks unnecessary resources, extracts grade and price directly from the DOM, and outputs only needed fields
- All scripts output pure JSON for easy ML dataset creation
- Handles thousands of eBay listings with rate limiting and error recovery

**Machine Learning:**

- **Professional-grade PSA grading**: Model trained specifically for PSA 9/10 distinction (most financially important)
- **Transfer learning approach**: Leverages ImageNet-pretrained ResNet50 for robust feature extraction
- **Custom loss functions**: Heavy penalties for high-value grade misclassifications
- **Complete card assessment**: Processes both front and back images like real PSA graders
- **Early stopping & validation**: Prevents overfitting with comprehensive accuracy tracking
- **Production ready**: Includes model checkpointing, evaluation metrics, and inference pipeline

**Game Integration:**

- The game UI shows price hints (from eBay) hidden by default with toggle functionality
- Real eBay slab images provide authentic grading practice experience
- Score tracking helps users improve their PSA grading skills over time

## License

MIT
