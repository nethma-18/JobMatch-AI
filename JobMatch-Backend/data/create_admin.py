"""
Creates the first admin user using direct bcrypt.
Usage:
    python data/create_admin_simple.py
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime
import bcrypt

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "jobmatch_ai")

async def create_admin():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    print("\n=== Create Admin User ===\n")
    name = input("Admin name: ").strip()
    email = input("Admin email: ").strip()
    password = input("Admin password: ").strip()
    
    if not name or not email or not password:
        print("❌ All fields are required!")
        client.close()
        return
    
    # Check if user exists
    existing = await db["users"].find_one({"email": email})
    if existing:
        print(f"⚠️  User {email} already exists")
        # Option to update password
        update = input("Update password? (y/n): ").strip().lower()
        if update == 'y':
            # Hash new password
            salt = bcrypt.gensalt(rounds=12)
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
            await db["users"].update_one(
                {"email": email},
                {"$set": {"password_hash": password_hash}}
            )
            print(f"✅ Password updated for {email}")
        client.close()
        return
    
    # Hash the password using bcrypt directly
    print("🔒 Hashing password...")
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    # Create admin user
    admin_user = {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "role": "admin",
        "company_name": None,
        "created_at": datetime.utcnow(),
        "last_login": datetime.utcnow(),
        "is_active": True,
    }
    
    result = await db["users"].insert_one(admin_user)
    
    # Verify the password works
    print("🔍 Verifying...")
    test_user = await db["users"].find_one({"_id": result.inserted_id})
    is_valid = bcrypt.checkpw(password.encode('utf-8'), test_user["password_hash"].encode('utf-8'))
    
    if is_valid:
        print(f"\n✅ Admin created successfully!")
        print(f"   ID: {result.inserted_id}")
        print(f"   Name: {name}")
        print(f"   Email: {email}")
        print(f"   Role: admin")
    else:
        print("❌ Password verification failed!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_admin())