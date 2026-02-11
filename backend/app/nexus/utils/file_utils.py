"""File utilities for Nexus resume uploads."""

from pathlib import Path
import uuid
import aiofiles
from fastapi import UploadFile
from app.config import settings


def allowed_file_type(filename: str, allowed_extensions=None) -> bool:
    if allowed_extensions is None:
        allowed_extensions = settings.allowed_file_extensions
    extension = Path(filename).suffix.lower()
    return extension in {ext.lower() for ext in allowed_extensions}


async def save_resume_file(file: UploadFile) -> tuple[str, str]:
    if not allowed_file_type(file.filename):
        raise ValueError(f"File type not allowed: {file.filename}")

    resumes_dir = Path(settings.data_dir) / "resumes"
    resumes_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename).suffix
    unique_name = f"{uuid.uuid4().hex}{suffix}"
    target_path = resumes_dir / unique_name

    async with aiofiles.open(target_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    return file.filename, str(target_path)


def get_abs_path(file_path: str) -> str:
    if not file_path:
        raise ValueError("File path cannot be empty")

    abs_path = Path(file_path)
    if not abs_path.exists():
        raise FileNotFoundError(f"File does not exist: {abs_path}")

    return str(abs_path)
