# Document Thumbnails Implementation Guide

## Overview

The frontend now supports document thumbnails/preview images with automatic fallbacks to file-type icons.

## Current Implementation

### Frontend Components

1. **DocumentThumbnail Component** (`/frontend/src/components/documents/DocumentThumbnail.tsx`)
   - Displays thumbnail image if available
   - Falls back to color-coded file type icons
   - Three sizes: sm (16px), md (24px), lg (32px)
   - Glassmorphic design with gradients
   - Handles image loading errors gracefully

2. **Integrated in Views**
   - Grid View: Large thumbnails (lg size)
   - List View: Small thumbnails (sm size)

### File Type Icons

The component automatically assigns colors and icons based on file type:

- **PDF**: Red icon (FileText)
- **DOC/DOCX**: Blue icon (FileText)
- **TXT**: Gray icon (File)
- **MD**: Purple icon (FileCode)
- **Images (JPG/PNG)**: Green icon (ImageIcon)

## Backend Implementation Required

To enable actual thumbnail generation, implement the following:

### 1. Add Thumbnail Field to Database

```python
# backend/app/models/document.py
class Document(Base):
    __tablename__ = "documents"

    # ... existing fields ...
    thumbnail_url = Column(String, nullable=True)  # Add this field
```

### 2. Generate Thumbnails on Upload

```python
# backend/app/services/thumbnail_service.py
from PIL import Image
import io
import os

class ThumbnailService:
    THUMBNAIL_SIZE = (300, 400)
    THUMBNAIL_DIR = "./thumbnails"

    def generate_thumbnail(self, file_path: str, file_type: str) -> str | None:
        """Generate thumbnail and return URL"""

        if file_type.lower() == 'pdf':
            return self._generate_pdf_thumbnail(file_path)
        elif file_type.lower() in ['jpg', 'jpeg', 'png']:
            return self._generate_image_thumbnail(file_path)
        else:
            return None  # No thumbnail for text files

    def _generate_pdf_thumbnail(self, pdf_path: str) -> str:
        """Generate thumbnail from first page of PDF"""
        import pdf2image

        # Convert first page to image
        images = pdf2image.convert_from_path(
            pdf_path,
            first_page=1,
            last_page=1,
            size=self.THUMBNAIL_SIZE
        )

        # Save thumbnail
        thumbnail_filename = f"{os.path.basename(pdf_path)}_thumb.jpg"
        thumbnail_path = os.path.join(self.THUMBNAIL_DIR, thumbnail_filename)
        images[0].save(thumbnail_path, 'JPEG')

        # Return URL (adjust based on your static file serving)
        return f"/thumbnails/{thumbnail_filename}"

    def _generate_image_thumbnail(self, image_path: str) -> str:
        """Generate thumbnail from image file"""
        with Image.open(image_path) as img:
            img.thumbnail(self.THUMBNAIL_SIZE)

            thumbnail_filename = f"{os.path.basename(image_path)}_thumb.jpg"
            thumbnail_path = os.path.join(self.THUMBNAIL_DIR, thumbnail_filename)
            img.save(thumbnail_path, 'JPEG')

            return f"/thumbnails/{thumbnail_filename}"
```

### 3. Update Upload Endpoint

```python
# backend/app/api/v1/endpoints/documents.py
from app.services.thumbnail_service import ThumbnailService

thumbnail_service = ThumbnailService()

@router.post("/", response_model=DocumentResponse)
async def upload_document(...):
    # ... existing upload logic ...

    # Generate thumbnail
    thumbnail_url = thumbnail_service.generate_thumbnail(
        file_path=saved_path,
        file_type=file_extension
    )

    # Create document with thumbnail URL
    document = Document(
        filename=file.filename,
        file_type=file_extension,
        file_path=saved_path,
        file_size=file_size,
        thumbnail_url=thumbnail_url,  # Add this
        category=category
    )

    # ... save to database ...
```

### 4. Serve Thumbnail Files

```python
# backend/app/main.py
from fastapi.staticfiles import StaticFiles

app.mount("/thumbnails", StaticFiles(directory="thumbnails"), name="thumbnails")
```

### 5. Database Migration

```bash
# Create migration
cd backend
alembic revision --autogenerate -m "Add thumbnail_url to documents"
alembic upgrade head
```

## Dependencies Needed

Add to `backend/requirements.txt`:

```
Pillow==10.1.0          # For image processing
pdf2image==1.16.3       # For PDF thumbnail generation
poppler-utils           # System dependency for pdf2image
```

Install system dependencies:

```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows
# Download poppler binaries from https://github.com/oschwartz10612/poppler-windows/releases/
```

## Optional Enhancements

### 1. Async Thumbnail Generation

For large files, generate thumbnails asynchronously:

```python
from fastapi import BackgroundTasks

@router.post("/")
async def upload_document(
    background_tasks: BackgroundTasks,
    ...
):
    # Save document first
    document = Document(...)
    db.add(document)
    db.commit()

    # Generate thumbnail in background
    background_tasks.add_task(
        generate_and_update_thumbnail,
        document.id,
        document.file_path,
        document.file_type
    )

    return document
```

### 2. CDN Integration

For production, store thumbnails in cloud storage (S3, CloudFlare R2):

```python
def upload_to_cdn(thumbnail_path: str) -> str:
    """Upload thumbnail to CDN and return public URL"""
    # Example with boto3 for S3
    s3_client.upload_file(
        thumbnail_path,
        bucket_name='my-thumbnails',
        key=os.path.basename(thumbnail_path)
    )
    return f"https://cdn.example.com/thumbnails/{os.path.basename(thumbnail_path)}"
```

### 3. Caching

Cache thumbnails to avoid regenerating:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_thumbnail_url(document_id: str) -> str | None:
    # Check cache or database
    return thumbnail_url
```

## Testing

Test with various file types:

```bash
# Upload PDF
curl -X POST "http://localhost:8000/api/v1/documents" \
  -F "file=@test.pdf" \
  -F "category=reports"

# Check thumbnail in response
# Should include: "thumbnail_url": "/thumbnails/test.pdf_thumb.jpg"

# Verify thumbnail is accessible
curl "http://localhost:8000/thumbnails/test.pdf_thumb.jpg" --output thumb.jpg
```

## Current Status

✅ Frontend thumbnail component implemented
✅ Automatic fallback to file-type icons
✅ Responsive sizing (sm/md/lg)
✅ Glassmorphic design with hover effects
✅ Error handling for missing images

⏳ Backend thumbnail generation (needs implementation)
⏳ Database schema update (needs migration)
⏳ Static file serving setup (needs configuration)

## Notes

- Thumbnails are optional - system works perfectly without them
- File type icons provide good visual distinction
- Adding real thumbnails will significantly enhance user experience for PDFs and images
- Consider storage costs for large deployments
