---
title: I can't trust modifiedDateTime. What do I do?
layer: cross-cutting
status: working
related:
  - Cross-Cutting/Watermark Strategy.md
  - cross-cutting/hash-comparison.md
  - Cross-Cutting/Delete Detection Strategies.md
  - Gold/Dimension Patterns/Dimension Incremental Load.md
  - silver/schema-drift.md
---

## What this is

A decision guide for the moment you discover — usually via a manual reconciliation, an angry stakeholder, or a diff against source — that rows changed in the source but your gold layer didn't pick it up, even though your watermark logic looks correct. This walks through what to check before reaching for a bigger hammer, and what to reach for when the timestamp genuinely can't be trusted.

## When to use it

- Gold data is stale for rows that should have been caught by an incremental load, and the pipeline reports success (no errors, watermark advanced).
- You're seeing this repeatedly for the same class of change (e.g., always after a specific type of edit), not as a one-off.
- You've already ruled out a hard failure (the pipeline actually erroring, a stuck watermark, a truncated load) — this is about correct-looking pipelines producing wrong results.

## When NOT to use it

- The pipeline is actually failing or the watermark isn't advancing — that's an operational bug, not a change-detection problem. Fix the bug first.
- You haven't confirmed the specific rows and specific change that were missed. Don't add hash comparison speculatively; find the actual gap first.
- The gap is a delete, not an update — that's `Cross-Cutting/Delete Detection Strategies.md`, a related but distinct problem (the row didn't change, it disappeared, which a timestamp-based watermark can't signal at all regardless of reliability).

## How it works

**Step 1: Confirm it's actually a change-detection problem, not a watermark logic bug.**

Before concluding the timestamp itself is untrustworthy, rule out the cheaper explanations:
- Wrong column: are you watermarking on a row-modification timestamp when you need a transaction-level date (posting date, invoice date), or vice versa? See `Cross-Cutting/Watermark Strategy.md`'s note on `SinkModifiedOn` vs. `modifiedDateTime` — these answer different questions and using the wrong one looks exactly like "the watermark doesn't work."
- Clock skew or missing overlap buffer: was the missed row modified right at the watermark boundary?
- Off-by-something in the comparison: `>` vs. `>=`, timezone mismatch between stored watermark and source timestamp.

Most "the watermark is unreliable" reports turn out to be one of these, not a fundamental limitation of timestamp-based detection. Fix these first — they're cheaper and don't add a second mechanism to maintain.

**Step 2: If the timestamp genuinely doesn't move on the change you need, identify why.**

Two distinct causes, per `Cross-Cutting/Watermark Strategy.md`:
- Cascading change: a related record changed, but the record you're watermarking on didn't get its timestamp bumped.
- Semantic/enum drift: a value's *meaning* changed (e.g., a status code was redefined) without any row being written at all. See `silver/schema-drift.md`.

**Step 3: Choose a fallback based on what Step 2 revealed.**

- **Cascading changes, isolated to specific known relationships:** Consider watermarking on the *child* table's timestamp instead of (or in addition to) the parent's, if the child is what's actually changing. Cheaper than hash comparison if it's structurally available.
- **Genuinely invisible changes (no timestamp moves anywhere):** Reach for [row-hash comparison](cross-cutting/hash-comparison.md), bounded to a recency window or reconciliation cadence rather than run on every incremental cycle.
- **Change signal is unreliable across the board and native CDC is available:** Prefer a native change feed (Fabric Link CDC — see `Bronze/CDC and Change Feed.md`) over building hash comparison on top of an unreliable source. This is a bronze-layer decision, not something gold can fully fix on its own — flag it upstream.
- **None of the above, or the entity is small:** A full reload on a schedule (nightly, weekly) that doesn't depend on any change signal may be cheaper than engineering around the problem. See `gold/dimension-patterns/full-load.md`.

## The hard parts

Hash comparison is a fallback with real, ongoing cost (see `cross-cutting/hash-comparison.md`'s hard parts) — it is not a free upgrade over a watermark. The most common actual fix, in practice, turns out to be Step 1: a wrong column or a missing overlap buffer, not a missing detection mechanism. Resist reaching for hash comparison as a first move; it adds a second thing to maintain (the hashed-column list) that silently goes stale exactly the same way the original timestamp did.

## F&O specific notes

See `Gold/Dimension Patterns/Dimension Incremental Load.md`'s "Change detection at silver" note and `Cross-Cutting/Watermark Strategy.md` for the specific F&O failure modes (cascading changes not bumping `modifiedDateTime`, `SinkModifiedOn` measuring export time rather than business change time). No catalogue of specific F&O entities known to have this problem exists yet in this project — add to it as they're found.

## Related patterns

- [Watermark management](../Cross-Cutting/Watermark%20Strategy.md) — What you're diagnosing as unreliable; read this first.
- [Row-hash change detection](cross-cutting/hash-comparison.md) — The fallback mechanism this guide routes to.
- [The delete detection problem](../Cross-Cutting/Delete%20Detection%20Strategies.md) — Related but distinct: a row disappearing, not a row changing silently.
- [Schema drift](silver/schema-drift.md) — Semantic/enum drift as a specific cause.

## Open questions

- Is there a way to detect that a watermark has "gone silent" on a specific change type proactively, rather than discovering it via manual reconciliation after the fact?
- What's a reasonable default reconciliation cadence (hash comparison pass) for tables known to have unreliable timestamps — daily, weekly?
- How do you decide between "watermark on the child table instead" vs. "add hash comparison" when both are structurally possible? Is there a cost/complexity rule of thumb?
- Has this project ever actually needed hash comparison in production, or has every real incident so far been a Step 1 (watermark logic) fix?
