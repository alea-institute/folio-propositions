# Gold annotation cycle learnings — template

> Complete one copy after each gold annotation cycle. Preserve raw counts and
> free-text observations even when no schema revision follows.

## Cycle and opinion

- Cycle identifier: `[CYCLE-ID]`
- Date completed: `[YYYY-MM-DD]`
- Opinion identifier: `[DOCUMENT-ID]`
- Opinion citation: `[LEGAL CITATION]`
- Court level / jurisdiction: `[COURT LEVEL — JURISDICTION]`
- Annotator: `[NAME OR APPROVED ANNOTATOR ID]`

## Session configuration

- folio-enrich version: `[VERSION / COMMIT OR RELEASE ID]`
- folio-propositions schema version: `[SCHEMA_VERSION]`
- Annotation session configuration: `[PATH, IDENTIFIER, OR INLINE SUMMARY]`
- Pre-selector model/tool and version: `[TOOL — VERSION]`
- Pre-selector threshold or other settings: `[CONFIGURATION]`

## Counts

| Measure | Count |
|---|---:|
| Pre-selected candidates | `[N]` |
| Candidates accepted | `[N]` |
| Candidates rejected | `[N]` |
| Candidates revised | `[N]` |
| Candidates left unresolved | `[N]` |
| Candidates marked assumed-arguendo | `[N]` |
| Hand-added propositions | `[N]` |
| Final proposition total | `[N]` |

- Annotation density numerator: `[FINAL PROPOSITION COUNT]`
- Annotation density denominator: `[OPINION WORDS / CHARACTERS / PAGES — NAME UNIT]`
- Annotation density: `[VALUE PER UNIT]`

## New-type tags surfaced

| Verbatim tag | Occurrences | Decision (`promote` / `merge` / `reject`) | Merge target, if any | Rationale |
|---|---:|---|---|---|
| `[TAG]` | `[N]` | `[DECISION]` | `[TARGET OR N/A]` | `[RATIONALE]` |

## Unclassifiable spans

| Span / locator | Text or concise description | Why unclassifiable | Proposed response |
|---|---|---|---|
| `[START–END / PAGE-PIN]` | `[TEXT OR DESCRIPTION]` | `[REASON]` | `[NEW TAG / STRUCTURAL CHANGE / DEFER]` |

## Forced-fit cases

| Proposition ID / span | Chosen type, role, edge, or shape | Better natural description | Why the fit was forced |
|---|---|---|---|
| `[ID / LOCATOR]` | `[CURRENT ENCODING]` | `[NATURAL ENCODING]` | `[RATIONALE]` |

## Structural misfits — free-text channel

`[Describe ledger rows that would not construct, relationships the models could
not preserve, workflow friction, span/reference problems, and any other schema
misfit. Write "None observed" when appropriate.]`

## Resulting revisions and migration

### Taxonomy and schema decisions

- Post-cycle decision: `[NO CHANGE / SUMMARY OF APPROVED CHANGES]`
- Previous schema version: `[N]`
- Resulting schema version: `[N]`
- Effective next cycle: `[CYCLE-ID]`

### Migration shipped

- Migration required: `[YES / NO]`
- Migration identifier or code location: `[PATH / RELEASE / N/A]`
- Records in scope: `[DESCRIPTION / N/A]`
- Verification evidence: `[TEST / DRY-RUN / ROUND-TRIP RESULT / N/A]`
- Shipped date: `[YYYY-MM-DD / N/A]`
- Owner: `[OWNER / N/A]`

## Sign-off

- Learnings reviewed by: `[NAME / FORUM]`
- Review date: `[YYYY-MM-DD]`
- Gold record location: `[PATH / RECORD IDENTIFIER]`
