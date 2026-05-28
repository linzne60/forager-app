"""
Downloads additional images from iNaturalist API for all 105 species.

Targets:
    - 1,500 images per species (baseline)
    - 2,500 images for species that scored under 85% in the B7 confusion matrix

Skips images already in data/raw/ and respects iNaturalist API rate limits.

Usage (from project root):
    python ml/scripts/download_inat.py
    python ml/scripts/download_inat.py --dry-run        # preview counts only
    python ml/scripts/download_inat.py --species elderberry  # single species
"""

import argparse
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent.parent
SPECIES_JSON = ML_DIR / "configs" / "species.json"
OUTPUT_DIR = ML_DIR / "data" / "raw"

BASELINE_TARGET = 1500
BOOST_TARGET = 2500

BOOST_SPECIES = {
    "elderberry", "black_walnut", "highbush_blueberry", "butternut",
    "red_raspberry", "hackberry", "shagbark_hickory", "red_mulberry",
    "black_raspberry", "wild_grape", "chanterelle", "persimmon",
    "red_elderberry", "chicken_of_the_woods", "lowbush_blueberry",
    "american_elderberry", "smooth_chanterelle",
    "white_pored_chicken_of_the_woods", "white_mulberry", "muscadine",
}

API_BASE = "https://api.inaturalist.org/v1/observations"
HEADERS = {"User-Agent": "ForagerAI/1.0 (educational project)"}
PER_PAGE = 200
API_DELAY = 1.0
DOWNLOAD_DELAY = 0.1


def get_target(class_name):
    if class_name in BOOST_SPECIES:
        return BOOST_TARGET
    return BASELINE_TARGET


def get_existing_count(class_name):
    species_dir = OUTPUT_DIR / class_name
    if not species_dir.exists():
        return 0
    return len(list(species_dir.glob("*")))


def fetch_observations(scientific_name, page=1):
    params = urllib.parse.urlencode({
        "taxon_name": scientific_name,
        "quality_grade": "research",
        "photos": "true",
        "per_page": PER_PAGE,
        "page": page,
        "order": "desc",
        "order_by": "votes",
    })
    url = f"{API_BASE}?{params}"

    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def extract_photo_urls(observations):
    urls = []
    for obs in observations:
        for photo in obs.get("photos", []):
            photo_id = photo["id"]
            url = photo.get("url", "")
            if url:
                medium_url = url.replace("/square.", "/medium.")
                urls.append((photo_id, medium_url))
    return urls


def download_image(url, dest_path):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            if len(data) < 1000:
                return False
            dest_path.write_bytes(data)
            return True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return False


def download_species(class_name, scientific_name, dry_run=False):
    target = get_target(class_name)
    existing = get_existing_count(class_name)
    needed = target - existing

    if needed <= 0:
        print(f"  {class_name:45} {existing:>5} existing, target {target} — SKIP")
        return 0

    print(f"  {class_name:45} {existing:>5} existing, target {target}, need {needed}")

    if dry_run:
        return 0

    species_dir = OUTPUT_DIR / class_name
    species_dir.mkdir(parents=True, exist_ok=True)

    existing_files = {f.stem for f in species_dir.glob("*")}

    downloaded = 0
    page = 1
    consecutive_failures = 0
    max_consecutive_failures = 20

    while downloaded < needed:
        try:
            data = fetch_observations(scientific_name, page=page)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"    API error on page {page}: {e}")
            break

        results = data.get("results", [])
        if not results:
            break

        photo_urls = extract_photo_urls(results)

        for photo_id, url in photo_urls:
            if downloaded >= needed:
                break

            filename = f"inat_{photo_id}"
            if filename in existing_files:
                continue

            dest = species_dir / f"{filename}.jpg"
            if download_image(url, dest):
                downloaded += 1
                existing_files.add(filename)
                consecutive_failures = 0

                if downloaded % 50 == 0:
                    print(f"    {downloaded}/{needed} downloaded...")
            else:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    print(f"    Too many consecutive failures, moving on")
                    break

            time.sleep(DOWNLOAD_DELAY)

        if consecutive_failures >= max_consecutive_failures:
            break

        total_results = data.get("total_results", 0)
        if page * PER_PAGE >= total_results:
            print(f"    Exhausted all {total_results} observations (got {downloaded})")
            break

        page += 1
        time.sleep(API_DELAY)

    print(f"    Done: +{downloaded} images (total now: {existing + downloaded})")
    return downloaded


def main():
    parser = argparse.ArgumentParser(description="Download images from iNaturalist API")
    parser.add_argument("--dry-run", action="store_true", help="Preview counts without downloading")
    parser.add_argument("--species", type=str, help="Download for a single species only")
    args = parser.parse_args()

    with open(SPECIES_JSON) as f:
        all_species = json.load(f)["species"]

    if args.species:
        all_species = [s for s in all_species if s["class_name"] == args.species]
        if not all_species:
            print(f"Species '{args.species}' not found in species.json")
            return

    all_species.sort(key=lambda s: s["class_name"])

    print(f"{'DRY RUN — ' if args.dry_run else ''}Downloading images for {len(all_species)} species")
    print(f"Baseline target: {BASELINE_TARGET} | Boost target: {BOOST_TARGET}")
    print(f"Boost species: {len(BOOST_SPECIES)}\n")

    total_downloaded = 0
    for i, s in enumerate(all_species):
        class_name = s["class_name"]
        scientific_name = s["scientific_name"]
        print(f"[{i+1}/{len(all_species)}] {class_name} ({scientific_name})")

        downloaded = download_species(class_name, scientific_name, dry_run=args.dry_run)
        total_downloaded += downloaded

    print(f"\nTotal downloaded: {total_downloaded} images")


if __name__ == "__main__":
    main()
