"""
File upload and text extraction utilities.
"""
import os
import uuid
from pathlib import Path
from typing import Tuple

from fastapi import UploadFile
import aiofiles

from app.core.config import settings
from app.services.archive_service import ArchiveService


# Directory to store uploaded files
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def save_upload_file(upload_file: UploadFile) -> Tuple[str, int, str, str]:
    """
    Save an uploaded file to disk and optionally to archive.

    Args:
        upload_file: FastAPI UploadFile object

    Returns:
        Tuple of (file_path, file_size, archive_path, storage_location)
        - file_path: Path to local working copy
        - file_size: Size of file in bytes
        - archive_path: Path to archived original (None if not archived)
        - storage_location: "local" or "archive"
    """
    # Generate unique filename
    file_extension = Path(upload_file.filename or "file.txt").suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    # Save file locally first (needed for processing)
    file_size = 0
    async with aiofiles.open(file_path, "wb") as f:
        while chunk := await upload_file.read(8192):  # Read in 8KB chunks
            await f.write(chunk)
            file_size += len(chunk)

    # Archive original if enabled
    archive_path = None
    storage_location = "local"

    if settings.archive_enabled:
        try:
            file_type = file_extension.lstrip(".")
            archive_path, storage_location = await ArchiveService.save_to_archive(
                source_path=str(file_path),
                filename=upload_file.filename or "unknown",
                file_type=file_type,
            )
        except Exception:
            # If archiving fails, continue with local storage
            # Error is already logged by ArchiveService
            pass

    return str(file_path), file_size, archive_path, storage_location


async def extract_text_from_file(file_path: str, file_type: str) -> str:
    """
    Extract text content from a file.

    Args:
        file_path: Path to the file
        file_type: File extension/type

    Returns:
        Extracted text content
    """
    file_type = file_type.lower().lstrip(".")

    try:
        if file_type in ["txt", "md", "markdown"]:
            return await _extract_text_plain(file_path)
        elif file_type == "pdf":
            return await _extract_text_pdf(file_path)
        elif file_type in ["doc", "docx"]:
            return await _extract_text_docx(file_path)
        else:
            # Try to read as plain text
            return await _extract_text_plain(file_path)
    except Exception as e:
        return f"Error extracting text: {str(e)}"


async def _extract_text_plain(file_path: str) -> str:
    """Extract text from plain text files."""
    async with aiofiles.open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return await f.read()


async def _extract_text_pdf(file_path: str) -> str:
    """Extract text from PDF files."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)
    except ImportError:
        return "PDF extraction not available (pypdf not installed)"
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


async def _extract_text_docx(file_path: str) -> str:
    """Extract text from DOCX files."""
    try:
        from docx import Document

        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n\n".join(paragraphs)
    except ImportError:
        return "DOCX extraction not available (python-docx not installed)"
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"


async def delete_file(file_path: str) -> bool:
    """
    Delete a file from disk.

    Args:
        file_path: Path to the file

    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False
    except Exception:
        return False
