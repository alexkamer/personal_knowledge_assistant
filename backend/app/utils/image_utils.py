"""
Image utility functions for processing and manipulating images.
"""
import base64
import io
import logging
from typing import Tuple, Optional

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


def create_thumbnail(
    base64_image: str,
    size: Tuple[int, int] = (256, 256),
    format: str = "PNG"
) -> Optional[str]:
    """
    Create a thumbnail from a base64 encoded image.

    Args:
        base64_image: Base64 encoded image data
        size: Thumbnail dimensions (width, height), default (256, 256)
        format: Output format (PNG, JPEG, WEBP), default PNG

    Returns:
        Base64 encoded thumbnail image, or None if PIL not available

    Raises:
        ValueError: If image data is invalid
    """
    if not PIL_AVAILABLE:
        logger.warning("PIL not available - skipping thumbnail generation")
        return None

    try:
        # Decode base64 to bytes
        image_bytes = base64.b64decode(base64_image)

        # Open image with PIL
        img = Image.open(io.BytesIO(image_bytes))

        # Convert RGBA to RGB if saving as JPEG
        if format.upper() == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            # Create white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background

        # Create thumbnail (maintains aspect ratio)
        img.thumbnail(size, Image.Resampling.LANCZOS)

        # Save to buffer
        buffer = io.BytesIO()
        img.save(buffer, format=format.upper())
        buffer.seek(0)

        # Encode to base64
        thumbnail_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        logger.debug(f"Created {size[0]}x{size[1]} thumbnail in {format} format")
        return thumbnail_base64

    except Exception as e:
        logger.error(f"Failed to create thumbnail: {e}", exc_info=True)
        raise ValueError(f"Invalid image data: {e}")


def get_image_dimensions(base64_image: str) -> Optional[Tuple[int, int]]:
    """
    Get dimensions (width, height) of a base64 encoded image.

    Args:
        base64_image: Base64 encoded image data

    Returns:
        Tuple of (width, height), or None if PIL not available

    Raises:
        ValueError: If image data is invalid
    """
    if not PIL_AVAILABLE:
        logger.warning("PIL not available - cannot get image dimensions")
        return None

    try:
        # Decode base64 to bytes
        image_bytes = base64.b64decode(base64_image)

        # Open image with PIL
        img = Image.open(io.BytesIO(image_bytes))

        return img.size  # (width, height)

    except Exception as e:
        logger.error(f"Failed to get image dimensions: {e}", exc_info=True)
        raise ValueError(f"Invalid image data: {e}")


def validate_image_format(base64_image: str) -> bool:
    """
    Validate that a base64 string contains valid image data.

    Args:
        base64_image: Base64 encoded image data

    Returns:
        True if valid image, False otherwise
    """
    if not PIL_AVAILABLE:
        logger.warning("PIL not available - cannot validate image format")
        return True  # Assume valid if we can't check

    try:
        image_bytes = base64.b64decode(base64_image)
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()  # Verify it's a valid image
        return True
    except Exception as e:
        logger.debug(f"Image validation failed: {e}")
        return False


def optimize_image_size(
    base64_image: str,
    max_size_kb: int = 500,
    format: str = "PNG",
    quality: int = 85
) -> str:
    """
    Optimize image size by reducing quality if it exceeds max_size_kb.

    Useful for storing web-optimized versions without huge database bloat.

    Args:
        base64_image: Base64 encoded image data
        max_size_kb: Maximum size in kilobytes
        format: Output format (PNG, JPEG, WEBP)
        quality: JPEG/WEBP quality (1-100), ignored for PNG

    Returns:
        Optimized base64 encoded image

    Raises:
        ValueError: If PIL not available or image data invalid
    """
    if not PIL_AVAILABLE:
        raise ValueError("PIL required for image optimization")

    try:
        # Decode base64 to bytes
        image_bytes = base64.b64decode(base64_image)
        original_size_kb = len(image_bytes) / 1024

        # If already under limit, return as-is
        if original_size_kb <= max_size_kb:
            logger.debug(f"Image already optimized ({original_size_kb:.1f}KB <= {max_size_kb}KB)")
            return base64_image

        # Open image
        img = Image.open(io.BytesIO(image_bytes))

        # Convert RGBA to RGB for JPEG
        if format.upper() == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background

        # Try reducing quality iteratively
        current_quality = quality
        while current_quality > 20:
            buffer = io.BytesIO()

            if format.upper() == "PNG":
                # PNG doesn't have quality, use optimize flag
                img.save(buffer, format="PNG", optimize=True)
            else:
                img.save(buffer, format=format.upper(), quality=current_quality, optimize=True)

            buffer.seek(0)
            optimized_bytes = buffer.getvalue()
            optimized_size_kb = len(optimized_bytes) / 1024

            if optimized_size_kb <= max_size_kb:
                logger.info(
                    f"Optimized image from {original_size_kb:.1f}KB to {optimized_size_kb:.1f}KB "
                    f"(quality={current_quality})"
                )
                return base64.b64encode(optimized_bytes).decode("utf-8")

            current_quality -= 10

        # If we still can't get under limit, return best effort
        logger.warning(
            f"Could not optimize image below {max_size_kb}KB "
            f"(final size: {optimized_size_kb:.1f}KB)"
        )
        return base64.b64encode(optimized_bytes).decode("utf-8")

    except Exception as e:
        logger.error(f"Failed to optimize image: {e}", exc_info=True)
        raise ValueError(f"Image optimization failed: {e}")
