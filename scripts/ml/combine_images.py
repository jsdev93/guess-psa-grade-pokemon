#!/usr/bin/env python3
"""
Combine front and back card images into side-by-side pairs for comprehensive PSA grading.
This creates combined images that show both sides of each card for better ML training.
"""
import os
from pathlib import Path
from PIL import Image
import argparse

def combine_front_back_images(dataset_dir, output_dir=None, target_size=(224, 224)):
    """
    Combine front and back images into side-by-side pairs.
    
    Args:
        dataset_dir: Directory containing grade folders with front/back images
        output_dir: Directory to save combined images (default: dataset_combined)  
        target_size: Size to resize each individual image before combining
    """
    dataset_path = Path(dataset_dir)
    output_path = Path(output_dir or f"{dataset_dir}_combined")
    output_path.mkdir(exist_ok=True)
    
    stats = {
        'total_pairs': 0,
        'successful_pairs': 0,
        'missing_back': 0,
        'missing_front': 0,
        'by_grade': {}
    }
    
    print(f"Combining images from {dataset_path} → {output_path}")
    print(f"Target size per image: {target_size}")
    print(f"Combined image size: {target_size[0]*2}x{target_size[1]}")
    
    # Process each grade folder
    for grade_folder in sorted(dataset_path.iterdir()):
        if not grade_folder.is_dir():
            continue
            
        grade = grade_folder.name
        print(f"\nProcessing Grade {grade}...")
        
        # Create output grade folder
        output_grade_dir = output_path / grade
        output_grade_dir.mkdir(exist_ok=True)
        
        # Initialize grade stats
        stats['by_grade'][grade] = {
            'attempted': 0,
            'successful': 0,
            'missing_back': 0,
            'missing_front': 0
        }
        
        # Group images by item ID
        image_pairs = {}
        for img_file in grade_folder.glob('*.jpg'):
            # Parse filename: itemId_side.jpg
            parts = img_file.stem.split('_')
            if len(parts) >= 2:
                item_id = '_'.join(parts[:-1])  # Everything except last part
                side = parts[-1]  # front or back
                
                if item_id not in image_pairs:
                    image_pairs[item_id] = {}
                image_pairs[item_id][side] = img_file
        
        # Combine pairs
        for item_id, sides in image_pairs.items():
            stats['by_grade'][grade]['attempted'] += 1
            stats['total_pairs'] += 1
            
            front_path = sides.get('front')
            back_path = sides.get('back')
            
            if not front_path:
                print(f"  Missing front image for {item_id}")
                stats['by_grade'][grade]['missing_front'] += 1
                stats['missing_front'] += 1
                continue
                
            if not back_path:
                print(f"  Missing back image for {item_id}")
                stats['by_grade'][grade]['missing_back'] += 1 
                stats['missing_back'] += 1
                continue
            
            try:
                # Load and resize images
                front_img = Image.open(front_path).convert('RGB')
                back_img = Image.open(back_path).convert('RGB')
                
                front_img = front_img.resize(target_size, Image.LANCZOS)
                back_img = back_img.resize(target_size, Image.LANCZOS)
                
                # Create combined image (side-by-side)
                combined_width = target_size[0] * 2
                combined_height = target_size[1]
                combined_img = Image.new('RGB', (combined_width, combined_height))
                
                # Paste front on left, back on right
                combined_img.paste(front_img, (0, 0))
                combined_img.paste(back_img, (target_size[0], 0))
                
                # Save combined image
                output_file = output_grade_dir / f"{item_id}_combined.jpg"
                combined_img.save(output_file, quality=95)
                
                stats['by_grade'][grade]['successful'] += 1
                stats['successful_pairs'] += 1
                
                if stats['successful_pairs'] % 100 == 0:
                    print(f"  Created {stats['successful_pairs']} combined images...")
                
            except Exception as e:
                print(f"  Error combining {item_id}: {e}")
    
    # Print final statistics
    print("\n" + "="*60)
    print("IMAGE COMBINATION COMPLETE")
    print("="*60)
    print(f"Total image pairs attempted: {stats['total_pairs']}")
    print(f"Successful combinations: {stats['successful_pairs']}")
    print(f"Missing front images: {stats['missing_front']}")
    print(f"Missing back images: {stats['missing_back']}")
    
    print(f"\nCombined images by grade:")
    for grade in sorted(stats['by_grade'].keys()):
        successful = stats['by_grade'][grade]['successful']
        attempted = stats['by_grade'][grade]['attempted']
        print(f"  Grade {grade}: {successful}/{attempted} pairs")
    
    print(f"\nCombined dataset location: {output_path.absolute()}")
    
    if stats['successful_pairs'] > 0:
        print(f"\n✅ SUCCESS! Created {stats['successful_pairs']} combined images")
        print(f"📐 Each combined image: {target_size[0]*2}x{target_size[1]} pixels")
        print(f"🎯 Ready for ML training with: python3 ml_starter.py")
        print(f"    (Update config.DATA_DIR = '{output_path.name}')")
    else:
        print(f"\n❌ No successful combinations created")
        
    return stats

def main():
    parser = argparse.ArgumentParser(description="Combine front/back card images for PSA grading")
    parser.add_argument('--dataset', '-d', default='dataset', 
                       help='Dataset directory with front/back images (default: dataset)')
    parser.add_argument('--output', '-o',
                       help='Output directory for combined images (default: dataset_combined)')
    parser.add_argument('--size', '-s', nargs=2, type=int, default=[224, 224],
                       metavar=('WIDTH', 'HEIGHT'),
                       help='Target size for each individual image (default: 224 224)')
    
    args = parser.parse_args()
    
    if not Path(args.dataset).exists():
        print(f"❌ Error: Dataset directory '{args.dataset}' not found!")
        return 1
    
    target_size = tuple(args.size)
    stats = combine_front_back_images(args.dataset, args.output, target_size)
    
    if stats['successful_pairs'] > 0:
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(main())