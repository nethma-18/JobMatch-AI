"""
Fixed complete seeder for all datasets.

Usage:
    cd backend
    python data/seed_training_pool.py

Handles all actual file paths and formats found in data/datasets/
"""

import asyncio
import os
import json
import re
import pickle
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import Counter
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL   = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "jobmatch_ai")
DATASETS_DIR  = Path("data/datasets")
MODEL_DIR     = Path("data/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

BATCH_SIZE = 500  # Insert in batches to avoid memory issues


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _make_doc(text: str, data_type: str, category: str = "") -> dict:
    return {
        "source":                  "public_dataset",
        "source_upload_id":        None,
        "data_type":               data_type,
        "category":                category,
        "cleaned_text":            text.strip(),
        "extracted_skills":        [],
        "extracted_experience":    None,
        "extracted_education":     [],
        "quality_score":           80,
        "added_to_training_at":    datetime.utcnow(),
        "used_in_retraining_count": 0,
        "last_used_at":            None,
    }


async def _bulk_insert(db, docs: list, label: str):
    """Insert in batches and report count."""
    if not docs:
        print(f"   ⚠️  {label}: 0 docs — skipping")
        return 0
    total = 0
    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i:i + BATCH_SIZE]
        await db["training_pool"].insert_many(batch)
        total += len(batch)
    print(f"   ✅ {label}: {total:,} docs inserted")
    return total


def _load_json_safe(path: Path) -> list:
    """Load JSON or JSONL file safely."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read().strip()
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Some datasets wrap list in a key
            for v in data.values():
                if isinstance(v, list):
                    return v
    except json.JSONDecodeError:
        pass
    # Try JSONL
    result = []
    for line in content.splitlines():
        line = line.strip()
        if line:
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return result


def _read_csv_safe(path: Path, **kwargs) -> pd.DataFrame:
    """Read CSV with fallback encodings."""
    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            return pd.read_csv(path, encoding=enc, on_bad_lines="skip", **kwargs)
        except Exception:
            continue
    return pd.DataFrame()


def _extract_text_from_pdf(path: Path) -> str:
    """Extract text from PDF using PyPDF2."""
    try:
        import PyPDF2
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n".join(pages).strip()
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════
# Dataset loaders
# ═══════════════════════════════════════════════════════════════

async def load_resume_csv(db) -> int:
    """
    Dataset: resume-dataset/Resume/Resume.csv
    Columns: Resume_str, Category
    """
    path = DATASETS_DIR / "resume-dataset" / "Resume" / "Resume.csv"
    if not path.exists():
        print(f"   ⚠️  Resume CSV not found: {path}")
        return 0

    df = _read_csv_safe(path)
    print(f"   📄 Resume CSV columns: {list(df.columns)}")

    # Detect text column
    text_col = next((c for c in df.columns if "resume" in c.lower() or "text" in c.lower()), None)
    cat_col  = next((c for c in df.columns if "category" in c.lower()), None)

    if not text_col:
        print(f"   ⚠️  Cannot detect text column in Resume CSV. Columns: {list(df.columns)}")
        return 0

    docs = []
    for _, row in df.iterrows():
        text = str(row[text_col]).strip()
        cat  = str(row[cat_col]).strip() if cat_col else "General"
        if len(text) > 200:
            docs.append(_make_doc(text, "resume", category=cat))

    return await _bulk_insert(db, docs, "Resume CSV (snehaanbhawal)")


async def load_updated_resume_csv(db) -> int:
    """
    Dataset: updated-resume-dataset/UpdatedResumeDataSet.csv
    Columns: Category, Resume
    """
    path = DATASETS_DIR / "updated-resume-dataset" / "UpdatedResumeDataSet.csv"
    if not path.exists():
        print(f"   ⚠️  UpdatedResumeDataSet.csv not found")
        return 0

    df = _read_csv_safe(path)
    print(f"   📄 Updated Resume columns: {list(df.columns)}")

    text_col = next((c for c in df.columns if c.lower() in ["resume", "text", "resume_str"]), None)
    cat_col  = next((c for c in df.columns if "category" in c.lower()), None)

    if not text_col:
        print(f"   ⚠️  Cannot detect text column. Columns: {list(df.columns)}")
        return 0

    docs = []
    for _, row in df.iterrows():
        text = str(row[text_col]).strip()
        cat  = str(row[cat_col]).strip() if cat_col else "General"
        if len(text) > 200:
            docs.append(_make_doc(text, "resume", category=cat))

    return await _bulk_insert(db, docs, "Updated Resume CSV (jillanisofttech)")


async def load_resume_pdfs(db) -> int:
    """
    Dataset: resume-dataset/data/data/<CATEGORY>/*.pdf
    Thousands of actual resume PDFs organised by job category.
    """
    base = DATASETS_DIR / "resume-dataset" / "data" / "data"
    if not base.exists():
        print(f"   ⚠️  Resume PDF folder not found: {base}")
        return 0

    categories = [d for d in base.iterdir() if d.is_dir()]
    print(f"   📁 Found {len(categories)} resume categories")

    total = 0
    for cat_dir in sorted(categories):
        category = cat_dir.name
        pdfs     = list(cat_dir.glob("*.pdf"))
        docs     = []

        for pdf_path in pdfs:
            text = _extract_text_from_pdf(pdf_path)
            if len(text) > 200:
                docs.append(_make_doc(text, "resume", category=category))

        if docs:
            await db["training_pool"].insert_many(docs)
            total += len(docs)

        print(f"      {category}: {len(docs)}/{len(pdfs)} PDFs extracted")

    print(f"   ✅ Resume PDFs: {total:,} total docs inserted")
    return total


async def load_resume_ner_json(db) -> int:
    """
    Dataset: resume-entities-for-ner/Entity Recognition in Resumes.json
    Format: list of {content: str, annotation: [...]}
    """
    path = DATASETS_DIR / "resume-entities-for-ner" / "Entity Recognition in Resumes.json"
    if not path.exists():
        print(f"   ⚠️  NER JSON not found: {path}")
        return 0

    items = _load_json_safe(path)
    docs  = []
    for item in items:
        text = (item.get("content") or item.get("text") or "").strip()
        if len(text) > 200:
            docs.append(_make_doc(text, "resume"))

    return await _bulk_insert(db, docs, "Resume NER JSON (dataturks)")


async def load_jobs_csv(db) -> int:
    """
    Dataset: jobs-and-job-description/job_title_des.csv
    Actual filename differs from what old script expected.
    """
    # Try all possible filenames
    candidates = [
        DATASETS_DIR / "jobs-and-job-description" / "job_title_des.csv",
        DATASETS_DIR / "jobs-and-job-description" / "jobs.csv",
        DATASETS_DIR / "jobs-and-job-description" / "job_descriptions.csv",
        DATASETS_DIR / "jobs-and-job-description" / "data.csv",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if not path:
        print(f"   ⚠️  Jobs CSV not found in jobs-and-job-description/")
        return 0

    df = _read_csv_safe(path)
    print(f"   📄 Jobs CSV ({path.name}) columns: {list(df.columns)}")

    # Auto-detect title and description columns
    title_col = next((c for c in df.columns
                      if any(k in c.lower() for k in ["title", "job_title", "position"])), None)
    desc_col  = next((c for c in df.columns
                      if any(k in c.lower() for k in ["description", "desc", "summary", "detail"])), None)

    if not desc_col and not title_col:
        # Use all columns as text
        print(f"   ⚠️  Cannot detect title/desc columns — using all text")
        desc_col = df.columns[0]

    docs = []
    for _, row in df.iterrows():
        title = str(row[title_col]).strip() if title_col else ""
        desc  = str(row[desc_col]).strip()  if desc_col  else ""
        text  = f"{title}\n\n{desc}".strip() if title else desc
        if len(text) > 100:
            docs.append(_make_doc(text, "job_description", category=title))

    return await _bulk_insert(db, docs, f"Jobs CSV ({path.name})")


async def load_linkedin_jobs(db) -> int:
    """
    Dataset: linkedin-jobs-2024/
    Files: linkedin_job_postings.csv + job_summary.csv + job_skills.csv
    These share a job_link or job_id — join them for full text.
    """
    folder = DATASETS_DIR / "linkedin-jobs-2024"
    if not folder.exists():
        print(f"   ⚠️  LinkedIn folder not found: {folder}")
        return 0

    # ── Load main postings ────────────────────────────────────────
    postings_path = folder / "linkedin_job_postings.csv"
    summary_path  = folder / "job_summary.csv"
    skills_path   = folder / "job_skills.csv"

    if not postings_path.exists():
        print(f"   ⚠️  linkedin_job_postings.csv not found")
        return 0

    print(f"   📄 Loading linkedin_job_postings.csv ...")
    # Load in chunks to handle large file; limit to 50K rows for training
    chunks = []
    for chunk in pd.read_csv(postings_path, encoding="latin-1", on_bad_lines="skip",
                             chunksize=10_000):
        chunks.append(chunk)
        if sum(len(c) for c in chunks) >= 50_000:
            break
    postings = pd.concat(chunks, ignore_index=True)
    print(f"      Postings loaded: {len(postings):,} rows")
    print(f"      Columns: {list(postings.columns)}")

    # ── Load summary (contains description text) ──────────────────
    summary_df = pd.DataFrame()
    if summary_path.exists():
        print(f"   📄 Loading job_summary.csv ...")
        summary_df = _read_csv_safe(summary_path)
        print(f"      Summary columns: {list(summary_df.columns)}")

    # ── Load skills ───────────────────────────────────────────────
    skills_df = pd.DataFrame()
    if skills_path.exists():
        print(f"   📄 Loading job_skills.csv ...")
        skills_df = _read_csv_safe(skills_path)
        print(f"      Skills columns: {list(skills_df.columns)}")

    # ── Detect join key ───────────────────────────────────────────
    # Common join keys: job_link, job_id, id
    join_key = None
    for candidate in ["job_link", "job_id", "id", "jobId"]:
        if candidate in postings.columns:
            join_key = candidate
            break

    # ── Merge if possible ─────────────────────────────────────────
    merged = postings.copy()

    if join_key and not summary_df.empty and join_key in summary_df.columns:
        merged = merged.merge(summary_df, on=join_key, how="left", suffixes=("", "_sum"))
        print(f"      Merged with summary on '{join_key}'")

    if join_key and not skills_df.empty and join_key in skills_df.columns:
        # Skills may be multiple rows per job — aggregate
        skills_agg = (skills_df.groupby(join_key)
                      .apply(lambda g: ", ".join(g.iloc[:, 1].dropna().astype(str)))
                      .reset_index(name="skills_combined"))
        merged = merged.merge(skills_agg, on=join_key, how="left")
        print(f"      Merged with skills on '{join_key}'")

    # ── Detect text columns in merged result ─────────────────────
    title_col = next((c for c in merged.columns
                      if any(k in c.lower() for k in ["title", "job_title", "position"])), None)
    desc_col  = next((c for c in merged.columns
                      if any(k in c.lower() for k in
                             ["description", "summary", "body", "detail", "about"])), None)
    skills_col = "skills_combined" if "skills_combined" in merged.columns else \
                  next((c for c in merged.columns if "skill" in c.lower()), None)

    print(f"      Using → title: '{title_col}', desc: '{desc_col}', skills: '{skills_col}'")

    docs = []
    for _, row in merged.iterrows():
        title  = str(row[title_col]).strip()  if title_col  else ""
        desc   = str(row[desc_col]).strip()   if desc_col   else ""
        skills = str(row[skills_col]).strip() if skills_col else ""

        # Skip if all nan
        if all(v in ("", "nan") for v in [title, desc, skills]):
            continue

        parts = []
        if title  and title  != "nan": parts.append(title)
        if desc   and desc   != "nan": parts.append(desc)
        if skills and skills != "nan": parts.append(f"Skills: {skills}")
        text = "\n\n".join(parts)

        if len(text) > 100:
            docs.append(_make_doc(text, "job_description", category=title))

    return await _bulk_insert(db, docs, "LinkedIn Jobs (linkedin-jobs-2024)")


async def load_hr_interview_json(db) -> int:
    """
    Dataset: hr-interview-questions/hr_interview_questions_dataset.json
    """
    # Actual folder/file from the tree
    candidates = [
        DATASETS_DIR / "hr-interview-questions" / "hr_interview_questions_dataset.json",
        DATASETS_DIR / "hr-interview-questions-and-ideal-answers" / "hr_interview_questions_dataset.json",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if not path:
        print(f"   ⚠️  HR Interview JSON not found")
        return 0

    items = _load_json_safe(path)
    print(f"   📄 HR JSON loaded: {len(items)} items")
    if items:
        print(f"      Sample keys: {list(items[0].keys()) if isinstance(items[0], dict) else type(items[0])}")

    docs = []
    for item in items:
        if not isinstance(item, dict):
            continue
        # Try common key names
        q = (item.get("question") or item.get("Question") or item.get("q") or "").strip()
        a = (item.get("answer")   or item.get("Answer")   or item.get("a")
             or item.get("ideal_answer") or item.get("Ideal_Answer") or "").strip()
        text = f"Q: {q}\nA: {a}" if q else a
        if len(text) > 30:
            docs.append(_make_doc(text, "interview_qa"))

    return await _bulk_insert(db, docs, "HR Interview Q&A JSON")


async def load_interview_selection_csv(db) -> int:
    """
    Dataset: interview-selection-dataset/Data - Base.csv
    Actual filename has a space — old script never found it.
    """
    candidates = [
        DATASETS_DIR / "interview-selection-dataset" / "Data - Base.csv",
        DATASETS_DIR / "interview-selection-dataset" / "data.csv",
        DATASETS_DIR / "interview-selection-dataset" / "interview_selection.csv",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if not path:
        print(f"   ⚠️  Interview Selection CSV not found")
        return 0

    df = _read_csv_safe(path)
    print(f"   📄 Interview Selection ({path.name}) columns: {list(df.columns)}")

    text_col  = next((c for c in df.columns
                      if any(k in c.lower() for k in ["resume", "text", "cv", "content"])), None)
    label_col = next((c for c in df.columns
                      if any(k in c.lower() for k in ["selected", "label", "result", "hired", "status"])), None)

    if not text_col:
        # If no clear text col, concatenate all string columns
        str_cols = df.select_dtypes(include="object").columns.tolist()
        if str_cols:
            text_col = str_cols[0]
            print(f"      Auto-selecting first string column: '{text_col}'")

    docs = []
    for _, row in df.iterrows():
        text  = str(row[text_col]).strip() if text_col else ""
        label = row[label_col]             if label_col and label_col in row else None
        if len(text) > 50:
            doc = _make_doc(text, "resume")
            if label is not None and str(label) not in ("nan", ""):
                try:
                    doc["selection_label"] = int(float(str(label)))
                except ValueError:
                    doc["selection_label_str"] = str(label)
            docs.append(doc)

    return await _bulk_insert(db, docs, f"Interview Selection ({path.name})")


async def load_ats_train_json(db) -> int:
    """
    Dataset: ats-scoring-dataset/train/train_data.json
    """
    path = DATASETS_DIR / "ats-scoring-dataset" / "train" / "train_data.json"
    if not path.exists():
        print(f"   ⚠️  ATS train JSON not found: {path}")
        return 0

    items = _load_json_safe(path)
    print(f"   📄 ATS train JSON: {len(items)} items")
    if items:
        print(f"      Sample keys: {list(items[0].keys()) if isinstance(items[0], dict) else type(items[0])}")

    docs = []
    for item in items:
        if not isinstance(item, dict):
            continue
        # Try common key names for resume text
        text  = (item.get("resume_text") or item.get("text") or
                 item.get("Resume")      or item.get("content") or "").strip()
        score = item.get("ats_score") or item.get("score") or item.get("label")

        if len(text) > 100:
            doc = _make_doc(text, "resume")
            if score is not None:
                try:
                    doc["ats_score_label"] = float(score)
                except (ValueError, TypeError):
                    pass
            docs.append(doc)

    return await _bulk_insert(db, docs, "ATS Train JSON")


# ═══════════════════════════════════════════════════════════════
# Skills Lexicon Builder
# ═══════════════════════════════════════════════════════════════

TECH_SKILLS_BASE = [
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "php",
    "swift", "kotlin", "go", "rust", "scala", "r", "matlab", "perl",
    # Frontend
    "react", "angular", "vue", "html", "css", "sass", "webpack", "nextjs",
    "nuxtjs", "jquery", "bootstrap", "tailwind",
    # Backend
    "nodejs", "django", "flask", "fastapi", "spring", "laravel", "express",
    "rails", "asp.net", "dotnet",
    # Mobile
    "flutter", "android", "ios", "react native", "xamarin",
    # Databases
    "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle", "mssql",
    "dynamodb", "cassandra", "elasticsearch",
    # Cloud / DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
    "gitlab", "github", "ci/cd", "linux", "nginx", "ansible",
    # ML / Data
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
    "pandas", "numpy", "data science", "nlp", "computer vision", "keras",
    # Tools
    "git", "jira", "figma", "photoshop", "excel", "powerpoint", "postman",
    "selenium", "pytest", "jest", "agile", "scrum", "rest api", "graphql",
    "socket.io", "websocket", "microservices", "gojs", "three.js",
    # Soft skills (intentionally few — don't want noise)
    "leadership", "communication", "teamwork", "problem solving",
]

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "are",
    "you", "was", "not", "but", "they", "will", "been", "has", "had",
    "can", "all", "one", "more", "also", "about", "just", "into", "some",
    "their", "which", "when", "were", "what", "how", "any", "its", "our",
    "your", "who", "him", "her", "his", "she", "use", "used", "using",
    "work", "worked", "working", "able", "new", "well", "good", "strong",
    "other", "such", "each", "both", "over", "than", "then", "now",
    "only", "also", "very", "much", "many", "most", "same", "way",
    "may", "need", "make", "made", "take", "help", "provide", "ensure",
    "support", "manage", "build", "develop", "create", "design", "implement",
    "experience", "skills", "knowledge", "ability", "understand", "learn",
    "gain", "grow", "join", "start", "fast", "quick", "next", "base",
    "plus", "across", "where", "assist", "report", "move", "similar",
    "opportunity", "world", "hands", "industry", "manual", "business",
    "improving", "quickly", "contribute", "attention", "feature", "startup",
    "mentorship", "passion", "developer", "product", "familiarity",
    "perform", "application", "active", "pace", "eager", "improvement",
    "practice", "platform", "intern", "internship", "alongside", "client",
    "saas", "deployment", "release", "exposure", "collaborate",
    "reliability", "testing", "enhance", "case", "technical", "identify",
    "solve", "bug", "move",
}


async def build_skills_lexicon(db):
    """Build a clean skills_lexicon.json — no stopwords, no JD filler words."""
    print("\n🔧 Building skills lexicon ...")

    # Sample training docs for frequency analysis
    cursor = db["training_pool"].find(
        {"cleaned_text": {"$exists": True}, "data_type": {"$in": ["resume", "job_description"]}},
        {"cleaned_text": 1}
    ).limit(10_000)
    docs = await cursor.to_list(length=10_000)
    print(f"   Sampling {len(docs):,} docs for lexicon")

    # Count technical-looking tokens
    pattern = re.compile(r"\b([a-zA-Z][a-zA-Z0-9+#.\-]{2,20})\b")
    word_counts: Counter = Counter()

    for doc in docs:
        text  = doc.get("cleaned_text", "").lower()
        words = pattern.findall(text)
        word_counts.update(words)

    # Start from curated base
    skill_set = set(s.lower() for s in TECH_SKILLS_BASE)

    # Add high-frequency words that look like skills (not stopwords)
    for word, count in word_counts.most_common(3000):
        word_lower = word.lower()
        if (
            count >= 8
            and word_lower not in STOPWORDS
            and word_lower not in skill_set
            and len(word_lower) >= 3
            and not word_lower.isdigit()
            and not all(c in ".-_" for c in word_lower)
        ):
            skill_set.add(word_lower)

    lexicon_path = Path("data/skills_lexicon.json")
    lexicon_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lexicon_path, "w") as f:
        json.dump(sorted(skill_set), f, indent=2)

    print(f"   ✅ Skills lexicon: {len(skill_set):,} skills → {lexicon_path}")


# ═══════════════════════════════════════════════════════════════
# TF-IDF Retrainer
# ═══════════════════════════════════════════════════════════════

async def retrain_tfidf(db):
    """Train TF-IDF vectorizer on all training pool text."""
    print("\n🤖 Training TF-IDF vectorizer ...")

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        print("   ⚠️  scikit-learn not installed — skipping TF-IDF training")
        return

    cursor = db["training_pool"].find(
        {"cleaned_text": {"$exists": True, "$ne": ""}},
        {"cleaned_text": 1}
    ).limit(50_000)
    docs  = await cursor.to_list(length=50_000)
    texts = [d["cleaned_text"] for d in docs if d.get("cleaned_text")]
    print(f"   Training on {len(texts):,} documents ...")

    vectorizer = TfidfVectorizer(
        max_features=15_000,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=3,
        sublinear_tf=True,
    )
    vectorizer.fit(texts)

    # Quick self-similarity accuracy check
    sample = texts[:50]
    matrix = vectorizer.transform(sample)
    sim    = cosine_similarity(matrix)
    correct = sum(1 for i in range(len(sample)) if sim[i].argmax() == i)
    accuracy = round(correct / len(sample) * 100, 1)

    out_path = MODEL_DIR / "tfidf_vectorizer.pkl"
    with open(out_path, "wb") as f:
        pickle.dump(vectorizer, f)

    print(f"   ✅ TF-IDF trained: vocab={len(vectorizer.vocabulary_):,}, "
          f"accuracy={accuracy}%, saved → {out_path}")


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

async def main():
    client = AsyncIOMotorClient(MONGODB_URL)
    db     = client[DATABASE_NAME]

    print("\n🗑  Clearing existing public dataset entries ...")
    res = await db["training_pool"].delete_many({"source": "public_dataset"})
    print(f"   Cleared {res.deleted_count:,} docs")

    print("\n🌱 Seeding training pool ...\n")
    grand_total = 0

    # ── CSV / JSON datasets ───────────────────────────────────────
    print("── 1. Resume CSV (snehaanbhawal) ──────────────────────────")
    grand_total += await load_resume_csv(db)

    print("\n── 2. Updated Resume CSV (jillanisofttech) ────────────────")
    grand_total += await load_updated_resume_csv(db)

    print("\n── 3. Resume NER JSON (dataturks) ─────────────────────────")
    grand_total += await load_resume_ner_json(db)

    print("\n── 4. Jobs & JD CSV ────────────────────────────────────────")
    grand_total += await load_jobs_csv(db)

    print("\n── 5. LinkedIn Jobs (linkedin-jobs-2024) ───────────────────")
    grand_total += await load_linkedin_jobs(db)

    print("\n── 6. HR Interview Questions JSON ──────────────────────────")
    grand_total += await load_hr_interview_json(db)

    print("\n── 7. Interview Selection CSV ──────────────────────────────")
    grand_total += await load_interview_selection_csv(db)

    print("\n── 8. ATS Train JSON ───────────────────────────────────────")
    grand_total += await load_ats_train_json(db)

    # ── Resume PDFs (slow — runs last) ───────────────────────────
    print("\n── 9. Resume PDFs (resume-dataset/data/data/) ──────────────")
    print("   ⏳ This may take several minutes for thousands of PDFs ...")
    grand_total += await load_resume_pdfs(db)

    # ── Post-processing ───────────────────────────────────────────
    await build_skills_lexicon(db)
    await retrain_tfidf(db)

    # ── Final summary ─────────────────────────────────────────────
    total_in_db = await db["training_pool"].count_documents({})
    by_type = {}
    for dtype in ["resume", "job_description", "interview_qa"]:
        by_type[dtype] = await db["training_pool"].count_documents({"data_type": dtype})

    print(f"""
{'='*55}
✅ SEEDING COMPLETE
{'='*55}
   Inserted this run : {grand_total:,}
   Total in pool     : {total_in_db:,}

   By type:
     resumes          : {by_type.get('resume', 0):,}
     job descriptions : {by_type.get('job_description', 0):,}
     interview Q&A    : {by_type.get('interview_qa', 0):,}
{'='*55}
""")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())