"""
MoleWatch — one-off data preparation.

Reads the raw HAM10000 download, writes a folder that train_molewatch.py
can consume: resized images plus train/val/test split CSVs.

Run from the project root:   python prep_molewatch.py

NOTE ON SPLITS
--------------
This reproduces Fareedah's splitting (StratifiedGroupKFold, grouped on
lesion_id, random_state=42). It should give the same splits as hers, but
"should" is not "does" — a different scikit-learn version can shuffle
differently. Use these to get the pipeline working tonight, then replace
the three CSVs with the team's official ones before reporting any numbers.
"""

from pathlib import Path

import pandas as pd
from PIL import Image
from sklearn.model_selection import StratifiedGroupKFold

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------

RAW_DIR = Path("raw_data/ham10000")
OUT_DIR = Path("processed_data")

IMG_SIZE = 224
CROP_RATIO = 0.8          # Fareedah's setting; set to None for no crop
SQUARE_CROP = False       # True = largest centre square (no distortion)

SUSPICIOUS = ["mel", "bcc", "akiec"]
SEED = 42

# ----------------------------------------------------------------------


def build_metadata() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "HAM10000_metadata")
    df["is_suspicious"] = df.dx.isin(SUSPICIOUS).astype(int)
    print(f"{len(df):,} images, {df.is_suspicious.mean():.1%} suspicious, "
          f"{df.lesion_id.nunique():,} unique lesions")
    return df


def make_splits(df: pd.DataFrame):
    """Group-aware splits: every photo of one lesion stays on one side."""
    sgkf = StratifiedGroupKFold(n_splits=7, shuffle=True, random_state=SEED)
    trainval_idx, test_idx = next(
        sgkf.split(df, y=df.is_suspicious, groups=df.lesion_id)
    )
    trainval = df.iloc[trainval_idx].reset_index(drop=True)
    test = df.iloc[test_idx].reset_index(drop=True)

    sgkf2 = StratifiedGroupKFold(n_splits=6, shuffle=True, random_state=SEED)
    train_idx, val_idx = next(
        sgkf2.split(trainval, y=trainval.is_suspicious, groups=trainval.lesion_id)
    )
    train = trainval.iloc[train_idx].reset_index(drop=True)
    val = trainval.iloc[val_idx].reset_index(drop=True)

    # the check that matters — no lesion may appear in two splits
    splits = {"train": train, "val": val, "test": test}
    for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
        overlap = set(splits[a].lesion_id) & set(splits[b].lesion_id)
        assert not overlap, f"{len(overlap)} lesions leak between {a} and {b}"
    print("no lesion overlap between splits")

    return train, val, test


def process_image(src: Path, dest: Path):
    img = Image.open(src).convert("RGB")

    if SQUARE_CROP:
        w, h = img.size
        side = min(w, h)
        left, top = (w - side) // 2, (h - side) // 2
        img = img.crop((left, top, left + side, top + side))
    elif CROP_RATIO:
        w, h = img.size
        m = (1 - CROP_RATIO) / 2
        img = img.crop((int(w * m), int(h * m), int(w * (1 - m)), int(h * (1 - m))))

    img = img.resize((IMG_SIZE, IMG_SIZE), Image.LANCZOS)
    img.save(dest, quality=95)


def main():
    img_out = OUT_DIR / "images"
    img_out.mkdir(parents=True, exist_ok=True)

    df = build_metadata()
    train, val, test = make_splits(df)

    src_dir = RAW_DIR / "images"
    for i, img_id in enumerate(df.image_id, 1):
        process_image(src_dir / f"{img_id}.jpg", img_out / f"{img_id}.jpg")
        if i % 1000 == 0:
            print(f"  {i:,} / {len(df):,}")

    for name, split in [("train", train), ("val", val), ("test", test)]:
        cols = ["image_id", "lesion_id", "dx", "is_suspicious"]
        split[cols].to_csv(OUT_DIR / f"{name}_split.csv", index=False)
        print(f"{name:<6} {len(split):>6} images, "
              f"{split.is_suspicious.mean():.1%} suspicious")

    print(f"\ndone — upload the '{OUT_DIR}' folder to Drive")


if __name__ == "__main__":
    main()
