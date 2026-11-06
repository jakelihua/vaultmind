# Reconciliation Business Specification

## Core Business Logic

1. **Document Pairing**:
   - Matches invoice documents to contracts by Vendor Name, Tax ID, or Explicit Agreement Reference number.
   - Requires exact ISO 4217 currency match (e.g., USD to USD). Currency conversions are flagged for manual review.

2. **Numerical Variance Calculation**:
   - `Variance = Billed Amount - Agreed Amount`
   - Accounts for net amounts vs gross amounts based on explicitly stated tax terms.
   - Any absolute variance greater than $0.00 is flagged as a `Discrepancy`.

3. **Coverage & Missing Source Handling**:
   - If an invoice has no corresponding contract in the authorized folder, it is flagged as `Needs Review`.
   - The system never fabricates or assumes missing contract terms.

4. **Approval & Replay Boundary**:
   - All write operations require user consent.
   - Re-running reconciliation on the same directory yields deterministic results and avoids overwriting without confirmation.
