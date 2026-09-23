---
title: "@ForceUpdate"
layer: cross-cutting
related:
  - Gold/Fact Audit and Repair.md
  - Gold/Dimension Patterns/Dimension Incremental Load.md
---

Every load procedure accepts `@ForceUpdate`, so the orchestrator can request a routine load, reconciliation, or a rebuild through the same interface. Each pattern implements those modes according to what it needs to preserve.

Incremental procedures default to `0`. A procedure that always reloads can accept the parameter without changing its behavior. The caller does not need a separate list of which procedures support which arguments.

## The three modes

| Mode | Purpose | What it relies on |
|---|---|---|
| `0` | Routine incremental load | The watermark or change tracker identifies the work. |
| `1` | Reconciliation and repair | A source comparison or reapplication bypasses the normal change signal. |
| `2` | Rebuild the requested scope | The target is recreated from its inputs. |

Mode `1` can repair data too; mode `2` is not a synonym for every repair. Choose the mode based on the work required, not on whether the job runs nightly or monthly.

A caller can use the same parameter for each operation. These calls illustrate the interface for the customer load described in the [dimension article](../Gold/Dimension%20Patterns/Dimension%20Incremental%20Load.md):

```sql
EXEC gold.uspLoadDimCustomer @DataAreaId = 'USMF', @ForceUpdate = 0;
EXEC gold.uspLoadDimCustomer @DataAreaId = 'USMF', @ForceUpdate = 1;
```

Run the reconciliation call when required; the two calls are examples, not a required sequence.

## What each pattern does

| Pattern | `0` | `1` | `2` |
|---|---|---|---|
| Dimension | Update changed members and handle arrivals/removals | Reapply attributes while keeping existing keys | Recreate members and assign new keys |
| Fact partition rebuild | Replace flagged partitions | Compare against expected output and replace discrepancies | Replace every partition in scope |
| Fact open/settled rebuild | Replace open rows and changed settled rows | Compare and repair independently of the routine selection | Rebuild the fact scope |
| Full load | Reload | Reload | Reload |

The procedure must define its scope. A company-specific rebuild clears and reloads that company; a whole-table truncate requires a whole-table reload. Mode `2` must not accidentally remove data outside the caller's requested scope.

## Dimension rebuilds require fact recovery

Recreating dimension members can assign different surrogate keys. Existing facts still hold the previous values, so dimension and fact recovery must be coordinated before reports use the rebuilt data. Reapplying attributes with mode `1` avoids that key change and is the normal response to stale dimension attributes.

A rebuild also cannot recover data missing from its input. If silver missed a source deletion, rebuilding gold from silver reproduces the same error. Reconcile at the layer where the gap originates.

## Keep the evidence from reconciliation

Record the partitions or rows that differed before repairing them, along with counts or measure deltas. That tells you how much drift the routine load is leaving and whether the reconciliation schedule is adequate.

An unconditional dimension reapplication does not measure how many values were wrong unless it also compares or logs them. Likewise, a clean count-and-sum check establishes agreement only for the measures checked. See [fact audit and repair](../Gold/Fact%20Audit%20and%20Repair.md).
