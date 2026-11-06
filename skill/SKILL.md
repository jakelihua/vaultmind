---
name: vaultmind-knowledge-agent
description: Ultra-private local knowledge base, self-healing RAG, and automated file organization agent running on UGREEN AI NAS. Orchestrates document indexing, directory-aware chunk merging, citation isolation, and autonomous storage housekeeping.
---

# VaultMind: Private AI Knowledge & Workflow Skill

VaultMind is an industrial-grade local AI Skill engineered for the UGREEN AI NAS and UGOS Pro ecosystem (powered by the Uliya local AI engine). It delivers 100% offline, zero-data-leakage document intelligence and automated file curation.

## 🎯 User Goals & Capabilities
1. **Zero-Leakage Local RAG**: Index and query sensitive documents (tax forms, legal contracts, proprietary code, personal finance) strictly within the local NAS storage.
2. **Self-Healing Retrieval**: Employs dynamic relative thresholding (`0.9x TopScore`) and sliding window expansion to eliminate hallucinations and truncated answers.
3. **Automated File Organization**: Intelligently identifies misplaced downloads, extracts metadata, tags items, and moves files into organized directory trees.
4. **Citation Isolation (`[S1..Sn]`)**: Strips raw system paths and UUIDs from model context, presenting clean verifiable references while retaining verified pointers in the local registry.

## 🤖 Agent Delegation Architecture
VaultMind operates via pure agentic orchestration, coordinating with UGREEN UGOS built-in expert agents:
* **`knowledge-agent`**: Executes local hybrid vector + BM25 keyword recall with Reciprocal Rank Fusion (RRF). See [retrieval_rules.md](references/retrieval_rules.md).
* **`document-agent`**: Performs directory-aware hierarchical parsing and sliding window extraction on PDFs, Word, Markdown, and tabular files. See [architecture.md](references/architecture.md).
* **`file-agent`**: Inspects file system events, generates semantic directory trees, and applies safe batch file operations with user approval gates.

## 🔄 Core Workflow Execution

```
[User Query / File Ingestion Event]
         │
         ▼
[VaultMind Orchestrator]
         │
         ├──> Step 1: Pre-process & Deduplicate Sub-Queries
         ├──> Step 2: Delegate to `knowledge-agent` for Local Hybrid Recall (RRF)
         ├──> Step 3: Apply Relative Threshold Filter (0.9x Cutoff)
         ├──> Step 4: Enforce 48 KiB Strict Context Byte Budget
         ├──> Step 5: Format Verified Passages with [S1..Sn] Short Labels
         └──> Step 6: Generate Verified Local Answer or Trigger `file-agent` Action
```

For complete technical specifications and error recovery states, consult:
* [Architecture & Data Flow](references/architecture.md)
* [Retrieval & Citation Rules](references/retrieval_rules.md)
* [Error States & Self-Healing SOP](references/error_handling.md)
