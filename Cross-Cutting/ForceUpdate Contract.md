---
title: "@ForceUpdate"
layer: cross-cutting
related:
  - Gold/Fact Audit and Repair.md
  - Gold/Dimension Patterns/Dimension Incremental Load.md
---

Every load procedure takes `@ForceUpdate INT = 0`, including the ones that ignore it. It is a calling contract, not a feature of any one pattern.

## The ladder

Three levels of trust in the change signal.

| Mode | Trusts | Means |
|---|---|---|
| `0` | the change signal | Load what the watermark or tracker says moved |
| `1` | a comparison | Ignore the change signal, compare against source, repair the differences |
| `2` | nothing | Rebuild from empty |

Nightly is `0`. Reconciliation is `1`. Repair is `2`.

## Why every procedure takes it

An orchestrator reconciling the warehouse shouldn't have to know which pattern each table uses. `@ForceUpdate = 1` means the same thing everywhere — don't trust the change signal this run — whether the target is a merged dimension, a partition-reloaded fact, or a table that always truncates.

A procedure with no incremental path still declares it:

```sql
CREATE OR ALTER PROCEDURE gold.uspLoadFactBudget
    @ForceUpdate INT = 2   -- accepted, ignored; this fact always reloads
```

That costs nothing. The alternative is an orchestrator carrying a lookup of which procedures accept which arguments, which is where the next outage comes from.

## What the modes mean per pattern

| Pattern | `0` | `1` | `2` |
|---|---|---|---|
| Dimension MERGE | update rows whose watermark moved | re-apply every matched row, keys unchanged | truncate and reload, **every surrogate key reassigned** |
| Fact date partition | reload partitions the tracker flagged | compare counts and sums, reload what disagrees | reload every partition |
| Fact open/settled | rebuild open rows and moved settled rows | same comparison | truncate and reload |
| Full load | reload | reload | reload |

## The one dangerous mode

`2` on a dimension reassigns every surrogate key and invalidates every fact pointing at it. It is a repair for a broken dimension — a natural key collision, a watermark past saving — not a reconciliation and not a routine. Reconciliation is `1`, and that is most of why `1` exists.

## Mode 1 is the instrument

Repairing tells you nothing unless you record what needed repairing. Log the partitions and magnitudes each `1` run finds, and after a few weeks that is a measured error rate per table — which is what decides whether a pattern is leaking and whether the cadence can be relaxed. See [audit and repair](../Gold/Fact%20Audit%20and%20Repair.md).
