"""
ai/detection/remap_classes.py - Remap 54 Fine-Grained Classes to 15 Core Defect Categories

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Context: The Roboflow Sewer dataset uses 54 sub-classes with severe long-tail imbalance
(18 classes with near-zero validation counts). This script groups them into 15 standard
civil engineering defect categories based on international sewer inspection codes (CJJ 181 / WRc).

What it does:
1. Reads dataset/processed/sewer_grouped/ (leakage-safe split).
2. Maps each class ID (0..53) to its corresponding 15-class parent ID (0..14).
3. Links image files (zero extra disk space using NTFS hardlinks) into dataset/processed/sewer_15class/.
4. Writes remapped YOLO label files (.txt) for train, val, and test.
5. Emits a clean dataset/processed/sewer_15class/data.yaml with descriptive class labels.
6. Prints a distribution audit across all 15 defect classes.
"""

import ast
import os
import shutil
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "dataset" / "processed" / "sewer_grouped"
DEST_ROOT = PROJECT_ROOT / "dataset" / "processed" / "sewer_15class"
SPLITS = ["train", "val", "test"]

# 15 Standard Defect Taxonomy with Engineering Meanings
DEFECT_METADATA = {
    "AJ": {"name": "AJ_Illicit_Tap", "desc": "Illicit tap or unauthorized pipe connection"},
    "BX": {"name": "BX_Deformation", "desc": "Pipe deformation / ovality / cross-section loss"},
    "CJ": {"name": "CJ_Sediment", "desc": "Sediment, silt, or sludge deposition (blockage risk)"},
    "CK": {"name": "CK_Dislocation", "desc": "Joint offset / dislocation between pipe segments"},
    "CQ": {"name": "CQ_Sagging", "desc": "Pipe sagging / invert dip holding stagnant water"},
    "CR": {"name": "CR_Disconnection", "desc": "Open joint / pulled joint / disconnection"},
    "FS": {"name": "FS_Corrosion", "desc": "Surface corrosion / chemical or biological erosion"},
    "JG": {"name": "JG_Encrustation", "desc": "Mineral encrustation / hard calcified deposits"},
    "PL": {"name": "PL_Crack", "desc": "Fracture / longitudinal or circumferential crack"},
    "QF": {"name": "QF_Defective_Joint", "desc": "Defective joint interface or lateral connection"},
    "SG": {"name": "SG_Root_Intrusion", "desc": "Tree root intrusion penetrating pipe joints"},
    "SL": {"name": "SL_Infiltration", "desc": "Groundwater infiltration / active water leakage"},
    "TJ": {"name": "TJ_Obstacle", "desc": "Protruding obstacle / construction debris"},
    "TL": {"name": "TL_Seal_Failure", "desc": "Gasket / rubber seal displacement or failure"},
    "ZW": {"name": "ZW_Foreign_Object", "desc": "Foreign object penetration into the sewer line"},
}


def load_original_classes(yaml_path: Path):
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("names:"):
            return ast.literal_eval(line.split(":", 1)[1].strip())
    raise ValueError("No 'names:' line found in source data.yaml")


def build_mapping(orig_classes):
    """Map original 54 class indices to 15 unified classes."""
    sorted_prefixes = sorted(DEFECT_METADATA.keys())
    prefix_to_id = {prefix: i for i, prefix in enumerate(sorted_prefixes)}
    class_names_15 = [DEFECT_METADATA[p]["name"] for p in sorted_prefixes]

    old_id_to_new_id = {}
    for old_id, name in enumerate(orig_classes):
        prefix = name.split("_")[0]
        if prefix not in prefix_to_id:
            raise KeyError(f"Unknown class prefix: {prefix} in {name}")
        old_id_to_new_id[old_id] = prefix_to_id[prefix]

    return old_id_to_new_id, class_names_15, sorted_prefixes


def link_or_copy(src_path: Path, dst_path: Path):
    """Hardlink to save space, fallback to copy if cross-device."""
    if dst_path.exists():
        return
    try:
        os.link(src_path, dst_path)
    except OSError:
        shutil.copyfile(src_path, dst_path)


def process_dataset():
    print("=" * 70)
    print("  AI Sewer Intelligence - 15-Class Defect Remapping")
    print("=" * 70)
    print(f"Source Dataset: {SRC_ROOT}")
    print(f"Target Dataset: {DEST_ROOT}")

    if not SRC_ROOT.exists():
        raise SystemExit(f"Source dataset not found at {SRC_ROOT}")

    orig_classes = load_original_classes(SRC_ROOT / "data.yaml")
    print(f"Original Classes Count: {len(orig_classes)}")

    old_id_to_new_id, class_names_15, sorted_prefixes = build_mapping(orig_classes)
    print(f"Mapped into {len(class_names_15)} Defect Categories.\n")

    DEST_ROOT.mkdir(parents=True, exist_ok=True)
    counts = {s: Counter() for s in SPLITS}
    total_boxes = {s: 0 for s in SPLITS}
    total_images = {s: 0 for s in SPLITS}

    for split in SPLITS:
        src_img_dir = SRC_ROOT / split / "images"
        src_lbl_dir = SRC_ROOT / split / "labels"
        dst_img_dir = DEST_ROOT / split / "images"
        dst_lbl_dir = DEST_ROOT / split / "labels"

        dst_img_dir.mkdir(parents=True, exist_ok=True)
        dst_lbl_dir.mkdir(parents=True, exist_ok=True)

        for img_path in sorted(src_img_dir.iterdir()):
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue
            total_images[split] += 1
            dst_img = dst_img_dir / img_path.name
            link_or_copy(img_path, dst_img)

            # Process label file
            src_lbl = src_lbl_dir / (img_path.stem + ".txt")
            dst_lbl = dst_lbl_dir / (img_path.stem + ".txt")

            if not src_lbl.exists():
                dst_lbl.write_text("", encoding="utf-8")
                continue

            with open(src_lbl, "r", encoding="utf-8") as f:
                lines = [ln.strip() for ln in f if ln.strip()]

            new_lines = []
            for line in lines:
                parts = line.split()
                old_id = int(parts[0])
                new_id = old_id_to_new_id[old_id]
                new_line = f"{new_id} {' '.join(parts[1:])}"
                new_lines.append(new_line)
                counts[split][new_id] += 1
                total_boxes[split] += 1

            with open(dst_lbl, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines) + ("\n" if new_lines else ""))

    # Write target data.yaml
    yaml_text = (
        f"path: {DEST_ROOT.as_posix()}\n"
        f"train: train/images\n"
        f"val: val/images\n"
        f"test: test/images\n\n"
        f"nc: {len(class_names_15)}\n"
        f"names: {class_names_15}\n"
    )
    (DEST_ROOT / "data.yaml").write_text(yaml_text, encoding="utf-8")

    # Print distribution table
    print("=== Defect Class Distribution Summary ===")
    print(f"{'ID':>2} {'Code':<5} {'Defect Name':<22} {'Train':>7} {'Val':>6} {'Test':>6} {'Total':>7}")
    print("-" * 60)
    for cid, prefix in enumerate(sorted_prefixes):
        cname = class_names_15[cid]
        tr = counts["train"][cid]
        vl = counts["val"][cid]
        te = counts["test"][cid]
        tot = tr + vl + te
        flag = " [ZERO IN VAL]" if vl == 0 else ""
        print(f"{cid:>2} {prefix:<5} {cname:<22} {tr:>7} {vl:>6} {te:>6} {tot:>7}{flag}")

    print("-" * 60)
    print(f"{'':>2} {'':<5} {'TOTAL BOXES':<22} {total_boxes['train']:>7} {total_boxes['val']:>6} {total_boxes['test']:>6} {sum(total_boxes.values()):>7}")
    print(f"{'':>2} {'':<5} {'TOTAL IMAGES':<22} {total_images['train']:>7} {total_images['val']:>6} {total_images['test']:>6} {sum(total_images.values()):>7}")
    print("\nDataset generated successfully at:", DEST_ROOT)
    print("New configuration saved to:", DEST_ROOT / "data.yaml")


if __name__ == "__main__":
    process_dataset()
