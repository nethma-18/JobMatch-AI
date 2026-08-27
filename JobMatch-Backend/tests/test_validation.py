import pytest
from app.validation.quality_scorer import quality_scorer
from app.validation.spam_detector import spam_detector

def test_quality_scorer_empty():
    res = quality_scorer.score("")
    assert res["total_score"] == 0
    assert res["auto_decision"] == "auto_rejected"

def test_quality_scorer_simple():
    # Simple resume with name, email, skills, experience, education
    resume_text = """
    John Doe
    Email: john.doe@example.com
    Phone: +1-555-0199
    
    Education:
    Bachelor of Science in Computer Science, Stanford University
    
    Experience:
    Software Engineer, Tech Corp (2 years experience)
    Worked on Python, Java, SQL, and Docker microservices.
    
    Skills:
    Python, Javascript, Git, Docker, Postgresql, Communication
    """
    res = quality_scorer.score(resume_text, ".pdf")
    assert res["total_score"] >= 70
    assert res["auto_decision"] == "auto_approved"
    assert "has_name" in res["breakdown"]
    assert res["breakdown"]["has_email"] > 0

def test_spam_detector_valid():
    valid_text = """
    Jane Smith
    jane.smith@example.com
    Professional Experience:
    Senior Developer with 5 years experience in Python and React.
    Skills: React, Python, Django, AWS, Kubernetes, Time Management.
    Education: Stanford University, BS in Computer Science.
    """
    res = spam_detector.check(valid_text)
    assert res["is_spam"] is False
    assert res["passed"] is True

def test_spam_detector_spam_pattern():
    spam_text = "Hello world! This is a test upload of a fake resume for mock purposes. asdfghjkl."
    res = spam_detector.check(spam_text)
    assert res["is_spam"] is True
    assert res["passed"] is False
    assert any("Spam pattern" in issue or "gibberish" in issue for issue in res["issues"])
