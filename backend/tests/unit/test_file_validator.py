"""
Tests for file validation utilities.
"""

import io
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile

from app.utils.file_validator import (
    get_file_extension,
    validate_file_content_magic,
    validate_file_extension,
    validate_file_mime_type,
    validate_uploaded_file,
)


def test_get_file_extension():
    """Test safe file extension extraction."""
    # Normal cases
    assert get_file_extension("document.pdf") == "pdf"
    assert get_file_extension("note.txt") == "txt"
    assert get_file_extension("README.md") == "md"

    # Edge cases
    assert get_file_extension("file.tar.gz") == "gz"  # Gets last extension
    assert get_file_extension("malicious.pdf.exe") == "exe"  # Catches disguised files
    assert get_file_extension("noextension") == ""
    assert get_file_extension(".hidden") == ""  # Hidden files have no extension
    assert get_file_extension("") == ""

    # Case insensitivity
    assert get_file_extension("FILE.PDF") == "pdf"
    assert get_file_extension("Document.TXT") == "txt"


def test_validate_file_extension():
    """Test file extension validation."""
    allowed = {"pdf", "txt", "md", "docx"}

    # Valid extensions
    is_valid, error = validate_file_extension("document.pdf", allowed)
    assert is_valid is True
    assert error is None

    is_valid, error = validate_file_extension("note.txt", allowed)
    assert is_valid is True
    assert error is None

    # Invalid extensions
    is_valid, error = validate_file_extension("script.exe", allowed)
    assert is_valid is False
    assert "not supported" in error

    is_valid, error = validate_file_extension("malicious.pdf.exe", allowed)
    assert is_valid is False
    assert ".exe" in error

    # No extension
    is_valid, error = validate_file_extension("noextension", allowed)
    assert is_valid is False
    assert "must have an extension" in error


@pytest.mark.asyncio
async def test_validate_file_mime_type():
    """Test MIME type validation."""
    # Valid PDF
    file = MagicMock(spec=UploadFile)
    file.filename = "document.pdf"
    file.content_type = "application/pdf"

    is_valid, error = await validate_file_mime_type(file, "pdf")
    assert is_valid is True
    assert error is None

    # Invalid MIME type for PDF
    file.content_type = "application/x-executable"
    is_valid, error = await validate_file_mime_type(file, "pdf")
    assert is_valid is False
    assert "does not match" in error

    # Valid text file
    file.filename = "note.txt"
    file.content_type = "text/plain"
    is_valid, error = await validate_file_mime_type(file, "txt")
    assert is_valid is True

    # No content type
    file.content_type = None
    is_valid, error = await validate_file_mime_type(file, "txt")
    # Should try to guess from filename
    assert is_valid is True or "Could not determine" in error


@pytest.mark.asyncio
async def test_validate_file_content_magic_pdf():
    """Test magic bytes validation for PDF files."""
    # Valid PDF magic bytes
    pdf_content = b"%PDF-1.4\n..."
    file = MagicMock(spec=UploadFile)
    file.seek = AsyncMock()
    file.read = AsyncMock(side_effect=[pdf_content[:8], pdf_content])

    is_valid, error = await validate_file_content_magic(file, "pdf")
    assert is_valid is True
    assert error is None

    # Invalid PDF (missing magic bytes)
    file.read = AsyncMock(side_effect=[b"not a pdf", b"not a pdf"])
    is_valid, error = await validate_file_content_magic(file, "pdf")
    assert is_valid is False
    assert "PDF signature" in error


@pytest.mark.asyncio
async def test_validate_file_content_magic_docx():
    """Test magic bytes validation for DOCX files."""
    # Valid DOCX (ZIP signature)
    docx_content = b"PK\x03\x04..."
    file = MagicMock(spec=UploadFile)
    file.seek = AsyncMock()
    file.read = AsyncMock(side_effect=[docx_content[:8], docx_content])

    is_valid, error = await validate_file_content_magic(file, "docx")
    assert is_valid is True
    assert error is None

    # Invalid DOCX
    file.read = AsyncMock(side_effect=[b"not docx", b"not docx"])
    is_valid, error = await validate_file_content_magic(file, "docx")
    assert is_valid is False
    assert "ZIP signature" in error


@pytest.mark.asyncio
async def test_validate_file_content_magic_text():
    """Test magic bytes validation for text files."""
    # Valid UTF-8 text
    text_content = b"This is a text file with valid UTF-8 content."
    file = MagicMock(spec=UploadFile)
    file.seek = AsyncMock()
    file.read = AsyncMock(side_effect=[text_content[:8], text_content])

    is_valid, error = await validate_file_content_magic(file, "txt")
    assert is_valid is True
    assert error is None

    # Invalid UTF-8 (binary data)
    binary_content = b"\xff\xfe\x00\x00\x00\x00\x00\x00"
    file.read = AsyncMock(side_effect=[binary_content, binary_content])
    is_valid, error = await validate_file_content_magic(file, "txt")
    assert is_valid is False
    assert "not UTF-8" in error


@pytest.mark.asyncio
async def test_validate_uploaded_file_comprehensive():
    """Test comprehensive file validation."""
    # Valid PDF file
    pdf_content = b"%PDF-1.4\n" + b"x" * 100
    file = MagicMock(spec=UploadFile)
    file.filename = "document.pdf"
    file.content_type = "application/pdf"
    file.seek = AsyncMock()
    file.read = AsyncMock(side_effect=[pdf_content[:8], pdf_content])

    is_valid, error, extension = await validate_uploaded_file(file)
    assert is_valid is True
    assert error is None
    assert extension == "pdf"

    # Disguised executable (malicious.pdf.exe)
    file.filename = "malicious.pdf.exe"
    file.content_type = "application/pdf"

    is_valid, error, extension = await validate_uploaded_file(file)
    assert is_valid is False
    assert "not supported" in error or ".exe" in error
    assert extension == ""


@pytest.mark.asyncio
async def test_validate_uploaded_file_skip_checks():
    """Test validation with optional checks disabled."""
    file = MagicMock(spec=UploadFile)
    file.filename = "document.pdf"
    file.content_type = "application/pdf"
    file.seek = AsyncMock()
    file.read = AsyncMock(return_value=b"invalid pdf content")

    # With mime and magic disabled, only extension is checked
    is_valid, error, extension = await validate_uploaded_file(
        file,
        validate_mime=False,
        validate_magic=False,
    )
    assert is_valid is True  # Only extension matters
    assert extension == "pdf"
