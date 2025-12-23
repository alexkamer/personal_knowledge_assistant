"""
Document archive service for managing external drive storage.

This service handles:
- Saving original documents to external drive
- Retrieving documents from archive
- Fallback to local storage when external drive is unavailable
- Archive path management and validation
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime
import logging

import aiofiles

from app.core.config import settings

logger = logging.getLogger(__name__)


class ArchiveService:
    """Service for managing document archives on external drive."""

    @staticmethod
    def is_archive_available() -> bool:
        """
        Check if the external archive drive is available.

        Returns:
            True if archive is enabled and drive is mounted, False otherwise
        """
        if not settings.archive_enabled:
            return False

        archive_path = Path(settings.archive_base_path)
        return archive_path.exists() and archive_path.is_dir()

    @staticmethod
    def get_archive_documents_dir() -> Path:
        """
        Get the documents directory within the archive.

        Returns:
            Path to archive documents directory

        Raises:
            RuntimeError: If archive is not available
        """
        if not ArchiveService.is_archive_available():
            raise RuntimeError("Archive drive is not available")

        archive_docs_path = Path(settings.archive_base_path) / settings.archive_documents_path
        archive_docs_path.mkdir(parents=True, exist_ok=True)
        return archive_docs_path

    @staticmethod
    def get_archive_backups_dir() -> Path:
        """
        Get the backups directory within the archive.

        Returns:
            Path to archive backups directory

        Raises:
            RuntimeError: If archive is not available
        """
        if not ArchiveService.is_archive_available():
            raise RuntimeError("Archive drive is not available")

        archive_backups_path = Path(settings.archive_base_path) / settings.archive_backups_path
        archive_backups_path.mkdir(parents=True, exist_ok=True)
        return archive_backups_path

    @staticmethod
    def _generate_archive_path(
        filename: str,
        file_type: str,
        base_dir: Path,
    ) -> Tuple[Path, str]:
        """
        Generate a structured archive path for a document.

        Uses date-based directory structure: YYYY/MM/DD/UUID.ext

        Args:
            filename: Original filename
            file_type: File extension (without dot)
            base_dir: Base directory for archive

        Returns:
            Tuple of (full_path, relative_path_from_base)
        """
        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")

        # Create date-based subdirectory
        date_dir = base_dir / year / month / day
        date_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_extension = f".{file_type.lstrip('.')}"
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        full_path = date_dir / unique_filename

        # Calculate relative path from base
        relative_path = str(full_path.relative_to(base_dir))

        return full_path, relative_path

    @staticmethod
    async def save_to_archive(
        source_path: str,
        filename: str,
        file_type: str,
    ) -> Tuple[str, str]:
        """
        Save a document to the archive.

        Copies the file to external drive with date-based organization.
        Falls back to local storage if archive is unavailable and fallback is enabled.

        Args:
            source_path: Path to the source file to archive
            filename: Original filename
            file_type: File extension

        Returns:
            Tuple of (archive_path, storage_location)
            - archive_path: Full path where file is stored
            - storage_location: "archive" or "local"

        Raises:
            RuntimeError: If archive is unavailable and fallback is disabled
            IOError: If file save fails
        """
        archive_available = ArchiveService.is_archive_available()

        if not archive_available:
            if settings.archive_fallback_to_local:
                logger.warning(
                    f"Archive unavailable, saving {filename} to local storage"
                )
                # File is already in local upload directory, just return its path
                return source_path, "local"
            else:
                raise RuntimeError(
                    "Archive drive is not available and fallback is disabled"
                )

        try:
            archive_docs_dir = ArchiveService.get_archive_documents_dir()
            archive_path, relative_path = ArchiveService._generate_archive_path(
                filename, file_type, archive_docs_dir
            )

            # Copy file to archive (keep original for now)
            shutil.copy2(source_path, archive_path)

            logger.info(f"Archived {filename} to {archive_path}")
            return str(archive_path), "archive"

        except Exception as e:
            logger.error(f"Failed to archive {filename}: {str(e)}")
            if settings.archive_fallback_to_local:
                logger.warning(f"Falling back to local storage for {filename}")
                return source_path, "local"
            raise IOError(f"Failed to save to archive: {str(e)}")

    @staticmethod
    async def retrieve_from_archive(archive_path: str) -> bytes:
        """
        Retrieve a document from the archive.

        Args:
            archive_path: Path to archived document

        Returns:
            File contents as bytes

        Raises:
            FileNotFoundError: If file does not exist
            IOError: If file read fails
        """
        path = Path(archive_path)
        if not path.exists():
            raise FileNotFoundError(f"Archive file not found: {archive_path}")

        try:
            async with aiofiles.open(path, "rb") as f:
                return await f.read()
        except Exception as e:
            raise IOError(f"Failed to read archive file: {str(e)}")

    @staticmethod
    async def delete_from_archive(archive_path: str) -> bool:
        """
        Delete a document from the archive.

        Args:
            archive_path: Path to archived document

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            path = Path(archive_path)
            if path.exists() and path.is_file():
                path.unlink()
                logger.info(f"Deleted archived file: {archive_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete archive file {archive_path}: {str(e)}")
            return False

    @staticmethod
    def get_archive_stats() -> dict:
        """
        Get statistics about the archive.

        Returns:
            Dictionary with archive statistics:
            - available: Whether archive is available
            - total_size: Total size in bytes (if available)
            - document_count: Number of archived documents (if available)
            - base_path: Archive base path
        """
        stats = {
            "available": ArchiveService.is_archive_available(),
            "base_path": settings.archive_base_path,
            "enabled": settings.archive_enabled,
        }

        if not stats["available"]:
            stats["total_size"] = 0
            stats["document_count"] = 0
            return stats

        try:
            archive_docs_dir = ArchiveService.get_archive_documents_dir()

            # Count files and calculate total size
            total_size = 0
            document_count = 0

            for root, _, files in os.walk(archive_docs_dir):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        document_count += 1

            stats["total_size"] = total_size
            stats["document_count"] = document_count

        except Exception as e:
            logger.error(f"Failed to get archive stats: {str(e)}")
            stats["total_size"] = 0
            stats["document_count"] = 0

        return stats
