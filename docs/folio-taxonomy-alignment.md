# FOLIO taxonomy alignment — top-down + bottom-up analysis

> Requested by Damien (decision sheet `propositions-dns-and-cycle1`, q2 answer,
> 2026-08-17): before confirming the cycle-1 adjudication, find "all the gold in
> FOLIO" — what it already has (top-down) and what a proposition taxonomy needs
> (bottom-up) — "and between them, we'll have a better idea of what should be."
> Method: folio-python over the live FOLIO OWL (enrich's pinned copy).

## Top-down — what FOLIO already has

The **Document Components** shelf contains most of the conceptual frame:

| FOLIO class | IRI suffix | Note |
|---|---|---|
| Legal Argument | `R77n3Z14OcgllZTAx8sw9xZ` | "structured presentation of facts and law aimed at persuading a court" |
| ├─ **Legal Proposition** | `RNICD9MDcFQJJX6nxX11Vt` | "a statement that outlines a principle, rule, or application of law that arguably applies" — an **asserted, not-yet-adopted** proposition |
| │ └─ **Judicial Legal Conclusion** | `RKTUVhpkOGaH53JFNJ4X4s` | "as **adopted by a decisionmaker**" — the **validated** counterpart |
| Factual Statement | `RnKWv1E6U2Ssc5SRsG14NO` | a document's statement of fact |
| └─ **Judicial Finding of Fact** | `R7ZrWzdAOf6mXVtcQ49gWat` | "finding of fact **as adopted by a decisionmaker**" |
| Judicial Dissent | `RI3QONzSYBIXBgMFfpUDhk` | opinion-context component (not a proposition type) |
| Judicial Concurrence | `RTNLwK1SAJaRJJu2kYrJZg` | ditto |
| Legal Issue | `RCN2STLOwO6wSS7w4e1hj8L` | adjacent: the *question* a proposition answers |
| Citation to Legal Authority (+ Caselaw, Statutes, Constitutions, Secondary, Record, …) | `R7fEpxSrDSl1VojeYSxppg` etc. | typed citation targets — homes for our `CitationEdge` targets |

Elsewhere: `Stipulation` (`R8zxICG1ccCZO0nNV776P8B`) and its children exist as
Trial Court Practice **Documents** (the filing, not the proposition);
`Judicial Notice` did not surface as a proposition-shaped class; `Authority`
(`R9ikrznaQwm4RUsMzP9KXFR`) exists under Deontic Specification.

**The headline:** FOLIO already encodes the ledger's central distinction —
asserted vs. adopted — TWICE, in parallel, on both the law side (Legal
Proposition → Judicial Legal Conclusion) and the fact side (Factual Statement →
Judicial Finding of Fact). The double-entry ledger is a generalization of a
pattern FOLIO natively expresses through subclassing. And FOLIO models dissent
and concurrence as *document components* (attribution context), **not** as
proposition types — independently confirming the cycle-1 call to reject
`dissenting judicial proposition` as a type and carry dissent on asserter
attribution.

## Bottom-up — what the working taxonomy needs, mapped

| Working type (v0.2.0) | FOLIO home today | Fit |
|---|---|---|
| party proposition of law | Legal Proposition | **exact** |
| judicial proposition of law | Judicial Legal Conclusion | **exact** |
| party proposition of fact | Factual Statement | close (FOLIO's is document-scoped) |
| judicial proposition of fact | Judicial Finding of Fact | **exact** |
| cited-authority proposition | Citation to Legal Authority family covers the *citation*; no class for the cited *proposition content* | **gap** (candidate: "Cited Authority Proposition" under Legal Proposition) |
| stipulation | Stipulation (document class) | mismatch of kind — **gap** (candidate: "Stipulated Proposition") |
| arguendo assumption | — | **gap** (candidate: "Assumed Proposition (Arguendo)") |
| judicial notice | — | **gap** (candidate under Judicial Finding of Fact) |
| hypothetical illustration | — | **gap** |
| policy proposition | — | **gap** (nearest: Legal Argument generally) |
| definitional proposition (held tag) | — | gap; weak evidence (2 spans) |

## What should be — recommendation for adjudication

1. **Damien's parent instinct is right and FOLIO-shaped:** a generalized
   **`Proposition`** parent (above `Legal Proposition`, and arguably above
   `Factual Statement`) would give the asserted/adopted pairs one root and give
   our ledger its anchor class. This is a FOLIO *addition* proposal (Phase E
   flywheel material; also belongs in the v2.0 review packet).
2. **Rename-to-align (library v0.3.0, confirmed by Damien 2026-08-17):** adopt FOLIO
   labels + IRIs for the four exact/close matches (e.g. `judicial proposition
   of law` → `Judicial Legal Conclusion` with IRI), keeping our extra types as
   free-typed until FOLIO grows them. Mechanically: `WORKING_TAXONOMY` becomes
   a label→optional-IRI mapping — metadata, not a ledger-shape change (stays
   consistent with the q3 "defer shape changes" decision).
3. **The six gaps are the FOLIO proposal packet seed** — exactly the flywheel
   output Phase E anticipated, now grounded in both cycle-1 annotation evidence
   and a top-down inventory.
4. **Cycle-1 adjudication status:** unchanged in substance — the three
   promotions and the dissent-as-attribution call all survive contact with
   FOLIO (dissent modeling is *confirmed* by it). What changes is naming: the
   promoted/seed types should align to FOLIO labels+IRIs where matches exist.
   Damien confirmed this recommendation as written; v0.3.0 carries the
   metadata alignment and a v2→v3 migration without changing ledger shape.
