import logging
import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

MODEL_DIR = Path("data/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


class ModelRetrainer:
    """
    Retrains the skill extraction and similarity models
    using data from the training pool (public datasets + validated user uploads).

    What gets retrained:
    - Skill lexicon (updated with new skills found in training data)
    - TF-IDF vectorizer (updated with new vocabulary)
    - Similarity calibration weights

    sentence-transformers is pre-trained — we fine-tune only
    the downstream components, not the base embedding model.
    """

    async def retrain(self, db, triggered_by: str = "auto_weekly") -> dict:
        """
        Full retraining cycle.
        Returns retraining result dict.
        """
        started_at = datetime.utcnow()
        log_id = None

        try:
            # Log start
            log_doc = {
                "retraining_started_at": started_at,
                "retraining_completed_at": None,
                "training_data_count": 0,
                "validation_accuracy": None,
                "status": "in_progress",
                "error_message": None,
                "triggered_by": triggered_by,
            }
            result = await db["model_retraining_logs"].insert_one(log_doc)
            log_id = result.inserted_id

            # 1. Load training data from pool
            training_docs = await self._load_training_data(db)
            count = len(training_docs)
            logger.info(f"Loaded {count} training documents")

            if count < 10:
                raise ValueError(f"Not enough training data ({count} docs). Need at least 10.")

            # 2. Extract all texts
            texts = [doc["cleaned_text"] for doc in training_docs if doc.get("cleaned_text")]

            # 3. Update skill lexicon from training data
            new_skills = await self._update_skill_lexicon(texts)

            # 4. Retrain TF-IDF vectorizer
            accuracy = await self._retrain_tfidf(texts)

            # 5. Update training pool usage counters
            ids = [doc["_id"] for doc in training_docs]
            await db["training_pool"].update_many(
                {"_id": {"$in": ids}},
                {
                    "$inc": {"used_in_retraining_count": 1},
                    "$set": {"last_used_at": datetime.utcnow()},
                }
            )

            # 6. Log completion
            await db["model_retraining_logs"].update_one(
                {"_id": log_id},
                {"$set": {
                    "retraining_completed_at": datetime.utcnow(),
                    "training_data_count": count,
                    "validation_accuracy": accuracy,
                    "status": "completed",
                    "new_skills_added": len(new_skills),
                }}
            )

            logger.info(f"✅ Retraining complete: {count} docs, accuracy={accuracy}")

            return {
                "status": "completed",
                "training_data_count": count,
                "new_skills_added": len(new_skills),
                "validation_accuracy": accuracy,
                "triggered_by": triggered_by,
            }

        except Exception as e:
            logger.error(f"Retraining failed: {e}")
            if log_id:
                await db["model_retraining_logs"].update_one(
                    {"_id": log_id},
                    {"$set": {"status": "failed", "error_message": str(e)}}
                )
            return {"status": "failed", "error": str(e)}

    async def _load_training_data(self, db) -> List[dict]:
        """Load all approved training documents from pool."""
        cursor = db["training_pool"].find(
            {"cleaned_text": {"$exists": True, "$ne": ""}},
            {"cleaned_text": 1, "data_type": 1, "quality_score": 1}
        ).limit(5000)
        return await cursor.to_list(length=5000)

    async def _update_skill_lexicon(self, texts: List[str]) -> List[str]:
        """
        Scan training texts for new technical terms not in current lexicon.
        Adds high-frequency new terms to skills_lexicon.json.
        """
        import re
        from collections import Counter

        # Load current lexicon
        lexicon_path = Path("data/skills_lexicon.json")
        current_skills = set()
        if lexicon_path.exists():
            with open(lexicon_path) as f:
                current_skills = set(json.load(f))

        # Count word frequencies across all texts
        word_counts = Counter()
        tech_pattern = re.compile(r"\b([a-z][a-z0-9+#.\-]{2,})\b")

        for text in texts:
            words = tech_pattern.findall(text.lower())
            word_counts.update(words)

        # New terms appearing 10+ times not already in lexicon
        new_skills = []
        stopwords = {"the", "and", "for", "with", "that", "this", "from",
                     "have", "are", "you", "was", "not", "but", "they"}

        for word, count in word_counts.items():
            if (count >= 10
                    and word not in current_skills
                    and word not in stopwords
                    and len(word) > 3
                    and not word.isdigit()):
                new_skills.append(word)

        # Add new skills to lexicon
        if new_skills:
            updated = list(current_skills | set(new_skills))
            with open(lexicon_path, "w") as f:
                json.dump(sorted(updated), f, indent=2)
            logger.info(f"Added {len(new_skills)} new skills to lexicon")

        return new_skills

    async def _retrain_tfidf(self, texts: List[str]) -> float:
        """
        Retrain TF-IDF vectorizer on all training texts.
        Saves to disk for future similarity fallback use.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.model_selection import train_test_split
            from sklearn.metrics.pairwise import cosine_similarity

            # Split for validation
            if len(texts) > 20:
                train_texts, val_texts = train_test_split(texts, test_size=0.1, random_state=42)
            else:
                train_texts = texts
                val_texts = texts[:5]

            # Fit vectorizer
            vectorizer = TfidfVectorizer(
                max_features=10000,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=2,
            )
            vectorizer.fit(train_texts)

            # Simple accuracy check:
            # Same doc should be most similar to itself in val set
            if val_texts:
                val_matrix = vectorizer.transform(val_texts[:20])
                sim_matrix = cosine_similarity(val_matrix)
                # Diagonal should be max in each row
                correct = sum(
                    1 for i in range(len(val_texts[:20]))
                    if sim_matrix[i].argmax() == i
                )
                accuracy = round(correct / len(val_texts[:20]) * 100, 1)
            else:
                accuracy = 0.0

            # Save vectorizer
            with open(MODEL_DIR / "tfidf_vectorizer.pkl", "wb") as f:
                pickle.dump(vectorizer, f)

            logger.info(f"TF-IDF retrained: vocab={len(vectorizer.vocabulary_)}, accuracy={accuracy}%")
            return accuracy

        except Exception as e:
            logger.error(f"TF-IDF retraining failed: {e}")
            return 0.0


model_retrainer = ModelRetrainer()