# AGENTS.md

Guidance for AI contributors working in this knowledge vault. Read `CLAUDE.md`,
`STYLE.md`, and `Pattern Index.md` before writing or editing patterns.

## What this repo is

An Obsidian-style vault of incremental-load BI patterns for D365 F&O to
bronze/silver/gold lakehouse to Power BI. It is a graph of linked pattern files,
not a linear document. It is also a teamai-cli team knowledge repo (`teamai.yaml`).

## Folder layers and what belongs in each

- `Bronze/` — source extraction patterns (full load, CDC, partition-based).
- `Silver/` — transformation and conforming patterns (hard delete, change tracking).
- `Gold/` — dimensional model loads; `Gold/Dimension Patterns/` for dimensions,
  `Gold/Fact Patterns/` for facts, plus gold-level anti-patterns.
- `Cross-Cutting/` — concerns shared across layers: watermarks, delete detection,
  partition keys, the `@ForceUpdate` contract.
- `Decisions/` — decision records framed as the question a practitioner asks.
- `Semantic Model/` — Power BI refresh patterns.
- `Snapshots/` — snapshot and history-tracking patterns.
- `learnings/` — session learnings contributed via teamai (see below).
- `skills/`, `rules/` — teamai shared skills and rules.

## Authoring conventions

- One pattern per file. Link related patterns; do not merge them.
- Every pattern file starts with YAML frontmatter:
  - `title:` the pattern name
  - `layer:` one of `bronze`, `silver`, `gold`, `cross-cutting`, `decisions`,
    `semantic-model`, `snapshots`
  - `status:` one of `draft`, `working`, `stable`
  - `related:` a list of repo-relative `.md` paths to tightly coupled patterns only.
    Every listed path must exist.
- Every new pattern gets a row in `Pattern Index.md` in the correct layer table.
- CI (`scripts/validate_vault.py`) enforces all of the above. Run it locally
  before committing.

## Style (from STYLE.md)

- Narrative first, then code. One or two sentences, then the snippet.
- Code blocks are capped at ~10 lines; break long queries into steps.
- Use real F&O object names (CustTable, SalesOrderHeader, LedgerJournalEntry).
- No Kimball SCD terminology. Describe the mechanism ("snapshots",
  "overwrite in place") instead of "SCD Type 1/2".
- No hedging, no speculation, no filler. State assumptions directly.

## Session learnings

- Session discoveries go in `learnings/` as one Markdown file per learning.
- Frontmatter: `title:`, `author:`, `date:` (YYYY-MM-DD), `tags:` (2-5 tags).
- Learnings are published via PR only, never pushed directly to `main`.
  Reviewers are listed in `teamai.yaml`.

## Knowledge retrieval (teamai vs direct search)

- `teamai recall` indexes `learnings/`, `skills/`, `rules/`, and `docs/`.
- The seven Obsidian layer folders (`Bronze/`, `Silver/`, `Gold/`, `Cross-Cutting/`, `Decisions/`, `Semantic Model/`, `Snapshots/`) remain at the repository root to preserve the vault's graph structure and link integrity.
- For AI agents (such as Coop): use `teamai recall` to query field discoveries in `learnings/`; search the layer folders directly via grep or ripgrep across the local clone (see the `team-knowledge` skill in Coop).
