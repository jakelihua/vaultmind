# Reconciliation Receipt Format

The Reconciliation Receipt is a structured markdown artifact presented to the user upon completing invoice-to-contract analysis. It serves as both the conversational approval preview and the persistent audit document saved to the NAS.

## Receipt Structure

```markdown
# Monthly Reconciliation Receipt
Date: YYYY-MM-DD
Target Directory: <authorized_folder_path>

## Summary Statistics
- Files checked: 5
- Discrepancies: 1
- Needs review: 1
- Matches verified: 3

## Line Item Audit Table
| Invoice ID | Contract Ref | Billed Amount | Agreed Amount | Variance | Tax Basis | Status | Source Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| INV-2025-1102 | AGR-2025-04 | USD 2,640.00 | USD 2,400.00 | +USD 240.00 | Net Exclusive | Discrepancy | Invoice Page 1 / Contract Sec 4.1 |
| INV-CLOUD-9941 | None | USD 350.00 | — | — | Tax Exempt | Needs Review | Not found within reviewed files |
| INV-2025-1108 | AGR-2025-09 | USD 1,200.00 | USD 1,200.00 | USD 0.00 | Net Exclusive | Match | Invoice Page 1 / Contract Sec 3.2 |

## Status States
- `Awaiting approval`: Displayed in chat UI awaiting explicit user confirmation.
- `Saved`: Persisted to NAS storage following tool confirmation receipt.
- `Cancelled`: User rejected save action; storage remains unmodified.
- `Save failed`: Downstream agent reported storage error; raw markdown displayed to user.
```
