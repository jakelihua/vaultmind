"""
Context Budget Guardian & Window Manager
Guarantees tool outputs never exceed max_bytes to prevent LLM context bloat or timeout.
Provides sliding window slicing around matched passage keywords.
"""

import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class ContextBudgetGuardian:
    DEFAULT_MAX_BYTES = 48 * 1024 # 48 KiB (49,152 bytes)
    DEFAULT_WINDOW_CHARS = 12000

    @classmethod
    def enforce_byte_limit(cls, text: str, max_bytes: int = DEFAULT_MAX_BYTES) -> Tuple[str, bool]:
        """Truncates text safely at UTF-8 boundary such that total returned text <= max_bytes."""
        raw_bytes = text.encode("utf-8")
        if len(raw_bytes) <= max_bytes:
            return text, False

        warning = "\n\n[System Note: Content truncated due to context budget constraint. Use `read_document_window` to inspect subsequent sections.]"
        warning_bytes = len(warning.encode("utf-8"))

        if max_bytes > warning_bytes:
            avail_bytes = max_bytes - warning_bytes
            truncated_bytes = raw_bytes[:avail_bytes]
            safe_text = truncated_bytes.decode("utf-8", errors="ignore")
            result = safe_text + warning
        else:
            # If max_bytes cannot even fit the warning, truncate raw text directly to max_bytes without warning
            truncated_bytes = raw_bytes[:max_bytes]
            result = truncated_bytes.decode("utf-8", errors="ignore")

        # Guarantee strict invariant against UTF-8 re-encoding quirks
        while len(result.encode("utf-8")) > max_bytes and len(result) > 0:
            result = result[:-1]

        return result, True

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
