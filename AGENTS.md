---
publish: false
---

# Instructions for Editing ERP Analytics Incrementals

This repository is a practitioner's reference for ERP analytics load patterns, focused on Dynamics 365 Finance & Operations and bronze/silver/gold pipelines feeding Power BI. The articles are the product. Read [README.md](README.md) for the repository map and [STYLE.md](STYLE.md) for writing guidance.

## Editing articles

- Explain the problem, the mechanism, and the assumptions behind a pattern. Assume working knowledge of SQL and F&O, but do not assume the reader participated in the design discussion.
- Follow STYLE.md. Keep the article body focused on how the pattern works and why. State essential assumptions briefly, preserve useful code, and move unimplemented complexities to short bullets in a final “Not covered” section. Do not explain every edge case in the walkthrough.
- Preserve the author's meaning. Distinguish prose improvements from technical changes, and flag conflicting claims rather than silently choosing between them.
- Ground examples in the project's F&O stack. State platform-specific assumptions and distinguish verified behavior from proposed approaches.
- Keep gaps visible. Do not invent implementation details, benchmarks, or validation evidence to make an unfinished article appear complete.
- Describe history behavior directly, such as “overwrite in place,” “retain each observed version,” or “capture state at period close.” Do not use numbered SCD terminology.
- Before designing a snapshot or history-tracking pattern, check whether the source already maintains the required date-effective history. See [Snapshots overview](Snapshots/Snapshots%20Overview.md).

## Keep examples simple

- Use the simplest code that demonstrates how the pattern works and why. Include only the structure needed for that example.
- Prefer a direct query for a simple join. Do not wrap a table in a pass-through CTE or add intermediate steps just to make the example look structured.
- Add CTEs, temporary tables, and helper expressions when they perform useful work or their result is reused. Do not add them merely to illustrate every available SQL convention.
- For a simple example, keep its scope filter in the direct query rather than adding a CTE solely to hold the predicate. This is a project-specific exception to the external pre-join filtering convention.
- Keep essential logic, including the combined source timestamp and matching scope. Put unimplemented production concerns in “Not covered” instead of expanding the example with scaffolding.

## SQL naming

- Use `dim.Customer` for the customer dimension and `PKCustomer` for its primary key. Match it to the natural/business key `dataareaid` plus `customerid`.
- Use source-system schemas for source tables, such as `d365fo.custtable` and `d365fo.dirpartytable`.
- Never use the `dbo` schema in SQL examples. Follow the external standards for identity generation and supporting-object placement.

## External SQL standards

- SQL examples follow the SQL standards in the sibling repository `../coop-standards/`. Read its [README](../coop-standards/README.md) to locate the current SQL and applicable technology articles, then read the articles relevant to the objects being edited. Include formatting, table, procedure, view, and target-platform rules as applicable.
- Read [SQL Formatting.md](../coop-standards/SQL/SQL%20Formatting.md) for every SQL editing task. New and fully rewritten statements use its canonical style; targeted edits preserve established formatting in unrelated code.
- Keep the standards external. Do not copy, assemble, or synchronize their contents into this repository. Do not edit files in `coop-standards` as part of work here.
- This reference adopts SQL standards, not the other repository's agent instructions or prose style. STYLE.md governs these explanatory articles. Explicit user instructions and this project's stated overrides take precedence.
- Keep standards changes separate from algorithm changes. If applying a standard would change a pattern's behavior, identify the conflict rather than silently redesigning the pattern.
- The shared repository is [Cooptimize Standards](https://github.com/cooptimize/coop-standards). Other machines should have an accessible checkout beside this repository. If it is unavailable, report that the standards could not be read; do not claim compliance from memory.

## Organization

- Keep each pattern in its own Markdown file under the appropriate layer or topic folder. Link related patterns where their choices interact.
- Use the existing human-readable filenames and actual directory capitalization. When adding, moving, or renaming an article, update [Pattern Index.md](Pattern%20Index.md) and affected links and frontmatter references.
- Keep README.md focused on human orientation and navigation, Overview.md on the architectural explanation, and STYLE.md on writing guidance. Maintain agent instructions here rather than in a separate tool-specific instruction file.
- Preserve article metadata. The status convention is `draft` for incomplete content, `working` for content that still needs implementation validation, and `stable` for patterns validated against real implementations. Do not promote status solely because the writing improved; a missing status is not evidence of validation.
- Keep repository guidance marked `publish: false`. Preserve the existing publishing configuration unless the task concerns publishing.

## Validation

- Check edited Markdown for balanced code fences, valid local links, and whitespace errors.
- Review related articles for conflicting terminology, assumptions, and examples. Report unresolved technical contradictions separately from completed editorial changes.
- For code changes, use validation appropriate to the target platform. Clearly state when examples have not been executed; Markdown checks do not validate SQL or DAX behavior.
- Preserve unrelated working changes. Summarize what changed, what was checked, and any remaining gaps.
