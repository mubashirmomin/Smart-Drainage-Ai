"""
prepare_dataset.py - build a leakage-safe, short-named copy of the raw dataset.

What it does, in order:
  1. Reads every image/label pair from the raw train/valid/test folders (pooled).
  2. Fingerprints each image (MD5) and drops exact duplicate images that have
     identical labels.
  3. Groups images that must stay together: frames from the same source video,
     and images with identical content.
  4. Assigns WHOLE groups to train / val / test (about 80/10/10 by image count),
     trying to spread rare classes across the splits.
  5. Verifies that no video and no image content appears in two splits.
  6. Copies files into dataset/processed/sewer_grouped/ with short names and
     writes a mapping table, a run record and a YOLO data.yaml.

The raw download is never modified. Labels are copied unchanged (still the
original 54 classes). Standard library only.

Run from the project root:
    python ai/detection/prepare_dataset.py
    python ai/detection/prepare_dataset.py --seed 7 --force     (rebuild)
"""
import argparse
import csv
import hashlib
import json
import random
import shutil
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone

# Reuse helpers from the audit script (same folder).
from inspect_dataset import (DATASET_ROOT, IMAGE_SUFFIXES, PROJECT_ROOT,
                             SPLITS as RAW_SPLITS, load_class_names,
                             long_path, parse_filename)

OUT_SPLITS = ["train", "val", "test"]
RATIOS = {"train": 0.8, "val": 0.1, "test": 0.1}
# How much "keep each split at its target size" counts compared with "spread
# every class across the splits". At 1.0 the size term dominated and starved
# val/test of most classes; 0.1 tested far better on a simulation that used
# this dataset's real class totals.
IMAGE_WEIGHT = 0.1
OUT_ROOT = PROJECT_ROOT / "dataset" / "processed" / "sewer_grouped"
META_DIR = PROJECT_ROOT / "dataset" / "metadata"


# --- Step 1: read everything ---------------------------------------------------
def file_md5(path):
    """MD5 fingerprint of a file's bytes (identical images give identical hashes)."""
    digest = hashlib.md5()
    with open(long_path(path), "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_samples(class_names):
    """Return one dict per image/label pair found in the raw splits."""
    samples = []
    for raw_split in RAW_SPLITS:
        images_dir = DATASET_ROOT / raw_split / "images"
        labels_dir = DATASET_ROOT / raw_split / "labels"
        # NOTE: we compare names from a directory listing instead of calling
        # Path.exists(), which wrongly returns False for very long Windows paths.
        label_stems = {p.stem for p in labels_dir.glob("*.txt")}
        for image_path in sorted(images_dir.iterdir()):
            if image_path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            if image_path.stem not in label_stems:
                print(f"  skipped (no label file): ...{image_path.name[-40:]}")
                continue
            label_path = labels_dir / (image_path.stem + ".txt")
            with open(long_path(label_path), encoding="utf-8") as f:
                lines = [ln.strip() for ln in f.read().splitlines() if ln.strip()]
            try:
                class_ids = [int(ln.split()[0]) for ln in lines]
            except ValueError:
                raise SystemExit(f"Malformed label in {label_path.name}. "
                                 f"Run inspect_dataset.py first.")
            if any(not 0 <= c < len(class_names) for c in class_ids):
                raise SystemExit(f"Class id out of range in {label_path.name}.")
            video_id, seconds = parse_filename(image_path.name)
            samples.append({
                "raw_split": raw_split,
                "image_path": image_path,
                "label_path": label_path,
                "image_name": image_path.name,
                "video_id": video_id,
                "seconds": seconds,
                "md5": file_md5(image_path),
                "label_key": tuple(sorted(lines)),
                "class_ids": class_ids,
            })
    return samples


# --- Step 2: exact duplicates --------------------------------------------------
def drop_exact_duplicates(samples):
    """Drop later copies of an identical image if its labels are identical too.

    Identical image + DIFFERENT labels is kept (and counted as a conflict) so we
    never silently discard a disagreement between annotations.
    """
    kept, dropped, seen, conflicts = [], [], {}, []
    for s in samples:
        first = seen.get(s["md5"])
        if first is None:
            seen[s["md5"]] = s
        elif first["label_key"] == s["label_key"]:
            dropped.append(s)
            continue
        else:
            conflicts.append((first, s))
        kept.append(s)
    return kept, dropped, conflicts


# --- Step 3: groups that must not be separated ---------------------------------
def _find(parent, i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]  # path compression
        i = parent[i]
    return i


def build_groups(samples):
    """Union-find: link images that share a video or share identical content."""
    parent = list(range(len(samples)))
    first_seen = {}
    for i, s in enumerate(samples):
        keys = [("md5", s["md5"])]
        if s["video_id"] != "UNKNOWN":
            keys.append(("video", s["video_id"]))
        for key in keys:
            if key in first_seen:
                ra, rb = _find(parent, i), _find(parent, first_seen[key])
                if ra != rb:
                    parent[rb] = ra
            else:
                first_seen[key] = i

    members = defaultdict(list)
    for i in range(len(samples)):
        members[_find(parent, i)].append(i)

    groups = []
    for idxs in members.values():
        classes = Counter()
        for i in idxs:
            classes.update(samples[i]["class_ids"])
        groups.append({"members": idxs, "size": len(idxs), "classes": classes})
    return groups


# --- Step 4: assign whole groups to splits -------------------------------------
def assign_groups(groups, seed):
    """Greedy stratified group split.

    Groups holding the rarest classes are placed first. Each group goes to the
    split that is currently furthest below its target for (a) the classes in the
    group and (b) the total image count (b counts only IMAGE_WEIGHT as much).
    """
    rng = random.Random(seed)
    class_totals = Counter()
    for g in groups:
        class_totals.update(g["classes"])
    n_images = sum(g["size"] for g in groups)

    img_target = {s: RATIOS[s] * n_images for s in OUT_SPLITS}
    img_cur = {s: 0 for s in OUT_SPLITS}
    cls_cur = {s: Counter() for s in OUT_SPLITS}

    def rarity(gi):
        counts = [class_totals[c] for c in groups[gi]["classes"]]
        return min(counts) if counts else float("inf")

    order = list(range(len(groups)))
    rng.shuffle(order)  # random tie-breaking, reproducible via the seed
    order.sort(key=lambda gi: (rarity(gi), -groups[gi]["size"]))

    assignment = [None] * len(groups)
    for gi in order:
        group = groups[gi]
        best_split, best_score = None, None
        for s in OUT_SPLITS:
            score = IMAGE_WEIGHT * (img_target[s] - img_cur[s]) / n_images
            for c, n in group["classes"].items():
                target = RATIOS[s] * class_totals[c]
                score += n * (target - cls_cur[s][c]) / class_totals[c]
            if best_score is None or score > best_score:
                best_split, best_score = s, score
        assignment[gi] = best_split
        img_cur[best_split] += group["size"]
        cls_cur[best_split].update(group["classes"])
    return assignment


# --- Step 5: prove there is no leakage -----------------------------------------
def verify_no_leakage(samples):
    problems = 0
    for key in ("video_id", "md5"):
        seen = defaultdict(set)
        for s in samples:
            if key == "video_id" and s["video_id"] == "UNKNOWN":
                continue
            seen[s[key]].add(s["split"])
        bad = sum(1 for splits in seen.values() if len(splits) > 1)
        print(f"  {key} values found in more than one split: {bad}")
        problems += bad
    if problems:
        raise SystemExit("Leakage check FAILED - nothing was copied.")


# --- Step 6: names, copies, metadata -------------------------------------------
def name_samples(samples):
    """Give every sample a short, unique, deterministic name: v<video>_<index>."""
    video_numbers = {v: n for n, v in
                     enumerate(sorted({s["video_id"] for s in samples}), start=1)}
    ordered = sorted(samples, key=lambda s: (
        s["video_id"], -1.0 if s["seconds"] is None else s["seconds"],
        s["image_name"]))
    for idx, s in enumerate(ordered, start=1):
        s["video_no"] = video_numbers[s["video_id"]]
        s["new_name"] = f"v{s['video_no']:04d}_{idx:05d}"


def copy_files(samples):
    for split in OUT_SPLITS:
        (OUT_ROOT / split / "images").mkdir(parents=True, exist_ok=True)
        (OUT_ROOT / split / "labels").mkdir(parents=True, exist_ok=True)
    for n, s in enumerate(samples, start=1):
        suffix = s["image_path"].suffix.lower()
        dest_img = OUT_ROOT / s["split"] / "images" / (s["new_name"] + suffix)
        dest_lbl = OUT_ROOT / s["split"] / "labels" / (s["new_name"] + ".txt")
        shutil.copyfile(long_path(s["image_path"]), dest_img)
        shutil.copyfile(long_path(s["label_path"]), dest_lbl)
        if n % 1000 == 0:
            print(f"  copied {n}/{len(samples)}")


def write_metadata(samples, dropped, conflicts, class_names, args, n_groups):
    META_DIR.mkdir(parents=True, exist_ok=True)

    with open(META_DIR / "sample_index.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["new_name", "split", "raw_split", "original_image_name",
                         "video_id", "video_no", "seconds", "md5", "n_boxes",
                         "class_ids"])
        for s in sorted(samples, key=lambda s: s["new_name"]):
            writer.writerow([s["new_name"], s["split"], s["raw_split"],
                             s["image_name"], s["video_id"], s["video_no"],
                             "" if s["seconds"] is None else s["seconds"],
                             s["md5"], len(s["class_ids"]),
                             ";".join(str(c) for c in sorted(set(s["class_ids"])))])

    with open(META_DIR / "dropped_duplicates.csv", "w", newline="",
              encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["raw_split", "original_image_name", "md5"])
        for s in dropped:
            writer.writerow([s["raw_split"], s["image_name"], s["md5"]])

    with open(META_DIR / "duplicate_label_conflicts.csv", "w", newline="",
              encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["md5", "image_1", "raw_split_1", "labels_1",
                         "image_2", "raw_split_2", "labels_2"])
        for a, b in conflicts:
            writer.writerow([a["md5"], a["image_name"], a["raw_split"],
                             " | ".join(a["label_key"]), b["image_name"],
                             b["raw_split"], " | ".join(b["label_key"])])

    run_record = {
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": args.seed,
        "ratios": RATIOS,
        "grouping_key": "video_id (filename text before '-mp4-t-') + identical image content",
        "raw_dataset": str(DATASET_ROOT),
        "raw_pairs_found": len(samples) + len(dropped),
        "exact_duplicates_dropped": len(dropped),
        "same_image_different_labels": len(conflicts),
        "image_weight": IMAGE_WEIGHT,
        "groups": n_groups,
        "images_per_split": {s: sum(1 for x in samples if x["split"] == s)
                             for s in OUT_SPLITS},
    }
    (META_DIR / "prepare_run.json").write_text(
        json.dumps(run_record, indent=2), encoding="utf-8")

    # YOLO config with an ABSOLUTE path (machine-specific; not for git).
    yaml_text = (
        f"path: {OUT_ROOT.as_posix()}\n"
        f"train: train/images\n"
        f"val: val/images\n"
        f"test: test/images\n\n"
        f"nc: {len(class_names)}\n"
        f"names: {json.dumps(class_names)}\n"
    )
    (OUT_ROOT / "data.yaml").write_text(yaml_text, encoding="utf-8")


def print_summary(samples, class_names):
    total = len(samples)
    print("\n=== Result ===")
    print(f"{'split':6} {'images':>7} {'share':>7} {'videos':>7} {'boxes':>7}")
    for s in OUT_SPLITS:
        part = [x for x in samples if x["split"] == s]
        boxes = sum(len(x["class_ids"]) for x in part)
        videos = len({x["video_id"] for x in part})
        print(f"{s:6} {len(part):>7} {100 * len(part) / total:>6.1f}% "
              f"{videos:>7} {boxes:>7}")

    counts = {s: Counter() for s in OUT_SPLITS}
    for x in samples:
        counts[x["split"]].update(x["class_ids"])
    print(f"\n{'id':>3} {'class':8} {'train':>6} {'val':>6} {'test':>6}")
    for cid, name in enumerate(class_names):
        row = [counts[s][cid] for s in OUT_SPLITS]
        flag = "  <-- zero in val or test" if row[1] == 0 or row[2] == 0 else ""
        print(f"{cid:>3} {name:8} {row[0]:>6} {row[1]:>6} {row[2]:>6}{flag}")

    sizes = [sum(1 for x in samples if x["video_id"] == v)
             for v in {x["video_id"] for x in samples}]
    print(f"\nLargest group of frames from one video: {max(sizes)} "
          f"(median {statistics.median(sizes)})")


def parse_args():
    parser = argparse.ArgumentParser(description="Build the video-grouped dataset.")
    parser.add_argument("--seed", type=int, default=42,
                        help="random seed for tie-breaking (default 42)")
    parser.add_argument("--force", action="store_true",
                        help="delete and rebuild an existing processed dataset")
    return parser.parse_args()


def main():
    args = parse_args()
    if not DATASET_ROOT.exists():
        raise SystemExit(f"Raw dataset not found: {DATASET_ROOT}")
    if OUT_ROOT.exists() and any(OUT_ROOT.iterdir()):
        if not args.force:
            raise SystemExit(f"{OUT_ROOT} already exists. "
                             f"Re-run with --force to rebuild it.")
        shutil.rmtree(OUT_ROOT)

    class_names = load_class_names(DATASET_ROOT / "data.yaml")

    print("Step 1/6  Reading and fingerprinting images (about a minute)...")
    samples = collect_samples(class_names)
    print(f"          {len(samples)} image/label pairs found in the raw download.")

    print("Step 2/6  Looking for exact duplicate images...")
    samples, dropped, conflicts = drop_exact_duplicates(samples)
    print(f"          dropped {len(dropped)} exact duplicates; "
          f"{len(conflicts)} same-image-different-label cases kept.")

    print("Step 3/6  Grouping frames by source video and identical content...")
    groups = build_groups(samples)
    print(f"          {len(groups)} groups.")

    print("Step 4/6  Assigning whole groups to train / val / test...")
    assignment = assign_groups(groups, args.seed)
    for group, split in zip(groups, assignment):
        for i in group["members"]:
            samples[i]["split"] = split

    print("Step 5/6  Leakage check:")
    verify_no_leakage(samples)

    print("Step 6/6  Copying files and writing metadata...")
    name_samples(samples)
    copy_files(samples)
    write_metadata(samples, dropped, conflicts, class_names, args, len(groups))

    print_summary(samples, class_names)
    print(f"\nOutput folder : {OUT_ROOT}")
    print(f"Mapping table : {META_DIR / 'sample_index.csv'}")


if __name__ == "__main__":
    main()
