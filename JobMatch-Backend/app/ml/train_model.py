import os
import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.ml.similarity import similarity_engine
from app.ml.skill_extractor import skill_extractor

DATASETS_DIR = BASE_DIR / "data" / "datasets"
MODELS_DIR   = BASE_DIR / "data" / "models"

def extract_features_from_df(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract feature matrix X and target labels y from a resume-job dataframe.
    Features:
    [0]: Sentence-BERT Cosine Similarity (0-100)
    [1]: Exact Skill Overlap Score (0-100)
    [2]: Total Candidate Skill Count
    [3]: Required Job Skill Count
    """
    X_rows = []
    y = df["label"].values

    for _, row in df.iterrows():
        resume_text = str(row["resume_text"])
        jd_text     = str(row["job_description"])

        # Compute baseline embedding score
        emb_score, _ = similarity_engine._embedding_similarity(resume_text, jd_text)

        # Compute skill overlap
        resume_skills = set(skill_extractor.extract(resume_text))
        jd_skills     = set(skill_extractor.extract(jd_text))

        if len(jd_skills) > 0:
            overlap_score = (len(resume_skills & jd_skills) / len(jd_skills)) * 100.0
        else:
            overlap_score = emb_score

        X_rows.append([emb_score, overlap_score, float(len(resume_skills)), float(len(jd_skills))])

    return np.array(X_rows), y

def train_supervised_matcher(random_seed: int = 42):
    """
    Trains a supervised classifier on the training set and exports model artifact.
    """
    print(f"\n=== PHASE 6: SUPERVISED MODEL TRAINING ===")

    train_path = DATASETS_DIR / "cleaned_train.csv"
    val_path   = DATASETS_DIR / "cleaned_val.csv"

    if not train_path.exists() or not val_path.exists():
        print("Preprocessing splits not found. Running dataset preprocessor first...")
        from app.ml.preprocess_dataset import preprocess_and_split
        res = preprocess_and_split()
        if res is None:
            print("❌ Cannot proceed with training: No valid dataset available.")
            return None

    train_df = pd.read_csv(train_path)
    val_df   = pd.read_csv(val_path)

    print(f"Extracting NLP feature vectors for Train set ({len(train_df)} rows)...")
    X_train, y_train = extract_features_from_df(train_df)

    print(f"Extracting NLP feature vectors for Val set ({len(val_df)} rows)...")
    X_val, y_val = extract_features_from_df(val_df)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled   = scaler.transform(X_val)

    # Train LogisticRegression classifier
    clf = LogisticRegression(random_state=random_seed, max_iter=1000)
    clf.fit(X_train_scaled, y_train)

    # Threshold optimization on Validation set
    val_probs = clf.predict_proba(X_val_scaled)[:, 1]
    best_thresh = 0.5
    best_f1 = 0.0

    for thresh in np.arange(0.3, 0.8, 0.05):
        preds = (val_probs >= thresh).astype(int)
        f1 = f1_score(y_val, preds, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = thresh

    print(f"Training completed successfully!")
    print(f"Optimal Validation Decision Threshold: {round(best_thresh, 2)} (Val F1={round(best_f1, 4)})")

    # Export model artifact
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = MODELS_DIR / "supervised_matcher.joblib"
    artifact = {
        "model": clf,
        "scaler": scaler,
        "optimal_threshold": float(best_thresh),
        "feature_names": ["emb_score", "overlap_score", "resume_skill_cnt", "jd_skill_cnt"],
        "random_seed": random_seed,
    }

    joblib.dump(artifact, artifact_path)
    print(f"Saved trained model artifact -> {artifact_path} ({round(os.path.getsize(artifact_path)/1024, 1)} KB)")

    return artifact_path

if __name__ == "__main__":
    train_supervised_matcher()
