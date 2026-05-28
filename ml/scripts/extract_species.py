"""
Extracts only the 77 target species from an iNat 2021 train archive.
Maps iNat's long directory names to clean class_name folders in ml/data/raw/.

Supports both the mini (50/species) and full (300/species) archives.

Usage (from project root):
    python ml/scripts/extract_species.py                    # uses full archive
    python ml/scripts/extract_species.py --mini             # uses mini archive

Requires:
    ml/data/train_full.tar.gz   — the full 316GB archive (default)
    ml/data/train_mini.tar.gz   — the 42GB mini archive (--mini)
    ml/configs/species.json     — the 77 species list
"""

import argparse
import json
import tarfile
from pathlib import Path

ARCHIVE_FULL = Path("ml/data/train_full.tar.gz")
ARCHIVE_MINI = Path("ml/data/train_mini.tar.gz")
SPECIES_JSON = Path("ml/configs/species.json")
OUTPUT_DIR = Path("ml/data/raw")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract target species from iNat archive")
    parser.add_argument("--mini", action="store_true", help="Use the mini archive instead of full")
    args = parser.parse_args()

    archive = ARCHIVE_MINI if args.mini else ARCHIVE_FULL

    if not archive.exists():
        print(f"Archive not found: {archive}")
        return

    species = json.loads(SPECIES_JSON.read_text())["species"]

    # Map image_dir_name -> class_name for fast lookup
    # Archive paths look like: train_mini/{image_dir_name}/{uuid}.jpg
    dir_to_class = {s["image_dir_name"]: s["class_name"] for s in species}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for class_name in dir_to_class.values():
        (OUTPUT_DIR / class_name).mkdir(exist_ok=True)

    print(f"Extracting {len(dir_to_class)} species from {archive} ...")
    print(f"Output: {OUTPUT_DIR}/\n")

    extracted = 0
    skipped = 0
    counts: dict[str, int] = {s["class_name"]: 0 for s in species}

    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            # Path format: train/{image_dir_name}/{filename} (or train_mini/...)
            parts = Path(member.name).parts
            if len(parts) != 3:
                continue

            _, dir_name, filename = parts
            if dir_name not in dir_to_class:
                skipped += 1
                continue

            class_name = dir_to_class[dir_name]
            member.name = filename  # strip the prefix — extract just the filename
            tar.extract(member, path=OUTPUT_DIR / class_name, filter="data")
            counts[class_name] += 1
            extracted += 1

            if extracted % 1000 == 0:
                print(f"  {extracted} images extracted...")

    print(f"\nDone. {extracted} images extracted across {len(dir_to_class)} species.")
    print(f"Skipped {skipped} members not in species list.\n")

    print("Image counts per species:")
    for s in sorted(species, key=lambda x: x["class_name"]):
        count = counts[s["class_name"]]
        flag = " *** LOW (<200)" if count < 200 else ""
        print(f"  {s['class_name']:45} {count:>3}{flag}")

    low = [s["class_name"] for s in species if counts[s["class_name"]] < 200]
    if low:
        print(f"\n{len(low)} species below 200 images — consider supplementing via API.")
    else:
        print("\nAll species have >= 200 images.")


if __name__ == "__main__":
    main()
