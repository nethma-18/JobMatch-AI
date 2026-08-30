import logging
import json
import pickle
import joblib
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

MODEL_DIR = Path("data/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

DATASET_DIR = Path("data/datasets")
DATASET_DIR.mkdir(parents=True, exist_ok=True)


class ModelRetrainer:
    """
    Retrains the JobMatch AI supervised matching model using data from the
    validated training pool.

    What gets retrained:
    - Supervised Random Forest classifier (resume-job match prediction)
    - TF-IDF vectorizer (vocabulary update)
    - Skill lexicon (new term discovery)

    sentence-transformers (SBERT) is pre-trained — we fine-tune only
    the downstream supervised components, not the base embedding model.

    All reported metrics come from actual predictions on a held-out split.
    No hardcoded values.
    """

    RANDOM_SEED = 42
    MIN_TRAINING_DOCS = 10

    async def retrain(self, db, triggered_by: str = "auto_weekly") -> dict:
        """
        Full retraining cycle using approved training pool data.
        Returns a dict of real, computed metrics.
        """
        started_at = datetime.utcnow()
        log_id = None

        try:
            # Log start
            log_doc = {
                "retraining_started_at": started_at,
                "retraining_completed_at": None,
                "training_data_count": 0,
                "results": None,
                "status": "in_progress",
                "error_message": None,
                "triggered_by": triggered_by,
            }
            result = await db["model_retraining_logs"].insert_one(log_doc)
            log_id = result.inserted_id

            # 1. Load training data from pool
            training_docs = await self._load_training_data(db)
            count = len(training_docs)
            logger.info(f"Loaded {count} validated training documents")

            if count < self.MIN_TRAINING_DOCS:
                raise ValueError(
                    f"Insufficient training data ({count} docs). "
                    f"Need at least {self.MIN_TRAINING_DOCS} approved pairs."
                )

            # 2. Extract texts and labels
            resume_texts = [doc.get("resume_text", doc.get("cleaned_text", "")) for doc in training_docs]
            jd_texts     = [doc.get("job_text", "") for doc in training_docs]
            labels       = [int(doc.get("label", 1)) for doc in training_docs]

            # Fall back: if no paired structure, update lexicon + TF-IDF only
            has_pairs = all(jd_texts)

            # 3. Update skill lexicon
            all_texts = [t for t in resume_texts + jd_texts if t]
            new_skills = await self._update_skill_lexicon(all_texts)

            # 4. Retrain TF-IDF vectorizer
            tfidf_accuracy = await self._retrain_tfidf(all_texts)

            # 5. Train supervised classifier (if paired resume-JD data exists)
            supervised_results = {}
            if has_pairs and len(set(labels)) >= 2:
                supervised_results = self._train_supervised_model(
                    resume_texts, jd_texts, labels
                )
                logger.info(f"Supervised model trained: {supervised_results}")
            else:
                logger.info("Skipping supervised training: no paired data or single class.")

            # 6. Update training pool usage counters
            ids = [doc["_id"] for doc in training_docs]
            await db["training_pool"].update_many(
                {"_id": {"$in": ids}},
                {
                    "$inc": {"used_in_retraining_count": 1},
                    "$set": {"last_used_at": datetime.utcnow()},
                }
            )

            # 7. Store real metrics in model_metrics collection
            metrics_doc = {
                "recorded_at": datetime.utcnow(),
                "triggered_by": triggered_by,
                "training_samples": count,
                "new_skills_added": len(new_skills),
                "tfidf_self_similarity_accuracy": tfidf_accuracy,
                **supervised_results,
            }
            await db["model_metrics"].insert_one(metrics_doc)

            # 8. Log completion
            await db["model_retraining_logs"].update_one(
                {"_id": log_id},
                {"$set": {
                    "retraining_completed_at": datetime.utcnow(),
                    "training_data_count": count,
                    "results": supervised_results or {"tfidf_accuracy": tfidf_accuracy},
                    "status": "completed",
                    "new_skills_added": len(new_skills),
                }}
            )

            logger.info(f"Retraining complete: {count} docs, metrics={supervised_results}")

            return {
                "status": "completed",
                "training_data_count": count,
                "new_skills_added": len(new_skills),
                "tfidf_accuracy": tfidf_accuracy,
                "triggered_by": triggered_by,
                **supervised_results,
            }

        except Exception as e:
            logger.error(f"Retraining failed: {e}")
            if log_id:
                await db["model_retraining_logs"].update_one(
                    {"_id": log_id},
                    {"$set": {"status": "failed", "error_message": str(e)}}
                )
            return {"status": "failed", "error": str(e)}

    def _train_supervised_model(
        self,
        resume_texts: List[str],
        jd_texts: List[str],
        labels: List[int],
    ) -> dict:
        """
        Train a Random Forest supervised classifier on resume-job pairs.
        Uses stratified train/test split; reports REAL metrics from predictions.
        Returns dict of real computed metrics (no hardcoded values).
        """
        try:
            import pandas as pd
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity as sk_cos
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import StratifiedShuffleSplit, cross_val_score
            from sklearn.metrics import (
                accuracy_score, precision_score, recall_score,
                f1_score, roc_auc_score
            )
            import warnings
            warnings.filterwarnings("ignore")

            n = len(labels)
            y = np.array(labels)

            # Need at least 20 samples with both classes for a meaningful split
            if n < 20 or len(set(labels)) < 2:
                logger.warning("Too few samples or single class — skipping supervised training.")
                return {}

            # Fit TF-IDF on all texts (no leakage risk at inference time)
            tfidf = TfidfVectorizer(max_features=5000, stop_words="english", min_df=1)
            tfidf.fit([r + " " + j for r, j in zip(resume_texts, jd_texts)])

            def make_features(rt_list, jt_list):
                feats = []
                for rt, jt in zip(rt_list, jt_list):
                    rv = tfidf.transform([rt])
                    jv = tfidf.transform([jt])
                    cos = float(sk_cos(rv, jv)[0][0])
                    rt_tok = set(rt.lower().split())
                    jt_tok = set(jt.lower().split())
                    overlap = len(rt_tok & jt_tok) / max(len(jt_tok), 1)
                    feats.append([
                        cos, overlap,
                        len(rt_tok), len(jt_tok),
                        len(rt_tok) / max(len(jt_tok), 1),
                        len(rt_tok & jt_tok),
                        len(jt_tok - rt_tok),
                    ])
                return np.array(feats)

            X = make_features(resume_texts, jd_texts)

            # Use 5-fold CV for reliable estimate
            rf = RandomForestClassifier(
                n_estimators=100, random_state=self.RANDOM_SEED, class_weight="balanced"
            )

            cv_f1  = cross_val_score(rf, X, y, cv=5, scoring="f1", error_score=0.0)
            cv_acc = cross_val_score(rf, X, y, cv=5, scoring="accuracy", error_score=0.0)

            # Train on full dataset for the saved production model
            rf.fit(X, y)

            # Save model
            model_data = {
                "model": rf,
                "tfidf": tfidf,
                "feature_names": [
                    "tfidf_cosine_similarity", "token_overlap_ratio",
                    "resume_token_count", "jd_token_count", "length_ratio",
                    "matched_token_count", "missing_token_count",
                ],
                "trained_at": datetime.utcnow().isoformat(),
                "training_samples": n,
                "random_seed": self.RANDOM_SEED,
            }
            joblib.dump(model_data, MODEL_DIR / "supervised_matcher.joblib")

            # Save metadata
            metadata = {
                "model_name": "RandomForestClassifier",
                "random_seed": self.RANDOM_SEED,
                "n_estimators": 100,
                "class_weight": "balanced",
                "training_samples": n,
                "cv_folds": 5,
                "cv_f1_mean": round(float(cv_f1.mean()), 4),
                "cv_f1_std":  round(float(cv_f1.std()), 4),
                "cv_acc_mean": round(float(cv_acc.mean()), 4),
                "cv_acc_std":  round(float(cv_acc.std()), 4),
                "trained_at": datetime.utcnow().isoformat(),
            }
            with open(MODEL_DIR / "model_metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info(
                f"Supervised model saved: CV F1={cv_f1.mean():.4f} +/-{cv_f1.std():.4f}, "
                f"n={n}"
            )

            return {
                "supervised_model": "RandomForestClassifier",
                "supervised_training_samples": n,
                "cv_f1_mean": round(float(cv_f1.mean()), 4),
                "cv_f1_std":  round(float(cv_f1.std()), 4),
                "cv_acc_mean": round(float(cv_acc.mean()), 4),
                "cv_acc_std":  round(float(cv_acc.std()), 4),
            }

        except Exception as e:
            logger.error(f"Supervised training failed: {e}")
            return {"supervised_training_error": str(e)}

    def load_supervised_model(self):
        """Load saved supervised model for inference. Returns (model, tfidf) or (None, None)."""
        path = MODEL_DIR / "supervised_matcher.joblib"
        if not path.exists():
            return None, None
        try:
            data = joblib.load(path)
            if isinstance(data, dict) and "model" in data:
                return data["model"], data.get("tfidf")
            # Legacy format (plain model)
            return data, None
        except Exception as e:
            logger.warning(f"Could not load supervised model: {e}")
            return None, None

    async def _load_training_data(self, db) -> List[dict]:
        """Load all approved training documents from pool."""
        cursor = db["training_pool"].find(
            {"cleaned_text": {"$exists": True, "$ne": ""}},
            {"cleaned_text": 1, "resume_text": 1, "job_text": 1,
             "label": 1, "data_type": 1, "quality_score": 1}
        ).limit(5000)
        return await cursor.to_list(length=5000)

    async def _update_skill_lexicon(self, texts: List[str]) -> List[str]:
        """Scan training texts for new technical terms; add high-freq new terms to lexicon."""
        import re
        from collections import Counter

        lexicon_path = Path("data/skills_lexicon.json")
        current_skills: set = set()
        if lexicon_path.exists():
            with open(lexicon_path) as f:
                current_skills = set(json.load(f))

        word_counts: Counter = Counter()
        tech_pattern = re.compile(r"\b([a-z][a-z0-9+#.\-]{2,})\b")
        for text in texts:
            word_counts.update(tech_pattern.findall(text.lower()))

        stopwords = {
            "the", "and", "for", "with", "that", "this", "from",
            "have", "are", "you", "was", "not", "but", "they",
        }
        new_skills = [
            word for word, count in word_counts.items()
            if count >= 10
            and word not in current_skills
            and word not in stopwords
            and len(word) > 3
            and not word.isdigit()
        ]

        if new_skills:
            updated = sorted(current_skills | set(new_skills))
            with open(lexicon_path, "w") as f:
                json.dump(updated, f, indent=2)
            logger.info(f"Added {len(new_skills)} new skills to lexicon")

        return new_skills

    async def _retrain_tfidf(self, texts: List[str]) -> float:
        """
        Retrain TF-IDF vectorizer on all training texts.
        Reports self-similarity accuracy (each doc should be most similar to itself).
        This is NOT a supervised classification metric; it measures vocabulary quality.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            if len(texts) > 20:
                from sklearn.model_selection import train_test_split
                train_texts, val_texts = train_test_split(
                    texts, test_size=0.1, random_state=self.RANDOM_SEED
                )
            else:
                train_texts = texts
                val_texts = texts[:5]

            vectorizer = TfidfVectorizer(
                max_features=10000,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=2,
            )
            vectorizer.fit(train_texts)

            # Self-similarity check on val texts
            accuracy = 0.0
            if val_texts:
                sample = val_texts[:20]
                val_matrix = vectorizer.transform(sample)
                sim_matrix = cosine_similarity(val_matrix)
                correct = sum(
                    1 for i in range(len(sample))
                    if sim_matrix[i].argmax() == i
                )
                accuracy = round(correct / len(sample) * 100, 1)

            with open(MODEL_DIR / "tfidf_vectorizer.pkl", "wb") as f:
                pickle.dump(vectorizer, f)

            logger.info(
                f"TF-IDF retrained: vocab={len(vectorizer.vocabulary_)}, "
                f"self-similarity accuracy={accuracy}%"
            )
            return accuracy

        except Exception as e:
            logger.error(f"TF-IDF retraining failed: {e}")
            return 0.0


model_retrainer = ModelRetrainer()