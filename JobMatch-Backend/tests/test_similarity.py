import pytest
import numpy as np
from unittest.mock import patch
from app.ml.similarity import similarity_engine

def test_tfidf_fallback():
    # Test that fallback works and scores identical documents highly
    doc = "Experienced Python developer with React and AWS knowledge."
    score = similarity_engine._tfidf_fallback(doc, doc)
    assert score > 90.0

    # Unrelated docs
    score_unrelated = similarity_engine._tfidf_fallback("Python software developer", "Nursing assistant medical care")
    assert score_unrelated < 20.0

def test_compute_match_empty():
    res = similarity_engine.compute_match("", "Python Developer")
    assert res["score"] == 0
    assert "error" in res

@patch('app.ml.embeddings.embedding_engine.encode')
def test_compute_match_mocked(mock_encode):
    # Mock embedding engine to return two unit vectors
    # We want a cosine similarity of 0.8
    # For unit vectors, dot product = cosine similarity
    mock_encode.return_value = np.array([
        [1.0, 0.0],  # Vector for resume
        [0.8, 0.6]   # Vector for JD
    ])

    resume_text = "Python developer React"
    jd_text = "Python developer React Docker"

    # Skill overlap will be computed sync via skill_extractor
    res = similarity_engine.compute_match(resume_text, jd_text)
    assert res["score"] > 0
    assert "embedding_score" in res
    assert "skill_overlap_score" in res
    assert isinstance(res["interview_eligible"], bool)

def test_to_probability():
    assert similarity_engine._to_probability(88.0) == "Very High (85–100%)"
    assert similarity_engine._to_probability(72.0) == "High (70–84%)"
    assert similarity_engine._to_probability(60.0) == "Medium (55–69%)"
    assert similarity_engine._to_probability(45.0) == "Low (40–54%)"
    assert similarity_engine._to_probability(20.0) == "Very Low (<40%)"
