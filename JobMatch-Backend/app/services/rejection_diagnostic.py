import re
import logging
from app.ml.similarity import similarity_engine
from app.ml.skill_extractor import skill_extractor

logger = logging.getLogger(__name__)


class RejectionDiagnosticService:
    """
    Feature 4: Resume Rejection Diagnostic
    Explains why a resume was likely rejected and
    gives actionable improvement suggestions.
    """

    def diagnose(self, resume_text: str, jd_text: str) -> dict:
        if not resume_text or not jd_text:
            return {"error": "Both resume and job description are required"}

        match = similarity_engine.compute_match(resume_text, jd_text)

        issues = []
        suggestions = []
        weak_sections = []
        formatting_issues = []

        # ── Skill gaps ───────────────────────────────────────────
        missing_skills = match.get("missing_skills", [])
        if missing_skills:
            issues.append(f"Missing {len(missing_skills)} required skills")
            suggestions.append(
                f"Add these skills explicitly: {', '.join(missing_skills[:8])}. "
                "List them in your Skills section AND use them in experience bullets."
            )

        # ── Low semantic match ───────────────────────────────────
        if match["embedding_score"] < 50:
            issues.append("Resume language does not match job description tone or terminology")
            suggestions.append(
                "Copy 5–8 exact phrases from the job description and "
                "incorporate them naturally into your resume."
            )

        # ── Section weaknesses ───────────────────────────────────
        text_lower = resume_text.lower()

        section_checks = {
            "Work Experience": ["experience", "employment", "work history"],
            "Skills Section":  ["skills", "technical skills", "competencies"],
            "Education":       ["education", "degree", "university"],
            "Summary/Objective": ["summary", "objective", "profile"],
            "Achievements/Projects": ["projects", "achievements", "portfolio"],
        }

        for section_name, keywords in section_checks.items():
            if not any(kw in text_lower for kw in keywords):
                weak_sections.append(section_name)
                suggestions.append(
                    f"Add a '{section_name}' section — ATS and recruiters "
                    f"specifically look for this."
                )

        # ── Quantification gaps ──────────────────────────────────
        quant_count = len(re.findall(
            r"\b\d+\s*(%|percent|million|k\b|users|customers|team|projects?)\b",
            text_lower
        ))
        if quant_count < 2:
            issues.append("Lack of quantified achievements")
            suggestions.append(
                "Add numbers to your achievements. Examples: "
                "'Increased revenue by 25%', 'Managed team of 8', "
                "'Reduced load time by 40%'."
            )

        # ── Formatting issues ────────────────────────────────────
        if len(resume_text.split()) < 200:
            formatting_issues.append("Resume too short — under 200 words")
            suggestions.append("Expand your resume. Aim for 400–700 words with detailed bullets.")

        if resume_text.count("\n") < 10:
            formatting_issues.append("Very few line breaks detected — possible formatting issue")
            suggestions.append(
                "Use clear line breaks between sections. Single-column "
                "plain text formats parse best."
            )

        # ── Overall rejection reason ─────────────────────────────
        score = match["score"]
        if score < 40:
            primary_reason = (
                f"Very low match ({score:.0f}%). The resume and job description "
                "share very little in common — skills, terminology, and experience level "
                "all appear misaligned."
            )
        elif score < 65:
            primary_reason = (
                f"Below interview threshold ({score:.0f}%). Missing key skills "
                f"({', '.join(missing_skills[:3])}) likely triggered ATS filtering."
            )
        else:
            primary_reason = (
                f"Match score {score:.0f}% is above threshold but may have been "
                "filtered due to formatting, missing sections, or lack of quantified impact."
            )

        # Priority ranking of suggestions
        priority_suggestions = self._prioritize(suggestions, match)

        return {
            "overall_score": score,
            "primary_rejection_reason": primary_reason,
            "issues_found": issues,
            "weak_sections": weak_sections,
            "formatting_issues": formatting_issues,
            "missing_skills": missing_skills,
            "matched_skills": match.get("matched_skills", []),
            "priority_suggestions": priority_suggestions,
            "all_suggestions": suggestions,
            "improvement_potential": self._improvement_potential(score, len(missing_skills)),
        }

    def _prioritize(self, suggestions: list, match: dict) -> list:
        """Return top 5 suggestions in priority order."""
        prioritized = []

        # Skills always first
        missing = match.get("missing_skills", [])
        if missing:
            prioritized.append({
                "priority": 1,
                "action": "Add missing skills",
                "detail": f"Add to Skills section: {', '.join(missing[:5])}",
                "impact": "High",
            })

        # Quantification second
        prioritized.append({
            "priority": 2,
            "action": "Quantify achievements",
            "detail": "Add numbers: percentages, team sizes, revenue impact",
            "impact": "High",
        })

        # Language matching third
        if match["embedding_score"] < 60:
            prioritized.append({
                "priority": 3,
                "action": "Mirror job description language",
                "detail": "Use exact phrases from the job posting in your bullets",
                "impact": "Medium",
            })

        # Remaining suggestions
        for i, s in enumerate(suggestions[2:5], start=4):
            prioritized.append({
                "priority": i,
                "action": "Improve resume content",
                "detail": s,
                "impact": "Medium",
            })

        return prioritized[:5]

    def _improvement_potential(self, score: float, missing_count: int) -> str:
        potential_gain = missing_count * 3 + (65 - score if score < 65 else 0)
        if potential_gain > 30:
            return "High — adding missing skills could push you above the interview threshold"
        elif potential_gain > 15:
            return "Medium — targeted improvements will significantly improve your score"
        else:
            return "Low — resume is already strong, minor tweaks needed"


rejection_diagnostic_service = RejectionDiagnosticService()