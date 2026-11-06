# VaultMind Architecture Specification

## Local Sandboxed Execution
VaultMind runs entirely on the local UGOS runtime without external network calls.

### Core Modules
1. **Directory-Aware Hierarchical Parser**: Preserves multi-level table of contents and sections before chunking.
2. **Hybrid In-Memory Indexer**: Integrates local lightweight vector embeddings with SQLite-vec and BM25Okapi.
3. **Budget Guard**: Limits single tool context delivery to 48 KiB to prevent local LLM context overflow.
