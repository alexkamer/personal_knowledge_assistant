"""
Semantic-aware text chunking that preserves document structure and adapts to content type.
"""
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

import tiktoken


class ContentType(str, Enum):
    """Types of content for adaptive chunking."""
    CODE = "code"
    NARRATIVE = "narrative"
    LIST = "list"
    TABLE = "table"
    HEADING = "heading"
    MIXED = "mixed"


@dataclass
class ChunkMetadata:
    """Metadata for a text chunk."""
    content_type: ContentType
    heading_hierarchy: List[str]
    section_title: Optional[str]
    has_code: bool
    token_count: int
    semantic_density: float  # 0-1, higher = more dense


@dataclass
class SemanticChunk:
    """A chunk with content and rich metadata."""
    content: str
    metadata: ChunkMetadata


class SemanticChunker:
    """
    Advanced chunker that preserves document structure and adapts to content type.

    Features:
    - Preserves markdown structure (headers, code blocks, tables)
    - Adaptive chunk sizes based on content type
    - Rich metadata for better retrieval
    - Smart overlap strategies
    """

    def __init__(
        self,
        min_chunk_size: int = 256,
        max_chunk_size: int = 768,
        encoding_name: str = "cl100k_base",
    ):
        """
        Initialize the semantic chunker.

        Args:
            min_chunk_size: Minimum tokens per chunk
            max_chunk_size: Maximum tokens per chunk
            encoding_name: Tiktoken encoding to use
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.encoding = tiktoken.get_encoding(encoding_name)

        # Adaptive sizes by content type
        self.target_sizes = {
            ContentType.CODE: 384,
            ContentType.NARRATIVE: 512,
            ContentType.LIST: 384,
            ContentType.TABLE: 512,
            ContentType.HEADING: 256,
            ContentType.MIXED: 512,
        }

        # Overlap percentages by content type
        self.overlap_ratios = {
            ContentType.CODE: 0.05,  # Minimal overlap for code
            ContentType.NARRATIVE: 0.10,  # Standard overlap
            ContentType.LIST: 0.05,
            ContentType.TABLE: 0.0,  # No overlap for tables
            ContentType.HEADING: 0.0,
            ContentType.MIXED: 0.10,
        }

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def split_text(self, text: str) -> List[SemanticChunk]:
        """
        Split text into semantic chunks with metadata.

        Args:
            text: Text to split

        Returns:
            List of semantic chunks with metadata
        """
        if not text or not text.strip():
            return []

        # Parse document structure
        blocks = self._parse_document_structure(text)

        # Group blocks into chunks
        chunks = self._create_chunks_from_blocks(blocks)

        return chunks

    def _parse_document_structure(self, text: str) -> List[dict]:
        """
        Parse text into structural blocks (headers, code, paragraphs, etc.).

        Args:
            text: Text to parse

        Returns:
            List of block dictionaries with type and content
        """
        blocks = []
        current_hierarchy = []

        # Split into lines for parsing
        lines = text.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for markdown headers
            if header_match := re.match(r"^(#{1,6})\s+(.+)$", line):
                level = len(header_match.group(1))
                title = header_match.group(2)

                # Update hierarchy
                current_hierarchy = current_hierarchy[:level-1] + [title]

                blocks.append({
                    "type": ContentType.HEADING,
                    "content": line,
                    "hierarchy": current_hierarchy.copy(),
                    "level": level,
                })
                i += 1

            # Check for code blocks
            elif line.strip().startswith("```"):
                code_block, end_idx = self._extract_code_block(lines, i)
                blocks.append({
                    "type": ContentType.CODE,
                    "content": code_block,
                    "hierarchy": current_hierarchy.copy(),
                })
                i = end_idx + 1

            # Check for tables (markdown tables with |)
            elif "|" in line and i + 1 < len(lines) and "|" in lines[i + 1]:
                table_block, end_idx = self._extract_table(lines, i)
                blocks.append({
                    "type": ContentType.TABLE,
                    "content": table_block,
                    "hierarchy": current_hierarchy.copy(),
                })
                i = end_idx + 1

            # Check for lists
            elif re.match(r"^\s*[\-\*\+]\s+", line) or re.match(r"^\s*\d+\.\s+", line):
                list_block, end_idx = self._extract_list(lines, i)
                blocks.append({
                    "type": ContentType.LIST,
                    "content": list_block,
                    "hierarchy": current_hierarchy.copy(),
                })
                i = end_idx + 1

            # Regular paragraph
            else:
                para_block, end_idx = self._extract_paragraph(lines, i)
                if para_block.strip():
                    blocks.append({
                        "type": ContentType.NARRATIVE,
                        "content": para_block,
                        "hierarchy": current_hierarchy.copy(),
                    })
                i = end_idx + 1

        return blocks

    def _extract_code_block(self, lines: List[str], start: int) -> Tuple[str, int]:
        """Extract a complete code block."""
        code_lines = [lines[start]]
        i = start + 1

        while i < len(lines):
            code_lines.append(lines[i])
            if lines[i].strip().startswith("```"):
                break
            i += 1

        return "\n".join(code_lines), i

    def _extract_table(self, lines: List[str], start: int) -> Tuple[str, int]:
        """Extract a complete markdown table."""
        table_lines = []
        i = start

        while i < len(lines) and "|" in lines[i]:
            table_lines.append(lines[i])
            i += 1

        return "\n".join(table_lines), i - 1

    def _extract_list(self, lines: List[str], start: int) -> Tuple[str, int]:
        """Extract a complete list (ordered or unordered)."""
        list_lines = []
        i = start

        while i < len(lines):
            line = lines[i]
            # Check if line is a list item or continuation (indented)
            if re.match(r"^\s*[\-\*\+]\s+", line) or re.match(r"^\s*\d+\.\s+", line) or (line.startswith(" ") and list_lines):
                list_lines.append(line)
                i += 1
            elif not line.strip():  # Empty line, might continue
                list_lines.append(line)
                i += 1
            else:
                break

        # Return i-1 as end index, but ensure we advance at least one line
        end_idx = max(i - 1, start)
        return "\n".join(list_lines), end_idx

    def _extract_paragraph(self, lines: List[str], start: int) -> Tuple[str, int]:
        """Extract a paragraph (text until empty line or special block)."""
        para_lines = []
        i = start

        while i < len(lines):
            line = lines[i]

            # Stop at empty line
            if not line.strip():
                break

            # Stop at special blocks
            if (line.strip().startswith("#") or
                line.strip().startswith("```") or
                re.match(r"^\s*[\-\*\+]\s+", line) or
                re.match(r"^\s*\d+\.\s+", line) or
                "|" in line):
                break

            para_lines.append(line)
            i += 1

        # Return i-1 as end index, but ensure we advance at least one line
        end_idx = max(i - 1, start)
        return "\n".join(para_lines), end_idx

    def _create_chunks_from_blocks(self, blocks: List[dict]) -> List[SemanticChunk]:
        """
        Group blocks into appropriately-sized chunks.

        Args:
            blocks: List of document blocks

        Returns:
            List of semantic chunks
        """
        chunks = []
        current_blocks = []
        current_tokens = 0
        current_type = None

        for block in blocks:
            block_tokens = self.count_tokens(block["content"])
            block_type = block["type"]

            # Get target size for this content type
            target_size = self.target_sizes.get(block_type, self.max_chunk_size)

            # If block alone exceeds max size, split it
            if block_tokens > self.max_chunk_size:
                # Save current chunk if exists
                if current_blocks:
                    chunks.append(self._create_chunk(current_blocks))
                    current_blocks = []
                    current_tokens = 0
                    current_type = None

                # Split large block
                split_chunks = self._split_large_block(block)
                chunks.extend(split_chunks)
                continue

            # If adding this block would exceed target, finalize current chunk
            if current_tokens + block_tokens > target_size and current_blocks:
                chunks.append(self._create_chunk(current_blocks))
                current_blocks = []
                current_tokens = 0
                current_type = None

            # Add block to current chunk
            current_blocks.append(block)
            current_tokens += block_tokens
            current_type = block_type if current_type is None else ContentType.MIXED

            # Finalize chunk if we've reached a good size or it's a standalone block
            if (current_tokens >= target_size * 0.8 or
                block_type in [ContentType.CODE, ContentType.TABLE]):
                chunks.append(self._create_chunk(current_blocks))
                current_blocks = []
                current_tokens = 0
                current_type = None

        # Add remaining blocks
        if current_blocks:
            chunks.append(self._create_chunk(current_blocks))

        return chunks

    def _split_large_block(self, block: dict) -> List[SemanticChunk]:
        """Split a block that's too large into smaller chunks."""
        content = block["content"]
        block_type = block["type"]
        hierarchy = block["hierarchy"]

        # For code blocks, try to split by function/class
        if block_type == ContentType.CODE:
            return self._split_code_block(content, hierarchy)

        # For other types, split by sentences
        chunks = []
        sentences = re.split(r"(?<=[.!?])\s+", content)

        current_content = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            if current_tokens + sentence_tokens > self.max_chunk_size and current_content:
                chunk_text = " ".join(current_content)
                chunks.append(SemanticChunk(
                    content=chunk_text,
                    metadata=ChunkMetadata(
                        content_type=block_type,
                        heading_hierarchy=hierarchy,
                        section_title=hierarchy[-1] if hierarchy else None,
                        has_code=False,
                        token_count=current_tokens,
                        semantic_density=self._calculate_density(chunk_text),
                    )
                ))
                current_content = []
                current_tokens = 0

            current_content.append(sentence)
            current_tokens += sentence_tokens

        if current_content:
            chunk_text = " ".join(current_content)
            chunks.append(SemanticChunk(
                content=chunk_text,
                metadata=ChunkMetadata(
                    content_type=block_type,
                    heading_hierarchy=hierarchy,
                    section_title=hierarchy[-1] if hierarchy else None,
                    has_code=False,
                    token_count=current_tokens,
                    semantic_density=self._calculate_density(chunk_text),
                )
            ))

        return chunks

    def _split_code_block(self, code: str, hierarchy: List[str]) -> List[SemanticChunk]:
        """Split a large code block intelligently."""
        # Try to split by function/class definitions
        lines = code.split("\n")
        chunks = []
        current_lines = []
        current_tokens = 0

        # Keep opening ``` line
        if lines[0].strip().startswith("```"):
            lang = lines[0].strip()
            current_lines = [lang]
            start_idx = 1
        else:
            lang = "```"
            start_idx = 0

        for i in range(start_idx, len(lines)):
            line = lines[i]
            line_tokens = self.count_tokens(line)

            # Check for function/class definitions
            is_definition = (
                re.match(r"^\s*def\s+", line) or
                re.match(r"^\s*class\s+", line) or
                re.match(r"^\s*function\s+", line) or
                re.match(r"^\s*const\s+\w+\s*=\s*\(", line)
            )

            # Split if we're at a definition and would exceed size
            if is_definition and current_tokens + line_tokens > self.max_chunk_size and len(current_lines) > 1:
                # Close current chunk
                current_lines.append("```")
                chunk_text = "\n".join(current_lines)
                chunks.append(SemanticChunk(
                    content=chunk_text,
                    metadata=ChunkMetadata(
                        content_type=ContentType.CODE,
                        heading_hierarchy=hierarchy,
                        section_title=hierarchy[-1] if hierarchy else None,
                        has_code=True,
                        token_count=current_tokens,
                        semantic_density=0.9,  # Code is dense
                    )
                ))
                current_lines = [lang]
                current_tokens = 0

            current_lines.append(line)
            current_tokens += line_tokens

        # Add final chunk
        if len(current_lines) > 1:
            if not current_lines[-1].strip().startswith("```"):
                current_lines.append("```")
            chunk_text = "\n".join(current_lines)
            chunks.append(SemanticChunk(
                content=chunk_text,
                metadata=ChunkMetadata(
                    content_type=ContentType.CODE,
                    heading_hierarchy=hierarchy,
                    section_title=hierarchy[-1] if hierarchy else None,
                    has_code=True,
                    token_count=current_tokens,
                    semantic_density=0.9,
                )
            ))

        return chunks

    def _create_chunk(self, blocks: List[dict]) -> SemanticChunk:
        """Create a semantic chunk from a list of blocks."""
        # Combine block contents
        content_parts = []
        for block in blocks:
            content_parts.append(block["content"])

        content = "\n\n".join(content_parts)

        # Determine primary content type
        type_counts = {}
        for block in blocks:
            block_type = block["type"]
            type_counts[block_type] = type_counts.get(block_type, 0) + 1

        primary_type = max(type_counts, key=type_counts.get) if type_counts else ContentType.MIXED
        if len(type_counts) > 1:
            primary_type = ContentType.MIXED

        # Get hierarchy from last block
        hierarchy = blocks[-1]["hierarchy"] if blocks else []

        # Check if contains code
        has_code = any(block["type"] == ContentType.CODE for block in blocks)

        # Create metadata
        metadata = ChunkMetadata(
            content_type=primary_type,
            heading_hierarchy=hierarchy,
            section_title=hierarchy[-1] if hierarchy else None,
            has_code=has_code,
            token_count=self.count_tokens(content),
            semantic_density=self._calculate_density(content),
        )

        return SemanticChunk(content=content, metadata=metadata)

    def _calculate_density(self, text: str) -> float:
        """
        Calculate semantic density of text (0-1).

        Higher density = more information per token (code, technical writing)
        Lower density = more conversational (narrative, examples)
        """
        # Simple heuristic based on:
        # - Average word length
        # - Punctuation density
        # - Special characters (code indicators)

        words = text.split()
        if not words:
            return 0.5

        avg_word_length = sum(len(w) for w in words) / len(words)

        # Count special characters (indicators of code/technical content)
        special_chars = sum(1 for c in text if c in "{}[]()<>=+-*/%&|^~$@")
        special_density = special_chars / len(text) if text else 0

        # Normalize to 0-1
        # Long words and special chars = higher density
        density = min(1.0, (avg_word_length / 10 + special_density) / 2)

        return round(density, 2)


# Global instance
default_semantic_chunker = SemanticChunker()
