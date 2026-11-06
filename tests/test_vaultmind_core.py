"""
Unit & Contract Tests for VaultMind Core Engine
Verifies:
1. [S1..Sn] Citation Isolation & Registry decoupling
2. 48 KiB Context Budget Guardian & Sliding Window
3. Query deduplication & RRF rank fusion
4. Relative score ratio pruning (0.9x cutoff)
5. Tri-state error handling
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
        file_name="Tax_2025.pdf",
        page=2,
        content="Adjusted gross income was $185,000."
    )
    chunk2 = RetrievedChunk(
        doc_id="internal_doc_9982",
        file_name="Mortgage_Statement.pdf",
        page=5,
        content="Remaining principal is $420,000."
    )

    formatted = registry.format_passages([chunk1, chunk2])
    # Model should ONLY see [S1] and [S2], never internal_doc_9981
    assert "[S1] 《Tax_2025.pdf》 Page 2" in formatted
    assert "[S2] 《Mortgage_Statement.pdf》 Page 5" in formatted
    assert "internal_doc_9981" not in formatted

    source1 = registry.get_source("S1")
    assert source1["doc_id"] == "internal_doc_9981"
    assert source1["file_name"] == "Tax_2025.pdf"

def test_context_budget_guardian():
    # Test strict 48 KiB limit
    small_text = "Standard context"
    safe, truncated = ContextBudgetGuardian.enforce_byte_limit(small_text, max_bytes=100)
    assert not truncated
    assert safe == small_text

    large_text = "A" * 60000
    safe_large, truncated = ContextBudgetGuardian.enforce_byte_limit(large_text, max_bytes=48 * 1024)
    assert truncated
    assert len(safe_large.encode("utf-8")) <= (48 * 1024 + 300) # text + warning message
    assert "System Note: Content truncated due to 48 KiB" in safe_large

def test_sliding_window():
    full_doc = "X" * 1000 + "TARGET_KEYWORD" + "Y" * 1000
    window = ContextBudgetGuardian.extract_sliding_window(full_doc, hit_offset=1000, window_chars=500)
    assert "TARGET_KEYWORD" in window
    assert len(window) < len(full_doc)

def test_retriever_deduplication():
    queries = [
        "How is the mortgage calculated?",
        "How is the mortgage calculated",
        "how is the mortgage calculated??",
        "Different query"
    ]
    deduped = DeduplicatedHybridRetriever.dedupe_queries(queries)
    assert len(deduped) == 2
    assert deduped[0] == "How is the mortgage calculated?"
    assert deduped[1] == "Different query"

def test_hybrid_rrf_and_relative_cutoff():
    retriever = DeduplicatedHybridRetriever(rrf_k=60, relative_cutoff=0.9)
    docs = [
        {"id": "doc_1", "file_name": "Apple_10k.pdf", "page": 1, "content": "Services revenue grew 14% to $96 billion."},
        {"id": "doc_2", "file_name": "Apple_10k.pdf", "page": 2, "content": "iPhone revenue reached $200 billion worldwide."},
        {"id": "doc_3", "file_name": "Cooking_Recipes.pdf", "page": 1, "content": "Bake chocolate cake at 350 degrees."}
    ]
    retriever.index_documents(docs)

    results = retriever.retrieve("Apple Services revenue growth")
    assert len(results) >= 1
    top_hit = results[0]
    assert top_hit.file_name == "Apple_10k.pdf"
    assert "Services revenue grew" in top_hit.content

    # The recipe doc should be pruned by relative cutoff
    found_recipe = any(r.file_name == "Cooking_Recipes.pdf" for r in results)
    assert not found_recipe

def test_orchestrator_tri_state():
    retriever = DeduplicatedHybridRetriever()
    retriever.index_documents([
        {"id": "doc_1", "file_name": "Passport.pdf", "page": 1, "content": "Passport expires in 2032."}
    ])
    orchestrator = VaultMindOrchestrator(retriever)

    # 1. Matching grounded answer
    resp_match = orchestrator.answer_query("When does passport expire?")
    assert resp_match["status"] == "SUCCESS_GROUNDED"
    assert resp_match["citations_count"] >= 1

    # 2. Unmatched query (refusal to hallucinate)
    resp_nomatch = orchestrator.answer_query("What is the nuclear launch code?")
    assert resp_nomatch["status"] == "ZERO_RECORDS_FOUND"
    assert "Refusing to hallucinate" in resp_nomatch["answer"]
