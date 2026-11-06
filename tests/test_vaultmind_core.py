"""
Unit & Contract Tests for VaultMind Core Engine
Verifies:
1. [S1..Sn] Citation Isolation & Registry decoupling
2. 48 KiB Context Budget Guardian (strict byte limit guarantee)
3. Ghost citation prevention (no unrendered citations in manifest)
4. Query deduplication & RRF rank fusion
5. Relative score ratio pruning (0.9x cutoff)
6. Tri-state error handling
"""

import pytest
from vaultmind.core.registry import CitationRegistry, RetrievedChunk
from vaultmind.core.budget import ContextBudgetGuardian
from vaultmind.core.retriever import DeduplicatedHybridRetriever
from vaultmind.agent.orchestrator import VaultMindOrchestrator

def test_citation_isolation():
    registry = CitationRegistry()
    chunk1 = RetrievedChunk(
        doc_id="internal_doc_9981",
        file_name="Studio_Contract_2025.pdf",
        page=2,
        content="Monthly retainer fee agreed is $2,400.00 USD."
    )
    chunk2 = RetrievedChunk(
        doc_id="internal_doc_9982",
        file_name="Studio_Invoice_Nov.pdf",
        page=1,
        content="Total amount billed: $2,640.00 USD."
    )

    formatted = registry.format_passages([chunk1, chunk2])
    # Model should ONLY see [S1] and [S2], never internal_doc_9981
    assert "[S1] 《Studio_Contract_2025.pdf》 Page 2" in formatted
    assert "[S2] 《Studio_Invoice_Nov.pdf》 Page 1" in formatted
    assert "internal_doc_9981" not in formatted

    source1 = registry.get_source("S1")
    assert source1["doc_id"] == "internal_doc_9981"
    assert source1["file_name"] == "Studio_Contract_2025.pdf"

def test_context_budget_guardian_strict_limit():
    # Test strict 48 KiB limit: total output bytes MUST be <= max_bytes
    small_text = "Standard context"
    safe, truncated = ContextBudgetGuardian.enforce_byte_limit(small_text, max_bytes=100)
    assert not truncated
    assert safe == small_text

    max_bytes = 48 * 1024 # 49,152 bytes
    large_text = "A" * 60000
    safe_large, truncated = ContextBudgetGuardian.enforce_byte_limit(large_text, max_bytes=max_bytes)
    assert truncated
    assert len(safe_large.encode("utf-8")) <= max_bytes
    assert "System Note: Content truncated" in safe_large

def test_ghost_citation_prevention():
    registry = CitationRegistry()
    huge_chunk = RetrievedChunk(
        doc_id="doc_huge",
        file_name="Huge_Doc.pdf",
        page=1,
        content="H" * 100000
    )
    # Give budget of only 500 bytes
    formatted = registry.format_passages([huge_chunk], max_bytes=500)
    assert len(formatted.encode("utf-8")) <= 500
    manifest = registry.dump_manifest()
    # If the chunk was included (even truncated), citations count must match registry exactly
    assert manifest["total_citations"] == 1
    assert "S1" in manifest["citations"]

def test_sliding_window():
    full_doc = "X" * 1000 + "TARGET_KEYWORD" + "Y" * 1000
    window = ContextBudgetGuardian.extract_sliding_window(full_doc, hit_offset=1000, window_chars=500)
    assert "TARGET_KEYWORD" in window
    assert len(window) < len(full_doc)

def test_retriever_deduplication():
    queries = [
        "How is the invoice variance calculated?",
        "How is the invoice variance calculated",
        "how is the invoice variance calculated??",
        "Different query"
    ]
    deduped = DeduplicatedHybridRetriever.dedupe_queries(queries)
    assert len(deduped) == 2
    assert deduped[0] == "How is the invoice variance calculated?"
    assert deduped[1] == "Different query"

def test_hybrid_rrf_and_relative_cutoff():
    retriever = DeduplicatedHybridRetriever(rrf_k=60, relative_cutoff=0.9)
    docs = [
        {"id": "doc_1", "file_name": "Studio_Agreement.pdf", "page": 1, "content": "Design fee is fixed at $2,400 monthly."},
        {"id": "doc_2", "file_name": "Studio_Invoice.pdf", "page": 1, "content": "Billed amount is $2,640 with overtime."},
        {"id": "doc_3", "file_name": "Cooking_Recipes.pdf", "page": 1, "content": "Bake chocolate cake at 350 degrees."}
    ]
    retriever.index_documents(docs)

    results = retriever.retrieve("Studio Design fee monthly retainer")
    assert len(results) >= 1
    top_hit = results[0]
    assert top_hit.file_name == "Studio_Agreement.pdf"
    assert "Design fee is fixed" in top_hit.content

    # The recipe doc should be pruned by relative cutoff
    found_recipe = any(r.file_name == "Cooking_Recipes.pdf" for r in results)
    assert not found_recipe

def test_orchestrator_tri_state():
    retriever = DeduplicatedHybridRetriever()
    retriever.index_documents([
        {"id": "doc_1", "file_name": "Contract_Design.pdf", "page": 1, "content": "Contract signed on November 1st."}
    ])
    orchestrator = VaultMindOrchestrator(retriever)

    # 1. Matching grounded answer
    resp_match = orchestrator.answer_query("When was contract signed?")
    assert resp_match["status"] == "SUCCESS_GROUNDED"
    assert resp_match["citations_count"] >= 1

    # 2. Unmatched query (refusal to hallucinate)
    resp_nomatch = orchestrator.answer_query("What is the secret server password?")
    assert resp_nomatch["status"] == "ZERO_RECORDS_FOUND"
    assert "Refusing to hallucinate" in resp_nomatch["answer"]
