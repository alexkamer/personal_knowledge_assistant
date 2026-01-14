"""
File validation utilities for secure file uploads.

Validates file types using both extension and MIME type detection.
"""

import io
import mimetypes
from pathlib import Path
from typing import Optional, Tuple

from fastapi import UploadFile


# Mapping of allowed extensions to their valid MIME types
ALLOWED_FILE_TYPES = {
    "txt": ["text/plain", "application/octet-stream"],
    "md": ["text/plain", "text/markdown", "application/octet-stream"],
    "pdf": ["application/pdf"],
    "docx": [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    ],
}


def get_file_extension(filename: str) -> str:
    """
    Safely extract file extension from filename.

    Handles edge cases:
    - Files with no extension -> ""
    - Files with multiple dots (e.g., "file.tar.gz") -> "gz"
    - Malicious names (e.g., "malicious.pdf.exe") -> "exe"

    Args:
        filename: The filename to extract extension from

    Returns:
        Lowercase file extension without the dot, or empty string if none
    """
    if not filename or "." not in filename:
        return ""

    # Use Path to safely handle extension
    extension = Path(filename).suffix.lower()
    # Remove leading dot
    return extension[1:] if extension else ""


def validate_file_extension(filename: str, allowed_extensions: set[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate file extension against allowed types.

    Args:
        filename: Name of the file to validate
        allowed_extensions: Set of allowed extensions (without dots)

    Returns:
        Tuple of (is_valid, error_message)
    """
    extension = get_file_extension(filename)

    if not extension:
        return False, "File must have an extension"

    if extension not in allowed_extensions:
        return False, f"File type '.{extension}' not supported. Allowed: {', '.join(sorted(allowed_extensions))}"

    return True, None


async def validate_file_mime_type(file: UploadFile, expected_extension: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file MIME type matches expected type for the extension.

    Uses content-type header and validates against known MIME types for the extension.

    Args:
        file: The uploaded file
        expected_extension: Expected file extension (without dot)

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Get content type from upload
    content_type = file.content_type

    if not content_type:
        # Try to guess from filename as fallback
        guessed_type, _ = mimetypes.guess_type(file.filename or "")
        content_type = guessed_type

    if not content_type:
        return False, "Could not determine file MIME type"

    # Get allowed MIME types for this extension
    allowed_mimes = ALLOWED_FILE_TYPES.get(expected_extension, [])

    if not allowed_mimes:
        return False, f"Unknown file type: {expected_extension}"

    # Check if content type matches any allowed MIME type
    if content_type not in allowed_mimes:
        return False, f"File MIME type '{content_type}' does not match expected types for '.{expected_extension}' files"

    return True, None


async def validate_file_content_magic(file: UploadFile, expected_extension: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file content using magic bytes (file signature).

    Reads first few bytes to verify file type matches extension.

    Args:
        file: The uploaded file
        expected_extension: Expected file extension (without dot)

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Read first 8 bytes for magic number detection
    await file.seek(0)
    magic_bytes = await file.read(8)
    await file.seek(0)  # Reset for later use

    if not magic_bytes:
        return False, "File is empty"

    # Check magic bytes for common types
    if expected_extension == "pdf":
        if not magic_bytes.startswith(b"%PDF"):
            return False, "File does not appear to be a valid PDF (missing PDF signature)"

    elif expected_extension == "docx":
        # DOCX files are ZIP archives
        if not magic_bytes.startswith(b"PK\x03\x04"):
            return False, "File does not appear to be a valid DOCX (missing ZIP signature)"

    # TXT and MD files have no magic bytes, just validate they contain text
    elif expected_extension in ["txt", "md"]:
        # Try to decode as UTF-8 to verify it's text
        try:
            await file.seek(0)
            sample = await file.read(1024)
            await file.seek(0)
            sample.decode("utf-8")
        except UnicodeDecodeError:
            return False, f"File does not appear to be valid text (not UTF-8 decodable)"

    return True, None


async def validate_uploaded_file(
    file: UploadFile,
    allowed_extensions: Optional[set[str]] = None,
    validate_mime: bool = True,
    validate_magic: bool = True,
) -> Tuple[bool, Optional[str], str]:
    """
    Comprehensive file validation for uploads.

    Validates:
    1. File has a valid extension
    2. Extension is in allowed list
    3. MIME type matches extension (optional)
    4. Magic bytes match file type (optional)

    Args:
        file: The uploaded file
        allowed_extensions: Set of allowed extensions, defaults to ALLOWED_FILE_TYPES keys
        validate_mime: Whether to validate MIME type
        validate_magic: Whether to validate magic bytes

    Returns:
        Tuple of (is_valid, error_message, detected_extension)
    """
    if not file.filename:
        return False, "File must have a filename", ""

    if allowed_extensions is None:
        allowed_extensions = set(ALLOWED_FILE_TYPES.keys())

    # Step 1: Validate extension
    is_valid, error = validate_file_extension(file.filename, allowed_extensions)
    if not is_valid:
        return False, error, ""

    extension = get_file_extension(file.filename)

    # Step 2: Validate MIME type
    if validate_mime:
        is_valid, error = await validate_file_mime_type(file, extension)
        if not is_valid:
            return False, error, extension

    # Step 3: Validate magic bytes
    if validate_magic:
        is_valid, error = await validate_file_content_magic(file, extension)
        if not is_valid:
            return False, error, extension

    return True, None, extension
