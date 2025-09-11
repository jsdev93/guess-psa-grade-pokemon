# download_images_by_grade.py
"""
Download card images from a JSON file (output from bulk_scrape_to_json.js)
Organize images into folders by grade for ML training.

Usage:
    python3 scripts/download_images_by_grade.py output.json dataset/
"""
import os
import sys
import requests
from urllib.parse import urlparse

if len(sys.argv) != 3:
    print("Usage: python3 scripts/download_images_by_grade.py <input_json> <output_dir>")
    sys.exit(1)

input_json = sys.argv[1]
output_dir = sys.argv[2]

import json
with open(input_json, 'r') as f:
    items = json.load(f)

def safe_filename(url):
    return os.path.basename(urlparse(url).path).split('?')[0]

def download(url, out_path):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        with open(out_path, 'wb') as f:
            f.write(r.content)
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

for item in items:
    grade = str(item.get('grade', 'unknown'))
    for side in ['imgUrlFront', 'imgUrlBack']:
        url = item.get(side)
        if not url:
            continue
        folder = os.path.join(output_dir, grade)
        os.makedirs(folder, exist_ok=True)
        fname = f"{item.get('id','unknown')}_{side}_{safe_filename(url)}"
        out_path = os.path.join(folder, fname)
        if not os.path.exists(out_path):
            print(f"Downloading {url} -> {out_path}")
            download(url, out_path)
