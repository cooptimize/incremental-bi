# Pattern index

Every pattern gets its own file. Start with [delete detection](Cross-Cutting/Delete%20Detection%20Strategies.md) and [watermarks](Cross-Cutting/Watermark%20Strategy.md) — most architectural decisions flow from those two problems. [overview.md](Overview.md) explains why there is no single answer.

Status: `draft` (structure only) | `working` (written, not validated against a real environment) | `stable` (validated).

---

## Cross-cutting

| File | Pattern | Status | Notes |
|---|---|---|---|
| `Cross-Cutting/Delete Detection Strategies.md` | Delete detection | working | Where deletions are and aren't visible. Soft flag, audit table, or reconciliation. Dimensions can hard-delete; facts usually can't. |
| `Cross-Cutting/Watermark Strategy.md` | Watermark strategy | working | `SinkModifiedOn` mechanics, control table per table, advance only on success. Cascading updates and gaps. |
| `Cross-Cutting/Partition Keys.md` | Partition keys | working | `SinkCreatedMonth` / `SinkCreatedDay` as stored columns derived from `SinkCreatedOn`. Why extraction time and never a business date. |
| `Cross-Cutting/ForceUpdate Contract.md` | `@ForceUpdate` | working | The calling contract every load procedure shares. 0 trusts the change signal, 1 trusts a comparison, 2 trusts nothing. Declared even by procedures that ignore it. |
| `Decisions/I Can't Trust modifiedDateTime.md` | I can't trust `modifiedDateTime` | working | What to rule out before concluding the timestamp is the problem. Usually a wrong column or a missing overlap buffer. |

---

## Bronze — extraction

The question: what change signal does the source provide?

| File | Pattern | Status | Notes |
|---|---|---|---|
| `Bronze/Full Load.md` | Full load | working | Truncate and reload. Deletes detectable by absence. Cost scales with table size. |
| `Bronze/CDC and Change Feed.md` | CDC / change feed | working | Source emits insert/update/delete events. Cleanest pattern where available. |
| `Bronze/Partition-Based Incremental.md` | Partition-based incremental | draft | Reload recent partitions by an immutable business date. No delete signal outside the window; needs separate reconciliation. |

---

## Silver — conforming

| File | Pattern | Status | Notes |
|---|---|---|---|
| `Silver/Full Load.md` | Full load | working | Rebuild from bronze. Use for schema changes and initial loads. Updates the change tracker after load. |
| `Silver/Incremental with Hard Delete.md` | Incremental with hard delete | working | Physically remove deleted rows. Simplifies silver, forces gold reloads. |
| `Silver/Change Tracking Partitions.md` | Change tracking partitions | working | `silver._ChangeTracker`: `MaxSinkModifiedOn` and `RowCount` per table per partition, so gold doesn't rescan sources. |

---

## Gold — dimensional model

### Dimensions

| File | Pattern | Status | Notes |
|---|---|---|---|
| `Gold/Dimension Patterns/Dimension Incremental Load.md` | Dimension incremental load | working | One MERGE. Match on business key + `DataAreaId`, update on watermark, delete what left the source. Surrogate keys from a SEQUENCE via a **default constraint** — `NEXT VALUE FOR` is not allowed inside MERGE. `NOT MATCHED BY SOURCE` must be scoped to the same company as the source or it deletes every other company. |

### Facts

Three patterns, split on one question: **can an existing fact row's values change?**

| File | Pattern | Status | Notes |
|---|---|---|---|
| `Gold/Fact Patterns/Fact Full Load.md` | Full load | working | Truncate and reload. Right more often than it looks — no delete problem, no tracker, nothing to reconcile. Measure amplification before building anything else. |
| `Gold/Fact Patterns/Fact Partition Rebuild.md` | Date partition rebuild | working | For insert/delete-only facts (posted GL, invoices). Reload whole `SinkCreatedMonth` partitions. Compares tracker watermark **and** row count against `gold._FactLoadState` — the watermark catches arrivals, the row count catches removals. |
| `Gold/Fact Patterns/Fact Open-Settled Rebuild.md` | Open/settled rebuild | working | For facts whose rows mutate after creation (InventTrans, SalesLine, CustTrans). Rebuild the whole open set each run, freeze settled rows, re-check settled rows whose watermark moved. Driven by a key list, not a partition list. |
| `Gold/Fact Audit and Repair.md` | Audit and repair | working | `@ForceUpdate = 1` for facts. Count and sum comparison by partition, rebuild only what disagrees. The only mechanism that catches a row offered to the fact and silently dropped. |

### Anti-pattern

| File | Pattern | Notes |
|---|---|---|
| `Gold/No-Load Direct Semantic.md` | No-load direct semantic | Skip gold, point Power BI at silver. Two fatal flaws: relationships stuck on string natural keys, and any fact complexity has no escape but a rebuild. |

---

## Snapshots

Before building any of these, check whether the source already keeps date-effective history. F&O does for prices, exchange rates, worker assignments and org hierarchies.

| File | Pattern | Status |
|---|---|---|
| `Snapshots/Snapshots Overview.md` | When a snapshot is the right answer | draft |
| `Snapshots/Period Snapshot.md` | State at regular intervals | draft |
| `Snapshots/Full History Snapshot.md` | Every change appended | draft |

---

## Semantic model

| File | Pattern | Status | Notes |
|---|---|---|---|
| `Semantic Model/Full Load.md` | Full refresh | working | The default. Simplest and most reliable. |
| `Semantic Model/Power BI Incremental Refresh with Deletions.md` | Incremental refresh with deletes | working | Advanced, for very large datasets. Don't partition Power BI by `SinkCreatedOn` — build a metadata layer instead. |

---

## How the choices cascade

1. **Bronze determines silver.** Full versus partition-based extraction decides whether silver can detect a delete at all.
2. **Silver determines gold cost.** Hard delete lets gold hard-delete; soft delete puts a filter in every downstream query forever.
3. **Every pattern either accepts a delete gap or pays to close it.** Know which one you chose before it gets discovered during an audit.

---

## Known gaps

- No DirectQuery or Direct Lake coverage — everything assumes an import semantic model.
- No measured amplification numbers from a real environment.
- Articles link to seven files that were never written: `cross-cutting/hash-comparison.md`, `cross-cutting/layer-strategy-mismatch.md`, `silver/schema-drift.md`, `silver/incremental-with-deletes.md`, `decisions/source-has-no-delete-signal.md`, `gold/incremental-aggregate-recalc.md`, `semantic-model/incremental-period.md`. Write them or drop the links.

## Removed and consolidated

- `facts/incremental-load.md` → split 2026-09-06 into `Gold/Fact Patterns/Fact Partition Rebuild.md` and `Gold/Fact Patterns/Fact Open-Settled Rebuild.md`
- `facts/partition-based-incremental-load.md`, `facts/watermark-based-load.md`, `facts/full-load.md` (old) → folded into the fact patterns above
- `force-update-modes.md` → restored as `Cross-Cutting/ForceUpdate Contract.md`
- `surrogate-key-management.md` → in `Gold/Dimension Patterns/Dimension Incremental Load.md`
- `dimension-rebuild-cascade.md`, `incremental-with-key-drift.md`, `incremental-aggregate-recalc.md`, `late-arriving-facts.md` → covered by the patterns above
- `INDEX-1.md` → merged into this file 2026-09-06
