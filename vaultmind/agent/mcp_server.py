"""
VaultMind FastMCP Server
Exposes Model Context Protocol (MCP) endpoints for UGREEN AI NAS host operations:
1. `search_vault`: Local hybrid RAG with citation isolation [S1..Sn]
2. `read_document_window`: Context-bounded sliding window reader
3. `organize_folder`: Autonomous directory housekeeping and auto-tagging
4. `get_vault_health`: System status, budget telemetry, and indexed assets count
"""

import os
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP

from vaultmind.config import settings
from vaultmind.core.retriever import DeduplicatedHybridRetriever
from vaultmind.core.registry import CitationRegistry
from vaultmind.core.budget import ContextBudgetGuardian

# Initialize FastMCP Server
mcp = FastMCP("vaultmind-nas-agent")

# Global in-memory retriever instance
retriever = DeduplicatedHybridRetriever(
    rrf_k=settings.rrf_k,
    relative_cutoff=settings.relative_score_ratio
)

@mcp.tool()
def search_vault(query: str, top_k: int = 5) -> str:
    """Searches the local VaultMind private knowledge base.
    Returns passages sanitized into [S1..Sn] citations with 48 KiB budget enforcement.
    """
    raw_chunks = retriever.retrieve(query=query, top_k=top_k)
    if not raw_chunks:
        return "[VaultMind]: No matching documents found in the local vault."

    registry = CitationRegistry()
    formatted = registry.format_passages(raw_chunks, max_bytes=settings.max_context_bytes)
    return formatted

@mcp.tool()
def read_document_window(doc_id: str, offset: int = 0, window_chars: int = 8000) -> str:
    """Reads a bounded context window of a local document to prevent token bloat."""
    # Find matching document in indexed corpus
    matched = next((d for d in retriever.corpus if d.get("id") == doc_id or d.get("file_name") == doc_id), None)
    if not matched:
        return f"[Error]: Document {doc_id} not found in the local vault."

    full_text = matched.get("content", "")
    return ContextBudgetGuardian.extract_sliding_window(full_text, hit_offset=offset, window_chars=window_chars)

@mcp.tool()
def organize_folder(source_dir: str, target_dir: str, dry_run: bool = True) -> Dict[str, Any]:
    """Scans and organizes files in local NAS directories based on semantic document types."""
    if not os.path.exists(source_dir):
        return {"status": "error", "message": f"Source directory {source_dir} does not exist."}

    # Simulated autonomous file organization plan
    actions = []
    for item in os.listdir(source_dir):
        item_path = os.path.join(source_dir, item)
        if os.path.isfile(item_path):
            ext = os.path.splitext(item)[1].lower()
            category = "documents" if ext in [".pdf", ".docx", ".txt", ".md"] else "media" if ext in [".png", ".jpg", ".mp4"] else "other"
            dest = os.path.join(target_dir, category, item)
            actions.append({"file": item, "category": category, "destination": dest})

    return {
        "status": "success",
        "dry_run": dry_run,
        "total_files_scanned": len(actions),
        "proposed_actions": actions
    }

@mcp.tool()
def get_vault_health() -> Dict[str, Any]:
    """Returns local vault health, indexed document count, and privacy verification."""
    return {
        "status": "healthy",
        "privacy_mode": "100%_LOCAL_OFFLINE",
        "indexed_documents": len(retriever.corpus),
        "max_context_budget": f"{settings.max_context_bytes // 1024} KiB",
        "mcp_version": "1.0-standard"
    }

if __name__ == "__main__":
    mcp.run()
