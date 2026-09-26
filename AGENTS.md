---
publish: false
---
# Writing and editing this wiki

This is a practical guide to ERP incremental loading, illustrated with D365FO. Read [Overview.md](Overview.md) for orientation and article navigation. This file governs how we explain and edit the material; technical decisions belong in the articles themselves.

## Write for a colleague

- Assume basic SQL and warehouse knowledge, but no in-depth experience managing incremental loads. Skip warehouse introductions while explaining the mechanics the reader needs to understand the pattern.
- Lead with the general problem and why an approach helps. Explain how it works next. Use source tables and business examples to illustrate the idea, rather than making them the subject of the article.
- Explain an action before naming its concept. For example, saving where the last successful load stopped introduces a checkpoint. Don't replace that explanation with jargon.
- Brevity means removing material the reader doesn't need, not compressing the explanation into clipped sentences. Use natural, connected prose and concrete examples.
- A short article may need only a few paragraphs. Don't add headings, code, caveats, or a conclusion just to fill a template.
- Use headings that describe concepts. Let heading levels reflect the relationship between ideas, with supporting details beneath the approach they qualify. Don't prescribe a hierarchy for an individual article here.
- Include a caveat only when it affects choosing, understanding, or applying the pattern. Put it beside the relevant explanation. Omit generic warnings, implementation wish lists, repeated disclaimers, and “Not covered” sections.

For example: “A full load replaces the fact on every run. If it fits the refresh window, you avoid maintaining change detection and a separate path for deletions.” Explain the mechanism from there; another paragraph praising simplicity adds nothing.

## Keep the articles consistent

- Before editing, read the related articles and compare their terminology, assumptions, examples, and recommendations. Use those articles as the source of technical context rather than duplicating their decisions in this guide.
- Distinguish intentional differences between strategies from contradictions. Different layers or source behaviors can justify different approaches; don't force one recipe across the wiki.
- When a decision changes, update the affected explanations and links together. If related articles disagree and the user's intent doesn't resolve it, flag the conflict rather than silently choosing a design.
- Keep each article focused on its own decision. Link to an explanation elsewhere instead of repeating it or turning it into a tangent.
- Consolidate pages that answer the same question. Preserve useful examples and essential assumptions, not every paragraph from the original pages.
- Use Overview as the single entry point for explanation and navigation. Follow the existing topic folders and human-readable filenames; avoid adding hierarchy without a reader need.

## Make examples earn their space

- Use the smallest example that makes the mechanism clear. Preserve useful code when shortening prose, but don't add scaffolding or alternative implementations that obscure the point.
- Add CTEs, temporary tables, parameters, and helper expressions when they do useful work. Don't add them merely to demonstrate conventions or introduce a scope the article doesn't need.
- Keep names and key relationships consistent with related examples. Be precise about which key or timestamp you mean rather than using an ambiguous “ID” or “modified date.”
- State the platform and inputs when they affect the example. Distinguish complete implementations from fragments and prepared fields from native source fields.
- Describe behavior directly. Explain what is retained, replaced, or updated rather than relying on terminology the reader may not know.
- Don't invent source behavior, fields, benchmarks, or validation results. Keep material implementation gaps visible where they affect the explanation.
- Separate prose improvements from technical changes. Don't redesign an algorithm while presenting the change as editorial cleanup.

## Use external standards

- SQL follows the sibling [coop-standards repository](../coop-standards/README.md). For SQL edits, read [SQL Conventions](../coop-standards/SQL/SQL%20Conventions.md), [SQL Layout](../coop-standards/SQL/SQL%20Layout.md), and applicable object and platform guidance.
- Keep those standards external. Don't copy them here or edit that repository as part of this work. If it is unavailable, report that rather than claiming compliance from memory.
- Adopt its technical standards, not its agent instructions or prose style. Explicit user directions take precedence. Respect ownership rules for generated code and make changes through its supported source or configuration.
- Preserve unrelated formatting during targeted edits. Keep examples simple: a direct scope filter needn't become a pass-through CTE solely to satisfy the external pre-join filtering convention.

## Finish the edit

- Resolve `@agent` notes, including obvious misspellings, when asked to review comments. Preserve the user's other edits.
- Update Overview navigation, local links, anchors, and related-page metadata when moving or removing articles.
- Preserve article metadata and publishing settings. Don't infer implementation readiness from improved prose. Keep this guide marked `publish: false`.
- Start the body immediately after the closing metadata delimiter, without an extra blank line or decorative separator. Keep normal paragraph spacing within the article.
- Check links, code fences, and whitespace. Validate changed code appropriately and state when it hasn't been executed on the target platform.
- Maintain this file as one writing and editing guide. Add reusable principles when needed, not a running list of individual article decisions.
