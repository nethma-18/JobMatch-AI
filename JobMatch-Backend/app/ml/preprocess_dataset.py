import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split

DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "datasets"

def preprocess_and_split(dataset_path: Path = None, random_seed: int = 42):
    """
    Loads, cleans, validates, and splits the dataset into Train, Validation, and Test sets.
    """
    if dataset_path is None:
        dataset_path = DATASETS_DIR / "sample_labeled_matches.csv"

    print(f"=== PHASE 3 & 4: DATASET PREPROCESSING & SPLITTING ===")
    print(f"Loading raw dataset from: {dataset_path}")

    if not dataset_path.exists():
        print(f"❌ Error: Dataset file not found at {dataset_path}")
        return None

    df = pd.read_csv(dataset_path)
    initial_count = len(df)
    print(f"Initial raw record count: {initial_count}")

    # Validate required columns
    required_cols = {"resume_text", "job_description", "label"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"❌ Error: Dataset missing required columns: {missing}")
        return None

    # Clean whitespace and drop invalid/empty rows
    df["resume_text"] = df["resume_text"].astype(str).str.strip()
    df["job_description"] = df["job_description"].astype(str).str.strip()
    df = df[(df["resume_text"] != "") & (df["job_description"] != "")]
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)

    # Deduplicate exact pairs
    df = df.drop_duplicates(subset=["resume_text", "job_description"])
    cleaned_count = len(df)

    pos_count = int((df["label"] == 1).sum())
    neg_count = int((df["label"] == 0).sum())
    pos_pct = round((pos_count / cleaned_count) * 100, 1) if cleaned_count > 0 else 0

    print(f"\n--- Preprocessing Summary ---")
    print(f"Cleaned valid records: {cleaned_count} (Dropped {initial_count - cleaned_count} duplicates/empty)")
    print(f"Positive samples (label=1): {pos_count} ({pos_pct}%)")
    print(f"Negative samples (label=0): {neg_count} ({round(100 - pos_pct, 1)}%)")

    if cleaned_count < 4:
        print("❌ Error: Not enough valid samples for stratified split.")
        return None

    # Perform Stratified Train (80%) / Val (10%) / Test (10%) split
    train_df, temp_df = train_test_split(
        df, test_size=0.20, random_state=random_seed, stratify=df["label"]
    )
    val_df, test_df = train_test_split(
        temp_df, test_size=0.50, random_state=random_seed, stratify=temp_df["label"]
    )

    # Save cleaned splits
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    train_path = DATASETS_DIR / "cleaned_train.csv"
    val_path   = DATASETS_DIR / "cleaned_val.csv"
    test_path  = DATASETS_DIR / "cleaned_test.csv"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    print(f"\n--- Split Summary (Random Seed = {random_seed}) ---")
    print(f"Train Set: {len(train_df)} rows saved -> {train_path.name}")
    print(f"Val Set:   {len(val_df)} rows saved -> {val_path.name}")
    print(f"Test Set:  {len(test_df)} rows saved -> {test_path.name}")

    return {
        "train_df": train_df,
        "val_df": val_df,
        "test_df": test_df,
        "total_valid": cleaned_count,
        "pos_count": pos_count,
        "neg_count": neg_count,
    }

if __name__ == "__main__":
    preprocess_and_split()
