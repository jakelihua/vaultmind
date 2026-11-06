# Error States & Self-Healing SOP

## Tri-State Recovery
1. **TRANSIENT_SYSTEM_BUSY**: Automatically retries with exponential backoff (1s, 2s).
2. **DEADLINE_EXCEEDED**: Concludes gracefully with partial verified knowledge; explicitly advises user of unfinished scopes without hallucinating.
3. **DOCUMENT_NOT_FOUND**: Prompts user for directory re-indexing or permission scope adjustment.
