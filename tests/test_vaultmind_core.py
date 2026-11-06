"""
Unit & Contract Tests for VaultMind Core Engine
Verifies:
1. [S1..Sn] Citation Isolation & Registry decoupling
2. 48 KiB Context Budget Guardian (strict byte limit guarantee across all ranges including small budgets)
3. Ghost citation prevention (no unrendered or blank citations in manifest)
4. Query deduplication & RRF rank fusion
5. Relative score ratio pruning (0.9x cutoff)
6. Tri-state error handling
7. Real synthetic file parsing & reconciliation fixture verification
"""

import os
import pytest
from vaultmind.core.registry import CitationRegistry, RetrievedChunk
from vaultmind.core.budget import ContextBudgetGuardian
from vaultmind.core.retriever import DeduplicatedHybridRetriever
from vaultmind.agent.orchestrator import VaultMindOrchestrator

def test_citation_isolation():
    registry = CitationRegistry()
    chunk1 = RetrievedChunk(
        doc_id="internal_doc_9981",
        file_name="Studio_Agreement_2025.txt",
        page=1,
        content="Monthly retainer fee agreed is USD 2,400.00."
    )
    chunk2 = RetrievedChunk(
        doc_id="internal_doc_9982",
        file_name="Invoice_Design_Nov_2025.txt",
        page=1,
        content="Total amount billed: USD 2,640.00."
    )

    formatted = registry.format_passages([chunk1, chunk2])
    # Model should ONLY see [S1] and [S2], never internal_doc_9981
    assert "[S1] 《Studio_Agreement_2025.txt》 Page 1" in formatted
    assert "[S2] 《Invoice_Design_Nov_2025.txt》 Page 1" in formatted
    assert "internal_doc_9981" not in formatted

    source1 = registry.get_source("S1")
    assert source1["doc_id"] == "internal_doc_9981"
    assert source1["file_name"] == "Studio_Agreement_2025.txt"

def test_context_budget_guardian_strict_limit():
    # Test strict limit across various small and large byte limits
    for max_bytes in [10, 50, 100, 200, 500, 48 * 1024]:
        large_text = "ABCDEFGHIJ" * 5000
        safe_text, truncated = ContextBudgetGuardian.enforce_byte_limit(large_text, max_bytes=max_bytes)
        assert truncated
        assert len(safe_text.encode("utf-8")) <= max_bytes

    small_text = "Short text"
    safe, truncated = ContextBudgetGuardian.enforce_byte_limit(small_text, max_bytes=100)
    assert not truncated
    assert safe == small_text

def test_ghost_citation_prevention_and_empty_chunks():
    registry = CitationRegistry()
    blank_chunk = RetrievedChunk(
        doc_id="doc_blank",
        file_name="Blank.txt",
        page=1,
        content="   \n  "
    )
    huge_chunk = RetrievedChunk(
        doc_id="doc_huge",
        file_name="Huge_Doc.txt",
        page=1,
        content="H" * 100000
    )
    # Give budget of only 500 bytes; blank chunk should be ignored entirely
    formatted = registry.format_passages([blank_chunk, huge_chunk], max_bytes=500)
    assert len(formatted.encode("utf-8")) <= 500
    manifest = registry.dump_manifest()
    # Blank chunk was NOT registered; only huge_chunk was registered
    assert manifest["total_citations"] == 1
    assert "S1" in manifest["citations"]
    assert manifest["citations"]["S1"]["doc_id"] == "doc_huge"

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
        {"id": "doc_1", "file_name": "Studio_Agreement.pdf", "page": 1, "content": "Design fee is fixed at USD 2,400 monthly."},
        {"id": "doc_2", "file_name": "Studio_Invoice.pdf", "page": 1, "content": "Billed amount is USD 2,640 with overtime."},
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

def test_synthetic_fixture_reconciliation():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    assert os.path.exists(fixtures_dir), "Fixtures directory must exist"

    docs = []
    for fname in ["Studio_Agreement_2025.txt", "Invoice_Design_Nov_2025.txt", "Invoice_CloudHosting_Nov_2025.txt"]:
        fpath = os.path.join(fixtures_dir, fname)
        assert os.path.isfile(fpath), f"Fixture {fname} must exist"
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        docs.append({"id": fname, "file_name": fname, "page": 1, "content": content})

    retriever = DeduplicatedHybridRetriever()
    retriever.index_documents(docs)

    # Query for contract retainer
    contract_hits = retriever.retrieve("AGR-2025-04 monthly flat retainer fee")
    assert len(contract_hits) >= 1
    assert "2,400.00" in contract_hits[0].content

    # Query for invoice total
    invoice_hits = retriever.retrieve("INV-2025-1102 Total Amount Billed")
    assert len(invoice_hits) >= 1
    assert "2,640.00" in invoice_hits[0].content

    # Query for missing contract PO-9941
    missing_hits = retriever.retrieve("PO-9941")
    # Only the cloud invoice contains PO-9941; no Agreement document contains it
    po_agreements = [h for h in missing_hits if "Agreement" in h.file_name and "PO-9941" in h.content]
    assert len(po_agreements) == 0
