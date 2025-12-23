"""
Unit tests for ArchiveService.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from app.services.archive_service import ArchiveService
from app.core.config import settings


@pytest.fixture
def temp_archive_dir():
    """Create a temporary directory for testing archive operations."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_source_file():
    """Create a temporary source file for testing."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file.write("Test content for archiving")
    temp_file.close()
    yield temp_file.name
    Path(temp_file.name).unlink(missing_ok=True)


class TestArchiveService:
    """Tests for ArchiveService."""

    def test_is_archive_available_when_disabled(self):
        """Test that archive is not available when disabled in settings."""
        with patch.object(settings, 'archive_enabled', False):
            assert ArchiveService.is_archive_available() is False

    def test_is_archive_available_when_path_not_exists(self):
        """Test that archive is not available when path doesn't exist."""
        with patch.object(settings, 'archive_enabled', True):
            with patch.object(settings, 'archive_base_path', '/nonexistent/path'):
                assert ArchiveService.is_archive_available() is False

    def test_is_archive_available_when_enabled_and_exists(self, temp_archive_dir):
        """Test that archive is available when enabled and path exists."""
        with patch.object(settings, 'archive_enabled', True):
            with patch.object(settings, 'archive_base_path', temp_archive_dir):
                assert ArchiveService.is_archive_available() is True

    def test_get_archive_documents_dir_creates_directory(self, temp_archive_dir):
        """Test that get_archive_documents_dir creates the directory if needed."""
        with patch.object(settings, 'archive_enabled', True):
            with patch.object(settings, 'archive_base_path', temp_archive_dir):
                with patch.object(settings, 'archive_documents_path', 'docs'):
                    docs_dir = ArchiveService.get_archive_documents_dir()
                    assert docs_dir.exists()
                    assert docs_dir.is_dir()
                    assert docs_dir.name == 'docs'

    def test_get_archive_documents_dir_raises_when_unavailable(self):
        """Test that get_archive_documents_dir raises error when archive unavailable."""
        with patch.object(settings, 'archive_enabled', False):
            with pytest.raises(RuntimeError, match="Archive drive is not available"):
                ArchiveService.get_archive_documents_dir()

    def test_get_archive_backups_dir_creates_directory(self, temp_archive_dir):
        """Test that get_archive_backups_dir creates the directory if needed."""
        with patch.object(settings, 'archive_enabled', True):
            with patch.object(settings, 'archive_base_path', temp_archive_dir):
                with patch.object(settings, 'archive_backups_path', 'backups'):
                    backups_dir = ArchiveService.get_archive_backups_dir()
                    assert backups_dir.exists()
                    assert backups_dir.is_dir()
                    assert backups_dir.name == 'backups'

    def test_generate_archive_path_structure(self, temp_archive_dir):
        """Test that archive paths use date-based structure."""
        base_dir = Path(temp_archive_dir)
        full_path, relative_path = ArchiveService._generate_archive_path(
            filename="test.pdf",
            file_type="pdf",
            base_dir=base_dir,
        )

        # Check that path includes date structure (YYYY/MM/DD)
        path_parts = Path(relative_path).parts
        assert len(path_parts) >= 4  # year/month/day/file
        assert path_parts[0].isdigit() and len(path_parts[0]) == 4  # year
        assert path_parts[1].isdigit() and len(path_parts[1]) == 2  # month
        assert path_parts[2].isdigit() and len(path_parts[2]) == 2  # day

        # Check that file has UUID and correct extension
        filename = path_parts[-1]
        assert filename.endswith('.pdf')

    @pytest.mark.asyncio
    async def test_save_to_archive_success(self, temp_archive_dir, temp_source_file):
        """Test successfully saving a file to archive."""
        with patch.object(settings, 'archive_enabled', True):
            with patch.object(settings, 'archive_base_path', temp_archive_dir):
                with patch.object(settings, 'archive_documents_path', 'documents'):
                    archive_path, storage_location = await ArchiveService.save_to_archive(
                        source_path=temp_source_file,
                        filename="test.txt",
                        file_type="txt",
                    )

                    assert storage_location == "archive"
                    assert Path(archive_path).exists()

                    # Verify content was copied
                    with open(archive_path, 'r') as f:
                        content = f.read()
                    assert content == "Test content for archiving"

    @pytest.mark.asyncio
    async def test_save_to_archive_fallback_to_local(self, temp_source_file):
        """Test fallback to local when archive is unavailable."""
        with patch.object(settings, 'archive_enabled', True):
            with patch.object(settings, 'archive_base_path', '/nonexistent/path'):
                with patch.object(settings, 'archive_fallback_to_local', True):
                    archive_path, storage_location = await ArchiveService.save_to_archive(
                        source_path=temp_source_file,
                        filename="test.txt",
                        file_type="txt",
                    )

                    assert storage_location == "local"
                    assert archive_path == temp_source_file

    @pytest.mark.asyncio
    async def test_save_to_archive_raises_without_fallback(self, temp_source_file):
        """Test that error is raised when archive unavailable and fallback disabled."""
        with patch.object(settings, 'archive_enabled', True):
            with patch.object(settings, 'archive_base_path', '/nonexistent/path'):
                with patch.object(settings, 'archive_fallback_to_local', False):
                    with pytest.raises(RuntimeError, match="Archive drive is not available"):
                        await ArchiveService.save_to_archive(
                            source_path=temp_source_file,
                            filename="test.txt",
                            file_type="txt",
                        )

    @pytest.mark.asyncio
    async def test_retrieve_from_archive_success(self, temp_source_file):
        """Test successfully retrieving a file from archive."""
        content = await ArchiveService.retrieve_from_archive(temp_source_file)
        assert content == b"Test content for archiving"

    @pytest.mark.asyncio
    async def test_retrieve_from_archive_not_found(self):
        """Test retrieving a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Archive file not found"):
            await ArchiveService.retrieve_from_archive("/nonexistent/file.txt")

    @pytest.mark.asyncio
    async def test_delete_from_archive_success(self, temp_source_file):
        """Test successfully deleting a file from archive."""
        # Verify file exists first
        assert Path(temp_source_file).exists()

        # Delete it
        result = await ArchiveService.delete_from_archive(temp_source_file)
        assert result is True
        assert not Path(temp_source_file).exists()

    @pytest.mark.asyncio
    async def test_delete_from_archive_not_found(self):
        """Test deleting a non-existent file returns False."""
        result = await ArchiveService.delete_from_archive("/nonexistent/file.txt")
        assert result is False

    def test_get_archive_stats_unavailable(self):
        """Test getting stats when archive is unavailable."""
        with patch.object(settings, 'archive_enabled', False):
            stats = ArchiveService.get_archive_stats()
            assert stats['available'] is False
            assert stats['enabled'] is False
            assert stats['total_size'] == 0
            assert stats['document_count'] == 0

    def test_get_archive_stats_available(self, temp_archive_dir):
        """Test getting stats when archive is available."""
        with patch.object(settings, 'archive_enabled', True):
            with patch.object(settings, 'archive_base_path', temp_archive_dir):
                with patch.object(settings, 'archive_documents_path', 'documents'):
                    # Create some test files
                    docs_dir = Path(temp_archive_dir) / 'documents'
                    docs_dir.mkdir(parents=True, exist_ok=True)

                    test_file1 = docs_dir / 'file1.txt'
                    test_file1.write_text('test content 1')

                    test_file2 = docs_dir / 'file2.txt'
                    test_file2.write_text('test content 2')

                    stats = ArchiveService.get_archive_stats()
                    assert stats['available'] is True
                    assert stats['enabled'] is True
                    assert stats['document_count'] == 2
                    assert stats['total_size'] > 0
