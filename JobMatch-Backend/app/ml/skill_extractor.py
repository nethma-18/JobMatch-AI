import re
import json
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class SkillExtractor:
    """
    Extracts skills from resume/JD text using:
    1. spaCy NER
    2. Custom skill lexicon (built from Kaggle datasets + ESCO)
    3. Regex pattern matching
    """

    def __init__(self):
        self.nlp = None
        self.skill_lexicon: set = set()
        self._load_lexicon()
        self._load_spacy()

    def _load_spacy(self):
        import spacy
        for model_name in ["en_core_web_sm", "en_core_web_md"]:
            try:
                self.nlp = spacy.load(model_name)
                logger.info(f"✅ spaCy model '{model_name}' loaded")
                return
            except Exception:
                continue
        logger.warning("spaCy not available: neither en_core_web_sm nor en_core_web_md could be loaded")
        self.nlp = None

    def _load_lexicon(self):
        """Load skill lexicon from JSON file."""
        lexicon_path = Path("data/skills_lexicon.json")
        if lexicon_path.exists():
            with open(lexicon_path, "r") as f:
                data = json.load(f)
                self.skill_lexicon = set(s.lower() for s in data)
            logger.info(f"✅ Skill lexicon loaded: {len(self.skill_lexicon)} skills")
        else:
            # Fallback built-in lexicon
            self.skill_lexicon = self._builtin_lexicon()
            logger.info(f"Using built-in lexicon: {len(self.skill_lexicon)} skills")

    def _builtin_lexicon(self) -> set:
        return {
            # Programming languages
            "python", "java", "javascript", "typescript", "c++", "c#", "c",
            "ruby", "php", "swift", "kotlin", "go", "golang", "rust", "scala",
            "r", "matlab", "perl", "shell", "bash", "powershell", "dart",
            "elixir", "haskell", "lua", "julia",

            # Web frameworks
            "react", "angular", "vue", "svelte", "nextjs", "nuxtjs",
            "django", "flask", "fastapi", "spring", "express", "rails",
            "laravel", "asp.net", "nestjs", "gatsby", "remix",

            # Databases
            "sql", "mysql", "postgresql", "mongodb", "redis", "sqlite",
            "oracle", "cassandra", "dynamodb", "elasticsearch", "neo4j",
            "firebase", "supabase", "mariadb", "mssql",

            # Cloud & DevOps
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
            "ansible", "jenkins", "github actions", "gitlab ci", "circleci",
            "nginx", "apache", "linux", "ubuntu", "centos", "heroku",
            "vercel", "netlify", "cloudflare",

            # ML / AI
            "machine learning", "deep learning", "neural networks",
            "tensorflow", "pytorch", "keras", "scikit-learn", "pandas",
            "numpy", "opencv", "nlp", "natural language processing",
            "computer vision", "data science", "data analysis",
            "hugging face", "transformers", "bert", "gpt",
            "reinforcement learning", "feature engineering",

            # Tools
            "git", "github", "gitlab", "bitbucket", "jira", "confluence",
            "figma", "photoshop", "illustrator", "sketch", "xd",
            "postman", "swagger", "vscode", "intellij", "eclipse",

            # Soft skills
            "leadership", "communication", "teamwork", "problem solving",
            "critical thinking", "project management", "agile", "scrum",
            "kanban", "time management", "mentoring", "collaboration",

            # Other tech
            "rest api", "graphql", "grpc", "microservices", "ci/cd",
            "test driven development", "tdd", "bdd", "unit testing",
            "selenium", "cypress", "jest", "pytest", "junit",
            "blockchain", "web3", "solidity", "iot", "embedded systems",
            "networking", "cybersecurity", "penetration testing",
        }

    def extract(self, text: str) -> List[str]:
        """Extract skills from text. Returns deduplicated list."""
        if not text:
            return []

        found_skills = set()
        text_lower = text.lower()

        # Method 1: Lexicon matching
        for skill in self.skill_lexicon:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text_lower):
                found_skills.add(skill)

        # Method 2: spaCy NER (catches proper nouns like company names used as skills)
        if self.nlp:
            try:
                doc = self.nlp(text[:10000])  # Limit for performance
                for ent in doc.ents:
                    ent_lower = ent.text.lower().strip()
                    if ent.label_ in ("ORG", "PRODUCT") and ent_lower in self.skill_lexicon:
                        found_skills.add(ent_lower)
            except Exception as e:
                logger.warning(f"spaCy extraction failed: {e}")

        # Method 3: Common patterns (e.g. "3 years of Python")
        pattern_skills = re.findall(
            r"\b(\d+\s*\+?\s*years?\s+(?:of\s+)?([A-Za-z+#.]+))\b",
            text
        )
        for _, skill in pattern_skills:
            s = skill.lower().strip()
            if len(s) > 2 and s in self.skill_lexicon:
                found_skills.add(s)

        return sorted(list(found_skills))

    def extract_experience_years(self, text: str) -> Optional[float]:
        """Extract total years of experience from text."""
        patterns = [
            r"(\d+)\s*\+?\s*years?\s+(?:of\s+)?(?:work\s+)?experience",
            r"experience\s*:?\s*(\d+)\s*\+?\s*years?",
            r"(\d+)\s*\+?\s*years?\s+(?:in\s+)?(?:the\s+)?(?:industry|field)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return float(match.group(1))

        # Infer from date ranges
        years = re.findall(r"\b(20\d{2}|19\d{2})\b", text)
        if len(years) >= 2:
            years_int = [int(y) for y in years]
            span = max(years_int) - min(years_int)
            if 0 < span <= 50:
                return float(span)

        return None

    def extract_education(self, text: str) -> List[dict]:
        """Extract education entries."""
        results = []
        text_lower = text.lower()

        degree_patterns = [
            r"(bachelor['\s]?s?|b\.?sc?\.?|b\.?eng\.?|b\.?a\.?)\s+(?:of\s+|in\s+)?([a-z\s]+)",
            r"(master['\s]?s?|m\.?sc?\.?|m\.?eng\.?|m\.?a\.?|mba)\s+(?:of\s+|in\s+)?([a-z\s]+)",
            r"(ph\.?d\.?|doctorate)\s+(?:of\s+|in\s+)?([a-z\s]+)",
            r"(diploma|certificate|associate)\s+(?:of\s+|in\s+)?([a-z\s]+)",
        ]

        for pattern in degree_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                degree = match.group(1).strip()
                field = match.group(2).strip()[:50] if match.lastindex >= 2 else ""
                if degree:
                    results.append({"degree": degree, "field": field, "institution": ""})

        return results[:5]  # Max 5 entries


skill_extractor = SkillExtractor()