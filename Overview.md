---
title: Overview
---

# ERP Analytics Incrementals

Incremental loading reduces repeated work by processing the data that needs attention. In an ERP pipeline, identifying that data is often harder than loading it: a row can disappear, a related table can change, or a correction can arrive in a period the load no longer reads.

This project explains patterns for those cases, using Dynamics 365 Finance & Operations and a bronze/silver/gold pipeline feeding an imported Power BI semantic model. Each article describes an approach, the assumptions it needs, and the work it leaves for downstream loads or reconciliation.

## Each layer has a different job

**Bronze extracts the source.** Its options depend on what the source exposes: a complete population, timestamp-filtered rows, date slices, or a change feed. If a deletion is invisible here, downstream transformations cannot recover it from the incoming rows alone.

**Silver maintains usable, conformed data.** It handles source types, keys, duplicates, and the representation of deleted records. A current-state table can remove rows, while a history requirement needs a different retention design.

**Gold builds the reporting model.** Facts and dimensions combine silver inputs, resolve surrogate keys, and expose business-facing names and grain. A changed source row must be mapped to the output rows or partitions that need recomputing.

**The semantic model serves the reports.** It adds measures, relationships, security, and its own refresh lifecycle. Updating gold does not automatically update an imported copy of an old partition.

For example, removing an old transaction from silver fixes silver's current state. Gold must still replace the affected result, and Power BI must reread it before the report reflects the deletion.

## Choose the pattern from the data's behavior

Three questions help narrow the choice:

- **How are deletions discovered?** An event, a retained flag, and a complete key comparison provide different coverage and costs.
- **How long can records change?** An old inventory transaction may still be open. A date window and an open/settled split select different work.
- **How do input changes affect output?** One-to-one loads can often replace by key. Joins and aggregates need a mapping from changed inputs to affected results.

Then measure whether a full load fits the window. If it does, incremental state and recovery logic may cost more to maintain than the repeated work they save. If it doesn't, select the smallest reliable unit of replacement for the actual workload.

## Reconciliation checks what the change signal misses

An incremental job can succeed while producing an incomplete result. A late dimension member may cause a join to drop a transaction, or a change may arrive behind the saved watermark.

Reconciliation compares the loaded result with what should be present, independently of the normal selection. Record the discrepancies before repairing them so you can assess the detection strategy and repair schedule. Agreement between gold and silver is useful, but it does not prove that silver captured every source change.

## Scope and maturity

These articles focus on import semantic models; DirectQuery and Direct Lake are not yet developed here. Performance arguments describe where work occurs, rather than reporting benchmark results from a measured environment.

`draft` articles retain unfinished implementation work. `working` articles describe approaches that still need validation in a real implementation. Several articles have no status label; that should not be read as evidence of validation. The snapshot patterns are exploratory, and source-provided history should be checked before building new history capture.

Start with the [pattern index](Pattern%20Index.md) for the available choices, [why deletions are hard](Why%20Deletions%20Are%20Hard.md) for the cross-layer problem, or [watermark strategy](Cross-Cutting/Watermark%20Strategy.md) for load boundaries. The [@ForceUpdate contract](Cross-Cutting/ForceUpdate%20Contract.md) connects routine loads, reconciliation, and rebuilds.
