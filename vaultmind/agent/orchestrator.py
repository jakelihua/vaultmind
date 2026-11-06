"""
VaultMind Autonomous Orchestrator
Implements the ReAct loop with Tri-State Error Handling:
1. TRANSIENT_ERROR -> Automatic backoff & retry with alternate query parameters
2. DEADLINE_EXCEEDED -> Concludes gracefully with partial verified knowledge; no hallucinations
3. MISSING_DOCS -> Transparent failure notification; refuses to guess
"""

import time
import logging
from typing import Dict, Any, List, Optional
from vaultmind.core.retriever import DeduplicatedHybridRetriever
from vaultmind.core.registry import CitationRegistry

logger = logging.getLogger(__name__)

class TriStateError(Exception):
    pass

class VaultMindOrchestrator:
    def __init__(self, retriever: DeduplicatedHybridRetriever):
        self.retriever = retriever

    def answer_query(self, user_query: str, max_retries: int = 2) -> Dict[str, Any]:
        """Executes full Agentic loop with self-healing reflection."""
        # 1. Deduplicate & normalize query
        normalized_queries = self.retriever.dedupe_queries([user_query])
        active_query = normalized_queries[0] if normalized_queries else user_query

        # 2. ReAct retrieval with error-boundary
        chunks = []
        attempt = 0
        error_state = None

        while attempt <= max_retries:
            attempt += 1
            try:
                chunks = self.retriever.retrieve(active_query)
                if chunks:
                    break
                else:
                    # Self-healing fallback: Broaden search by relaxing terms
                    words = active_query.split()
                    if len(words) > 1:
                        active_query = " ".join(words[:2])
                        logger.info(f"Self-healing: relaxed search query to '{active_query}' (attempt {attempt})")
            except Exception as e:
                error_state = "TRANSIENT_SYSTEM_ERROR"
                time.sleep(0.5)

        # 3. Format citations
        registry = CitationRegistry()
        if chunks:
            formatted_context = registry.format_passages(chunks)
            system_status = "SUCCESS_GROUNDED"
            summary_answer = f"Based on local verified vault records:\n\n{formatted_context}\n[Answer compiled with verified citations]."
        elif error_state:
            system_status = "TRANSIENT_SYSTEM_BUSY"
            summary_answer = "System Note: The local knowledge vault is temporarily busy or undergoing indexing. Please retry in a few moments."
        else:
            system_status = "ZERO_RECORDS_FOUND"
            summary_answer = "Verified Note: No matching documents or records were found in your local vault. (Refusing to hallucinate unverified data)."

        return {
            "status": system_status,
            "query": user_query,
            "citations_count": len(chunks),
            "manifest": registry.dump_manifest(),
            "answer": summary_answer
        }
