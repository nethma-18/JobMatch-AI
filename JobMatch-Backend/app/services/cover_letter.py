import re
import logging
from datetime import datetime
from typing import List, Optional
from app.ml.skill_extractor import skill_extractor

logger = logging.getLogger(__name__)


class CoverLetterService:
    """
    Feature 2: Cover Letter Generator
    Generates tailored cover letters using template + NLP extraction.
    No OpenAI needed — fully local generation with smart templates.
    """

    TONES = ["professional", "enthusiastic", "concise"]

    def generate(
        self,
        resume_text: str,
        jd_text: str,
        applicant_name: str = "Applicant",
        company_name: str = "the company",
        job_title: str = "this position",
        tone: str = "professional",
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
        exp_required: Optional[float] = None,
        edu_required: Optional[str] = None,
    ) -> dict:

        if not resume_text or not jd_text:
            return {"error": "Both resume and job description are required"}

        # Extract data from resume
        skills = set(s.lower() for s in skill_extractor.extract(resume_text))
        exp_years = skill_extractor.extract_experience_years(resume_text)
        education = skill_extractor.extract_education(resume_text)

        # Extract name from resume if not provided
        if applicant_name == "Applicant":
            applicant_name = self._extract_name(resume_text) or "Applicant"

        # Extract job title from JD if not provided
        if job_title == "this position":
            job_title = self._extract_job_title(jd_text) or "this position"

        # Clean job title to avoid pulling in qualifications/companies not in resume
        if job_title:
            for term in ["phd", "ph.d", "doctorate", "google", "facebook", "amazon", "apple", "netflix", "docker"]:
                if term not in resume_text.lower():
                    job_title = re.sub(r"\b" + re.escape(term) + r"\b", "", job_title, flags=re.IGNORECASE)
            job_title = re.sub(r"\s+", " ", job_title).strip()

        # Extract company name from JD if not provided
        if company_name == "the company":
            company_name = self._extract_company(jd_text) or "your company"

        # Match skills (casing insensitive mapping)
        jd_req = set(s.lower() for s in (required_skills or skill_extractor.extract(jd_text)))
        jd_pref = set(s.lower() for s in (preferred_skills or []))

        matched_req = sorted(list(skills & jd_req))
        matched_pref = sorted(list(skills & jd_pref))
        matched_skills_used = list(set(matched_req) | set(matched_pref))

        # Build clean strings for experience and education
        exp_str = ""
        if exp_years is not None and exp_years > 0:
            exp_str = f"With {exp_years:.0f} years of professional experience"
        else:
            exp_str = "Throughout my professional journey"

        edu_str = ""
        if education:
            edu_entry = education[0]
            degree = edu_entry.get("degree", "educational qualifications")
            field = edu_entry.get("field", "")
            if field:
                edu_str = f"Having completed my {degree} in {field},"
            else:
                edu_str = f"Having completed my {degree},"
        else:
            edu_str = "With my educational background,"

        skills_str = ""
        if matched_skills_used:
            skills_str = f"proficiency in {', '.join(matched_skills_used[:3])}"
        elif skills:
            skills_str = f"proficiency in {', '.join(sorted(list(skills))[:3])}"
        else:
            skills_str = "a range of relevant technical competencies"

        # Generate each paragraph
        opening   = self._opening(job_title, company_name, tone)
        body1     = self._body_skills(exp_str, edu_str, skills_str, tone)
        body2     = self._body_value(matched_skills_used, tone)
        closing   = self._closing(company_name, tone)
        signature = f"\nSincerely,\n{applicant_name}"

        letter = f"{opening}\n\n{body1}\n\n{body2}\n\n{closing}{signature}"

        return {
            "cover_letter": letter,
            "applicant_name": applicant_name,
            "job_title": job_title,
            "company_name": company_name,
            "tone": tone,
            "matched_skills_used": matched_skills_used,
            "relevant_experience_used": {
                "years_experience": exp_years,
                "education": [e.get("degree") for e in education if e.get("degree")]
            },
            "generation_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "word_count": len(letter.split()),
                "tone": tone
            },
            "word_count": len(letter.split()),
            "paragraphs": {
                "opening": opening,
                "body_skills": body1,
                "body_value": body2,
                "closing": closing
            }
        }

    # ── Paragraph generators ─────────────────────────────────────

    def _opening(self, title, company, tone):
        if tone == "enthusiastic":
            return (
                f"Dear Hiring Manager,\n\n"
                f"I am absolutely thrilled to apply for the {title} role at {company}! "
                f"Having followed {company}'s industry presence closely, I am incredibly excited by the opportunity "
                f"to bring my skills and passion to your team."
            )
        elif tone == "concise":
            return (
                f"Dear Hiring Manager,\n\n"
                f"Please accept this application for the {title} position at {company}."
            )
        else:  # professional
            return (
                f"Dear Hiring Manager,\n\n"
                f"I am writing to express my strong interest in the {title} position at {company}. "
                f"After reviewing the role requirements, I am confident that my background "
                f"and skills make me a strong fit for this opportunity."
            )

    def _body_skills(self, exp_str, edu_str, skills_str, tone):
        if tone == "enthusiastic":
            return (
                f"{exp_str}, I have built strong {skills_str}. "
                f"{edu_str} I love tackling complex technical challenges and have consistently "
                f"brought creative, high-performing solutions to life in collaborative environments."
            )
        elif tone == "concise":
            return (
                f"{exp_str}, I have developed {skills_str}. "
                f"{edu_str} I have a proven track record of applying these skills effectively to deliver results."
            )
        else:  # professional
            return (
                f"{exp_str}, I have developed strong {skills_str}. "
                f"{edu_str} I have successfully applied these competencies to deliver structured, "
                f"high-quality outcomes and meet organizational goals."
            )

    def _body_value(self, matched_skills, tone):
        focus = ""
        if matched_skills:
            focus = f"your requirements for {', '.join(matched_skills[:2])}"
        else:
            focus = "your team's key objectives"

        if tone == "enthusiastic":
            return (
                f"I am particularly drawn to {focus} and believe my experience "
                f"positions me to make a meaningful, immediate impact. I thrive in innovative "
                f"environments and am always eager to learn, grow, and help push project success."
            )
        elif tone == "concise":
            return (
                f"I am aligned with {focus} and ready to contribute to your projects."
            )
        else:  # professional
            return (
                f"I am particularly interested in {focus} as outlined in the job description. "
                f"I am confident in my capacity to contribute effectively to your team "
                f"and support your objectives through high-quality work."
            )

    def _closing(self, company, tone):
        if tone == "enthusiastic":
            return (
                f"I would love the opportunity to discuss how my background can "
                f"contribute to {company}'s continued success. Thank you so much "
                f"for considering my application — I look forward to hearing from you!\n"
            )
        elif tone == "concise":
            return (
                f"I welcome the opportunity to discuss my qualifications further. "
                f"Thank you for your consideration.\n"
            )
        else:  # professional
            return (
                f"I would welcome the opportunity to discuss how my experience "
                f"and qualifications align with the needs of {company}. Thank you for your time "
                f"and consideration. I look forward to the possibility of contributing to your team.\n"
            )

    # ── Extraction helpers ───────────────────────────────────────

    def _extract_name(self, text: str):
        lines = text.strip().split("\n")
        for line in lines[:5]:
            line = line.strip()
            match = re.match(r"^([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})$", line)
            if match and 4 < len(line) < 50:
                return match.group(1)
        return None

    def _extract_job_title(self, jd_text: str):
        patterns = [
            r"(?:position|role|title|job):\s*([A-Za-z\s]+)",
            r"(?:hiring|seeking|looking for)\s+(?:a|an)?\s*([A-Za-z\s]+(?:developer|engineer|manager|analyst|designer|lead|specialist))",
            r"^([A-Za-z\s]+(?:developer|engineer|manager|analyst|designer|lead|specialist))",
        ]
        for pattern in patterns:
            match = re.search(pattern, jd_text[:500], re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()[:60]
        return None

    def _extract_company(self, jd_text: str):
        patterns = [
            r"(?:at|join|company|organization|firm):\s*([A-Z][A-Za-z\s&.]+)",
            r"About\s+([A-Z][A-Za-z\s&.]{3,40})",
        ]
        for pattern in patterns:
            match = re.search(pattern, jd_text[:300], re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if 3 < len(name) < 50:
                    return name
        return None


cover_letter_service = CoverLetterService()