import os
from pydantic import BaseModel

class VaultConfig(BaseModel):
    # Data & Storage
    data_dir: str = os.getenv("VAULTMIND_DATA_DIR", "./data")
    nas_mount_path: str = os.getenv("UGOS_NAS_MOUNT_PATH", "/ugos/storage")
    
    # RAG Context & Budget Constraints
    max_context_bytes: int = int(os.getenv("VAULTMIND_MAX_CONTEXT_BYTES", str(48 * 1024))) # 48 KiB
    document_window_chars: int = int(os.getenv("VAULTMIND_WINDOW_CHARS", "12000"))
    relative_score_ratio: float = float(os.getenv("VAULTMIND_RELATIVE_SCORE_RATIO", "0.9"))
    
    # Retrieval Tuning
    default_top_k: int = int(os.getenv("VAULTMIND_TOP_K", "6"))
    rrf_k: int = int(os.getenv("VAULTMIND_RRF_K", "60"))
    
    # Server
    api_port: int = int(os.getenv("PORT", "8080"))
    api_host: str = os.getenv("HOST", "0.0.0.0")

settings = VaultConfig()
