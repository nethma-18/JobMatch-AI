import logging
from typing import List, Optional
from app.ml.similarity import similarity_engine
from app.ml.skill_extractor import skill_extractor

logger = logging.getLogger(__name__)


class ResumeEnhancerService:
    """
    Feature 1: Resume Enhancer
    """

    def analyze(
        self,
        resume_text: str,
        jd_text: str,
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
        exp_required: Optional[float] = None,
        edu_required: Optional[str] = None,
    ) -> dict:
        if not resume_text or not jd_text:
            return {"error": "Both resume and job description text are required"}

        # 1. Similarity match score
        match = similarity_engine.compute_match(
            resume_text=resume_text,
            jd_text=jd_text,
            required_skills=required_skills,
            preferred_skills=preferred_skills
        )

        # 2. ATS parsing compatibility analysis
        from app.services.ats_checker import ats_checker_service
        ats_result = ats_checker_service.check(
            resume_text=resume_text,
            jd_text=jd_text
        )

        # 3. Experience Gap Comparison
        cand_exp = skill_extractor.extract_experience_years(resume_text)
        exp_gap = None
        exp_status = "unknown"
        if exp_required is not None and exp_required > 0:
            if cand_exp is not None:
                exp_gap = max(0.0, float(exp_required) - float(cand_exp))
                exp_status = "meets_requirement" if cand_exp >= exp_required else "below_requirement"
        else:
            exp_status = "meets_requirement"

        # 4. Education Gap Comparison
        def extract_degree(text: str) -> Optional[str]:
            import re
            text_lower = text.lower()
            if re.search(r"\b(ph\.?d\.?|doctorate)\b", text_lower):
                return "PhD"
            if re.search(r"\b(master['\s]?s?|m\.?sc?\.?|m\.?eng\.?|m\.?a\.?|mba)\b", text_lower):
                return "Master's"
            if re.search(r"\b(bachelor['\s]?s?|b\.?sc?\.?|b\.?eng\.?|b\.?a\.?)\b", text_lower):
                return "Bachelor's"
            if re.search(r"\b(diploma|associate)\b", text_lower):
                return "Associate / Diploma"
            return None

        cand_edu = extract_degree(resume_text)
        edu_match = "unknown"
        if edu_required:
            if cand_edu:
                levels = {
                    "phd": 4,
                    "master's": 3,
                    "bachelor's": 2,
                    "associate / diploma": 1
                }
                req_level = levels.get(edu_required.lower(), 0)
                cand_level = levels.get(cand_edu.lower(), 0)
                if req_level == 0 or cand_level == 0:
                    edu_match = edu_required.lower() == cand_edu.lower()
                else:
                    edu_match = cand_level >= req_level
            else:
                edu_match = "unknown"
        else:
            edu_match = True

        # 5. Missing JD keywords
        missing_keywords = list(set(match.get("missing_required_skills", [])) | set(ats_result["skills"].get("missing_required", [])))

        # 6. Prioritized Actionable Improvements
        prioritized_improvements = []
        
        # Skill gaps (High Priority)
        for s in match.get("missing_required_skills", [])[:3]:
            prioritized_improvements.append({
                "text": f"Add missing required keyword skill: {s}.",
                "priority": "High"
            })
            
        # Contact gaps (High Priority)
        if not ats_result["contact"]["has_email"]:
            prioritized_improvements.append({
                "text": "Add a professional email address.",
                "priority": "High"
            })
        if not ats_result["contact"]["has_phone"]:
            prioritized_improvements.append({
                "text": "Add your phone number.",
                "priority": "High"
            })

        # Experience gaps (Medium Priority)
        if exp_status == "below_requirement" and exp_gap:
            prioritized_improvements.append({
                "text": f"Highlight experience closer to the required {exp_required} years (gap: {exp_gap} year(s)).",
                "priority": "Medium"
            })

        # Section gaps (Medium Priority)
        for sec in ats_result.get("sections_missing", []):
            prioritized_improvements.append({
                "text": f"Add missing recommended section: {sec}.",
                "priority": "Medium"
            })

        # Formatting/Readability fixes (Low Priority)
        for warning in ats_result.get("improvements", []):
            if "email" not in warning.lower() and "phone" not in warning.lower() and "skill" not in warning.lower() and "keyword" not in warning.lower():
                prioritized_improvements.append({
                    "text": warning,
                    "priority": "Low"
                })

        if not prioritized_improvements:
            prioritized_improvements.append({
                "text": "Your resume is highly optimized! Keep tailoring it for specific target roles.",
                "priority": "Low"
            })

        # Overall severity
        high_gaps = [imp for imp in prioritized_improvements if imp["priority"] == "High"]
        med_gaps = [imp for imp in prioritized_improvements if imp["priority"] == "Medium"]
        if high_gaps:
            severity = "High"
        elif med_gaps:
            severity = "Medium"
        else:
            severity = "Low"

        return {
            # New standard keys
            "overall_score": match["match_score"],
            "selection_probability": match["selection_probability"],
            "interview_eligible": match["interview_eligible"],
            "eligibility_label": match["eligibility_label"],
            
            "matched_required_skills": match["matched_required_skills"],
            "missing_required_skills": match["missing_required_skills"],
            "matched_preferred_skills": match["matched_preferred_skills"],
            "missing_preferred_skills": match["missing_preferred_skills"],
            "important_missing_keywords": missing_keywords,
            
            "detected_sections": ats_result["sections_found"],
            "missing_recommended_sections": ats_result["sections_missing"],
            
            "experience": {
                "required": float(exp_required) if exp_required is not None else None,
                "candidate": float(cand_exp) if cand_exp is not None else None,
                "gap": float(exp_gap) if exp_gap is not None else None,
                "status": exp_status
            },
            "education": {
                "required": edu_required,
                "candidate": cand_edu,
                "match": edu_match
            },
            
            "ats_score": ats_result["ats_score"],
            "ats_weaknesses": ats_result["improvements"],
            "resume_strengths": ats_result["strengths"],
            "prioritized_actionable_improvements": prioritized_improvements,
            "improvement_priority": severity,

            # Compatibility keys for any existing components
            "score": match["score"],
            "embedding_score": match["embedding_score"],
            "skill_overlap_score": match["skill_overlap_score"],
            "matched_skills": match["matched_required_skills"],
            "missing_skills": match["missing_required_skills"],
            "resume_skills": match["resume_skills"],
            "jd_required_skills": match["matched_required_skills"] + match["missing_required_skills"],
            "experience_years_detected": cand_exp,
            "education_detected": [cand_edu] if cand_edu else [],
            "section_scores": ats_result["breakdown"],
            "improvement_suggestions": [imp["text"] for imp in prioritized_improvements],
            "summary": ats_result["summary"]
        }


resume_enhancer_service = ResumeEnhancerService()