import re
from typing import List


class SpamDetector:
    """
    Stage 5 of validation pipeline.
    Detects spam, test uploads, gibberish, and irrelevant content.
    """

    # Obvious test/spam patterns
    SPAM_PATTERNS = [
        r"\btest\s+upload\b",
        r"\bfake\s+resume\b",
        r"\bsample\s+text\b",
        r"\blorem\s+ipsum\b",
        r"\bfoo\s+bar\b",
        r"\bhello\s+world\b",
        r"asdfghjkl",
        r"qwertyuiop",
        r"1234567890{3,}",
        r"aaaa{4,}",
        r"xxxx{4,}",
        r"\btest\b.*\btest\b.*\btest\b",
    ]

    # Legitimate resume signals — at least some should be present
    RESUME_SIGNALS = [
        r"\beducation\b",
        r"\bexperience\b",
        r"\bskills?\b",
        r"\buniversity\b",
        r"\bcollege\b",
        r"\bdegree\b",
        r"\bemployment\b",
        r"\bwork\b",
        r"\bproject\b",
        r"\bcertif",
        r"\bachievement\b",
        r"\bresponsibilit",
        r"\bprofessional\b",
        r"\bintern\b",
        r"\bjob\b",
        r"\bposition\b",
    ]

    # Gibberish detection — ratio of non-alphabetic chars
    MAX_GIBBERISH_RATIO = 0.6

    def check(self, text: str) -> dict:
        """
        Returns dict:
        {
            passed: bool,
            is_spam: bool,
            score_penalty: int,   # points deducted (0 or 20)
            issues: list[str],
            details: dict
        }
        """
        if not text or len(text.strip()) < 50:
            return {
                "passed": False,
                "is_spam": True,
                "score_penalty": 20,
                "issues": ["Text too short to evaluate — possible empty or corrupt file"],
                "details": {"text_length": len(text) if text else 0},
            }

        text_lower = text.lower()
        issues = []
        details = {}

        # Check spam patterns
        for pattern in self.SPAM_PATTERNS:
            if re.search(pattern, text_lower):
                issues.append(f"Spam pattern detected: '{pattern}'")
                break

        # Check gibberish ratio
        alpha_count = sum(1 for c in text if c.isalpha())
        total_count = len(text.replace(" ", "").replace("\n", ""))
        gibberish_ratio = 1 - (alpha_count / max(total_count, 1))
        details["gibberish_ratio"] = round(gibberish_ratio, 3)

        if gibberish_ratio > self.MAX_GIBBERISH_RATIO:
            issues.append(
                f"High gibberish ratio ({gibberish_ratio:.0%}) — possible corrupted or non-English file"
            )

        # Check for resume signals
        signal_count = sum(
            1 for sig in self.RESUME_SIGNALS
            if re.search(sig, text_lower)
        )
        details["resume_signals_found"] = signal_count

        if signal_count < 2:
            issues.append(
                f"Only {signal_count} resume keywords found — content may not be a resume or job description"
            )

        # Repetition check — same line repeated many times
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if lines:
            unique_ratio = len(set(lines)) / len(lines)
            details["unique_line_ratio"] = round(unique_ratio, 3)
            if unique_ratio < 0.3:
                issues.append("High line repetition detected — possible auto-generated spam")

        is_spam = len(issues) > 0
        passed = not is_spam

        return {
            "passed": passed,
            "is_spam": is_spam,
            "score_penalty": 20 if is_spam else 0,
            "issues": issues,
            "details": details,
        }


spam_detector = SpamDetector()