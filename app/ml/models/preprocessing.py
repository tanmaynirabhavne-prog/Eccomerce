"""
Preprocessing for the H&M articles catalog -> feeds train_model.py.

Location: app/ml/models/preprocessing.py
Reads:    app/ml/dataset/articles_hm.csv

This module is import-only (no top-level execution side effects other than
under `if __name__ == "__main__"`), so train_model.py can do:

    from preprocessing import load_and_clean

WHAT IT DOES
------------
1. Loads articles_hm.csv, keeping article_id/product_code as strings
   (they're zero-padded codes -- reading as int silently corrupts them).
2. Strips whitespace on text columns.
3. Fills missing detail_desc with "".
4. Builds a single `combined_features` text column per product by joining
   the key descriptive fields (name, type, group, colour, department,
   section, garment group, description). This is what train_model.py
   vectorizes with TF-IDF to measure product similarity.
"""

import os
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(SCRIPT_DIR, "..", "dataset", "articles_hm.csv")

ID_COLUMNS = ["article_id", "product_code"]

# Columns combined into one text blob for similarity matching.
FEATURE_COLUMNS = [
    "prod_name",
    "product_type_name",
    "product_group_name",
    "colour_group_name",
    "perceived_colour_master_name",
    "department_name",
    "index_name",
    "section_name",
    "garment_group_name",
    "detail_desc",
]

# Columns kept in the final lookup table (used to display results later).
OUTPUT_COLUMNS = [
    "article_id",
    "product_code",
    "prod_name",
    "product_type_name",
    "product_group_name",
    "colour_group_name",
    "department_name",
    "index_name",
    "section_name",
    "garment_group_name",
    "detail_desc",
]


def resolve_dataset_path(path: str = None) -> str:
    csv_path = path or DATASET_PATH
    csv_path = os.path.abspath(csv_path)
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(
            f"Could not find dataset at: {csv_path}\n"
            f"Make sure articles_hm.csv is in app/ml/dataset/, "
            f"or pass an explicit path to load_and_clean()."
        )
    return csv_path


def load_and_clean(path: str = None) -> pd.DataFrame:
    csv_path = resolve_dataset_path(path)

    dtype_map = {col: str for col in ID_COLUMNS}
    df = pd.read_csv(csv_path, dtype=dtype_map)

    # Strip whitespace on text columns
    obj_cols = df.select_dtypes(include=["object", "str"]).columns
    for col in obj_cols:
        df[col] = df[col].astype(str).str.strip()

    df = df.drop_duplicates(subset="article_id")

    if "detail_desc" in df.columns:
        df["detail_desc"] = df["detail_desc"].fillna("")

    # Build combined text feature for similarity
    present_feature_cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    df["combined_features"] = (
        df[present_feature_cols]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .str.lower()
    )

    present_output_cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    result = df[present_output_cols + ["combined_features"]].reset_index(drop=True)

    return result


if __name__ == "__main__":
    df = load_and_clean()
    print(f"Loaded and cleaned {len(df)} products.")
    print(df[["article_id", "prod_name", "combined_features"]].head(3))