from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from bson import ObjectId

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.user import (
    RegisterRequest, LoginRequest, TokenResponse,
    UserResponse, MessageResponse, UpdateProfileRequest,
    ChangePasswordRequest
)
from app.utils.helpers import serialize_doc, now

router = APIRouter()


# ── Register ────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest, db=Depends(get_db)):

    # Check duplicate email
    existing = await db["users"].find_one({"email": payload.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # HR must provide company name
    if payload.role == "hr" and not payload.company_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HR accounts require a company name",
        )

    user_doc = {
        "name": payload.name,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "role": payload.role,
        "company_name": payload.company_name,
        "created_at": now(),
        "last_login": now(),
        "is_active": True,
    }

    result = await db["users"].insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    # Create role-specific profile
    if payload.role == "seeker":
        await db["seeker_profiles"].insert_one({
            "user_id": result.inserted_id,
            "saved_resumes": [],
            "saved_jobs": [],
            "notification_preferences": {"email": True, "in_app": True},
            "created_at": now(),
        })
    elif payload.role == "hr":
        await db["hr_profiles"].insert_one({
            "user_id": result.inserted_id,
            "company_name": payload.company_name,
            "team_members": [],
            "subscription_tier": "free",
            "created_at": now(),
        })

    token = create_access_token({"sub": str(result.inserted_id), "role": payload.role})
    serialized = serialize_doc(user_doc)

    return TokenResponse(
        access_token=token,
        user=UserResponse(**serialized),
    )


# ── Login ───────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db=Depends(get_db)):

    user = await db["users"].find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Update last login
    await db["users"].update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": now()}}
    )

    token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    serialized = serialize_doc(user)

    return TokenResponse(
        access_token=token,
        user=UserResponse(**serialized),
    )


# ── Get current user ────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return UserResponse(**serialize_doc(current_user))


# ── Update profile ──────────────────────────────────────────────

@router.put("/me", response_model=UserResponse)
async def update_profile(
    payload: UpdateProfileRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    await db["users"].update_one(
        {"_id": current_user["_id"]},
        {"$set": updates}
    )

    updated = await db["users"].find_one({"_id": current_user["_id"]})
    return UserResponse(**serialize_doc(updated))


# ── Change password ─────────────────────────────────────────────

@router.put("/change-password", response_model=MessageResponse)
async def change_password(
    payload: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    if not verify_password(payload.current_password, current_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    await db["users"].update_one(
        {"_id": current_user["_id"]},
        {"$set": {"password_hash": hash_password(payload.new_password)}}
    )
    return MessageResponse(message="Password changed successfully")


# ── Logout (client-side) ────────────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
async def logout(current_user=Depends(get_current_user)):
    # JWT is stateless — client deletes the token
    # For full blacklisting, store token jti in Redis (future enhancement)
    return MessageResponse(message="Logged out successfully")


# ── Admin: list all users ───────────────────────────────────────

@router.get("/users")
async def list_users(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    cursor = db["users"].find({}, {"password_hash": 0}).skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    return [serialize_doc(u) for u in users]


# ── Admin: deactivate user ──────────────────────────────────────

@router.put("/users/{user_id}/deactivate", response_model=MessageResponse)
async def deactivate_user(
    user_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": False}}
    )
    return MessageResponse(message="User deactivated")