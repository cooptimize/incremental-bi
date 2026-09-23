---
title: Full history snapshot
layer: snapshots
status: draft
related:
  - Snapshots/Snapshots Overview.md
  - Snapshots/Period Snapshot.md
  - Cross-Cutting/Delete Detection Strategies.md
---

A full history snapshot retains a new version whenever the pipeline observes a record changing. Instead of overwriting the previous values, the load closes the old version's interval and appends the new one.

Use it when reports need changes between scheduled snapshots and the source does not already preserve the required history. The result is a history of observed versions; calling it a complete audit trail requires evidence that every relevant change reaches the pipeline.

## Record the version boundaries

Each version needs the record's key, the attributes being tracked, and dates identifying its interval. The load closes the previous version and opens the next as one operation so readers don't see overlapping current versions or a gap caused by a partial failure.

Decide whether the interval describes business-effective time or observation time. A correction received today may apply to last month. Assigning today's arrival time as its business start date would answer a different question.

Retries also need stable behavior. Replaying the same event should not create a second copy of the same version. The event identity and ordering rules depend on how the source exposes changes.

## The history is only as complete as the input

A reliable change feed can provide several versions between pipeline runs. A daily comparison of current-state tables sees only the state at each comparison. If a customer changes twice and returns to its earlier value before the next scan, that scan cannot reconstruct either change.

Comparing a full extract against the last observed state is still useful when that level of history meets the requirement. Be explicit about the capture interval rather than promising every intermediate state.

## Handle the end of a record

A deletion can close the final version, append a deletion marker, or require removal from retained history. These choices answer different business requirements. Define the expected query result after deletion and preserve enough information to implement it consistently. See [delete detection](../Cross-Cutting/Delete%20Detection%20Strategies.md).

High-churn tables can produce many versions, so estimate growth and test as-of queries at the intended retention period. If the requirement is only a monthly position, a [period snapshot](Period%20Snapshot.md) is usually easier to reason about.

## Still to validate

This draft needs a tested versioning load, including ordering, replay, late corrections, deletions, and interval queries. It also needs an F&O example showing why source-provided date-effective history is insufficient for the chosen requirement.
