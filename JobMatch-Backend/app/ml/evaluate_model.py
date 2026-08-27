import os
import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.ml.similarity import similarity_engine
from app.ml.skill_extractor import skill_extractor

DATASETS_DIR = BASE_DIR / "data" / "datasets"
MODELS_DIR   = BASE_DIR / "data" / "models"

def compute_metrics(y_true, y_pred):
    acc  = round(accuracy_score(y_true, y_pred), 4)
    prec = round(precision_score(y_true, y_pred, zero_division=0), 4)
    rec  = round(recall_score(y_true, y_pred, zero_division=0), 4)
    f1   = round(f1_score(y_true, y_pred, zero_division=0), 4)
    cm   = confusion_matrix(y_true, y_pred).tolist()
    return {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1, "confusion_matrix": cm}

def evaluate_all():
    """
    Evaluates both the Baseline matching engine and the Trained Supervised Model on held-out test data.
    """
    print(f"\n=== PHASE 5, 7 & 8: BASELINE VS TRAINED MODEL EVALUATION ===")

    test_path = DATASETS_DIR / "cleaned_test.csv"
    val_path  = DATASETS_DIR / "cleaned_val.csv"

    if not test_path.exists():
        print("Test set not found. Preprocessing dataset...")
        from app.ml.preprocess_dataset import preprocess_and_split
        res = preprocess_and_split()
        if res is None:
            print("Error: Cannot proceed with evaluation: Test dataset unavailable.")
            return None

    test_df = pd.read_csv(test_path)
    val_df  = pd.read_csv(val_path)
    y_test  = test_df["label"].values
    y_val   = val_df["label"].values

    print(f"Held-out Test set size: {len(test_df)} rows")

    # 1. EVALUATE BASELINE (65% Sentence-BERT + 35% Skill Overlap)
    print("\n--- 1. Evaluating Production Baseline (65% Sentence-BERT + 35% Skill Overlap) ---")

    val_base_scores = []
    for _, row in val_df.iterrows():
        res = similarity_engine.compute_match(str(row["resume_text"]), str(row["job_description"]))
        val_base_scores.append(res["match_score"])

    # Find threshold on Validation set
    best_base_thresh = 65.0
    best_base_f1 = 0.0
    for thresh in np.arange(40.0, 85.0, 2.5):
        preds = (np.array(val_base_scores) >= thresh).astype(int)
        f1 = f1_score(y_val, preds, zero_division=0)
        if f1 > best_base_f1:
            best_base_f1 = f1
            best_base_thresh = thresh

    print(f"Baseline Optimal Validation Threshold: {best_base_thresh} (Val F1={round(best_base_f1, 4)})")

    # Predict on untouched Test set
    test_base_scores = []
    for _, row in test_df.iterrows():
        res = similarity_engine.compute_match(str(row["resume_text"]), str(row["job_description"]))
        test_base_scores.append(res["match_score"])

    test_base_preds = (np.array(test_base_scores) >= best_base_thresh).astype(int)
    base_metrics = compute_metrics(y_test, test_base_preds)

    print(f"Baseline Test Accuracy: {base_metrics['accuracy']} | F1: {base_metrics['f1']} | Precision: {base_metrics['precision']} | Recall: {base_metrics['recall']}")

    # 2. EVALUATE TRAINED SUPERVISED MODEL
    model_artifact_path = MODELS_DIR / "supervised_matcher.joblib"
    trained_metrics = None

    if not model_artifact_path.exists():
        print("\nTrained model artifact not found. Training model now...")
        from app.ml.train_model import train_supervised_matcher
        train_supervised_matcher()

    if model_artifact_path.exists():
        print(f"\n--- 2. Evaluating Trained Supervised Model ({model_artifact_path.name}) ---")
        artifact = joblib.load(model_artifact_path)
        clf = artifact["model"]
        scaler = artifact["scaler"]
        opt_thresh = artifact.get("optimal_threshold", 0.5)

        from app.ml.train_model import extract_features_from_df
        X_test, _ = extract_features_from_df(test_df)
        X_test_scaled = scaler.transform(X_test)

        test_probs = clf.predict_proba(X_test_scaled)[:, 1]
        trained_preds = (test_probs >= opt_thresh).astype(int)
        trained_metrics = compute_metrics(y_test, trained_preds)

        print(f"Trained Model Test Accuracy: {trained_metrics['accuracy']} | F1: {trained_metrics['f1']} | Precision: {trained_metrics['precision']} | Recall: {trained_metrics['recall']}")

    # 3. COMPARISON TABLE (PHASE 8)
    print("\n" + "="*50)
    print("      PHASE 8: BASELINE VS TRAINED MODEL REPORT")
    print("="*50)
    print(f"| Metric       | Baseline (65/35) | Trained Model |")
    print(f"|--------------|-------------------|---------------|")
    print(f"| Accuracy     | {base_metrics['accuracy']:<17} | {trained_metrics['accuracy'] if trained_metrics else 'N/A':<13} |")
    print(f"| Precision    | {base_metrics['precision']:<17} | {trained_metrics['precision'] if trained_metrics else 'N/A':<13} |")
    print(f"| Recall       | {base_metrics['recall']:<17} | {trained_metrics['recall'] if trained_metrics else 'N/A':<13} |")
    print(f"| F1-Score     | {base_metrics['f1']:<17} | {trained_metrics['f1'] if trained_metrics else 'N/A':<13} |")
    print("="*50 + "\n")

    return {
        "baseline": base_metrics,
        "trained": trained_metrics,
    }

if __name__ == "__main__":
    evaluate_all()
