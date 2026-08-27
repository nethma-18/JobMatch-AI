import re
import logging
from typing import List, Optional, Dict, Any
from app.ml.skill_extractor import skill_extractor

logger = logging.getLogger(__name__)


class InterviewQuestionsService:
    """
    Feature 3: Interview Question Generator
    Generates role-specific questions categorized by category, difficulty, and relevance.
    """

    CATEGORIES = ["Technical", "Experience/Behavioral", "Skills", "Job-Specific", "Resume-Based"]
    DIFFICULTIES = ["Easy", "Medium", "Hard"]

    def generate(
        self,
        resume_text: str,
        jd_text: str,
        num_questions: int = 12,
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
        exp_required: Optional[float] = None,
        edu_required: Optional[str] = None,
    ) -> dict:

        if not resume_text or not jd_text:
            return {"error": "Both resume and job description are required"}

        if num_questions < 5 or num_questions > 20:
            return {"error": "Number of questions must be between 5 and 20"}

        # Extract context
        resume_skills_set = set(s.lower() for s in skill_extractor.extract(resume_text))
        jd_req_set = set(s.lower() for s in (required_skills or skill_extractor.extract(jd_text)))
        jd_pref_set = set(s.lower() for s in (preferred_skills or []))

        exp_years = skill_extractor.extract_experience_years(resume_text)
        education = skill_extractor.extract_education(resume_text)
        job_title = self._extract_job_title(jd_text)

        matched_req = sorted(list(resume_skills_set & jd_req_set))
        missing_req = sorted(list(jd_req_set - resume_skills_set))
        matched_pref = sorted(list(resume_skills_set & jd_pref_set))

        all_matched = sorted(list(set(matched_req) | set(matched_pref)))

        question_pool = []

        # 1. Questions on Missing Required Skills (High priority — Category: Skills)
        for skill in missing_req:
            question_pool.append({
                "question": f"The position requires {skill.title()}. What is your experience level with {skill.title()}, and how do you plan to apply your background to master it?",
                "category": "Skills",
                "difficulty": "Medium",
                "why_relevant": f"'{skill.title()}' is a core requirement listed in the Job Description but was not found on your resume.",
                "related_skill": skill.title(),
                "answer_framework": f"Acknowledge foundational knowledge → Share related skills → Outline active upskilling strategy.",
                "sample_answer": f"While my direct experience with {skill.title()} is developing, I have extensive experience in related areas. I am quick to learn and have already started studying its core concepts."
            })

        # 2. Questions on Matched Required Skills (Category: Technical)
        for skill in matched_req:
            question_pool.append({
                "question": f"Can you detail a complex technical project where you implemented {skill.title()}? What architecture decisions did you make?",
                "category": "Technical",
                "difficulty": "Hard",
                "why_relevant": f"Your resume shows proficiency in '{skill.title()}', which is a required skill for this role.",
                "related_skill": skill.title(),
                "answer_framework": "STAR Method: Situation → Technical Challenge → Design Decisions in " + skill.title() + " → Results.",
                "sample_answer": f"In a recent project using {skill.title()}, I designed the architecture to handle high throughput by implementing modular design patterns and optimized queries."
            })

        # 3. Questions on Candidate Resume Technologies (Category: Resume-Based)
        for skill in sorted(list(resume_skills_set - set(matched_req))):
            question_pool.append({
                "question": f"You listed {skill.title()} on your resume. How have you utilized {skill.title()} to solve production or project challenges?",
                "category": "Resume-Based",
                "difficulty": "Medium",
                "why_relevant": f"'{skill.title()}' is explicitly listed on your resume.",
                "related_skill": skill.title(),
                "answer_framework": "Context → Specific problem → Practical application of " + skill.title() + " → Outcome.",
                "sample_answer": f"I used {skill.title()} to automate workflow processes, which improved overall system efficiency."
            })

        # 4. Behavioral & Experience Questions (Category: Experience/Behavioral)
        if exp_years is not None and exp_years > 0:
            question_pool.append({
                "question": f"With your {exp_years:.0f} years of professional experience, tell me about a time you had to make a critical technical tradeoff under tight deadlines.",
                "category": "Experience/Behavioral",
                "difficulty": "Medium",
                "why_relevant": f"Evaluates your decision-making and delivery track record over your {exp_years:.0f} years of detected experience.",
                "related_skill": "Technical Tradeoffs",
                "answer_framework": "Context → Options considered → Criteria for decision → Final outcome.",
                "sample_answer": f"During a past release, we prioritized core functionality over secondary features to meet a hard deadline, resulting in an on-time launch."
            })
        else:
            question_pool.append({
                "question": "Describe a project where you had to collaborate under pressure to solve an unexpected problem.",
                "category": "Experience/Behavioral",
                "difficulty": "Medium",
                "why_relevant": "Evaluates teamwork, adaptability, and problem-solving skills under tight deadlines.",
                "related_skill": "Problem Solving",
                "answer_framework": "STAR Method: Situation → Your Role → Action Taken → Positive Result.",
                "sample_answer": "When a key component failed during staging, I collaborated with the team in shifts to fix the bug and deliver on schedule."
            })

        question_pool.append({
            "question": "Describe a scenario where you received critical code review or architectural feedback. How did you handle it?",
            "category": "Experience/Behavioral",
            "difficulty": "Easy",
            "why_relevant": "Tests receptiveness to feedback and continuous learning mindset.",
            "related_skill": "Collaboration & Feedback",
            "answer_framework": "Listen without defensiveness → Evaluate feedback objectively → Implement improvements.",
            "sample_answer": "I welcomed feedback on my code structure, refactored the module per team suggestions, and established better testing practices."
        })

        # 5. Job-Specific Questions (Category: Job-Specific)
        question_pool.append({
            "question": f"What specific aspects of the {job_title} role align best with your career goals and technical background?",
            "category": "Job-Specific",
            "difficulty": "Easy",
            "why_relevant": f"Assesses your understanding of the {job_title} position and your motivation.",
            "related_skill": "Role Alignment",
            "answer_framework": "Role responsibilities → Personal technical strengths → Alignment with company goals.",
            "sample_answer": f"My background in software development aligns directly with the key requirements of the {job_title} position."
        })

        question_pool.append({
            "question": f"How do your qualifications prepare you to tackle the primary responsibilities outlined in the {job_title} description?",
            "category": "Job-Specific",
            "difficulty": "Medium",
            "why_relevant": f"Measures how effectively you connect your experience to the {job_title} job requirements.",
            "related_skill": "Job Requirements",
            "answer_framework": "Highlight top matching skills → Connect to JD objectives → Express readiness.",
            "sample_answer": "My hands-on experience directly matches the responsibilities specified in the posting."
        })

        # Filter, deduplicate, and limit to requested count
        seen_questions = set()
        final_questions = []
        
        for q in question_pool:
            q_text = q["question"].strip()
            if q_text not in seen_questions:
                seen_questions.add(q_text)
                final_questions.append(q)
                if len(final_questions) >= num_questions:
                    break

        # Number questions
        for i, q in enumerate(final_questions, start=1):
            q["number"] = i

        return {
            "questions": final_questions,
            "total": len(final_questions),
            "job_title": job_title,
            "detected_skills": sorted(list(resume_skills_set))[:10],
            "jd_required_skills": sorted(list(jd_req_set))[:10],
            "experience_years": exp_years,
            "preparation_tips": self._preparation_tips(sorted(list(jd_req_set))),
        }

    def _extract_job_title(self, jd_text: str) -> str:
        patterns = [
            r"(?:hiring|seeking|looking for)\s+(?:a|an)?\s*([A-Za-z\s]+(?:developer|engineer|manager|analyst|designer|lead|specialist))",
            r"^([A-Za-z\s]+(?:developer|engineer|manager|analyst|designer|lead|specialist))",
            r"(?:position|role|title):\s*([^\n]+)",
        ]
        for pattern in patterns:
            m = re.search(pattern, jd_text[:500], re.IGNORECASE | re.MULTILINE)
            if m:
                title = m.group(1).strip()[:60]
                # Clean title
                title = re.sub(r"\b(phd|google|docker|amazon|facebook)\b", "", title, flags=re.IGNORECASE).strip()
                return title if title else "the role"
        return "the role"

    def _preparation_tips(self, jd_skills: list) -> list:
        tips = [
            "Research the company's products, mission, and recent tech blog posts before the interview.",
            "Prepare STAR stories for each major project highlighted on your resume.",
            "Formulate smart questions to ask the interviewer about technical architecture and team culture.",
            "Practice explaining your code and architecture out loud within a 2-minute limit.",
        ]
        if jd_skills:
            tips.append(
                f"Review core fundamentals of: {', '.join(jd_skills[:4])}."
            )
        return tips


interview_questions_service = InterviewQuestionsService()