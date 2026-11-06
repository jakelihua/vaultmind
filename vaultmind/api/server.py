"""
VaultMind Web API & Streaming Server
Provides REST endpoints and SSE real-time streaming for UGREEN NAS Web Dashboard.
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os

from vaultmind.config import settings
from vaultmind.core.retriever import DeduplicatedHybridRetriever
from vaultmind.core.parser import DirectoryAwareParser
from vaultmind.agent.orchestrator import VaultMindOrchestrator

app = FastAPI(
    title="VaultMind Local AI NAS Agent",
    description="Zero-leakage, self-healing private knowledge base for UGREEN AI NAS",
    version="1.0.0"
)

app.add_middleware(
    CORSMSMiddleware,
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
        "privacy": "100%_LOCAL",
        "docs_indexed": len(retriever.corpus)
    }

@app.post("/api/query")
def execute_query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return orchestrator.answer_query(req.query)

@app.post("/api/index/sample")
def index_sample_documents():
    """Indexes pre-baked sample documents for demonstration."""
    sample_docs = [
        {
            "id": "apple_10k_p12",
            "file_name": "Apple_2025_Annual_Report_10K.pdf",
            "page": 12,
            "content": "Services revenue grew 14% year-over-year to $96.2 billion, driven by strength in cloud services, payment services, and App Store subscriptions.",
            "metadata": {"category": "financial_report"}
        },
        {
            "id": "tax_2025_w2",
            "file_name": "Family_Tax_Return_2025_Verified.pdf",
            "page": 3,
            "content": "Total adjusted gross income for the fiscal year was recorded at $185,400. Deductions under mortgage interest and dependent care totaled $24,800.",
            "metadata": {"category": "tax_documents"}
        },
        {
            "id": "python_guide_p45",
            "file_name": "Python_312_Standard_Library.pdf",
            "page": 45,
            "content": "The sqlite3 module provides an SQL interface compliant with DB-API 2.0. In version 3.12, load_extension support for sqlite-vec is enabled by default.",
            "metadata": {"category": "technical_manual"}
        }
    ]
    retriever.index_documents(sample_docs)
    return {
        "status": "success",
        "indexed_count": len(sample_docs),
        "message": "VaultMind local index updated successfully."
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
