import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class BlindScreenerService:
    """
    Feature 15: Blind Screening (Unbiased Recruitment)
    Anonymizes candidate names, filenames, email addresses, phone numbers,
    and demographic PII to ensure bias-free candidate evaluation.
    """

    PII_PATTERNS = [
        (r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "[ANONYMIZED EMAIL]"),
        (r"(\+?\d[\d\s\-().]{7,}\d)", "[ANONYMIZED PHONE]"),
    ]

    def anonymize_candidate(self, candidate: Dict[str, Any], index: int = 1) -> Dict[str, Any]:
        """
        Anonymize a single candidate object.
        Replaces candidate name and filename with anonymized identifiers.
        """
        anon_cand = dict(candidate)

        # Generate anonymous name (e.g. Candidate #1, Candidate #2)
        rank = candidate.get("rank", index)
        anon_name = f"Candidate #{rank}"

        # Anonymize filename (e.g. Resume_Candidate_1.pdf)
        orig_filename = candidate.get("filename", "")
        ext = ""
        if "." in orig_filename:
            ext = "." + orig_filename.rsplit(".", 1)[-1]
        anon_filename = f"Resume_Candidate_{rank}{ext}"

        anon_cand["candidate_name"] = anon_name
        anon_cand["filename"] = anon_filename
        anon_cand["is_anonymized"] = True

        # Clear direct PII fields
        for field in ["email", "phone", "address", "location", "education_institutions", "institution", "profile_image"]:
            if field in anon_cand:
                anon_cand[field] = "[ANONYMIZED]"

        # Sanitize matched/missing text if it contains contact details
        if "text" in anon_cand and anon_cand["text"]:
            anon_cand["text"] = self.sanitize_text(anon_cand["text"])

        return anon_cand

    def anonymize_rankings(self, rankings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Anonymize a list of ranked candidate objects."""
        return [self.anonymize_candidate(c, i + 1) for i, c in enumerate(rankings)]

    def sanitize_text(self, text: str) -> str:
        """Strip email addresses and phone numbers from raw text snippet."""
        if not text:
            return ""
        sanitized = text
        for pattern, replacement in self.PII_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized)
        return sanitized


blind_screener_service = BlindScreenerService()
