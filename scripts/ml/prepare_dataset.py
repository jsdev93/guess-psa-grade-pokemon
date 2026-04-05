#!/usr/bin/env python3
"""
Dataset preparation script for PSA grade prediction.
Downloads images from JSON data and organizes by grade folders.
"""
import os
import json
import requests
from urllib.parse import urlparse
import time
from pathlib import Path
import hashlib
from PIL import Image
import io

class DatasetPreparer:
    def __init__(self, json_file, output_dir='dataset', max_images_per_grade=None):
        self.json_file = json_file
        self.output_dir = Path(output_dir)
        self.max_images_per_grade = max_images_per_grade
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'downloaded': 0,
            'failed': 0,
            'skipped_duplicates': 0,
            'by_grade': {}
        }
        
        # Track downloaded images to avoid duplicates
        self.downloaded_hashes = set()
        
    def load_data(self):
        """Load JSON data from file"""
        print(f"Loading data from {self.json_file}...")
        with open(self.json_file, 'r') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} items")
        return data
        
    def get_image_hash(self, image_content):
        """Generate hash for image content to detect duplicates"""
        return hashlib.md5(image_content).hexdigest()
        
    def download_image(self, url, retries=3):
        """Download image from URL with retries"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30, stream=True)
                response.raise_for_status()
                
                # Check if it's a valid image
                image_content = response.content
                try:
                    # Verify it's a valid image
                    with Image.open(io.BytesIO(image_content)) as img:
                        # Convert to RGB if needed (removes any transparency)
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        # Save as JPEG to standardize format
                        output = io.BytesIO()
                        img.save(output, format='JPEG', quality=95)
                        return output.getvalue()
                        
                except Exception as e:
                    print(f"Invalid image from {url}: {e}")
                    return None
                    
            except Exception as e:
                if attempt < retries - 1:
                    print(f"Download attempt {attempt + 1} failed for {url}: {e}")
                    time.sleep(1)
                else:
                    print(f"Final download failed for {url}: {e}")
                    return None
        return None
        
    def save_image(self, image_content, grade, item_id, image_type='front'):
        """Save image to appropriate grade folder"""
        grade_dir = self.output_dir / str(grade)
        grade_dir.mkdir(exist_ok=True)
        
        # Generate filename
        filename = f"{item_id}_{image_type}.jpg"
        filepath = grade_dir / filename
        
        # Check for duplicates using content hash
        image_hash = self.get_image_hash(image_content)
        if image_hash in self.downloaded_hashes:
            self.stats['skipped_duplicates'] += 1
            return False
            
        # Save image
        with open(filepath, 'wb') as f:
            f.write(image_content)
            
        # Track hash to prevent duplicates
        self.downloaded_hashes.add(image_hash)
        
        return True
        
    def process_item(self, item):
        """Process a single item from the JSON data"""
        grade = item['grade']
        item_id = item['id']
        
        # Initialize grade stats if needed
        if grade not in self.stats['by_grade']:
            self.stats['by_grade'][grade] = {'attempted': 0, 'downloaded': 0, 'failed': 0}
            
        self.stats['by_grade'][grade]['attempted'] += 1
        
        # Check if we've reached max images for this grade
        if (self.max_images_per_grade and 
            self.stats['by_grade'][grade]['downloaded'] >= self.max_images_per_grade):
            return
        
        downloaded_any = False
        
        # Download front image (primary)
        if 'imgUrlFront' in item and item['imgUrlFront']:
            print(f"Downloading front image for Grade {grade} - Item {item_id}")
            image_content = self.download_image(item['imgUrlFront'])
            if image_content:
                if self.save_image(image_content, grade, item_id, 'front'):
                    downloaded_any = True
                    
        # Download back image (essential for complete PSA grade evaluation)
        if 'imgUrlBack' in item and item['imgUrlBack']:
            print(f"Downloading back image for Grade {grade} - Item {item_id}")
            image_content = self.download_image(item['imgUrlBack'])
            if image_content:
                if self.save_image(image_content, grade, item_id, 'back'):
                    downloaded_any = True
        
        # Update stats
        if downloaded_any:
            self.stats['downloaded'] += 1
            self.stats['by_grade'][grade]['downloaded'] += 1
        else:
            self.stats['failed'] += 1
            self.stats['by_grade'][grade]['failed'] += 1
            
        self.stats['total_processed'] += 1
        
        # Small delay to be respectful to the server
        time.sleep(0.5)
        
    def prepare_dataset(self):
        """Main function to prepare the dataset"""
        print("Starting dataset preparation...")
        print(f"Output directory: {self.output_dir.absolute()}")
        
        if self.max_images_per_grade:
            print(f"Max images per grade: {self.max_images_per_grade}")
        
        data = self.load_data()
        
        # Group by grade to see distribution
        grade_counts = {}
        for item in data:
            grade = item['grade']
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
            
        print("\nGrade distribution in source data:")
        for grade in sorted(grade_counts.keys()):
            print(f"  Grade {grade}: {grade_counts[grade]} items")
        print()
        
        # Process each item
        for i, item in enumerate(data, 1):
            print(f"\nProgress: {i}/{len(data)}")
            self.process_item(item)
            
            # Progress update every 10 items
            if i % 10 == 0:
                self.print_progress()
                
        # Final statistics
        self.print_final_stats()
        
    def print_progress(self):
        """Print current progress"""
        print(f"Downloaded: {self.stats['downloaded']}, Failed: {self.stats['failed']}, "
              f"Duplicates skipped: {self.stats['skipped_duplicates']}")
              
    def print_final_stats(self):
        """Print final statistics"""
        print("\n" + "="*60)
        print("DATASET PREPARATION COMPLETE")
        print("="*60)
        print(f"Total items processed: {self.stats['total_processed']}")
        print(f"Images downloaded: {self.stats['downloaded']}")
        print(f"Failed downloads: {self.stats['failed']}")
        print(f"Duplicate images skipped: {self.stats['skipped_duplicates']}")
        
        print("\nFinal dataset by grade:")
        total_images = 0
        for grade in sorted(self.stats['by_grade'].keys()):
            downloaded = self.stats['by_grade'][grade]['downloaded']
            total_images += downloaded
            print(f"  Grade {grade}: {downloaded} images")
            
        print(f"\nTotal images in dataset: {total_images}")
        print(f"Dataset location: {self.output_dir.absolute()}")
        
        # Check for potential issues
        if total_images < 100:
            print("\n⚠️  WARNING: Dataset is quite small (<100 images). Consider:")
            print("   - Downloading more data")
            print("   - Using data augmentation heavily")
            print("   - Using a pre-trained model with transfer learning")
            
        # Check for imbalanced grades
        min_grade_count = min(self.stats['by_grade'][g]['downloaded'] 
                             for g in self.stats['by_grade'])
        max_grade_count = max(self.stats['by_grade'][g]['downloaded'] 
                             for g in self.stats['by_grade'])
        
        if max_grade_count > min_grade_count * 3:
            print("\n⚠️  WARNING: Dataset is imbalanced. Consider:")
            print("   - Using class weights in training")
            print("   - Oversampling minority classes")
            print("   - Collecting more data for underrepresented grades")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Prepare PSA grade dataset from JSON")
    parser.add_argument('--input', '-i', default='output.filtered.json',
                       help='Input JSON file (default: output.filtered.json)')
    parser.add_argument('--output', '-o', default='dataset',
                       help='Output directory (default: dataset)')
    parser.add_argument('--max-per-grade', type=int,
                       help='Maximum images per grade (for testing with smaller dataset)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found!")
        print("Make sure you have the scraped data JSON file.")
        return 1
        
    preparer = DatasetPreparer(
        json_file=args.input,
        output_dir=args.output,
        max_images_per_grade=args.max_per_grade
    )
    
    try:
        preparer.prepare_dataset()
        print(f"\n✅ Dataset preparation successful!")
        print(f"You can now run: python ml_starter.py")
        return 0
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())