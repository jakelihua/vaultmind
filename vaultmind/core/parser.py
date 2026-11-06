"""
Directory-Aware Document Parser
Preserves hierarchical structure, headings, and file system provenance.
Supports Markdown, Text, and clean table extraction.
"""

import os
import re
from typing import List, Dict, Any

class DirectoryAwareParser:
    @staticmethod
    def parse_text_file(file_path: str, chunk_size: int = 800, overlap: int = 150) -> List[Dict[str, Any]]:
        file_name = os.path.basename(file_path)
        rel_dir = os.path.dirname(file_path)

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        # Split by sections / headings if markdown
        sections = re.split(r"(?m)^(?=#{1,3}\s+)", text)
        chunks = []
        page = 1

        for sec in sections:
            sec_clean = sec.strip()
            if not sec_clean:
                continue

            if len(sec_clean) <= chunk_size:
                chunks.append({
                    "id": f"{file_name}_p{page}",
                    "file_name": file_name,
                    "directory": rel_dir,
                    "page": page,
                    "content": sec_clean,
                    "metadata": {"length": len(sec_clean)}
                })
                page += 1
            else:
                # Sliding window chunking
                start = 0
                while start < len(sec_clean):
                    end = min(len(sec_clean), start + chunk_size)
                    chunk_text = sec_clean[start:end]
                    chunks.append({
                        "id": f"{file_name}_p{page}",
                        "file_name": file_name,
                        "directory": rel_dir,
                        "page": page,
                        "content": chunk_text,
                        "metadata": {"length": len(chunk_text)}
                    })
                    page += 1
                    start += (chunk_size - overlap)

        return chunks
