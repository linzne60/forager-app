import csv
import json
from pathlib import Path

from sklearn.model_selection import train_test_split


ML_DIR = Path("ml")
RAW_DIR = ML_DIR / "data" / "raw"


def load_species():

    SPECIES_JSON = ML_DIR / "configs" / "species.json"
    species = json.loads(SPECIES_JSON.read_text())['species']

    return species


def build_merge_map(species):
    """Maps directory class_name → resolved label (applying merge_to if present)."""

    merge_map = {}

    for s in species:
        class_name = s["class_name"]
        resolved = s.get("merge_to", class_name)
        merge_map[class_name] = resolved

    return merge_map


def get_class_names(merge_map):
    """Returns sorted unique class names after merges are applied."""

    class_names = sorted(set(merge_map.values()))

    return class_names


def build_class_map(class_names):

    class_map = {}

    for i in range(len(class_names)):
        class_map[str(i)] = class_names[i]

    with open("ml/data/splits/class_map.json", "w") as f:
        json.dump(class_map, f, indent=4)

    return class_map


def collect_paths(species, merge_map):

    img_paths = []
    labels = []

    for s in species:
        class_name = s["class_name"]
        resolved_label = merge_map[class_name]
        class_path = RAW_DIR / class_name

        if not class_path.exists():
            print(f"  Warning: {class_path} not found, skipping")
            continue

        count = 0
        for path in class_path.glob("*.jpg"):
            img_paths.append(str(path))
            labels.append(resolved_label)
            count += 1

        if count > 0 and resolved_label != class_name:
            print(f"  Merged: {class_name} → {resolved_label} ({count} images)")

    return img_paths, labels


def make_splits(img_paths, labels):

    # first split
    paths_train_val, paths_test, labels_train_val, labels_test = train_test_split(
            img_paths, labels, test_size=0.15, stratify=labels, random_state=42
        )

    # second split
    paths_train, paths_val, labels_train, labels_val = train_test_split(
        paths_train_val, labels_train_val, test_size=0.176, stratify=labels_train_val, random_state=42
    )

    splits_dir = Path("ml/data/splits")
    splits_dir.mkdir(exist_ok=True)

    with open(splits_dir / "train.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["path", "label"])
        for path, label in zip(paths_train, labels_train):
            writer.writerow([path, label])

    with open(splits_dir / "val.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["path", "label"])
        for path, label in zip(paths_val, labels_val):
            writer.writerow([path, label])

    with open(splits_dir / "test.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["path", "label"])
        for path, label in zip(paths_test, labels_test):
            writer.writerow([path, label])

    return len(paths_train), len(paths_val), len(paths_test)


if __name__ == '__main__':

    species = load_species()
    merge_map = build_merge_map(species)
    class_names = get_class_names(merge_map)
    class_map = build_class_map(class_names)

    print(f"Species in config: {len(species)}")
    print(f"Classes after merges: {len(class_names)}")

    merges = [(s["class_name"], s["merge_to"]) for s in species if "merge_to" in s]
    if merges:
        print(f"\nMerges ({len(merges)}):")
        for source, target in merges:
            print(f"  {source} → {target}")
        print()

    img_paths, labels = collect_paths(species, merge_map)

    train_count, val_count, test_count = make_splits(img_paths, labels)

    print(f"\nSplits: {train_count} train / {val_count} val / {test_count} test")
    print(f"Total: {train_count + val_count + test_count} images")
