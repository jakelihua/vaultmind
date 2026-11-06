# Project Disclosures & Third-Party Attributions

## 1. AI Tool Usage & Primary Responsibilities

In compliance with Devpost competition rules, the following AI tools assisted during the development of VaultMind:
- **Claude / Anthropic & Gemini / Google DeepMind**: Used for architecture design review, test fixture generation, and markdown documentation formatting.
- **UGOS Skill Creation Tool (`uliya-skill-kit-0.7.3`)**: Official UGREEN toolchain used for schema verification and static validation.

All core domain logic, reconciliation specifications, state recovery machines, and integration code were authored, verified, and debugged by the entrant during the hackathon period.

## 2. Third-Party Components & Licenses

- **Rank BM25**: Pure-Python implementation of BM25Okapi scoring algorithm (MIT License).
- **FastMCP & Model Context Protocol SDK**: Standard interface definitions by Anthropic (MIT License).
- **ReportLab**: Open-source PDF generation engine used for document output (BSD License).
- **Pydantic & FastAPI**: Web schema validation and local HTTP server foundation (MIT License).

No proprietary enterprise code, undisclosed commercial SDKs, or closed APIs are included or required.

## 3. Core Capabilities Developed During This Hackathon

- **Multi-Expert Contract-to-Invoice Orchestration**: Chaining `file-agent`, `document-agent`, and `knowledge-agent` for end-to-end month-end reconciliation.
- **Reconciliation Receipt Protocol**: Markdown audit receipt with page-level citations, variance calculations, and missing contract detection.
- **Human Approval Gate**: Strict confirmation boundary ensuring no files are written without explicit user authorization.

## 4. Execution Boundary

The Uliya Skill package (`vaultmind-reconcile`) executes strictly through official native expert agents registered in the UGOS system. The separate Python prototype repository (`vaultmind`) provides standalone reference tests and is not required for running the Uliya Skill on target NAS hardware.
