---
title: Fact audit and repair
layer: gold
related:
  - Gold/Fact Patterns/Fact Partition Rebuild.md
  - Gold/Fact Patterns/Fact Open-Settled Rebuild.md
---

`@ForceUpdate = 1` for facts. Compare gold to silver at partition grain, rebuild only the partitions that disagree. The three modes are levels of trust in the change signal: `0` trusts the tracker, `1` trusts a comparison, `2` trusts nothing.

## Why it exists

No watermark scheme catches a row that was offered and silently dropped. If a row was present in silver but the fact's join dropped it — a dimension member that didn't exist yet — the load still succeeds and the watermark advances past it, whether that watermark is derived from gold or stored in a control table. The row is never reconsidered. Counting is the only mechanism that finds it.

## Two aggregates

What gold holds, by partition:

```sql
SELECT SinkCreatedMonth, COUNT(*) AS Rows, SUM(Amount) AS Amount
FROM gold.FactInventTrans
GROUP BY SinkCreatedMonth;
```

What the source holds, same grain:

```sql
SELECT SinkCreatedMonth, COUNT(*) AS Rows, SUM(CostAmountPosted) AS Amount
FROM silver.InventTrans
GROUP BY SinkCreatedMonth;
```

Two scans, no join until the small result sets, and the cost doesn't depend on how diffuse the changes were.

## The comparison

Count catches rows lost or duplicated. Sum catches values that drifted.

```sql
SELECT COALESCE(g.SinkCreatedMonth, s.SinkCreatedMonth) AS SinkCreatedMonth
INTO #Discrepant
FROM GoldState g
FULL OUTER JOIN SourceState s ON s.SinkCreatedMonth = g.SinkCreatedMonth
WHERE g.Rows IS NULL OR s.Rows IS NULL
   OR g.Rows <> s.Rows
   OR g.Amount <> s.Amount;
```

## Repair

Delete gold where `SinkCreatedMonth` is discrepant, reload the source for the same partitions. `SinkCreatedMonth` is immutable, so this works for both fact patterns even though open/settled loads by key. Repair is idempotent, so a false positive costs compute and nothing else.

## Unknown members are what make this usable

If the fact's inner joins drop rows with missing dimension members, gold's count is legitimately lower than the source's and every partition looks discrepant forever. Route unmatched keys to an unknown member instead and the counts match exactly — then any difference is a real defect. That is the practical argument for unknown members: without them this check is noise, with them it is an instrument.

## Log the deltas

Write each run's discrepant partitions and their magnitude to a table. After a few weeks that is a measured error rate per fact, which tells you whether the incremental is leaking and whether the reconciliation cadence can be relaxed. A repair that silently overwrites teaches you nothing.

## Blind spots

- **Non-additive attributes.** A status flag or dimension key that changed without moving count or sum passes clean. `SUM(CAST(BINARY_CHECKSUM(...) AS BIGINT))` catches most of it, probabilistically.
- **Repointed tables lose repair granularity.** If every row shares one partition, the check still works but the repair is a whole-table rebuild.
- **Gold is compared to silver.** If silver missed a delete from bronze, the two agree and the audit passes while both are wrong. That is what `@ForceUpdate = 2` and source reconciliation are for.
