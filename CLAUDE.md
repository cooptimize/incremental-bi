---
publish: false
---

# ERP Analytics Incrementals

A practitioner's reference for incremental load patterns in ERP-style analytics pipelines,
with a focus on Microsoft Dynamics 365 Finance & Operations (F&O) and the
bronze/silver/gold lakehouse architecture.

## What this is

Most documentation on ERP analytics describes the happy path. This project maps
the hard cases — deletions, watermarks, schema changes, dimension rebuilds, API
limitations — as they actually occur in practice. It is structured as a living
reference, not a finished document.

Primary stack context: F&O → Synapse/Fabric Link → bronze/silver/gold lakehouse
→ Power BI semantic model. Patterns are generalizable but examples are grounded
in this stack.

## Why this exists

- Kimball covers dimensional modeling. He does not cover "your source is a REST
  API with no delete signal and a rate limit."
- Microsoft documentation covers the happy path. It does not say when
  `modifiedDateTime` will fail you.
- Practitioner knowledge on this exists but lives in internal runbooks and
  people's heads. This project tries to make it findable.

## Structure

Each pattern gets its own file. Files link to each other where patterns interact.
This is intentionally a graph, not a linear document.

### Layers
- `Bronze/` — source extraction patterns
- `Silver/` — transformation and conforming patterns  
- `Gold/` — dimensional model load patterns
- `Semantic Model/` — Power BI semantic model patterns
- `Cross-Cutting/` — watermarks, delete detection, schema change, key management

### Status convention
Each file has a status in its frontmatter:
- `draft` — structure exists, content incomplete
- `working` — content present, not fully validated
- `stable` — validated against real implementations

## How to contribute / how I work on this

This project is built conversationally using Claude Desktop with periodic GitHub
commits. Sections get written when I have direct experience to draw on or when
I've done enough research to have a defensible position. Gaps are documented as
gaps, not papered over.

If you have scar tissue on a pattern that's wrong or missing, open an issue.

## What this is not

- Not a tutorial for beginners
- Not vendor documentation
- Not prescriptive — most of these patterns have multiple valid approaches
  depending on SLA, team, and stack maturity

## Language conventions

**Do not use Kimball SCD terminology** (SCD Type 1, SCD Type 2, etc.). These
terms are acronym-obscured and explain nothing about what the pattern actually
does. Describe the behavior directly instead:

- Instead of "SCD Type 2": use "snapshots" or describe the mechanism inline —
  when an attribute changes, the old row is retained and a new row is added
  with an effective date. See the `Snapshots/` section.
- Instead of "SCD Type 1": "overwrite in place" or "no history retained."

If a reader has to know what "Type 2" means before they can understand a
sentence, the sentence is doing it wrong.

**Before designing any snapshot or history-tracking pattern**, check whether
the source already maintains date-effective history. F&O tracks history
natively for many entities (prices, exchange rates, worker assignments,
org hierarchies). Rebuilding that history in the BI layer is unnecessary
complexity. See [Snapshots/Snapshots Overview.md](Snapshots/Snapshots%20Overview.md).

## Key concepts (start here)

- [Delete detection problem](Cross-Cutting/Delete%20Detection%20Strategies.md)
- [Watermark management](Cross-Cutting/Watermark%20Strategy.md)

## Pattern index

See [Pattern Index.md](Pattern%20Index.md) for the full list of patterns with status.
