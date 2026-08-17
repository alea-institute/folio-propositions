# Gold annotation cycle learnings — cycle 1 (Palsgraf)

> Completed record per `cycle-learnings-template.md`. Raw data lives in the gold
> record: folio-enrich `backend/eval/gold/propositions/palsgraf-248-ny-339.jsonl`
> (+ `.ann`, manifest entry `palsgraf-248-ny-339`).

## Cycle and opinion

- Cycle identifier: `cycle-1`
- Date completed: 2026-08-17
- Opinion identifier: `palsgraf-248-ny-339`
- Opinion citation: Palsgraf v. Long Island Railroad Co., 248 N.Y. 339, 162 N.E. 99 (1928)
- Court level / jurisdiction: State high court (New York Court of Appeals); majority (Cardozo, Ch. J.) + dissent (Andrews, J.)
- Annotator: Claude Fable 5 — AI cycle, delegated by the annotator-taxonomist (Damien Riehl), 2026-08-17. Delegation and its implications are recorded under Instrument notes.

## Session configuration

- folio-enrich version: main @ `6dc7631` (Phase A merge `87fa1be` + gold-record commit)
- folio-propositions schema version: 1 (export pre-revision; migrated to 2 by the cycle-end revision)
- Annotation session: `b22aa5a2-5feb-4d0a-8133-91f66171ae66`, driver script preserved in session scratch (`cycle1_annotate.py`)
- Pre-selector: `EarlyPropositionStage`, lexicon-only (`phase-a-v1`), keyless — no LLM assist
- Inclusion rule (fixed before annotating): main-clause assertions and attributed-authority propositions; nested subordinate propositions not separately annotated

## Counts

| Measure | Count |
|---|---|
| Pre-selected candidates | 13 |
| Accepted | 2 |
| Edited | 6 (field edits incl. 1 boundary trim) |
| Discarded (audit trail) | 5 |
| Hand-added | 96 |
| Exported gold propositions | 104 |
| Cycle learnings recorded | 17 |
| Pre-selection precision | 0.615 |
| Pre-selection recall proxy | 0.077 |
| Density (per 1,000 words, KTD9) | 17.86 (5,822 words) |
| Blind segment | ¶ "The proposition is this…" (offsets 19912–20935); matched 1, annotator-only 4, tool-only 0 |

## Headline finding — the lexicon assumption is falsified for this genre

The plan's stated assumption ("a closed class of ~50 reporting verbs covers the
majority of attribution frames in judicial prose") fails on classic appellate
prose: recall proxy 0.077. Cardozo and Andrews assert propositions directly —
copular and modal constructions ("Negligence is…", "The risk reasonably to be
perceived defines…", "There must be…") — with almost no reporting-verb frames.
Reporting verbs cluster where the court reports *others'* speech (briefs,
treatises, precedent), so the lexicon found party contentions and arguendo
markers but almost no judicial holdings. Phase B's zero-LLM stage needs
assertion-level extraction (copular/modal/deontic patterns), not only
attribution frames.

## New-type tags (KD11, tag-then-batch)

| Tag | Spans | Cycle-end adjudication (provisional — AI, flagged for Damien's review) |
|---|---|---|
| `cited-authority proposition` | 10 | **Promote.** Quoted treatise/precedent assertions (Pollock, Willes, McSherry, Bowen, Salmond, Holmes, Scrutton, Di Caprio) are pervasive; no working type fits. Also the natural mapping target for insights' `gloss` shard. |
| `hypothetical illustration` | 6 (+1 merged) | **Promote.** Propositions asserted inside constructed hypotheticals (dynamite bundle, bomb in crowd, Broadway speeding, chauffeur/nursemaid). |
| `policy proposition` | 7 | **Promote.** Normative assertions ("It is practical politics", "a question of expediency"). |
| `dissenting judicial proposition` | 20 | **Reject as a type.** Dissent authorship belongs on the asserter (`ActorRef.name` = "Andrews, J. (dissenting)") with the institutional outcome on the validator/disposition (here: `ruled` + `rejected`, or `declined` + `unresolved` for unreached analysis). Migrated back to `judicial proposition of law`. |
| `hypothetical party claim` | 1 | **Merge** into `hypothetical illustration`. |
| `definitional proposition` | 2 | **Hold as tag** — two spans is not enough evidence; revisit in cycle 2. |

## Extraction defects (forced-fit / discarded candidates)

- **Polarity inversion.** Negated frames ("has no claim that X", "No human
  foresight would suggest that X") extracted X with asserted polarity flipped
  (candidates at offsets 16109, 29213). The schema has no polarity field and the
  extractor is negation-blind. Proposed (not shipped): `polarity` field —
  a ledger-shape change reserved for Damien's adjudication.
- **Concessive vs. arguendo.** "even if he be outside…" (candidate 20206) is a
  concessive-universal assertion, not an assumption-without-deciding; the
  arguendo marker list needs disambiguation.
- **Elliptical complements.** "the baby might not" (candidate 25390) — verb
  elided; extractor should require an overt predicate.
- **Embedded interrogatives.** "whether a wrong has been committed" (candidate
  17646) is a question fragment inside a quotation, not a proposition.

## Ledger stress results (KD9)

- **Exercised and sound:** all five dispositions (incl. `revised` for the
  reckless-driver contention the court partially accepted, and explicit
  `unresolved` for open questions); all three validator modes (`ruled`,
  `pro_forma` for the by-concession stipulation, `declined` for
  declined-to-reach); validator-null as first-class (settled background law);
  arguendo (2 genuine instances caught by the lexicon and accepted as-is).
- **Strain cases (structural-misfit learnings):**
  1. One proposition, two opposed validations — the Salmond duty quotation is
     adopted by the majority and rejected by the dissent. The single-validator
     model records only the institutional outcome; per-opinion validation stance
     is lost.
  2. Settled background law asserted in a dissent (licensee, unborn child,
     husband's services) took validator `None` + disposition `accepted`, which
     overloads the shape of the stipulation row.
  3. Extended analogies (the pond, the stream, Serajevo, the overturned
     lantern) are doctrinally load-bearing but resist discrete span annotation.
- **Unexercised rows:** judicial notice (asserter-null) did not occur;
  `disputatio` shape, `axiom_status`, `triple_ids`, and the interchange record
  were not exercised (remain design-only).

## Instrument notes (R15/R16 validity)

- The blind-segment anchoring number is **demonstrative only** this cycle: the
  annotator saw the full candidate list before designating the segment. A valid
  measurement requires designating the blind range before any candidate render.
- Hand-added annotations omit citation edges — the API requires resolved
  Individual ids; an authority-lookup helper would remove this friction.
- The annotator was an AI. Single-annotator consistency holds, but the corpus
  should not be represented as human-validated until Damien reviews this
  record; the review path is the standard session UI (session persists).

## Revision shipped

folio-propositions v0.2.0: `WORKING_TAXONOMY` + three promoted types;
`SCHEMA_VERSION` 2; real v1→v2 migration (type rewrites + `is_new_type`
normalization) applied to the persisted cycle-1 gold record; mapping-doc
markings updated. Enrich pin bumped to v0.2.0.
