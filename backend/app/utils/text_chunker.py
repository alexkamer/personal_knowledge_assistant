"""
Text chunking utilities for splitting documents into processable chunks.
"""
import re
from typing import List

import tiktoken


class TextChunker:
    """Handles text chunking with token-aware splitting."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        encoding_name: str = "cl100k_base",
    ):
        """
        Initialize the text chunker.

        Args:
            chunk_size: Maximum number of tokens per chunk
            chunk_overlap: Number of tokens to overlap between chunks
            encoding_name: Tiktoken encoding to use for token counting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))

    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks using recursive splitting strategy.

        Strategy:
        1. Try to split by paragraphs (double newline)
        2. If paragraphs are too large, split by sentences
        3. If sentences are too large, split by character count

        Args:
            text: Text to split into chunks

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        # If the entire text fits in one chunk, return it
        if self.count_tokens(text) <= self.chunk_size:
            return [text.strip()]

        chunks = []
        current_chunk = ""
        current_tokens = 0

        # First, try splitting by paragraphs
        paragraphs = text.split("\n\n")

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            paragraph_tokens = self.count_tokens(paragraph)

            # If adding this paragraph would exceed chunk size, process current chunk
            if current_tokens + paragraph_tokens > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap from previous chunk
                current_chunk = self._get_overlap(current_chunk) + "\n\n" + paragraph
                current_tokens = self.count_tokens(current_chunk)
            # If paragraph alone exceeds chunk size, split it further
            elif paragraph_tokens > self.chunk_size:
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_tokens = 0

                # Split the large paragraph into smaller chunks
                sub_chunks = self._split_large_text(paragraph)
                chunks.extend(sub_chunks[:-1])  # Add all but the last sub-chunk

                # Start new chunk with the last sub-chunk
                if sub_chunks:
                    current_chunk = sub_chunks[-1]
                    current_tokens = self.count_tokens(current_chunk)
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_tokens = self.count_tokens(current_chunk)

        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_large_text(self, text: str) -> List[str]:
        """
        Split text that's larger than chunk_size by sentences.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        chunks = []
        current_chunk = ""
        current_tokens = 0

        # Split by sentences using regex
        sentences = re.split(r"(?<=[.!?])\s+", text)

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # If single sentence exceeds chunk size, split by characters
            if sentence_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_tokens = 0

                # Split by character count
                char_chunks = self._split_by_chars(sentence)
                chunks.extend(char_chunks[:-1])

                if char_chunks:
                    current_chunk = char_chunks[-1]
                    current_tokens = self.count_tokens(current_chunk)
            elif current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = self._get_overlap(current_chunk) + " " + sentence
                current_tokens = self.count_tokens(current_chunk)
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_tokens = self.count_tokens(current_chunk)

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_by_chars(self, text: str) -> List[str]:
        """
        Split text by character count when all else fails.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        chunks = []
        # Estimate characters per chunk (rough approximation: 4 chars per token)
        chars_per_chunk = self.chunk_size * 4
        overlap_chars = self.chunk_overlap * 4

        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chars_per_chunk
            chunk = text[start:end]

            # Adjust to not break in the middle of a word
            if end < text_len:
                last_space = chunk.rfind(" ")
                if last_space > chars_per_chunk // 2:  # Only adjust if space is in latter half
                    end = start + last_space

            chunks.append(text[start:end].strip())
            start = end - overlap_chars if end < text_len else end

        return chunks

    def _get_overlap(self, text: str) -> str:
        """
        Get the last portion of text to use as overlap for next chunk.

        Args:
            text: Text to extract overlap from

        Returns:
            Overlap text
        """
        tokens = self.encoding.encode(text)
        if len(tokens) <= self.chunk_overlap:
            return text

        overlap_tokens = tokens[-self.chunk_overlap :]
        return self.encoding.decode(overlap_tokens)


# Global instance for easy reuse
default_chunker = TextChunker(chunk_size=512, chunk_overlap=50)
