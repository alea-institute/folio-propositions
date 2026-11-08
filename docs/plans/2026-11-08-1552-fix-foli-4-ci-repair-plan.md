---
title: Foli-4 CI Repair and Reverification - Plan
type: fix
date: 2026-11-08
artifact_contract: ce-unified-plan/v1
product_contract_source: ce-plan-bootstrap
execution: code
item: foli-4
kind: expansion
---

# Foli-4 CI Repair and Reverification - Plan

## Goal Capsule

- **Objective:** Consumers can adopt PR #5's shared shard identity fixtures with passing checks on every supported Python version.
- **Means:** Preserve the current `foli-1` work, reverify its matrix, and deliver the requested superseding PR under KTD1–KTD3.
- **Authority:** The supplied `foli-4` mandate and standing drawdown rules govern this item. The chief repository's `docs/plans/2026-10-26-0705-feat-codex-drawdown-campaign-plan.md`, Goal Capsule and R11, R15, R16, R17, R19, and R20, remains the campaign authority; its availability gap is recorded below. The content contract is `README.md` → Content identity.
- **Execution profile:** One branch, `drawdown/foli-4`, and one controller-published PR superseding #5. This stage commits only this plan. The later build stage uses `lfg`; the controller handles scanning, publication, and campaign review, and the campaign gate handles merging.
- **Stop conditions:** Hold affected build work while the required source ref is missing or a proposed repair would violate R2 or R4. Report missing evidence without claiming that the repair or matrix verification is complete.

## Product Contract

### Summary

Reverify the current PR #5 head and retain its consumer fixtures in the replacement PR.
The latest observed matrix is already green, so no code defect is established for repair.

### Problem Frame

The mandate reports CI failures on Python 3.11, 3.12, and 3.13.
PR #5 subsequently moved to a different head, while this planning checkout lacks both that head and the required source branch.
Treating either the old failure report or this checkout as the repair baseline would risk changing the wrong revision.

### Requirements

**Preservation and repair scope**

- R1. Start build work on `drawdown/foli-4` from the verified current `drawdown/foli-1` local ref, or its supplied `origin/drawdown/foli-1` ref, preserving all of PR #5's work.
- R2. Limit repairs to a reproduced failure in the `foli-1` change; preserve the README identity contract, every existing test and assertion, and all golden fixture values.
- R3. Pass the existing CI test command, `pytest -q`, independently on Python 3.11, 3.12, and 3.13, including the repository's full suite.
- R4. Add focused regression coverage for any actual repair, without deleting, weakening, skipping, or marking an existing test as expected to fail (campaign R15–R16).

**Delivery**

- R5. Produce a controller-published replacement PR that explicitly supersedes #5 and retains the original fixture work (campaign R17, R19).
- R6. Keep this lane local and credential-free; the controller owns remote operations and campaign acceptance (campaign R11, R15, R19, R20).

### Scope Boundaries

The current stage changes only this plan.
Build-stage verification reads the existing fixture, identity, interchange, lifecycle, model, and conformance suites without changing them.
The expected build artifact is `docs/plans/evidence/foli-4-verification.md`, recording revision-specific results for controller publication.
No production-code change is justified by the evidence currently available.

If revalidation exposes a real failure, KTD3 governs a focused amendment before any repair.
Known `foli-1` files are `tests/test_consumer_compatibility.py`, `tests/fixtures/shared_shard_identity_v1.json`, `docs/consumer-compatibility.md`, `README.md`, and `docs/README.md`.
These paths identify the original change, not blanket permission to edit all of them.

Excluded: identity-recipe changes, fixture regeneration, dependency pins or upgrades, CI/workflow changes, broad test cleanup, new runtime APIs, schema migrations, data rewrites, package releases, outside services, deployment changes, spend, credentials or security-setting changes, messages in the user's voice, deletions without verified backups, and force-pushes.
No frontend change is planned, so the screenshot guardrail does not apply.
A new check framework would duplicate the existing matrix without addressing a demonstrated failure and is not planned.

`foli-2`, `foli-3`, and `foli-5` remain separate mandate items.

## Planning Contract

### Reverified Starting State

Observed on 2026-11-08:

| Evidence | Finding | Consequence |
|---|---|---|
| Local branch and working tree | Clean `drawdown/foli-4` at `be8db76172f3e5a792bf19823b709db2a4512eea` (`v0.5.0`) before this plan | This is the current upstream base, not the PR #5 head. |
| Local refs | `main` is `90f94bea43ce6f63176cd6271c7006c72f528dd3`; neither required `foli-1` ref exists; no remote is configured | R1 is an unmet build prerequisite. |
| Unreferenced Git objects | Original `foli-1` chain: `63ba753` → `9ca7d4c` → `213b845` → `5b4a4fa` | Available for historical inspection only; not a substitute for the newer PR head. |
| Original fixture change | 29 JSON cases, a consumer test module, reuse documentation, README links, and the original plan | Preserve the original deliverable; do not rebuild it from memory. |
| Repository instructions | No accessible repository or ancestor `AGENTS.md`/`CLAUDE.md`; no `docs/handoffs/`, `.planning/`, or `docs/solutions/` | Supplied lane instructions apply. The existing `docs/plans/2026-10-09-ci-drain.md` documents the CI lane. |
| Existing CI | `.github/workflows/ci.yml` installs `.[dev,signing]`, runs pytest, Ruff, and mypy on 3.11–3.13, and checks a core-only import separately | Reuse these checks without changing the workflow. |

The public PR API identifies the open [PR #5](https://github.com/alea-institute/folio-propositions/pull/5) head as `8cf35db6898175590593ae8f81dffd40db5161ce` on `drawdown/foli-1`, based on `be8db76172f3e5a792bf19823b709db2a4512eea`.
That head is absent from the local object database.

[CI run 41106707701](https://github.com/alea-institute/folio-propositions/actions/runs/41106707701) completed successfully on 2026-10-30 for that head.
The public job metadata reports successful Test, Lint, and Type check steps on [3.11](https://github.com/alea-institute/folio-propositions/actions/runs/41106707701/job/124238316955), [3.12](https://github.com/alea-institute/folio-propositions/actions/runs/41106707701/job/124238317405), and [3.13](https://github.com/alea-institute/folio-propositions/actions/runs/41106707701/job/124238316583).
The [core-only import job](https://github.com/alea-institute/folio-propositions/actions/runs/41106707701/job/124238317065) also succeeded.
These are prior CI observations, not fresh local test results or proof about the future replacement PR.
No tests, dependency installs, or product runtime probes were performed during planning.

### Prerequisites and Evidence Gaps

- **Controller prerequisite — source lineage:** Supply the current `foli-1` ref and a build checkout descending from it, retaining this plan commit without destructive history changes. Verify the supplied SHA against PR #5 again because the head can advance. Do not attach the old unreferenced tip or copy individual files to simulate ancestry.
- **Controller prerequisite — campaign authority:** The chief repository and requested campaign plan were unavailable in this isolated checkout. Its Goal Capsule and cited R-IDs were not independently read. The controller must provide or compare those exact sections before build acceptance; the supplied standing rules are the available restatement.
- **Build-time evidence:** Interpreter patch versions, dependency versions, fresh full-suite results, and any new failure belong to the later build. The historical PR description's test count and lint claim are not acceptance evidence for the newer head.

These prerequisites do not require a user login, credentials, or a taste decision.
The worker must not add a remote or search for authentication material to satisfy them.

### Key Technical Decisions

- KTD1. **Use the current PR head as the source of truth.** The branch requirement in R1 excludes the clean but incomplete planning checkout and the obsolete unreferenced tip. The controller must resolve lineage before the build can verify the requested work.
- KTD2. **Reverification is the supported implementation path.** The successful run supersedes the mandate's unverified failure assumption. Preserve the current implementation and collect fresh evidence for R3; no speculative patch is planned.
- KTD3. **A newly reproduced failure requires a specific repair amendment.** Record the exact test or CI step, interpreter, dependency versions, failing assertion, and causal `foli-1` change. Amend this plan with the affected file, minimal repair, and regression scenario before editing code. A failure outside R2 remains a reported blocker rather than an expanded cleanup task.
- KTD4. **Keep publication with the campaign controller.** R5–R6 define the delivery boundary. (session-settled: user-directed — chosen over holding every expansion for personal approval: the campaign authorizes merges behind its review and verification guardrails.)
- KTD5. **Retain the campaign's model choices.** Local work uses Astra; cloud builds use Codex Cloud's default Sol and still pass Astra and Fable reviews. (session-settled: user-directed — chosen over the Sol-first local ladder and forced cloud elevation: the campaign's supplied instructions settle these choices.)

### Assumptions

- The successful public run suggests that a fresh run of the supplied current head will need no code repair; this remains unverified locally.
- A replacement PR carrying the preserved fixture commits plus this plan and a verification receipt satisfies the requested supersession without manufacturing a code change.

## Implementation Units

### U1. Reverify the preserved fixture change

**Goal:** Establish passing results for the actual `foli-1` work on all three required interpreters.

**Requirements:** R1–R4, R6. **Dependencies:** Both controller prerequisites above.

**Files:** Read `.github/workflows/ci.yml`, `pyproject.toml`, `tests/test_consumer_compatibility.py`, `tests/fixtures/shared_shard_identity_v1.json`, `tests/test_identity.py`, `tests/test_interchange.py`, `tests/test_models.py`, `tests/test_lifecycle.py`, and `tests/test_conformance.py`; create `docs/plans/evidence/foli-4-verification.md`.

**Approach:** Follow KTD1–KTD3. Verify branch ancestry and preserved files, then run the existing checks in isolated environments for each supported interpreter using the documented development/signing dependencies and provided dependency cache. Record the source SHA, tested SHA, interpreter patch versions, dependency versions, commands, exit results, and collection counts in the receipt. Normalize any reported paths to repo-relative form.

**Execution note:** Establish the actual baseline before considering edits. A green baseline completes this unit through verification evidence alone; a failure activates KTD3 and prevents a completion claim.

**Patterns to follow:** `README.md` → Development checks, `.github/workflows/ci.yml`, and the original `docs/plans/2026-10-26-1318-feat-shared-shard-consumer-fixtures-plan.md` when supplied with the source branch.

**Verification scenarios:**

1. All original eight golden anchors and all 29 portable cases remain present with unchanged raw inputs and expected identities.
2. The existing consumer suite still checks normalization equivalence and distinctions, malformed fixtures, shared stamps, JSON round-trip, missing sources/text, and mismatched stamps without skips or weakened assertions.
3. Each required interpreter executes the same full-suite CI test command, including all existing lifecycle and conformance tests, and reports success independently.
4. The existing lint, type, and isolated core-import gates remain passing under the Verification Contract.
5. A missing interpreter, unavailable dependency, collection error, or unexplained test-count reduction is recorded as missing acceptance evidence, not a pass.

**Test expectation:** No new behavior is proposed, so no new test is justified on the green path. R4 and KTD3 require a concrete regression test before any later repair is accepted. The consumer test seam proves local fixture compatibility; it does not prove execution inside sibling products.

**Verification:** The receipt proves R1 and R3 against the supplied current head, with any unresolved failure explicitly recorded.

### U2. Prepare the superseding publication

**Goal:** Give the controller enough evidence to publish the requested replacement for PR #5.

**Requirements:** R2, R4–R6. **Dependencies:** U1.

**Files:** Complete `docs/plans/evidence/foli-4-verification.md`; preserve all original `foli-1` files.

**Approach:** Apply KTD4–KTD5. Review the final diff against both the supplied source head and the upstream base. Record whether a repair was necessary, retain the complete original fixture work, and give the controller a publication handoff that identifies #5 as superseded. Keep test evidence tied to the final code tree; rerun affected checks after any repair.

**Test expectation:** No new behavior. Review the receipt and preservation diff; U1 supplies the behavioral evidence.

**Verification:** Local commits are ready for controller scanning and publication, and the handoff distinguishes completed local work from the replacement PR and campaign reviews that remain controller-owned.

## Verification Contract

Checks below belong to the build stage and use the owning configuration at the verified source revision.
An unavailable check remains unmet until the controller or build environment supplies an observed result.

| Check | Evidence | Required outcome |
|---|---|---|
| Source preservation | Branch ancestry and diff against the supplied `foli-1` SHA | R1 holds; no fixture work is lost and no unrelated work enters the change. |
| Python 3.11 | `pytest -q` with `.[dev,signing]` | Complete suite passes; record exact interpreter and dependency versions. |
| Python 3.12 | Same CI command and extras | Complete suite passes independently. |
| Python 3.13 | Same CI command and extras | Complete suite passes independently. |
| Lint and types | `ruff check .` and `mypy src` on each matrix interpreter | Existing checks pass without suppressions. |
| Core-only import | Existing isolated `python -I` check in `.github/workflows/ci.yml`, in a separate Python 3.11 environment | Core package imports while `cryptography` is absent. |
| Conformance drift | Existing full-suite conformance checks and documented `scripts/generate_conformance.py --check` | Existing generated artifacts agree; no regeneration or expected-value rewrite. |
| Test integrity | Review assertions, parametrized cases, and collection counts against the source head | R2 and R4 hold; any actual repair has specific regression coverage. |
| Replacement PR | Controller-provided PR link, source head, final checks, and campaign review results | R5–R6 hold; the new PR explicitly supersedes #5. |

## Definition of Done

- U1 and U2 satisfy R1–R6, including fresh results for every required Python version.
- PR #5's original work survives intact, and any repair has a reproduced cause and additive regression evidence.
- The controller has published the superseding PR and completed the required campaign checks; the worker reports publication as pending until observed.
- No abandoned code, temporary environment files, credentials, or unrelated artifacts enter the diff.
- If the baseline stays green, the receipt states that no code repair was needed rather than inventing one.
