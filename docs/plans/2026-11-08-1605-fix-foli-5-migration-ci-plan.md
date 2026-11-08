---
title: Foli-5 Migration Example CI Repair - Plan
type: fix
date: 2026-11-08
artifact_contract: ce-unified-plan/v1
product_contract_source: ce-plan-bootstrap
execution: code
item: foli-5
kind: expansion
branch: drawdown/foli-5
---

# Foli-5 Migration Example CI Repair - Plan

## Goal Capsule

- **Objective:** Consumers can use PR #6's authorized-signer and lifecycle-replay examples with a passing test suite on Python 3.11, 3.12, and 3.13.
- **Means:** Reproduce the reported failures at the confirmed `foli-2` head, repair their demonstrated cause, and retain the original examples and coverage (KTD1–KTD3).
- **Authority:** The supplied `foli-5` mandate and the chief repository's `docs/plans/2026-10-26-0705-feat-codex-drawdown-campaign-plan.md`, limited to its Goal Capsule and campaign R11, R15, R16, R17, R19, and R20. The chief excerpts are unavailable here; prerequisite P2 records the required reconciliation.
- **Delivery:** One replacement PR for #6 on `drawdown/foli-5`. This stage commits only this plan. A later build invokes `lfg`; the controller handles publication and the campaign merge gate handles merging (R6, KTD4).
- **Build entry:** P1 and P2 must be resolved before implementation. This plan does not establish that the supplied branch already descends from `drawdown/foli-2`.

---

## Product Contract

### Summary

Repair the CI failures attributable to PR #6 while preserving the migration examples it introduced.
Verify the unchanged CI test command on every mandated Python version and provide the controller with evidence for a superseding PR.

### Problem Frame

The mandate reports CI failures on all three supported Python versions.
The supplied branch contains v0.5.0 work but lacks the `foli-2` source ref and example files, so testing or patching this checkout would not establish that PR #6 was repaired.
Recovered local history supplies the earlier implementation and a historical verification receipt, but neither confirms the current failing PR head.

### Requirements

**Repair and compatibility**

- R1. Base the implementation branch on the controller-confirmed `drawdown/foli-2` or `origin/drawdown/foli-2` ref and preserve its complete work, as required by `foli-5`.
- R2. The exact CI test command, `pytest -q`, must pass the complete suite on Python 3.11, 3.12, and 3.13 at the repair commit.
- R3. Preserve all existing tests and assertions, and add regression coverage for the demonstrated defect without skips, weakened assertions, or reduced discovery (campaign R15, R16).
- R4. Preserve the original example's signer authorization, native replay, explicit legacy trust, immutability, and runnable-script behavior.
- R5. Restrict changes to the failing change and its regression tests or directly affected documentation; unrelated baseline failures do not authorize broader cleanup.

**Delivery and boundaries**

- R6. Commit locally on `drawdown/foli-5`; the controller publishes a replacement explicitly superseding PR #6 and retains the campaign checks and review gates (campaign R15, R17, R19).
- R7. Follow the supplied campaign hard stops and public-safe writing rules, including no remote or credential discovery, spend, sends, unbacked deletion, or force-push (campaign R11, R20).
- R8. Add no schema migration, data rewrite, package release, outside service, or deployment change; this repair must retain the existing package and dependency boundaries (campaign R15, R16).

### Scope Boundaries

The expected repair seam is `tests/test_migration_examples.py` and, only if failure evidence identifies it, `examples/migration_v4.py`.
Changes to `README.md` or `docs/migration-0.4.0.md` require a corresponding correction to the documented invocation or result.
A new receipt at `docs/plans/evidence/foli-5-verification.md` records verification without rewriting historical evidence.

No public API, lifecycle policy, signing format, package layout, dependency upgrade, or CI-matrix redesign is proposed.
Global import-path changes, packaging the checkout examples, and speculative loader hardening are excluded absent a reproduced defect within R5.
There is no front-end change, so Playwright screenshot evidence is not applicable.

#### Deferred to Follow-Up Work

The separate `foli-1`/`foli-4` identity-fixture work and `foli-3` hygiene remain outside this item.
The historical Ruff issue in a pre-existing lifecycle test belongs with the controller's baseline reconciliation unless evidence establishes that the failing change introduced it.

---

## Planning Contract

### Verified Starting State

Static inspection on 2026-11-08 found a clean `drawdown/foli-5` at `be8db76172f3e5a792bf19823b709db2a4512eea`, the v0.5.0 merge.
The only other branch is `main` at `90f94bea43ce6f63176cd6271c7006c72f528dd3`; neither required `foli-2` ref nor any remote exists.
No repository `AGENTS.md`, `CLAUDE.md`, `docs/handoffs/`, or `.planning/` was present.
No tests, imports, example execution, or builds were run during this planning stage.

Local unreachable Git objects retain this candidate `foli-2` chain:

| Commit | Relevant content |
| --- | --- |
| `53a5970199237406c7647f20ff9d5577347069bd` | Original plan, `docs/plans/2026-10-26-1342-feat-foli-2-migration-examples-plan.md`, based on `90f94be`. |
| `c7576b762f27a26054b1378eb68515d1c9498e34` | Native authorized-replay example and tests. |
| `366df2e45232046d44e276fde70f86f200cacb1d` | Explicit legacy trust example and coverage. |
| `00637b8b0ff5e2af6886428c77b561b259775a1f` | Migration guidance and script entry-point coverage. |
| `37ad3b828b0112ac52366985f3fcb590b989ecf4` | Historical `docs/plans/evidence/foli-2-verification.md` receipt. |

At the candidate tip, the delta from `90f94be` is six files: the original plan, its receipt, `README.md`, `docs/migration-0.4.0.md`, `examples/migration_v4.py`, and `tests/test_migration_examples.py`.
These objects were inspected without restoring files or changing refs.

The historical receipt reports 137 passing tests, including 19 example cases, under Python 3.13.11.
It separately reports Ruff RUF100 at `tests/test_lifecycle.py:341`.
Those are dated reports, not current acceptance results or proof of the three-version failure's cause.

### Build Prerequisites and Deferred Evidence

- P1. **Controller source confirmation and branch provisioning:** Confirm PR #6's head against candidate `37ad3b8`, supply the authoritative source ref, and provision `drawdown/foli-5` from it with this plan carried forward. Preserve the supplied v0.5.0 head, the plan commit, and any unrelated work in verified reachable references before changing the branch base. Record both old and new base identities. Do not restore the candidate onto the present v0.5.0 tree and describe that as the mandated starting point.
- P2. **Campaign authority:** Supply or reconcile only the chief plan's Goal Capsule and campaign R11, R15, R16, R17, R19, and R20, together with applicable `ops/drawdown/mandates/_common.md` guidance. References to these R-IDs in this plan currently trace to the supplied lane rules, not an independent read of the chief file.
- E1. **Failure diagnosis, deferred to build:** Obtain failed-job output from the controller or reproduce it at the confirmed head. If that head is green, reconcile the PR revision, merge context, and resolved dependency versions before choosing a repair.
- E2. **Matrix availability, deferred to build:** Establish suitable environments for all three Python versions. An unavailable interpreter, dependency installation failure, or sandbox socket error is incomplete infrastructure evidence, not a passing check or a reason to weaken tests.

P1 and P2 are controller provisioning prerequisites; no product choice, account login, or credential from the user is presently needed.

### Key Technical Decisions

- KTD1. **Choose the fix from fresh failure evidence.** Classify collection, runtime, lint, and environment failures separately before changing a file; compare with the confirmed source baseline when attribution is unclear. This enforces R2 and R5.
- KTD2. **Keep checkout examples outside the package.** The candidate's `example` fixture already loads `examples/migration_v4.py` by file location, and the wheel includes only `src/folio_propositions`. Missing root imports are therefore not an established diagnosis. Current `tests/test_conformance.py::_load_generator` is a reference if module loading proves causal, not a reason to copy changes from v0.5.0. This preserves R4 and R8.
- KTD3. **Test the repair through the shipped example.** Extend `tests/test_migration_examples.py` at the demonstrated failure seam, retaining real ephemeral signatures and the actual subprocess entry-point check. Successful fixture loading alone does not prove the documented script works. This implements R3 and R4.
- KTD4. **Use the campaign delivery split.** Local commits go to the controller for the superseding PR and required review gates under R6. Expansions merge behind guardrails (session-settled: user-directed — chosen over holding expansions for user review: the campaign authorizes guarded merging).
- KTD5. **Retain the campaign execution choices.** Local work uses Astra (session-settled: user-directed — chosen over the Sol-first ladder: the campaign specifies Astra locally). Cloud builds use the default Sol model with Astra and Fable reviews (session-settled: user-directed — chosen over carrying the local model choice into cloud builds: the campaign separates those stages). Routine work does not wait on the user; exhausted mandates lead to durable hygiene, not speculative features.

### Assumptions

- A1. `37ad3b8` is a useful candidate for controller reconciliation because its commit chain and receipt explicitly identify `foli-2`; it is not assumed to be PR #6's authoritative head.
- A2. A bounded repair remains possible without changing the library's trust model or stored formats. Failure evidence contradicting R5 or R8 requires a controller scope determination, not an unrequested redesign.

---

## Implementation Units

### U1. Establish the confirmed failing baseline

**Goal:** Make the failure attributable to the preserved PR #6 work.

**Requirements:** R1, R2, R5–R7; KTD1, KTD4, KTD5.

**Dependencies:** P1 and P2.

**Files:** Read the confirmed `.github/workflows/ci.yml`, `pyproject.toml`, `tests/test_migration_examples.py`, and `examples/migration_v4.py`; create `docs/plans/evidence/foli-5-verification.md`.

**Approach:** Record the source and repair-base identities, capture each matrix environment's failures, and identify the smallest failure-bearing path. Retain relevant tracebacks and resolved interpreter/dependency versions. Keep historical reports distinguishable from fresh results.

**Test expectation:** No new behavioral test in this evidence unit; reproduce the existing full-suite command and identify the regression scenario U2 must add.

**Verification:** The evidence identifies the failing command, version, exception or check, and affected path. A green or unreproducible baseline remains an unresolved diagnosis.

### U2. Repair the demonstrated defect with additive coverage

**Goal:** Correct the attributed failure while retaining the delivered examples.

**Requirements:** R2–R5, R7, R8; KTD1–KTD3, KTD5.

**Dependencies:** U1 identifies a defect within R5.

**Files:** `tests/test_migration_examples.py`; `examples/migration_v4.py` only if implicated; `README.md` and `docs/migration-0.4.0.md` only for a directly affected instruction.

**Approach:** Add a regression case that fails for the observed reason on the confirmed original code, then apply the smallest supported correction. Preserve the original test bodies and parameterizations. Leave unrelated baseline defects for the controller under the scope boundary.

**Execution note:** Establish the failure before altering the implementation or test-loading seam.

**Patterns to follow:** The original example fixture and script subprocess test; existing lifecycle and interchange tests for signatures, validation, replay rejection, and immutability.

**Test scenarios:**

1. The exact U1 failure input or invocation reaches its expected result after repair on each supported interpreter; the added regression fails against the uncorrected seam.
2. The native walkthrough retains its four signed transitions, finishes superseded, and replays the unchanged recorded entries.
3. Valid outsider signatures, empty allowlists, tampered authorized signatures, and unauthorized earlier actors remain rejected.
4. The legacy opener remains unsigned and rejected by default; explicit trust permits the opener but never bypasses later signer or signature checks.
5. Obsolete or cross-identity replay and malformed saved-record structure remain rejected without changing source records.
6. The existing subprocess test still produces the seven documented output lines with successful exit and empty stderr.

Scenarios 2–6 primarily reuse existing cases; add only coverage required by the defect rather than duplicating the suite.
The example integration seam catches consumer composition and script execution; the unchanged library suites cover the underlying lifecycle and record contracts.

**Verification:** The focused example, lifecycle, and interchange suites pass, and the diff contains no deleted or weakened test or unrelated behavior change.

### U3. Complete matrix proof and controller handoff

**Goal:** Supply reviewable evidence that the repair meets the mandate.

**Requirements:** R1–R8; KTD4, KTD5.

**Dependencies:** U2.

**Files:** Complete `docs/plans/evidence/foli-5-verification.md`; inspect `.github/workflows/ci.yml` without changing its checks.

**Approach:** Run the verification contract at the repair commit, distinguish baseline defects from regressions, and record review results and remaining controller steps. Identify PR #6 as the PR being superseded.

**Test expectation:** No additional test framework; use the existing CI matrix and U2's regression coverage.

**Verification:** All required results have fresh evidence tied to the repair commit. Publication or one passing interpreter cannot substitute for incomplete matrix or review results.

---

## Verification Contract

Use the confirmed branch's editable development/signing installation described in `.github/workflows/ci.yml`.
Run each interpreter in its own environment and retain the existing workflow's console-script invocation.
The commands below identify acceptance checks, not results from this planning stage.

| Check | Required evidence |
| --- | --- |
| `pytest -q` | Complete suite passes on Python 3.11, 3.12, and 3.13; original tests and parameterizations are retained. |
| Focused example, lifecycle, and interchange tests | U2's regression and preserved signer/replay/legacy behavior pass. |
| `ruff check .` | Required CI lint passes; inherited failures are reported and resolved through the controller's scope process, never waived. |
| `mypy src` | Existing CI source type check passes on the supported matrix. |
| Documented `examples/migration_v4.py` entry point | Native and legacy demonstrations retain the output asserted by the existing subprocess test. |
| Existing core-only isolated import job | Core import succeeds without `cryptography` installed; example code has not become a core dependency. |
| Diff and publication review | No unrelated files or confidential content; controller records the replacement PR and required campaign reviews. |

Record command, exit status, commit, Python patch version, and resolved dependencies for each matrix environment.
The historical 137/19 counts orient preservation checks; compare collected test identities against the confirmed source rather than treating these counts as immutable when adding a regression.
An unrelated required check that remains red blocks a merge-ready claim even when the scoped repair is complete.

---

## Definition of Done

- The repair branch contains the confirmed `foli-2` work and this plan, with P1 and P2 resolved.
- U1 establishes the failure, U2 supplies a narrow repair with additive coverage, and U3 records fresh acceptance evidence.
- The complete suite passes on all three mandated Python versions, and required checks and reviews pass.
- No abandoned experimental code, weakened tests, schema/data changes, new services, or release changes enter the final diff.
- The build is simplified, reviewed, and committed locally; the controller publishes a replacement explicitly superseding PR #6 and the campaign gate completes merging.
- This planning-stage commit contains only the plan; it makes no implementation or passing-test claim.
