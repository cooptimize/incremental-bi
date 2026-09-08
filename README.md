# Incremental BI Patterns

A practitioner's reference and team knowledge base for incremental load patterns in ERP-style analytics pipelines, with a focus on Dynamics 365 Finance & Operations (D365FO) into lakehouse architectures (Fabric, Synapse, Databricks) and Power BI.

The vault is structured as an Obsidian-compatible graph of markdown notes, linked by topic and layer rather than linear documentation. It also serves as a shared team repository for [teamai-cli](https://github.com/tencent/teamai) and the [Coop agent](https://github.com/cooptimize/coop-agent).

## Vault Structure

Patterns are organized into seven primary layers:

- **`Bronze/`** - Source extraction patterns (CDC, change feed, partition-based full loads).
- **`Silver/`** - Conforming, deduplication, and cleansing patterns (hard delete handling, change tracking).
- **`Gold/`** - Dimensional model loads (`Gold/Dimension Patterns/`, `Gold/Fact Patterns/`, and anti-patterns).
- **`Cross-Cutting/`** - Shared contracts and mechanics (watermark strategies, ForceUpdate contracts, partition keys).
- **`Decisions/`** - Architectural decisions framed around real trade-offs and constraints.
- **`Semantic Model/`** - Power BI refresh and Direct Lake modeling patterns.
- **`Snapshots/`** - Periodic snapshotting and historical tracking patterns.
- **`learnings/`** - Field discoveries, bug fixes, and session learnings contributed by engineers and agents.
- **`skills/` & `rules/`** - Team-shared skills and operational rules consumed by AI tooling.

For an index of all patterns organized by status and layer, see [`Pattern Index.md`](Pattern%20Index.md). For high-level architectural concepts, see [`Overview.md`](Overview.md) and [`Why Deletions Are Hard.md`](Why%20Deletions%20Are%20Hard.md).

## Authoring and Style Guidelines

When adding or updating patterns, adhere to the principles in [`STYLE.md`](STYLE.md):

1. **Narrative first, then code.** Explain the step in 1 - 2 direct sentences, then provide the snippet that proves it.
2. **Cap code blocks at ~10 lines.** Break long queries into separate logical steps (source rollup, predicate, assembly).
3. **Use real F&O objects.** Name actual tables and fields (`CustTable`, `SalesTable`, `GeneralJournalEntry`).
4. **No Kimball SCD jargon.** Describe the actual data mechanics ("snapshot table", "overwrite in place") rather than textbook terms like "SCD Type 2".
5. **Direct language without hedging.** State assumptions and failure modes plainly without filler phrases or speculation.

### Pattern Frontmatter

Every pattern under the seven layer folders requires YAML frontmatter:

```yaml
---
title: Pattern Title
layer: bronze | silver | gold | cross-cutting | decisions | semantic-model | snapshots
status: draft | working | stable
related:
  - Relative/Path/To/Related Pattern.md
---
```

Every referenced path in `related:` must exist on disk. Every new or renamed pattern must also have a row in [`Pattern Index.md`](Pattern%20Index.md).

## Contributing Learnings

Engineers and agents capture day-to-day field solutions in `learnings/`:

- In the Coop terminal agent: run `/share-learning` to draft a standardized learning note.
- Learnings use frontmatter with `title`, `author`, `date` (YYYY-MM-DD), `tags`, and an `x-coop:` metadata block.
- **Guardrails:** Always scrub client names, connection strings, and credentials. Set `sensitivity: internal`.
- **Review:** All contributions are submitted via pull request to `main` for review. Never commit directly to `main`.

## Validation

Run the vault validator locally before opening a PR:

```bash
python3 scripts/validate_vault.py
```

This verifies frontmatter fields, valid layers and statuses, resolution of `related:` links, `Pattern Index.md` coverage, and `teamai.yaml` integrity.
