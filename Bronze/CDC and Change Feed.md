---
title: CDC / change feed
layer: bronze
status: draft
related:
  - Cross-Cutting/Delete Detection Strategies.md
  - Cross-Cutting/Watermark Strategy.md
  - silver/incremental-with-deletes.md
---

## What this is

The source system provides a change feed — a stream of insert, update, and delete
events. Bronze consumes that feed rather than re-pulling the full table. In the
F&O context, this is primarily Synapse Link / Fabric Link with CDC enabled.

This is the cleanest bronze pattern when it's available. Deletes are signaled
explicitly; you don't have to infer them.

## When to use it

- Fabric Link or Synapse Link with CDC enabled
- Source table is large enough that full load is expensive or slow
- You need reliable delete detection without periodic full reconciliation

## When NOT to use it

- Source doesn't support a change feed (most REST APIs, flat file extracts)
- CDC infrastructure isn't set up and the table is small enough for full load
- You need point-in-time historical snapshots — CDC gives you changes, not
  a full state at every moment

## How it works

_TODO — cover Fabric Link CDC mechanics: how the feed is structured, what the
change type column looks like, ordering guarantees, latency characteristics._

## The hard parts

_TODO — cover: initial load bootstrapping (you still need a full snapshot to
start), feed gaps if the pipeline is down, handling out-of-order events,
schema changes in the feed._

## F&O specific notes

_TODO — cover: which F&O entities are supported by Fabric Link, CDC vs.
non-CDC Fabric Link behavior, known gaps or unsupported entities._

## Related patterns

- [Delete detection](../Cross-Cutting/Delete%20Detection%20Strategies.md) — CDC is one of the
  few bronze patterns that gives you reliable delete signals
- [Silver incremental with deletes](../silver/incremental-with-deletes.md) —
  downstream consumer of this pattern

## Open questions

- Which F&O entities are excluded from Fabric Link CDC?
- What happens to the change feed during a Fabric Link reset / full resync?
- Ordering guarantees: are events strictly ordered per entity, or only
  approximately ordered across entities?
