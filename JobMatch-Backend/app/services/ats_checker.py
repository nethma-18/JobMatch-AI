import re
import logging
from typing import List, Optional, Tuple, Dict, Any
from app.ml.skill_extractor import skill_extractor
from app.services.job_description_parser import job_description_parser

logger = logging.getLogger(__name__)

STANDARD_FONTS_NOTE = "Use standard fonts: Arial, Calibri, Times New Roman, Helvetica."

PREFERRED_SECTIONS_ORDER = [
    "contact", "summary", "objective", "experience",
    "education", "skills", "projects", "certifications",
]


class ATSCheckerService:
    """
    Feature 6: ATS Checker
    Scores resume compatibility with Applicant Tracking Systems.
    """

    def check(self, resume_text: str, file_extension: str = ".pdf", jd_text: Optional[str] = None) -> dict:
        if not resume_text:
            return {
                "ats_score": 0,
                "score": 0,
                "grade": "Needs Improvement",
                "breakdown": {
                    "text_extractability": 0,
                    "structure": 0,
                    "sections": 0,
                    "keyword_alignment": 0,
                    "formatting": 0
                },
                "sections_found": [],
                "sections_missing": [
                    "Contact Information", "Professional Summary", "Skills",
                    "Work Experience", "Education", "Projects", "Certifications"
                ],
                "contact": {
                    "has_name": False,
                    "has_email": False,
                    "has_phone": False
                },
                "skills": {
                    "detected": [],
                    "matched_required": [],
                    "missing_required": [],
                    "matched_preferred": [],
                    "missing_preferred": []
                },
                "strengths": [],
                "improvements": ["Add resume content to check ATS compatibility."],
                "font_warning": STANDARD_FONTS_NOTE,
                "summary": "No resume content provided."
            }

        # 1. Text Extractability (max 20)
        ext_score, ext_warnings = self._evaluate_extractability(resume_text)

        # 2. Resume Structure (max 20)
        str_score, str_warnings, section_matches = self._evaluate_structure(resume_text)

        # 3. Required Sections (max 20)
        sec_score, found_labels, missing_labels = self._evaluate_sections(section_matches)

        # 4. Contact Information Check
        contact_score, contact_details = self._evaluate_contact(resume_text)

        # 5. Keyword/Skill Alignment (max 25)
        kw_score, kw_details = self._evaluate_keywords(resume_text, jd_text)

        # 6. Formatting/Readability (max 15)
        fmt_score, fmt_warnings = self._evaluate_formatting(resume_text, file_extension)

        # Compute total score dynamically bounded to 100
        breakdown = {
            "text_extractability": float(ext_score),
            "structure": float(str_score),
            "sections": float(sec_score),
            "keyword_alignment": float(kw_score),
            "formatting": float(fmt_score)
        }
        total_score = round(sum(breakdown.values()))
        total_score = min(max(total_score, 0), 100)

        # Strengths & Improvements feedback list
        strengths = []
        improvements = []

        # Populate strengths
        if contact_details["has_name"] and contact_details["has_email"] and contact_details["has_phone"]:
            strengths.append("All core contact details (name, email, phone) were successfully detected.")
        if ext_score >= 18:
            strengths.append("Excellent text extractability with standard character layouts.")
        if str_score >= 18:
            strengths.append("Strong resume structure with clear section headings.")
        if kw_score >= 20:
            strengths.append("High alignment of skills and keywords.")
        if len(found_labels) >= 5:
            strengths.append(f"Most critical sections detected: {', '.join(found_labels[:4])}.")

        # Populate improvements
        if not contact_details["has_name"]:
            improvements.append("Place your name clearly at the top of the resume.")
        if not contact_details["has_email"]:
            improvements.append("Add a professional email address.")
        if not contact_details["has_phone"]:
            improvements.append("Add your phone number to help recruiters contact you.")
        
        for warning in ext_warnings + str_warnings + fmt_warnings:
            improvements.append(warning)

        if jd_text:
            missing_req = kw_details.get("missing_required", [])
            if missing_req:
                improvements.append(f"Add missing required keyword skills: {', '.join(missing_req[:3])}.")
        else:
            improvements.append("Upload a job description to perform detailed keyword and skill alignment checks.")

        # Ensure suggestions lists compatibility
        suggestions = improvements

        grade = self._grade(total_score)

        return {
            "resume_id": None, # Filled in router
            "ats_score": total_score,
            "score": total_score,
            "grade": grade,
            "breakdown": breakdown,
            "sections_found": found_labels,
            "sections_missing": missing_labels,
            "contact": contact_details,
            "skills": kw_details,
            "strengths": strengths,
            "improvements": improvements,
            "suggestions": suggestions,
            "font_warning": STANDARD_FONTS_NOTE,
            "summary": self._summary(total_score)
        }

    def _evaluate_extractability(self, text: str) -> Tuple[int, List[str]]:
        warnings = []
        score = 20

        # Length check
        char_len = len(text.strip())
        if char_len < 200:
            warnings.append("Resume contains very little text. Review your document exporter settings.")
            score -= 10
        elif char_len < 500:
            warnings.append("Resume content is short. Expand your project descriptions and skills.")
            score -= 5

        # Character set safety
        # Exclude spaces and punctuation to find safe char ratio
        alphanumeric_or_tech = re.findall(r"[A-Za-z0-9\s.,!@#$%^&*()_\-+=|\\:;\"'<>?/]", text)
        safe_ratio = len(alphanumeric_or_tech) / max(len(text), 1)
        if safe_ratio < 0.90:
            warnings.append("Suspicious non-standard character codes detected. Re-export your PDF cleanly.")
            score -= 5

        return max(0, score), warnings

    def _evaluate_structure(self, text: str) -> Tuple[int, List[str], Dict[str, bool]]:
        warnings = []
        score = 20

        text_lower = text.lower()
        section_keywords = {
            "contact":        ["contact", "email", "phone", "address"],
            "summary":        ["summary", "objective", "profile", "about me"],
            "experience":     ["experience", "employment", "work history", "career"],
            "education":      ["education", "academic", "qualification", "degree"],
            "skills":         ["skills", "technical skills", "competencies", "expertise"],
            "projects":       ["projects", "portfolio", "work samples"],
            "certifications": ["certification", "certificate", "award", "achievement"],
        }

        section_matches = {}
        for section, keywords in section_keywords.items():
            section_matches[section] = any(kw in text_lower for kw in keywords)

        # Critical headings validation
        missing_critical = []
        for sec in ["experience", "education", "skills"]:
            if not section_matches[sec]:
                missing_critical.append(sec.capitalize())
        if missing_critical:
            warnings.append(f"Ensure critical sections ({', '.join(missing_critical)}) have distinct headers.")
            score -= len(missing_critical) * 4

        # Paragraph check
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        long_paragraphs = [p for p in paragraphs if len(p.strip()) > 1000]
        if long_paragraphs:
            warnings.append("Avoid large blocks of text. Break down descriptions into concise bullet points.")
            score -= 4

        # Bullet check
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        bullet_lines = [l for l in lines if l.startswith(("-", "*", "•", "o"))]
        if len(bullet_lines) < 3:
            warnings.append("Use list formats or bullet points to present achievements and roles.")
            score -= 4

        return max(0, score), warnings, section_matches

    def _evaluate_sections(self, section_matches: Dict[str, bool]) -> Tuple[int, List[str], List[str]]:
        labels_map = {
            "contact": "Contact Information",
            "summary": "Professional Summary",
            "skills": "Skills",
            "experience": "Work Experience",
            "education": "Education",
            "projects": "Projects",
            "certifications": "Certifications"
        }

        found_labels = []
        missing_labels = []
        score = 0

        for key, present in section_matches.items():
            label = labels_map[key]
            if present:
                found_labels.append(label)
                # Critical gets 3 points, additional gets 2.66 points
                score += 3 if key in ["contact", "experience", "education", "skills"] else 2.66
            else:
                missing_labels.append(label)

        return min(20, round(score)), found_labels, missing_labels

    def _evaluate_contact(self, text: str) -> Tuple[int, dict]:
        # Don't return actual values in response payload
        has_email = bool(re.search(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", text))
        has_phone = bool(re.search(r"(\+?\d[\d\s\-().]{7,}\d)", text))
        
        # Name detection: look for Capitalized Word patterns in the first 500 characters
        has_name = False
        first_lines = [l.strip() for l in text[:500].split("\n") if l.strip()]
        for line in first_lines[:3]:
            # A line with exactly 2 or 3 capitalized words (e.g. John Doe, Alice Jenkins)
            if re.match(r"^[A-Z][a-z]+(\s+[A-Z][a-z]+){1,2}$", line):
                has_name = True
                break

        score = 0
        if has_name:
            score += 8
        if has_email:
            score += 6
        if has_phone:
            score += 6

        return score, {
            "has_name": has_name,
            "has_email": has_email,
            "has_phone": has_phone
        }

    def _evaluate_keywords(self, text: str, jd_text: Optional[str] = None) -> Tuple[int, dict]:
        resume_skills = set(s.lower() for s in skill_extractor.extract(text))
        
        if not jd_text:
            # Fallback based on extracted skills count
            count = len(resume_skills)
            if count >= 10:
                score = 25
            elif count >= 5:
                score = 20
            elif count >= 1:
                score = 10
            else:
                score = 0

            return score, {
                "detected": sorted(list(resume_skills)),
                "matched_required": [],
                "missing_required": [],
                "matched_preferred": [],
                "missing_preferred": []
            }

        # Match against JD
        parsed = job_description_parser.parse(jd_text)
        required_set = set(s.lower() for s in parsed.get("required_skills", []))
        preferred_set = set(s.lower() for s in parsed.get("preferred_skills", []))

        matched_req = list(resume_skills & required_set)
        missing_req = list(required_set - resume_skills)
        matched_pref = list(resume_skills & preferred_set)
        missing_pref = list(preferred_set - resume_skills)

        req_ratio = len(matched_req) / len(required_set) if required_set else 1.0
        pref_ratio = len(matched_pref) / len(preferred_set) if preferred_set else 1.0

        # Required has 20 points weight, Preferred has 5 points weight
        score = req_ratio * 20 + pref_ratio * 5
        score = min(max(round(score), 0), 25)

        return score, {
            "detected": sorted(list(resume_skills)),
            "matched_required": sorted(matched_req),
            "missing_required": sorted(missing_req),
            "matched_preferred": sorted(matched_pref),
            "missing_preferred": sorted(missing_pref)
        }

    def _evaluate_formatting(self, text: str, ext: str) -> Tuple[int, List[str]]:
        warnings = []
        score = 15

        # Format (5 pts)
        if ext.lower() in (".pdf", ".docx"):
            score = 15
        elif ext.lower() in (".doc", ".txt"):
            warnings.append("Format doc/txt is less optimized. Convert to PDF or DOCX.")
            score = 11
        else:
            warnings.append(f"Format {ext} is unfriendly. Convert to PDF or DOCX.")
            score = 5

        # Line lengths
        lines = [l for l in text.split("\n") if l.strip()]
        long_lines = [l for l in lines if len(l) > 200]
        if len(long_lines) > 5:
            warnings.append("Several extremely long lines detected. Split text into multiple paragraphs.")
            score -= 3

        # Tables/Layout
        if text.count("|") > 15:
            warnings.append("Frequent vertical lines detected. Avoid complex tables and multi-column designs.")
            score -= 3

        return max(0, score), warnings

    def _grade(self, score: int) -> str:
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Very Good"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Fair"
        else:
            return "Needs Improvement"

    def _summary(self, score: int) -> str:
        if score >= 90:
            return "Excellent ATS compatibility! Your resume is highly optimized for target parsers."
        elif score >= 80:
            return "Very good structure and keyword alignment. Apply minor optimizations to score higher."
        elif score >= 70:
            return "Good formatting and section layout. Add missing skills and summary sections to stand out."
        elif score >= 60:
            return "Fair compatibility. Adjust line lengths, layouts, and add more target keywords."
        else:
            return "Poor ATS compatibility. Your resume structure and content require significant changes."


ats_checker_service = ATSCheckerService()