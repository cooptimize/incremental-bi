## Summary
<!-- Brief 1-3 sentence summary of the change or learning. -->

## Type of Change
- [ ] Pattern addition or update (under `Bronze/`, `Silver/`, `Gold/`, `Cross-Cutting/`, `Decisions/`, `Semantic Model/`, or `Snapshots/`)
- [ ] Session learning (under `learnings/`)
- [ ] Skill / rule addition or update (under `skills/` or `rules/`)
- [ ] Housekeeping / tooling / docs

## Checklist

### For Patterns
- [ ] Follows `STYLE.md` rules (narrative-first, ~10 line code cap, real F&O object names, no Kimball SCD jargon).
- [ ] YAML frontmatter contains `title`, `layer`, `status` (`draft` | `working` | `stable`), and `related`.
- [ ] All paths listed under `related:` exist and resolve cleanly.
- [ ] Added or updated row in `Pattern Index.md`.

### For Learnings (`learnings/`)
- [ ] YAML frontmatter contains `title`, `author`, `date` (YYYY-MM-DD), `tags`, and `x-coop:` block.
- [ ] Sanitization sweep: zero client-specific names, tenant IDs, credentials, or private connection strings.
- [ ] Content uses generic F&O / Fabric terminology and is set to `sensitivity: internal`.

### Verification
- [ ] `python3 scripts/validate_vault.py` passes locally.
