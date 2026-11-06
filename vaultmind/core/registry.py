"""
Reference Collector & Citation Isolation Protocol
Decouples internal document hashes, storage paths, and chunk UUIDs from the LLM prompt.
Presents clean [S1], [S2] short tags to the model and maintains a verified internal registry.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from vaultmind.core.budget import ContextBudgetGuardian

@dataclass
class RetrievedChunk:
    doc_id: str
    file_name: str
    page: int
    content: str
    dense_score: float = 0.0
    sparse_score: float = 0.0
    rrf_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class CitationRegistry:
    """Session-level citation mapper ensuring clean model prompts and verifiable references."""

    def __init__(self, start_index: int = 1):
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._counter = start_index

    def register(self, chunk: RetrievedChunk) -> str:
        tag = f"S{self._counter}"
        self._counter += 1
        self._registry[tag] = {
            "tag": tag,
            "doc_id": chunk.doc_id,
            "file_name": chunk.file_name,
            "page": chunk.page,
            "score": round(chunk.rrf_score, 4),
            "content": chunk.content,
            "metadata": chunk.metadata
        }
        return tag

    def format_passages(self, chunks: List[RetrievedChunk], max_bytes: int = 48 * 1024) -> str:
        """Formats passages for the model with strict byte budget constraints.
        Ensures chunks are only registered if they are non-empty and actually included in the output.
        """
        formatted_blocks = []
        accumulated_bytes = 0

        for chunk in chunks:
            # Skip empty or whitespace-only chunks
            if not chunk.content or not chunk.content.strip():
                continue

            tag_candidate = f"S{self._counter}"
            header = f"[{tag_candidate}] 《{chunk.file_name}》 Page {chunk.page}\n"
            body = chunk.content.strip() + "\n\n"
            block = header + body
            block_bytes = len(block.encode("utf-8"))

            if accumulated_bytes + block_bytes > max_bytes:
                # If even the first block exceeds max_bytes, apply sliding window truncation
                if not formatted_blocks:
                    header_bytes = len(header.encode("utf-8"))
                    avail = max_bytes - header_bytes - 20
                    if avail > 0:
                        truncated_content, _ = ContextBudgetGuardian.enforce_byte_limit(chunk.content.strip(), max_bytes=avail)
                        tag = self.register(chunk)
                        block = f"[{tag}] 《{chunk.file_name}》 Page {chunk.page}\n{truncated_content}\n\n"
                        formatted_blocks.append(block)
                break

            tag = self.register(chunk)
            formatted_blocks.append(block)
            accumulated_bytes += block_bytes

        return "".join(formatted_blocks)

    def get_source(self, tag: str) -> Optional[Dict[str, Any]]:
        clean_tag = tag.strip("[] ").upper()
        return self._registry.get(clean_tag)

    def dump_manifest(self) -> Dict[str, Any]:
        return {
            "total_citations": len(self._registry),
            "citations": self._registry
        }
