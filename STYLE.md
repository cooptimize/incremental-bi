---
publish: false
---

# Style guide

## Write for a colleague

Write like an experienced colleague explaining a pattern to another developer. Be direct, natural, and generous with the explanation that makes the idea click. The reader knows SQL, D365FO, and data pipelines; they may not know why this load replaces whole partitions or preserves a particular key.

Keep each article focused on how the pattern works and why it is built that way. Show the main path without explaining every surrounding complexity. Put out-of-scope cases in short bullets under a final “Not covered” heading.

## Make each paragraph earn its place

Every body paragraph should help explain a step or the reason for it. Cut paragraphs that merely announce the topic, repeat the conclusion, or insist that something is important.

Prefer a short, connected explanation over a pile of fragments. Use complete sentences and ordinary transitions. Contractions are welcome. Sound like someone helping a colleague understand, without manufacturing personality or adding jokes.

Give the main idea enough room to land. One concrete example often does more work than several abstract paragraphs. Don't explain it again after the example has made it clear.

For example:

> A full load replaces the fact table on every run. If it fits your refresh window, start here: you avoid maintaining change tracking and a separate path for deletions already reflected in the source.

That gives a recommendation, a condition, and a reason. It doesn't need a second paragraph declaring simplicity valuable.

## Let the subject determine the structure

Use headings when the subject changes, not every time you have another thought. Use numbered steps for a sequence and bullets or tables for parallel choices. Don't force every article into the same “what / when / how / guardrails” template.

Avoid obligatory introductions, summaries, and key takeaways. End pattern articles with a short “Not covered” list for complexities the example does not implement: retries, unusual source behavior, history, or alternate designs. Give each item a sentence and a link where useful; do not turn the list into another walkthrough. Omit it when there is nothing material to list.

Treat length as a symptom. If an article feels long, look for repetition, unnecessary background, or a second topic that deserves its own page. If it feels abrupt, restore the missing connection rather than adding a longer introduction. There is no fixed word, screen, or code-block limit.

## Show useful code

Explain what a query consumes and produces before showing it. Keep a complete logical operation together; split longer walkthroughs at meaningful steps. Preserve the examples needed to understand the mechanism rather than replacing them with vague prose.

Follow the external [SQL formatting standard](../coop-standards/SQL/SQL%20Formatting.md) and the applicable SQL standards identified in AGENTS.md. Read them from the shared library without copying or editing them. New and fully rewritten statements use the canonical style; targeted edits preserve established formatting in unrelated code.

Use real SQL or Python for executable examples. Identify the platform, required inputs, and essential assumptions briefly. Label excerpts rather than presenting them as complete procedures. Put unimplemented transaction, retry, and orchestration details in “Not covered”; include them in the walkthrough only when they are the mechanism being taught.

Use F&O objects where they clarify the pattern, and identify any conformed fields introduced by the example. Temp tables use `#PascalCase`, such as `#PartitionState`.

## Preserve meaning and confidence

State essential preconditions briefly so the example remains honest. Reserve “always,” “never,” and “guaranteed” for claims the mechanism supports. Acknowledge other limitations in “Not covered” rather than interrupting each step with an edge-case discussion.

Distinguish verified behavior, design assumptions, and unfinished implementation work. Preserve `draft`, `working`, and `stable` metadata; an editorial improvement is not technical validation. Keep specific research gaps visible without adding empty “Open questions” sections. Flag disagreements between articles rather than silently choosing an architecture.

Use bronze, silver, gold, and semantic model consistently. Explain project-specific terms when needed to follow the current article. Describe history behavior directly—“overwrite in place,” “retain each observed version,” or “capture state at period close”—instead of numbered SCD terminology.
