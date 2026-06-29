#!/usr/bin/env python3
"""Harvest CN method patent IDs from Google Patents for AI/ML domains.

Queries multiple technical domains to collect ~100 method-focused patents,
then downloads PDFs for offline analysis.
"""

import re
import time
import json
import requests
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path.home() / "paper2patent" / "data" / "patents"
PID_FILE = OUTPUT_DIR / "patent_ids.json"
PDF_DIR = OUTPUT_DIR / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# AI/ML domains for CN method patent search
# Each query targets method-type patents (发明 rather than 实用新型)
SEARCH_QUERIES = [
    # Computer Vision
    "image recognition neural network method device CN patent",
    "object detection deep learning method CN patent",
    "image segmentation convolutional neural network CN patent",
    "target tracking computer vision method CN patent",
    "image generation generative model method CN patent",

    # NLP
    "natural language processing transformer method CN patent",
    "text classification attention mechanism method CN patent",
    "language model training method device CN patent",
    "machine translation neural network method CN patent",
    "text generation large language model method CN patent",

    # Neural Network Architecture
    "neural network model compression method CN patent",
    "knowledge distillation deep learning method CN patent",
    "graph neural network training method CN patent",
    "reinforcement learning decision method device CN patent",
    "federated learning privacy preserving method CN patent",

    # Speech & Audio
    "speech recognition deep neural network method CN patent",
    "voice synthesis text to speech method CN patent",

    # Recommendation & Data
    "recommendation system collaborative filtering method CN patent",
    "anomaly detection machine learning method CN patent",
    "data augmentation training method CN patent",

    # Autonomous Driving / Robotics
    "autonomous driving trajectory prediction method CN patent",
    "path planning neural network method device CN patent",
    "multi-sensor fusion perception method CN patent",
    "scene understanding semantic segmentation method CN patent",
    "motion prediction trajectory generation method CN patent",
]


def search_google_patents(query: str, num_results: int = 12) -> list[str]:
    """Search Google Patents and return list of CN patent IDs."""
    patent_ids = []

    # Google Patents search URL
    url = f"https://patents.google.com/?q={requests.utils.quote(query)}&num={num_results}&language=ZH"

    headers = {"User-Agent": USER_AGENT}

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code}")
            return patent_ids

        # Extract CN patent IDs from the response
        # Google Patents results contain links like /patent/CN114XXXXXXA/zh
        pattern = re.compile(r'/patent/(CN\d+[A-Z])')
        matches = pattern.findall(resp.text)
        patent_ids = list(set(matches))  # deduplicate

        print(f"  Found {len(patent_ids)} patents")
    except Exception as e:
        print(f"  Error: {e}")

    return patent_ids


def download_patent_pdf(patent_id: str) -> bool:
    """Download a patent PDF from Google Patents direct URL."""
    pdf_path = PDF_DIR / f"{patent_id}.pdf"
    if pdf_path.exists():
        return True  # already downloaded

    # Direct PDF URL from Google Patents storage
    url = f"https://patentimages.storage.googleapis.com/pdfs/{patent_id}.pdf"

    headers = {"User-Agent": USER_AGENT}

    try:
        resp = requests.get(url, headers=headers, timeout=60)
        if resp.status_code == 200 and len(resp.content) > 10000:
            with open(pdf_path, "wb") as f:
                f.write(resp.content)
            return True
        else:
            return False
    except Exception as e:
        return False


def main():
    print(f"Output dir: {OUTPUT_DIR}")
    print()

    # Phase 1: Collect patent IDs
    if PID_FILE.exists():
        print("Loading existing patent IDs...")
        with open(PID_FILE) as f:
            all_ids = json.load(f)
        print(f"Loaded {len(all_ids)} patent IDs")
    else:
        all_ids = set()
        print("Searching Google Patents for AI/ML method patents...")
        print(f"Total queries: {len(SEARCH_QUERIES)}")
        print()

        for i, query in enumerate(SEARCH_QUERIES, 1):
            domain = query.split(" method")[0]
            print(f"[{i}/{len(SEARCH_QUERIES)}] {domain}")

            ids = search_google_patents(query)
            all_ids.update(ids)

            # Rate limiting
            time.sleep(3)

        all_ids = sorted(list(all_ids))
        print(f"\nTotal unique CN patents: {len(all_ids)}")

        # Save
        with open(PID_FILE, "w") as f:
            json.dump(all_ids, f, indent=2, ensure_ascii=False)
        print(f"Saved to {PID_FILE}")

    # Phase 2: Download PDFs
    print(f"\nDownloading PDFs...")
    success = 0
    failed = 0

    for i, pid in enumerate(all_ids):
        if (i + 1) % 20 == 0:
            print(f"  [{i+1}/{len(all_ids)}] {success} OK, {failed} fail")

        if download_patent_pdf(pid):
            success += 1
        else:
            failed += 1

        time.sleep(1.5)  # rate limit

    print(f"\nDone: {success} downloaded, {failed} failed")
    print(f"PDFs saved to: {PDF_DIR}")


if __name__ == "__main__":
    main()
