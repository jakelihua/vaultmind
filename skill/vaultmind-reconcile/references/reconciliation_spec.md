# Reconciliation Business Specification

## Core Business Logic & 3-Way Audit Taxonomy

1. **Strict 3-Way Classification**:
   - **`Match`**: Bilateral evidence located in both contract and invoice; billing period, currency code, and tax basis match; numerical variance is exactly USD 0.00.
   - **`Discrepancy`**: Bilateral evidence located in both contract and invoice; billing period, currency code, and tax basis match; numerical variance is non-zero (e.g., USD +240.00).
   - **`Needs Review`**: Any prerequisite is missing or ambiguous (e.g., no matching contract found within reviewed files, currency mismatch, unverified tax basis, or unreadable scan). In all `Needs Review` cases, **the numerical variance is left blank (`—`)** rather than calculated from incomplete data.

2. **Coverage & Missing Source Handling**:
   - When an invoice cannot be tied to an agreement for the billing period, it is classified as `Needs Review` with missing evidence explicitly noted.
   - Uncontracted invoices or batches containing only invoices naturally fall into `Needs Review`.
   - If candidate search reached the 50-file limit, missing contracts are described specifically as "not found within reviewed files" to avoid claiming non-existence beyond the inspected boundary.

3. **Numerical Variance Calculation**:
   - `Variance = Billed Amount - Agreed Amount` (only computed when bilateral evidence is verified).
   - Accounts for net vs gross amounts based on explicitly stated tax terms (net exclusive vs tax inclusive).

4. **Approval & Replay Boundary**:
   - All disk write operations require explicit human approval before execution.
   - Re-running reconciliation on the same directory inspects existing reports and asks for confirmation before updating, preventing unconfirmed overwrites.
