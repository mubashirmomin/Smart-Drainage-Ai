"""
inspect_dataset.py - read-only audit of the downloaded YOLO dataset.

It checks four things:
  1. Every image has a label file (and vice versa) and every label line is valid.
  2. How many boxes each class has in train / valid / test.
  3. How many distinct source videos each split contains.
  4. Whether the SAME video appears in more than one split (data leakage),
     and how close in time the shared frames are.

Standard library only, so no virtual environment is needed yet.
Run from the project root:   python ai/detection/inspect_dataset.py
"""
import ast
import os
import statistics
from collections import Counter, defaultdict
from pathlib import Path

# --- Locations ---------------------------------------------------------------
# This file lives at <project>/ai/detection/inspect_dataset.py,
# so parents[0] = detection, parents[1] = ai, parents[2] = project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = PROJECT_ROOT / "dataset" / "raw" / "sewer_v6"
SPLITS = ["train", "valid", "test"]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
WINDOWS_MAX_PATH = 260  # classic Windows limit on a full file path


def long_path(path):
    """Return a string path that Windows can open even when it is very long.

    Windows refuses to open files whose full path is 260+ characters unless the
    path starts with the extended-length marker (backslash backslash ? backslash).
    On other systems the path is returned unchanged.
    """
    path_str = os.path.abspath(path)
    if os.name == "nt" and not path_str.startswith("\\\\?\\"):
        path_str = "\\\\?\\" + path_str
    return path_str


def load_class_names(yaml_path):
    """Read the 'names: [...]' line of data.yaml without needing PyYAML."""
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("names:"):
            return ast.literal_eval(line.split(":", 1)[1].strip())
    raise ValueError("No 'names:' line found in data.yaml")


def parse_filename(image_name):
    """Return (video_id, seconds) from a Roboflow-exported image filename.

    '<video_id>-mp4-t-127-6_jpg.rf.<hash>.jpg'  ->  ('<video_id>', 127.6)
    Roboflow replaced '.' with '-', so '127-6' means 127.6 seconds.
    """
    marker = "-mp4-t-"
    if marker not in image_name:
        return "UNKNOWN", None
    video_id, rest = image_name.split(marker, 1)
    time_text = rest.split("_jpg")[0].replace("-", ".")
    try:
        return video_id, float(time_text)
    except ValueError:
        return video_id, None


def audit_split(split, class_names):
    """Collect integrity, class-count and source-video info for one split."""
    images_dir = DATASET_ROOT / split / "images"
    labels_dir = DATASET_ROOT / split / "labels"

    image_names = [p.name for p in images_dir.iterdir()
                   if p.suffix.lower() in IMAGE_SUFFIXES]
    image_stems = {Path(n).stem for n in image_names}
    label_paths = list(labels_dir.glob("*.txt"))
    label_stems = {p.stem for p in label_paths}

    too_long = sum(1 for p in label_paths if len(str(p)) >= WINDOWS_MAX_PATH)
    too_long += sum(1 for n in image_names
                    if len(str(images_dir / n)) >= WINDOWS_MAX_PATH)

    class_counts = Counter()
    empty_labels = 0
    bad_lines = []

    for label_path in label_paths:
        with open(long_path(label_path), encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.read().splitlines() if ln.strip()]
        if not lines:
            empty_labels += 1  # an empty file means "no defect in this image"
        for line in lines:
            parts = line.split()
            try:
                class_id = int(parts[0])
                coords = [float(v) for v in parts[1:]]
            except ValueError:
                bad_lines.append((label_path.name, line))
                continue
            # A detection label has exactly 5 numbers: class x y w h (all 0-1).
            # Segmentation labels would have more than 5 values.
            is_valid = (len(parts) == 5
                        and 0 <= class_id < len(class_names)
                        and all(0.0 <= c <= 1.0 for c in coords))
            if not is_valid:
                bad_lines.append((label_path.name, line))
                continue
            class_counts[class_id] += 1

    videos = defaultdict(list)  # video_id -> list of frame times (seconds)
    for name in image_names:
        video_id, seconds = parse_filename(name)
        videos[video_id].append(seconds)

    return {
        "n_images": len(image_names),
        "n_labels": len(label_paths),
        "missing_labels": len(image_stems - label_stems),
        "orphan_labels": len(label_stems - image_stems),
        "empty_labels": empty_labels,
        "too_long": too_long,
        "bad_lines": bad_lines,
        "class_counts": class_counts,
        "videos": videos,
    }


def report_leakage(info):
    """Measure how much the splits share source videos."""
    print("\n=== 4. Same video in more than one split? ===")
    for a, b in [("train", "valid"), ("train", "test"), ("valid", "test")]:
        shared = set(info[a]["videos"]) & set(info[b]["videos"])
        shared.discard("UNKNOWN")
        n_images_b = sum(len(info[b]["videos"][v]) for v in shared)
        print(f"{a} & {b}: {len(shared)} shared videos; "
              f"{n_images_b} of {info[b]['n_images']} {b} images come from them")

    gaps = []
    for split in ("valid", "test"):
        for video_id, times in info[split]["videos"].items():
            train_times = [t for t in info["train"]["videos"].get(video_id, [])
                           if t is not None]
            if not train_times:
                continue
            for t in times:
                if t is not None:
                    gaps.append(min(abs(t - x) for x in train_times))

    if gaps:
        print(f"\nFor the {len(gaps)} valid/test frames whose video is also in train,")
        print("distance in seconds to the nearest train frame of the same video:")
        print(f"  min={min(gaps):.2f}  median={statistics.median(gaps):.2f}  "
              f"max={max(gaps):.2f}")
        for limit in (2, 10, 30):
            share = 100 * sum(g <= limit for g in gaps) / len(gaps)
            print(f"  within {limit:>2} s: {share:.1f}%")
    else:
        print("\nNo valid/test frame shares a video with train.")


def main():
    if not DATASET_ROOT.exists():
        raise SystemExit(f"Dataset folder not found: {DATASET_ROOT}")

    class_names = load_class_names(DATASET_ROOT / "data.yaml")
    print(f"Dataset: {DATASET_ROOT}")
    print(f"Classes in data.yaml: {len(class_names)}")
    info = {s: audit_split(s, class_names) for s in SPLITS}

    print("\n=== 1. File integrity ===")
    for s in SPLITS:
        r = info[s]
        print(f"{s:6} images={r['n_images']:5} labels={r['n_labels']:5} "
              f"images_without_label={r['missing_labels']} "
              f"labels_without_image={r['orphan_labels']} "
              f"empty_labels={r['empty_labels']} "
              f"malformed_lines={len(r['bad_lines'])} "
              f"paths_over_259_chars={r['too_long']}")
        for fname, line in r["bad_lines"][:3]:
            print(f"   bad line in ...{fname[-30:]}: {line}")

    print("\n=== 2. Boxes per class ===")
    print(f"{'id':>3} {'class':8} {'train':>6} {'valid':>6} {'test':>6}")
    for class_id, name in enumerate(class_names):
        row = [info[s]["class_counts"][class_id] for s in SPLITS]
        flag = "  <-- zero in valid or test" if row[1] == 0 or row[2] == 0 else ""
        print(f"{class_id:>3} {name:8} {row[0]:>6} {row[1]:>6} {row[2]:>6}{flag}")
    totals = [sum(info[s]["class_counts"].values()) for s in SPLITS]
    print(f"{'':>3} {'TOTAL':8} {totals[0]:>6} {totals[1]:>6} {totals[2]:>6}")

    print("\n=== 3. Source videos per split ===")
    for s in SPLITS:
        videos = info[s]["videos"]
        sizes = [len(times) for times in videos.values()]
        print(f"{s:6} unique_videos={len(videos):4} "
              f"images_per_video: max={max(sizes)} median={statistics.median(sizes)}")
        if "UNKNOWN" in videos:
            print(f"   WARNING: {len(videos['UNKNOWN'])} filenames did not match "
                  f"the expected video pattern")

    report_leakage(info)


if __name__ == "__main__":
    main()
