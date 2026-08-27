import re
from typing import List, Tuple, Dict, Any, Optional
from app.ml.skill_extractor import skill_extractor

class JobDescriptionParser:
    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse raw job description text.
        Extracts:
        - normalized description (clean spaces)
        - required skills
        - preferred skills
        - experience requirements (years)
        - education requirements
        - certifications
        - employment type
        - location type
        """
        if not text:
            return {
                "description_clean": "",
                "required_skills": [],
                "preferred_skills": [],
                "experience_required": None,
                "education_required": None,
                "certifications": [],
                "employment_type": None,
                "location_type": None,
            }

        # Clean description
        description_clean = self._clean_text(text)

        # Extract skills (Required vs Preferred)
        required_skills, preferred_skills = self._extract_categorized_skills(text)

        # Extract experience years
        exp_years = skill_extractor.extract_experience_years(text)

        # Extract education requirements
        education = self._extract_education_requirements(text)

        # Extract certifications
        certs = self._extract_certifications(text)

        # Extract employment type
        emp_type = self._extract_employment_type(text)

        # Extract location type
        loc_type = self._extract_location_type(text)

        return {
            "description_clean": description_clean,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "experience_required": exp_years,
            "education_required": education,
            "certifications": certs,
            "employment_type": emp_type,
            "location_type": loc_type,
        }

    def _clean_text(self, text: str) -> str:
        # standard clean
        import re
        text = re.sub(r"[^\x20-\x7E\n\r\t]", " ", text)
        text = re.sub(r" {3,}", "  ", text)
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text.strip()

    def _extract_categorized_skills(self, text: str) -> Tuple[List[str], List[str]]:
        lines = text.split("\n")
        required_skills = set()
        preferred_skills = set()
        unclassified_skills = set()

        current_sec = "unclassified"

        req_patterns = [
            r"\b(required skills|requirements|must\s*have|qualifications|essential|what\s*you\s*need|what\s*you\s*bring|experience)\b"
        ]
        pref_patterns = [
            r"\b(preferred|nice\s*to\s*have|desirable|bonus|plus|nice-to-have)\b"
        ]
        other_patterns = [
            r"\b(benefits|salary|about\s*us|perks|company|culture)\b"
        ]

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            line_lower = line_stripped.lower()

            # Check if line resembles a section header
            # Usually shorter lines (e.g. less than 60 chars) or containing section names
            is_header = False
            if len(line_stripped) < 60:
                if any(re.search(pat, line_lower) for pat in req_patterns):
                    current_sec = "required"
                    is_header = True
                elif any(re.search(pat, line_lower) for pat in pref_patterns):
                    current_sec = "preferred"
                    is_header = True
                elif any(re.search(pat, line_lower) for pat in other_patterns):
                    current_sec = "other"
                    is_header = True

            if is_header:
                continue

            # Extract skills from line
            line_skills = skill_extractor.extract(line_stripped)
            if not line_skills:
                continue

            if current_sec == "required":
                required_skills.update(line_skills)
            elif current_sec == "preferred":
                preferred_skills.update(line_skills)
            elif current_sec == "unclassified":
                unclassified_skills.update(line_skills)

        # If we didn't find any explicit required/preferred sections, everything goes to required
        if not required_skills and not preferred_skills:
            required_skills = unclassified_skills
        else:
            # If we had some section separation, distribute the unclassified ones:
            # Put them in required_skills by default
            required_skills.update(unclassified_skills)

        # Clean overlap: a required skill should not be preferred
        preferred_skills.difference_update(required_skills)

        # Normalize casing (skills from extract are already lowercased and sorted)
        return sorted(list(required_skills)), sorted(list(preferred_skills))

    def _extract_education_requirements(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        if re.search(r"\b(ph\.?d\.?|doctorate)\b", text_lower):
            return "PhD"
        elif re.search(r"\b(master['\s]?s?|m\.?sc?\.?|m\.?eng\.?|m\.?a\.?|mba)\b", text_lower):
            return "Master's"
        elif re.search(r"\b(bachelor['\s]?s?|b\.?sc?\.?|b\.?eng\.?|b\.?a\.?)\b", text_lower):
            return "Bachelor's"
        elif re.search(r"\b(diploma|associate)\b", text_lower):
            return "Associate / Diploma"
        return None

    def _extract_certifications(self, text: str) -> List[str]:
        text_lower = text.lower()
        cert_list = []
        known_certs = {
            "aws": "AWS Certified",
            "pmp": "Project Management Professional (PMP)",
            "scrum master": "Certified ScrumMaster (CSM)",
            "cissp": "CISSP",
            "ccna": "CCNA",
            "itil": "ITIL",
        }
        for keyword, fullname in known_certs.items():
            if keyword in text_lower:
                cert_list.append(fullname)
        return cert_list

    def _extract_employment_type(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        if "full-time" in text_lower or "full time" in text_lower:
            return "Full-time"
        elif "part-time" in text_lower or "part time" in text_lower:
            return "Part-time"
        elif "contract" in text_lower:
            return "Contract"
        elif "internship" in text_lower or "intern" in text_lower:
            return "Internship"
        return None

    def _extract_location_type(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        if "remote" in text_lower:
            return "Remote"
        elif "hybrid" in text_lower:
            return "Hybrid"
        elif "on-site" in text_lower or "onsite" in text_lower:
            return "On-site"
        return None

job_description_parser = JobDescriptionParser()
