---
title: CDC / change feed
layer: bronze
status: draft
related:
  - Cross-Cutting/Delete Detection Strategies.md
  - Cross-Cutting/Watermark Strategy.md
  - Silver/Incremental with Hard Delete.md
---

A change feed gives bronze insert, update, and delete events instead of requiring a complete extraction on every run. An explicit delete event is particularly useful: it identifies the missing record while its key is still available.

Use this approach when the source exposes a suitable feed and processing changes saves enough work to justify checkpointing and recovery. A feed can carry changes for a history table as well as a current-state table; what bronze retains determines which downstream uses remain possible.

## Start from a known state

The consumer needs an initial snapshot and a feed position from which to continue. Those two must agree: a gap between the snapshot and the first consumed event can lose changes, while overlap requires safe replay.

After that, each run reads a bounded batch, applies it, and records the checkpoint only after success. Reprocessing a batch should produce the same result. For a current-state target, an older update must not overwrite a newer value simply because it arrived later.

The exact sequence field, ordering guarantees, and checkpoint mechanism belong to the source's feed contract. A timestamp alone should not be assumed to provide all three.

## Understand the export you're consuming

For F&O, Synapse Link supports create, update, and delete propagation, but a queryable current-state export and incremental change files are different inputs. Microsoft documents deletion metadata and the available export options in [Choose finance and operations data](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/azure-synapse-link-select-fno-data).

Confirm what your configured path exposes before implementing the consumer. A service applying deletes to its own table does not automatically mean your downstream job receives a durable log of every deleted key.

## Plan for replay and gaps

A consumer that falls behind must be able to resume from retained events. If the required events have expired, it needs a new baseline rather than guessing where to restart. Schema changes and reinitialization also need explicit handling so an apparently successful restart doesn't skip part of the data.

Reconciliation remains useful even with a feed. It checks whether the consumer applied what the source delivered and whether downstream transformations preserved the intended result.

## Still to validate

This draft does not yet provide a tested F&O consumer. It needs the selected export mode, event schema, ordering and retention guarantees, bootstrap sequence, and behavior during a link reset. Entity support also needs checking against the actual environment.

See [silver incremental with hard delete](../Silver/Incremental%20with%20Hard%20Delete.md) for the current-state destination and [full history snapshots](../Snapshots/Full%20History%20Snapshot.md) for retaining observed versions.
