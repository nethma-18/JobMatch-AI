import os
from pathlib import Path
from typing import Dict


class FormatChecker:
    """
    Stage 1 of validation pipeline.
    Checks file format, size, and basic readability.
    """

    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".txt"}
    MAX_SIZE_MB = 5.0
    MIN_SIZE_BYTES = 1024  # 1KB minimum — empty files rejected

    def check(self, file_path: str) -> dict:
        """
        Returns dict:
        {
            passed: bool,
            score: int,        # 0 or 10 (max points for format stage)
            issues: list[str],
            details: dict
        }
        """
        path = Path(file_path)
        issues = []
        details = {}

        # Check file exists
        if not path.exists():
            return {
                "passed": False,
                "score": 0,
                "issues": ["File does not exist on disk"],
                "details": {},
            }

        # Check extension
        ext = path.suffix.lower()
        details["extension"] = ext
        if ext not in self.ALLOWED_EXTENSIONS:
            issues.append(f"Invalid file type: '{ext}'")

        # Check file size
        size_bytes = path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        details["size_mb"] = round(size_mb, 3)
        details["size_bytes"] = size_bytes

        if size_bytes < self.MIN_SIZE_BYTES:
            issues.append(f"File too small ({size_bytes} bytes) — likely empty")

        if size_mb > self.MAX_SIZE_MB:
            issues.append(f"File too large ({size_mb:.1f}MB) — max {self.MAX_SIZE_MB}MB")

        passed = len(issues) == 0
        score = 10 if passed else 0

        return {
            "passed": passed,
            "score": score,
            "issues": issues,
            "details": details,
        }


format_checker = FormatChecker()