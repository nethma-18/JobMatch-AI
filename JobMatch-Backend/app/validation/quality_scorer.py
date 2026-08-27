import re
from typing import Optional


class QualityScorer:
    """
    Scores uploaded resume text 0–100.
    Each criterion adds points. Final score determines pipeline route.

    Score  0–39  → Auto-reject
    Score 40–69  → Flagged for admin review
    Score 70–100 → Auto-approved
    """

    # ── Scoring criteria weights ─────────────────────────────────

    CRITERIA = {
        "text_extracted":        20,  # Text could be read from file
        "min_length":            10,  # > 200 characters
        "has_name":              10,  # Detectable name
        "has_email":             10,  # Valid email address
        "has_phone":              5,  # Phone number (optional)
        "has_skills":            15,  # 2+ recognizable skills
        "has_experience":        10,  # Experience/work history
        "has_education":         10,  # Education section
        "format_bonus":          10,  # File was PDF or DOCX (best formats)
    }
    # Total possible: 100

    # Basic skill keywords for scoring (full extraction is in ml/skill_extractor.py)
    SKILL_KEYWORDS = [
        "python", "java", "javascript", "typescript", "react", "angular", "vue",
        "node", "django", "flask", "fastapi", "spring", "sql", "mysql",
        "postgresql", "mongodb", "redis", "docker", "kubernetes", "aws", "azure",
        "gcp", "git", "linux", "html", "css", "rest", "api", "machine learning",
        "deep learning", "tensorflow", "pytorch", "data analysis", "excel",
        "powerpoint", "photoshop", "figma", "agile", "scrum", "jira",
        "communication", "leadership", "management", "project management",
        "problem solving", "teamwork", "c++", "c#", "ruby", "php", "swift",
        "kotlin", "flutter", "android", "ios", "devops", "ci/cd", "testing",
    ]

    EXPERIENCE_PATTERNS = [
        r"\b\d+\s*\+?\s*years?\s*(of\s+)?(experience|exp)\b",
        r"\bexperience\b",
        r"\bemployment\b",
        r"\bwork\s+history\b",
        r"\bprofessional\s+background\b",
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4}\b",
        r"\bpresent\b",
        r"\bintern(ship)?\b",
        r"\bposition\b",
        r"\bjob\s+title\b",
    ]

    EDUCATION_PATTERNS = [
        r"\b(bachelor|master|phd|doctorate|diploma|associate|b\.?sc|m\.?sc|b\.?eng|mba)\b",
        r"\buniversity\b",
        r"\bcollege\b",
        r"\binstitute\b",
        r"\bschool\b",
        r"\bdegree\b",
        r"\bgraduate\b",
        r"\bgraduate\b",
        r"\bcgpa\b",
        r"\bgpa\b",
    ]

    def score(self, text: str, file_extension: str = "") -> dict:
        """
        Score the extracted text.
        Returns dict: {total_score, breakdown, threshold, auto_decision}
        """
        breakdown = {}
        total = 0

        if not text or len(text.strip()) < 10:
            return {
                "total_score": 0,
                "breakdown": {"text_extracted": 0},
                "threshold": "auto_reject",
                "auto_decision": "auto_rejected",
                "reasons": ["No readable text extracted from file"],
            }

        text_lower = text.lower()

        # 1. Text extracted successfully
        points = self.CRITERIA["text_extracted"]
        breakdown["text_extracted"] = points
        total += points

        # 2. Minimum length (> 200 chars)
        points = self.CRITERIA["min_length"] if len(text.strip()) > 200 else 0
        breakdown["min_length"] = points
        total += points

        # 3. Has name (simple heuristic: 2–4 capitalized words in first 10 lines)
        first_lines = "\n".join(text.split("\n")[:10])
        name_match = re.search(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", first_lines)
        points = self.CRITERIA["has_name"] if name_match else 0
        breakdown["has_name"] = points
        total += points

        # 4. Has email
        email_match = re.search(
            r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", text
        )
        points = self.CRITERIA["has_email"] if email_match else 0
        breakdown["has_email"] = points
        total += points

        # 5. Has phone
        phone_match = re.search(
            r"(\+?\d[\d\s\-().]{7,}\d)", text
        )
        points = self.CRITERIA["has_phone"] if phone_match else 0
        breakdown["has_phone"] = points
        total += points

        # 6. Has skills (2+ from keyword list)
        found_skills = [
            skill for skill in self.SKILL_KEYWORDS
            if re.search(r"\b" + re.escape(skill) + r"\b", text_lower)
        ]
        points = self.CRITERIA["has_skills"] if len(found_skills) >= 2 else (
            7 if len(found_skills) == 1 else 0
        )
        breakdown["has_skills"] = points
        breakdown["skills_found"] = found_skills[:10]
        total += points

        # 7. Has experience
        exp_matches = sum(
            1 for p in self.EXPERIENCE_PATTERNS
            if re.search(p, text_lower)
        )
        points = self.CRITERIA["has_experience"] if exp_matches >= 2 else (
            5 if exp_matches == 1 else 0
        )
        breakdown["has_experience"] = points
        total += points

        # 8. Has education
        edu_matches = sum(
            1 for p in self.EDUCATION_PATTERNS
            if re.search(p, text_lower)
        )
        points = self.CRITERIA["has_education"] if edu_matches >= 2 else (
            5 if edu_matches == 1 else 0
        )
        breakdown["has_education"] = points
        total += points

        # 9. Format bonus
        if file_extension in (".pdf", ".docx"):
            points = self.CRITERIA["format_bonus"]
        elif file_extension in (".doc", ".txt"):
            points = 5
        else:
            points = 0
        breakdown["format_bonus"] = points
        total += points

        # Clamp to 100
        total = min(total, 100)

        # Determine threshold and decision
        if total >= 70:
            threshold = "auto_approve"
            auto_decision = "auto_approved"
        elif total >= 40:
            threshold = "admin_review"
            auto_decision = "pending_review"
        else:
            threshold = "auto_reject"
            auto_decision = "auto_rejected"

        return {
            "total_score": total,
            "breakdown": breakdown,
            "threshold": threshold,
            "auto_decision": auto_decision,
            "reasons": self._build_reasons(breakdown),
        }

    def _build_reasons(self, breakdown: dict) -> list:
        reasons = []
        if breakdown.get("min_length", 0) == 0:
            reasons.append("Text too short (under 200 characters)")
        if breakdown.get("has_email", 0) == 0:
            reasons.append("No email address found")
        if breakdown.get("has_skills", 0) == 0:
            reasons.append("No recognizable skills found")
        if breakdown.get("has_experience", 0) == 0:
            reasons.append("No work experience section detected")
        if breakdown.get("has_education", 0) == 0:
            reasons.append("No education section detected")
        if breakdown.get("has_name", 0) == 0:
            reasons.append("No candidate name detected")
        return reasons


quality_scorer = QualityScorer()