"""
VaultMind Web API & Streaming Server
Provides REST endpoints and SSE real-time streaming for UGREEN NAS Web Dashboard.
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os

from vaultmind.config import settings
from vaultmind.core.retriever import DeduplicatedHybridRetriever
from vaultmind.core.parser import DirectoryAwareParser
from vaultmind.agent.orchestrator import VaultMindOrchestrator

app = FastAPI(
    title="VaultMind Local AI NAS Agent",
    description="Privacy-focused, self-healing knowledge base for UGREEN AI NAS",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instances
retriever = DeduplicatedHybridRetriever(
    rrf_k=settings.rrf_k,
    relative_cutoff=settings.relative_score_ratio
)
orchestrator = VaultMindOrchestrator(retriever)

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

@app.get("/")
def read_root():
    return {
        "app": "VaultMind",
        "status": "online",
        "privacy": "LOCAL_EXECUTION",
        "docs_indexed": len(retriever.corpus)
    }

@app.post("/api/query")
def execute_query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return orchestrator.answer_query(req.query)

@app.post("/api/index/sample")
def index_sample_documents():
    """Indexes verified mock contracts and invoices for reconciliation testing."""
    sample_docs = [
        {
            "id": "contract_design_2025",
            "file_name": "Studio_Design_Agreement_2025.pdf",
            "page": 1,
            "content": "Section 4.1 Compensation: Client agrees to pay Provider a monthly flat fee of $2,400.00 USD (net, exclusive of applicable taxes) due by the 5th of each month.",
            "metadata": {"category": "contract", "agreed_amount": 2400.0, "currency": "USD"}
        },
        {
            "id": "invoice_design_nov_2025",
            "file_name": "Invoice_Design_Nov_2025.pdf",
            "page": 1,
            "content": "Invoice #INV-2025-1102. Billed to Studio Client. Total Amount Due: $2,640.00 USD (Includes $240.00 unapproved overtime adjustment). Payment Terms: Net 15.",
            "metadata": {"category": "invoice", "billed_amount": 2640.0, "currency": "USD"}
        },
        {
            "id": "invoice_cloud_nov_2025",
            "file_name": "Invoice_CloudHosting_Nov_2025.pdf",
            "page": 1,
            "content": "Invoice #INV-CLOUD-9941. Dedicated Storage Server: $350.00 USD. Status: Missing matching vendor Master Services Agreement in authorized directory.",
            "metadata": {"category": "invoice", "billed_amount": 350.0, "currency": "USD", "status": "needs_review"}
        }
    ]
    retriever.index_documents(sample_docs)
    return {
        "status": "success",
        "indexed_count": len(sample_docs),
        "message": "VaultMind local index updated with mock reconciliation fixtures."
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "max_context_bytes": settings.max_context_bytes,
        "relative_cutoff": settings.relative_score_ratio
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("vaultmind.api.server:app", host=settings.api_host, port=settings.api_port, reload=False)
