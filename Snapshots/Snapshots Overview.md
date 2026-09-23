---
title: Snapshots — overview
layer: snapshots
status: draft
related:
  - Snapshots/Period Snapshot.md
  - Snapshots/Full History Snapshot.md
  - Cross-Cutting/Delete Detection Strategies.md
---

A snapshot preserves a state that later source changes would otherwise overwrite. Use one when a report needs to answer a historical question that current data cannot answer, such as the inventory position reported at month end.

The first step is to check whether the source already retains the required history. F&O has date-effective data for areas such as exchange rates and worker assignments. If that history answers the question, load it rather than reconstructing it from periodic observations. Also check that your extraction exposes the historical rows you need.

## Be precise about the historical question

“What rate applied on this date?” and “What rate did the report show that day?” may have different answers after a backdated correction. The first asks for business-effective history. The second asks for what the pipeline observed at the time.

That distinction determines which dates to retain and whether a later correction should change a prior result. It also prevents a current-state copy with a timestamp from being mistaken for a complete audit trail.

## Choose the capture interval

| Approach | What it preserves | Typical use |
|---|---|---|
| [Period snapshot](Period%20Snapshot.md) | State captured at scheduled intervals | Daily inventory, period-end balances, AR aging |
| [Full history snapshot](Full%20History%20Snapshot.md) | Each version the pipeline observes | Attribute history and investigation of changes between periods |

A period snapshot cannot show a change that happened and reversed between captures. A history table can preserve that change only if the pipeline receives both versions. Neither approach recreates events the source never exposed.

## Decide what to retain

Capture the grain and attributes required by the historical question. Copying every table every day adds storage and query work without necessarily preserving useful business history. For a period-end balance, a position by account and company may be the required result; for an attribute investigation, individual record versions may matter.

Define retention, correction, and deletion behavior before consumers depend on the table. A source deletion may end the current version while earlier observations remain, but the required behavior depends on what the history is meant to represent.

The snapshot articles are drafts. They still need tested load examples and an explicit treatment of late data, corrections, and source-provided history.
