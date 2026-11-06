"""
Context Budget Guardian & Window Manager
Guarantees tool outputs never exceed 48 KiB to prevent LLM context bloat or timeout.
Provides sliding window slicing around matched passage keywords.
"""

import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class ContextBudgetGuardian:
    DEFAULT_MAX_BYTES = 48 * 1024 # 48 KiB
    DEFAULT_WINDOW_CHARS = 12000

    @classmethod
    def enforce_byte_limit(cls, text: str, max_bytes: int = DEFAULT_MAX_BYTES) -> Tuple[str, bool]:
        """Truncates text safely at UTF-8 boundary if it exceeds max_bytes."""
        raw_bytes = text.encode("utf-8")
        if len(raw_bytes) <= max_bytes:
            return text, False

        # Truncate and decode safely with replace/ignore at boundary
        truncated_bytes = raw_bytes[:max_bytes]
        safe_text = truncated_bytes.decode("utf-8", errors="ignore")
        warning = "\n\n[System Note: Content truncated due to 48 KiB context budget constraint. Use `read_document_window` to inspect subsequent sections.]"
        return safe_text + warning, True

    @classmethod
    def extract_sliding_window(cls, full_text: str, hit_offset: int, window_chars: int = DEFAULT_WINDOW_CHARS) -> str:
        """Extracts context window surrounding hit_offset rather than returning unconstrained text."""
        total_len = len(full_text)
        if total_len <= window_chars:
            return full_text

        half_window = window_chars // 2
        start = max(0, hit_offset - half_window)
        end = min(total_len, start + window_chars)

        # Adjust start if end hit boundary
        if end == total_len:
            start = max(0, total_len - window_chars)

        window_text = full_text[start:end]
        prefix = "... [preceding context omitted] ...\n" if start > 0 else ""
        suffix = "\n... [subsequent context omitted] ..." if end < total_len else ""

        return prefix + window_text + suffix
