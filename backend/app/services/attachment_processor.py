"""
Service for processing file attachments in chat messages.

This service extracts text from uploaded files without permanently storing them
in the document library. Files are processed temporarily for RAG context injection.
"""
import logging
import tempfile
from pathlib import Path
from typing import Dict, List

from fastapi import UploadFile

from app.schemas.conversation import AttachmentMetadata
from app.utils.file_handler import extract_text_from_file

logger = logging.getLogger(__name__)

# Maximum total characters from all attachments to avoid context overflow
MAX_TOTAL_ATTACHMENT_LENGTH = 50_000

# File size limit (25 MB)
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024

# Allowed file types for attachments
ALLOWED_ATTACHMENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
    "text/plain",
    "text/markdown",
}


class AttachmentProcessor:
    """Processes file attachments for chat messages."""

    @staticmethod
    async def process_attachments(
        files: List[UploadFile],
    ) -> tuple[List[AttachmentMetadata], List[Dict[str, str]]]:
        """
        Process uploaded files and extract text content.

        Args:
            files: List of uploaded files

        Returns:
            Tuple of (attachment_metadata, attachment_contexts)
            - attachment_metadata: List of AttachmentMetadata for storing in message
            - attachment_contexts: List of dicts with "source" and "content" for RAG

        Raises:
            ValueError: If files exceed limits or have invalid types
        """
        if not files:
            return [], []

        if len(files) > 5:
            raise ValueError("Maximum 5 files allowed per message")

        attachment_metadata = []
        attachment_contexts = []
        total_extracted_length = 0

        for file in files:
            if not file.filename:
                logger.warning("Skipping file without filename")
                continue

            # Validate file type
            content_type = file.content_type or "application/octet-stream"
            if content_type not in ALLOWED_ATTACHMENT_TYPES:
                # Try to infer from extension
                file_ext = Path(file.filename).suffix.lower()
                if file_ext == ".pdf":
                    content_type = "application/pdf"
                elif file_ext == ".docx":
                    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif file_ext in [".txt", ".md", ".markdown"]:
                    content_type = "text/plain"
                else:
                    raise ValueError(
                        f"Unsupported file type: {content_type}. "
                        f"Allowed types: PDF, DOCX, TXT, MD"
                    )

            # Check file size
            file_content = await file.read()
            file_size = len(file_content)
            await file.seek(0)  # Reset for processing

            if file_size > MAX_FILE_SIZE_BYTES:
                size_mb = file_size / (1024 * 1024)
                raise ValueError(
                    f"File {file.filename} ({size_mb:.1f}MB) exceeds 25MB limit"
                )

            # Extract text from file
            try:
                extracted_text = await AttachmentProcessor._extract_text_from_upload(
                    file, file_content
                )

                # Check if we're exceeding total context limit
                extracted_length = len(extracted_text)
                if total_extracted_length + extracted_length > MAX_TOTAL_ATTACHMENT_LENGTH:
                    # Truncate this file's content
                    remaining_space = MAX_TOTAL_ATTACHMENT_LENGTH - total_extracted_length
                    if remaining_space > 0:
                        extracted_text = extracted_text[:remaining_space]
                        extracted_length = remaining_space
                        logger.warning(
                            f"Truncated {file.filename} to fit within total attachment limit"
                        )
                    else:
                        logger.warning(
                            f"Skipping {file.filename} - total attachment limit reached"
                        )
                        continue

                total_extracted_length += extracted_length

                # Create metadata
                metadata = AttachmentMetadata(
                    filename=file.filename,
                    file_type=content_type,
                    size_bytes=file_size,
                    extracted_length=extracted_length,
                    processing_status="processed",
                )
                attachment_metadata.append(metadata)

                # Create context for RAG
                context = {
                    "source": f"Attachment: {file.filename}",
                    "content": extracted_text,
                }
                attachment_contexts.append(context)

                logger.info(
                    f"Processed attachment {file.filename}: "
                    f"{file_size} bytes -> {extracted_length} chars"
                )

            except Exception as e:
                logger.error(f"Failed to process attachment {file.filename}: {e}")
                # Create error metadata
                metadata = AttachmentMetadata(
                    filename=file.filename,
                    file_type=content_type,
                    size_bytes=file_size,
                    extracted_length=0,
                    processing_status="error",
                    error_message=str(e),
                )
                attachment_metadata.append(metadata)

        return attachment_metadata, attachment_contexts

    @staticmethod
    async def _extract_text_from_upload(
        file: UploadFile, file_content: bytes
    ) -> str:
        """
        Extract text from an UploadFile by saving to temp file.

        Args:
            file: FastAPI UploadFile
            file_content: File bytes (already read)

        Returns:
            Extracted text content
        """
        # Create temporary file
        file_extension = Path(file.filename or "file.txt").suffix
        with tempfile.NamedTemporaryFile(
            suffix=file_extension, delete=False
        ) as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name

        try:
            # Extract text using existing utility
            file_type = file_extension.lstrip(".")
            extracted_text = await extract_text_from_file(temp_path, file_type)
            return extracted_text
        finally:
            # Clean up temp file
            try:
                Path(temp_path).unlink()
            except Exception:
                pass


# Singleton instance
_attachment_processor = AttachmentProcessor()


def get_attachment_processor() -> AttachmentProcessor:
    """Get the singleton AttachmentProcessor instance."""
    return _attachment_processor
