import os
import uuid
import shutil
import mimetypes
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.config import get_settings

settings = get_settings()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "image/jpeg",
    "image/png",
    "image/jpg",
    "text/plain",
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".txt"}


def validate_file(file: UploadFile) -> None:
    """Raise HTTPException if file is invalid."""

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Use: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content_type = file.content_type or ""
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        # Some browsers send wrong MIME — warn but don't block if extension is OK
        pass


async def save_upload(file: UploadFile, subfolder: str = "resumes") -> dict:
    """
    Save uploaded file to disk.
    Returns dict with: file_path, file_url, original_filename, file_size, mime_type
    """
    validate_file(file)

    ext = Path(file.filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_dir = Path(settings.upload_dir) / subfolder
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / unique_name

    # Read and check file size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Maximum is {settings.max_file_size_mb}MB",
        )

    with open(file_path, "wb") as f:
        f.write(contents)

    mime_type = file.content_type or _guess_mime(ext)

    return {
        "file_path": str(file_path),
        "file_url": f"/uploads/{subfolder}/{unique_name}",
        "original_filename": file.filename,
        "file_size_mb": round(size_mb, 3),
        "mime_type": mime_type,
        "extension": ext,
    }


def delete_file(file_path: str) -> bool:
    """Delete a file from disk. Returns True if deleted."""
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception:
        return False


def _guess_mime(ext: str) -> str:
    mapping = {
        ".pdf":  "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc":  "application/msword",
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".txt":  "text/plain",
    }
    return mapping.get(ext, "application/octet-stream")