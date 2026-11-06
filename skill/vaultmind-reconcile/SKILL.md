---
name: vaultmind-reconcile
description: Use when users need to reconcile invoices against contracts in an authorized NAS directory, identify billing discrepancies, and save verified audit reports.
---

# Goal

Verify invoice billing items against authorized contract terms, calculate numerical variances, flag missing source documents, and persist a verified markdown reconciliation receipt upon user confirmation.

# Required input

- Authorized folder path containing invoices and contracts
- User confirmation before writing any final review report

# Generation-time capability evidence

- `ug-filesystem` → `file-agent`
- `ug-document` → `document-agent`
- `ug-knowledge` → `knowledge-agent`

# Orchestration

Execute the multi-expert pipeline sequentially. Downstream steps must consume only real upstream results returned by preceding agents.

## Step 1: Discover documents

Delegate directory inspection to `file-agent` calling action `ug-filesystem find`:

`delegate --target file-agent --instruction 'Find contract and invoice documents within the user-authorized folder, matching supported document extensions without traversing beyond the specified scope.'`

The search scans candidate files matching supported extensions up to a maximum limit of 50 documents to prevent unconstrained traversals. If no results or zero matches are found, report the empty result to the user and stop execution immediately without querying unrelated directories.

## Step 2: Cross-examine line items

Pass real upstream file paths to `document-agent` calling action `ug-document reconcile`:

`delegate --target document-agent --instruction 'Extract contract terms and invoice items from the discovered document paths, reconcile payable totals, currency codes, and tax rates, and return structured discrepancies.'`

When a contract reference is missing or amounts diverge, mark the entry as needs review. Distinguish individual line-item statuses (verified, discrepancy, needs review) from agent delegation statuses.

## Step 3: User approval and report archiving

Present the markdown Reconciliation Receipt preview and target save location to the user. Details of the receipt structure are documented in [receipt_format.md](references/receipt_format.md). Business matching rules, error recoveries, and project compliance disclosures are detailed in [reconciliation_spec.md](references/reconciliation_spec.md), [error_handling.md](references/error_handling.md), and [disclosures.md](references/disclosures.md).

Only after explicit user confirmation, delegate saving to `knowledge-agent` calling action `ug-knowledge save-text`:

`delegate --target knowledge-agent --instruction 'Save the verified reconciliation receipt markdown content to the authorized audit report path.'`

# Completion and failure

Handle all delegation states across the workflow:

- `completed`: Upstream expert successfully returned verified business results. Proceed to downstream step or present final receipt.
- `failed`: Upstream expert returned an execution error. Halt dependent tasks, preserve partial findings, and explain the error to the user without retrying non-idempotent operations.
- `cancelled`: User cancelled execution during document discovery or reconciliation. Stop all background tasks and do not create or modify files.
- `waiting_user`: Required parameters such as the directory path or contract identification are ambiguous. Prompt the user for clarification before delegating further.
- `waiting_approval`: Pending user confirmation for saving the reconciliation receipt to disk. If user rejects, leave storage untouched and mark status as cancelled.
