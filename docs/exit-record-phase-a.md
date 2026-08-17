# Proposition System Phase A exit record

> Completed per `exit-record-template.md`. Status: **cycle 1 of the gold ladder
> complete; Phase A tooling complete; v2.0 review pending.** This record is
> updated at the review disposition (see `review-disposition.md`).

## Exit record

- Record date: 2026-08-17
- Phase A schema version: 2 (v0.2.0)
- Prepared by: Claude Fable 5 (AI, delegated) — pending review by Damien Riehl (annotator-taxonomist)
- Gold-corpus ladder completed: NO — 1 of ~5–6 opinions (state high court). Remaining rungs: federal appellate, federal district, state intermediate appellate, state trial, plus at least one modern opinion (post-1980) to test genre drift.

## Post-cycle taxonomy decision

- Decision: **ADOPT WITH REVISIONS** (provisional — AI adjudication under Damien's delegation; flagged for his confirmation)
- Final working taxonomy: `folio_propositions.WORKING_TAXONOMY` v0.2.0 — the seven seed types plus `cited-authority proposition`, `hypothetical illustration`, `policy proposition`
- Approved revisions: three type promotions; `dissenting judicial proposition` rejected as a type (modeled via asserter attribution + validator outcome); `hypothetical party claim` merged; `definitional proposition` held as tag
- Migration shipped: v1→v2 (`folio_propositions.migrate_record`), applied to the persisted cycle-1 gold record
- Rationale: grounded in cycle-1 counts (45% of gold spans required new types; 20-span dissent cluster resolves cleanly through existing asserter/validator fields; 2-span definitional cluster below promotion threshold)

## Unresolved risks

1. **Extraction recall (Phase B critical).** Lexicon-only recall proxy 0.077 on
   classic appellate prose. Phase B's zero-LLM stage must add assertion-level
   patterns (copular/modal/deontic), not just attribution frames; benchmark
   against this gold set.
2. **Polarity.** The schema cannot represent negated assertion extraction
   correctly; a `polarity` field is proposed but is a ledger-shape change
   reserved for Damien. Until decided, negation-blind extraction will produce
   inverted candidates.
3. **Per-opinion validation stance.** Majority-vs-dissent opposed validation of
   the same proposition collapses to the institutional outcome. If insights
   needs per-opinion stances (likely for `disputed_proposition` threads), the
   validator side needs multiplicity or stance edges.
4. **AI-annotated corpus.** Cycle 1 is AI-annotated under delegation. Human
   review of the session (or a human-annotated second opinion) is advisable
   before the packet is represented as human-validated gold.
5. **Blind-segment validity.** Anchoring measurement was demonstrative this
   cycle; the workflow needs designate-before-render to produce a real number.
6. **Unexercised schema surface.** Judicial notice, disputatio shape, axiom
   lifecycle, citation edges on hand-adds, interchange record — all still
   design-only; the ladder's remaining opinions should target them (e.g., an
   opinion taking judicial notice; a motion sequence for disputatio).

## Conditions for Phase B

Phase B (Propositions MVP: production stage + public tab + benchmark) proceeds when:

1. Damien confirms or amends the cycle-1 taxonomy adjudication (this record and
   `cycle-1-palsgraf-learnings.md`);
2. the v2.0 review records its disposition (`review-disposition.md`) — the
   identity-boundary split in `rationale.md` is the recommended adoption line;
3. Phase B's extraction design accounts for unresolved risk 1 (assertion-level
   patterns), with the cycle-1 gold set as its benchmark target.

Items 1–2 are decision gates for Damien; item 3 is a design constraint carried
into the Phase B brainstorm (seeded from the plan's "How This Work Fits
Together" section).

## Pointers

- Gold record: folio-enrich `backend/eval/gold/propositions/palsgraf-248-ny-339.{jsonl,ann}` + manifest
- Cycle learnings: `cycle-1-palsgraf-learnings.md`
- Review packet: `shard-mapping.md` (markings current through cycle 1), `rationale.md`, `review-disposition.md` (template, to be filled at review)
- Phase A implementation: folio-enrich PR #35 (merged `87fa1be`); plan `docs/plans/2026-08-16-2234-feat-proposition-system-phase-a-plan.md`
