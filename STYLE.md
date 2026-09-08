---
publish: false
---

# Style guide

## Target audience

Smart developers who:
- Know SQL, medallion architecture, have shipped data pipelines
- Know D365FO (assume CustTable, SalesTable, GL structure without explaining)
- Don't need ELI5 — want the pattern, code, and gotchas
- Skeptical of marketing speak and speculation

## Principles

1. **Narrative first, then the code.** One or two sentences saying what this step does, then the snippet that does it. Code confirms an idea the reader already has; it should never be where the idea is introduced.

2. **Specific > general.** State the assumption, don't hedge. "This breaks because X" not "Be aware that..."

3. **Directional > exhaustive.** "When to use it" is 2-3 bullets max. If it's obvious, skip the section. No inaccurate hedging.

4. **Front-load the pattern.** Tiny preamble (one sentence). Then the pattern. Then hard parts. Context last.

5. **Assume D365FO.** Don't explain what a timestamp is or what CustTable does. No "F&O specific notes" if it's just explaining basic concepts.

6. **Kill speculation.** No "open questions" or theoretical problems. If we haven't validated it, don't ask.

7. **Trim frontmatter.** No "status" field. No "when not to use" if it's just hedging. Just the pattern.

## Structure (example)

```markdown
---
title: [Pattern]
layer: [bronze | silver | gold]
related:
  - [closely related pattern]
---

## What this is

One sentence. What it does.

## The pattern

Small code snippet showing the core idea.

```sql
MERGE INTO silver.Customer t
USING bronze.Customer s ON t.id = s.id
WHEN MATCHED AND s.SinkModifiedOn > @watermark THEN UPDATE ...
WHEN NOT MATCHED THEN INSERT ...
WHEN NOT MATCHED BY SOURCE THEN DELETE;
```

**Why:** [One or two sentences on the tradeoff]

## How it works

The mechanics. Name the objects (CustTable, GeneralJournalEntry). Assume reader knows SQL.

```sql
-- Full stored procedure example (for reference/AI modeling only)
-- At the bottom if needed
```

## The hard parts

- **Problem 1:** Why it breaks and what to do about it
- **Problem 2:** How to validate this works in your case

## Related patterns

[Tightly coupled patterns only]
```

## Length targets

- Patterns: 80-150 lines (including code)
- Anti-patterns: 40-60 lines
- No article should require scrolling past 2-3 screens on a laptop

## Language

- Direct: "Do this"
- No filler: "This is an important consideration" → just state it
- No marketing: "harness the power of" → delete
- Specific: "When you add another system" not "In complex scenarios"

## Code

- **Hard cap ~10 lines per block.** Past that, eyes cross and the block gets skipped, which makes it worse than no code at all.
- A long query is not one block. Break it into the steps it is made of and give each step its own sentence: the source rollup, the comparison predicate, the assembly. Three snippets of eight lines beat one of twenty-four.
- Don't show the assembly when the parts are clear. "Wrap the rollup as a CTE and it's one statement" beats twenty lines proving it.
- No full reference procedure at the end. If the article body contains the statements, repeating them as a complete procedure is duplication — name the wrapper in a sentence instead.
- Use actual F&O objects (CustTable, SalesOrderHeader, LedgerJournalEntry)
- No pseudocode — real SQL or Python
- Temp tables are `#PascalCase` (`#PartitionState`), not `@table` variables or `tmp_snake_case`
- Don't show scaffolding the reader can write themselves (CREATE TABLE for a temp table, procedure shells). Show the statement that carries the idea

## What to remove

- Verbose "What this is" preamble
- "Status" field (if not stable, don't publish)
- "When to use it" if it's just hedging
- "Open questions" if unanswered
- "Related patterns" if not tightly coupled
- Any explanation of basic concepts (timestamp, MERGE syntax, etc.)
- Safety guardrails that sound like warnings ("Be careful...")
