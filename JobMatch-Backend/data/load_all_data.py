import asyncio
import pandas as pd
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import PyPDF2
from tqdm import tqdm
import json

DATASETS_DIR = Path("data/datasets")

async def load_all_data():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["jobmatch_ai"]
    
    # Clear existing
    await db["training_pool"].delete_many({})
    print("Cleared training_pool")
    
    total = 0
    
    # ============================================================
    # 1. LOAD 1M+ LINKEDIN JOB POSTINGS
    # ============================================================
    linkedin_path = DATASETS_DIR / "linkedin-jobs-2024" / "linkedin_job_postings.csv"
    if linkedin_path.exists():
        print(f"\n📊 Loading LinkedIn jobs (this will take a minute)...")
        
        # Read in chunks to handle 1M+ rows
        chunk_size = 50000
        jd_count = 0
        
        for chunk in tqdm(pd.read_csv(linkedin_path, chunksize=chunk_size), desc="LinkedIn Jobs"):
            # Clean and prepare
            chunk = chunk.fillna('')
            docs = []
            
            for _, row in chunk.iterrows():
                title = str(row.get('title', ''))[:200]
                description = str(row.get('description', ''))
                
                if len(description) > 200:  # Only substantial descriptions
                    docs.append({
                        "source": "public_dataset",
                        "data_type": "job_description",
                        "category": title,
                        "cleaned_text": f"{title}\n\n{description}"[:10000],
                        "quality_score": 85,
                        "added_to_training_at": datetime.utcnow(),
                    })
                    
                    jd_count += 1
                    
                    # Insert in batches
                    if len(docs) >= 1000:
                        await db["training_pool"].insert_many(docs)
                        total += len(docs)
                        docs = []
            
            # Insert remaining
            if docs:
                await db["training_pool"].insert_many(docs)
                total += len(docs)
            
            print(f"   Loaded {jd_count} job descriptions so far...")
        
        print(f"✅ Loaded {jd_count} job descriptions")
    
    # ============================================================
    # 2. LOAD UPDATED RESUME DATASET (has 25+ categories)
    # ============================================================
    resume_path = DATASETS_DIR / "updated-resume-dataset" / "UpdatedResumeDataSet.csv"
    if resume_path.exists():
        print(f"\n📄 Loading Updated Resume Dataset...")
        df = pd.read_csv(resume_path)
        
        docs = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Resumes"):
            text = str(row.get('Resume', ''))
            category = str(row.get('Category', 'Unknown'))
            
            if len(text) > 500:
                docs.append({
                    "source": "public_dataset",
                    "data_type": "resume",
                    "category": category,
                    "cleaned_text": text[:10000],
                    "quality_score": 90,
                    "added_to_training_at": datetime.utcnow(),
                })
        
        if docs:
            await db["training_pool"].insert_many(docs)
            total += len(docs)
            print(f"✅ Loaded {len(docs)} resumes from UpdatedResumeDataSet")
    
    # ============================================================
    # 3. LOAD KAGGLE RESUME DATASET (thousands of PDFs)
    # ============================================================
    pdf_folder = DATASETS_DIR / "resume-dataset" / "data" / "data"
    if pdf_folder.exists():
        print(f"\n📑 Reading PDF resumes (this will take time)...")
        
        pdf_count = 0
        docs = []
        
        # Walk through all category folders
        for category_folder in tqdm(list(pdf_folder.iterdir()), desc="Categories"):
            if category_folder.is_dir():
                category = category_folder.name
                
                for pdf_file in list(category_folder.glob("*.pdf"))[:1000]:  # Limit to 1000 per category
                    try:
                        # Extract text from PDF
                        with open(pdf_file, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            text = ''
                            for page in reader.pages[:3]:  # First 3 pages
                                text += page.extract_text() or ''
                        
                        if len(text) > 300:
                            docs.append({
                                "source": "public_dataset",
                                "data_type": "resume",
                                "category": category,
                                "cleaned_text": text[:10000],
                                "quality_score": 88,
                                "added_to_training_at": datetime.utcnow(),
                            })
                            pdf_count += 1
                            
                            # Batch insert
                            if len(docs) >= 500:
                                await db["training_pool"].insert_many(docs)
                                total += len(docs)
                                docs = []
                    
                    except Exception as e:
                        continue
        
        # Insert remaining
        if docs:
            await db["training_pool"].insert_many(docs)
            total += len(docs)
        
        print(f"✅ Loaded {pdf_count} resumes from PDFs")
    
    # ============================================================
    # 4. LOAD JOBS AND JOB DESCRIPTIONS DATASET
    # ============================================================
    jobs_path = DATASETS_DIR / "jobs-and-job-description" / "job_title_des.csv"
    if jobs_path.exists():
        print(f"\n💼 Loading job descriptions...")
        df = pd.read_csv(jobs_path)
        
        docs = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Job Descriptions"):
            title = str(row.get('job_title', ''))
            desc = str(row.get('job_description', ''))
            
            if len(desc) > 200:
                docs.append({
                    "source": "public_dataset",
                    "data_type": "job_description",
                    "category": title[:100],
                    "cleaned_text": f"{title}\n\n{desc}"[:10000],
                    "quality_score": 82,
                    "added_to_training_at": datetime.utcnow(),
                })
        
        if docs:
            await db["training_pool"].insert_many(docs)
            total += len(docs)
            print(f"✅ Loaded {len(docs)} job descriptions")
    
    # ============================================================
    # 5. LOAD INTERVIEW SELECTION DATASET
    # ============================================================
    interview_path = DATASETS_DIR / "interview-selection-dataset" / "Data - Base.csv"
    if interview_path.exists():
        print(f"\n🎯 Loading interview selection data...")
        df = pd.read_csv(interview_path)
        
        docs = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Interview Data"):
            # Extract relevant columns
            text_parts = []
            for col in df.columns:
                if 'resume' in col.lower() or 'text' in col.lower() or 'description' in col.lower():
                    text_parts.append(str(row.get(col, '')))
            
            text = ' '.join(text_parts)
            if len(text) > 200:
                docs.append({
                    "source": "public_dataset",
                    "data_type": "resume",
                    "category": "interview_data",
                    "cleaned_text": text[:10000],
                    "quality_score": 75,
                    "added_to_training_at": datetime.utcnow(),
                })
        
        if docs:
            await db["training_pool"].insert_many(docs)
            total += len(docs)
            print(f"✅ Loaded {len(docs)} interview records")
    
    # ============================================================
    # FINAL STATS
    # ============================================================
    final_count = await db["training_pool"].count_documents({})
    
    # Show breakdown by data_type
    pipeline = [
        {"$group": {"_id": "$data_type", "count": {"$sum": 1}}}
    ]
    breakdown = await db["training_pool"].aggregate(pipeline).to_list(None)
    
    print(f"\n{'='*60}")
    print(f"✅ LOADING COMPLETE!")
    print(f"{'='*60}")
    print(f"Total documents in training_pool: {final_count:,}")
    print(f"\nBreakdown by type:")
    for item in breakdown:
        print(f"   {item['_id']}: {item['count']:,}")
    print(f"{'='*60}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(load_all_data())