# Error Handling & State Recovery

## Delegation Error Recovery

1. **File Agent Failures (`file-agent`)**:
   - If the folder is inaccessible or permissions are denied, halt immediately and notify the user.
   - If no valid invoices or contracts are found, report zero matches and conclude without invoking document-agent.

2. **Document Agent Failures (`document-agent`)**:
   - If a file is corrupted or unreadable, flag the file as unprocessable and continue reconciling remaining documents.
   - Do not halt the entire batch due to a single corrupted document.

3. **Knowledge Agent Failures (`knowledge-agent`)**:
   - If saving the report encounters a disk full or permission error, present the complete markdown report directly in the chat interface.
   - Never perform unverified overwrite actions on existing reports without confirmation.

4. **Tri-State Delegation Mapping**:
   - `waiting_user`: Missing folder path or ambiguous contract selection.
   - `waiting_approval`: User confirmation required before writing to disk.
   - `cancelled`: User rejects file modification or aborts operation.
   - `failed`: Terminal failure in underlying system services.
   - `completed`: Full audit completed with verified receipts.
