# Maintenance verification — 2026-11-08

Scope: [maintenance assurance plan](../2026-10-26-1419-chore-foli-3-maintenance-assurance-plan.md), on `drawdown/foli-3`. This is local execution evidence, not a hosted CI or campaign merge receipt.

## Intake and baseline

Intake HEAD was `c5cf3e7`, with the plan committed at `5e2c12c`, migration/signing tests at `2e29892`, and the core-wheel smoke at `c5cf3e7`. The unfinished workflow, coverage, dependency-audit and documentation edits already matched this item's scope. They were preserved, backed up and verified before completion. No package source or API behavior changed.

The original source, tests and project metadata from `90f94be` were extracted into a disposable directory without changing this branch. The original suite ran with the same Python 3.11.14 interpreter, dependency resolution, coverage 7.17.2 and branch/source/relative-path settings used for the final measurement. Baseline tests: **118 passed**. Baseline mypy: **six source files passed**. Baseline Ruff 0.17.4 reported one unused `DTZ001` suppression in `tests/test_lifecycle.py`; the existing `2e29892` commit removes that comment without changing the test or its assertions. The baseline was not wholly green.

No repository `AGENTS.md`, `CLAUDE.md`, handoff directory or `.planning/` was present. The chief campaign repository is not mounted; the controller still owns the campaign-source cross-check recorded in the plan. No remote or account lookup is needed for this local stage.

## Full suites

Linux x86_64; uv 0.9.22. Fresh development environments installed `.[dev,signing]`. Exact dependency inventories and audit outcomes appear in the [audit receipt](foli-3-audit.md).

| Interpreter | Full pytest suite | `ruff check .` | `mypy src` |
|---|---:|---|---|
| CPython 3.11.14 | 154 passed | Pass | Pass, six source files |
| CPython 3.12.12 | 154 passed | Pass | Pass, six source files |
| CPython 3.13.11 | 154 passed | Pass | Pass, six source files |

The added cases characterize migration downgrade/dispatch errors, restored temporary registry changes, detached nested migration copies, missing/null/noninteger versions, DID codec/key-length validation and signature decoding failures paired with a valid signature. Fifteen offline audit-gate cases verify accepted inventories, refusal before transmission, incomplete/malformed/skipped/vulnerable reports and preservation of the auditor's nonzero exit. Existing tests and assertions remain active.

## Coverage

The 3.11 run used `coverage run -m pytest -q`, `coverage report` and `coverage json`. Every package module is included. Counts below are statements covered/total and branches covered/total; the percentage combines both as coverage.py reports it.

| Module under `src/folio_propositions/` | Baseline statements | Final statements | Baseline branches | Final branches | Combined baseline → final |
|---|---:|---:|---:|---:|---:|
| `__init__.py` | 7/7 | 7/7 | 0/0 | 0/0 | 100.00% → 100.00% |
| `identity.py` | 42/42 | 42/42 | 8/8 | 8/8 | 100.00% → 100.00% |
| `interchange.py` | 142/148 | 147/148 | 63/72 | 66/72 | 93.18% → 96.82% |
| `lifecycle.py` | 112/115 | 112/115 | 47/50 | 47/50 | 96.36% → 96.36% |
| `models.py` | 112/112 | 112/112 | 24/24 | 24/24 | 100.00% → 100.00% |
| `signing.py` | 72/75 | 74/75 | 21/24 | 23/24 | 93.94% → 97.98% |
| **Total** | **487/499** | **494/499** | **163/178** | **168/178** | **96.01% → 97.78%** |

The persistent floor is **97%**, the final combined percentage rounded down. No module regressed. No omissions or exclusions were added; coverage.py's default exclusions account for the same 11 lines in both runs. Remaining missing statements are `interchange.py:280`, `lifecycle.py:94`, `lifecycle.py:155`, `lifecycle.py:212` and `signing.py:111`. The JSON report also identifies ten uncovered branches. Raising the command-line threshold to 100% returned exit **2**, demonstrating that the gate fails. See [coverage report semantics](https://coverage.readthedocs.io/en/latest/commands/cmd_report.html).

## Installed wheel and failure controls

A fresh Python 3.11 build environment installed the declared Hatchling requirements. `uv build --wheel --no-build-isolation` used that interpreter. Pre-build and post-build freezes matched byte for byte. A separate fresh core environment installed only the resulting wheel and its transitive core dependencies.

`python -I tests/core_smoke.py`: **six tests passed**. The script proved installation beneath the new environment's site-packages, wheel provenance, `py.typed`, absent `cryptography`, JSON round trips, migration and identity stamping without input mutation, accepting/rejecting verifier behavior, and ordered verification of every signed history entry. The synthetic verifier tests the protocol; real Ed25519 tests remain in pytest.

Running the smoke in the signing-enabled development environment failed as intended because `cryptography` was present. A separate core-only editable installation also failed the provenance test while passing the five consumer-operation tests. The audited wheel identifier and SHA-256 are in the audit receipt. No wheel was published or committed.

## Workflow and documentation

The workflow parses as YAML and keeps its Python 3.11–3.13 matrix, full pytest/Ruff/mypy checks, read-only contents permission, PR concurrency cancellation, original triggers and bounded job timeouts. All embedded shell steps and `scripts/audit-dependencies.sh` pass `bash -n`; there is no `continue-on-error`. The coverage leg collects the full suite. Core-wheel build and both backend/core audits run independently from development environments. Exact inventories, complete reports and successful exit codes are required by the audit gate.

A real pip-audit negative control queried one synthetic nonexistent package with the same strict, no-resolver options. Collection failed with exit **1**, confirming that unavailable advisory evidence cannot report success. This package was a failure probe, not an application dependency.

The README's development, coverage, wheel-build and audit command sequences were exercised with disposable environment names. Current documentation distinguishes structural validation, signature verification and consumer authorization, and no longer implies model immutability. Documentation links and named public exports were checked against the checkout. `git diff --check` passed.

This library has no frontend change, so a Playwright screenshot is inapplicable. Hosted Actions execution and the campaign's Astra/Fable PR reviews remain controller-owned; local checks do not claim to replace them. No schema migration, data rewrite, release, outside service integration or user decision was introduced.

## Local review and delivery

The LFG simplification pass used five separate reviews for reuse, quality, efficiency, test value and comments. It retained all logic and proof tests and removed four redundant prose-comment lines from the audit script. The 15 audit-gate tests, Ruff and mypy passed after that cleanup.

The subsequent `ce-code-review` checked the complete diff from `90f94be`, including the cleanup, against the explicit plan. Its scope helper counted 69 executable non-test changed lines and no full-review floor; the skill selected its in-context correctness review. All seven requirements and five implementation units were covered, with no actionable findings or unresolved local test gaps. This local review does not replace the campaign's required PR reviews.

All deliverables are committed on `drawdown/foli-3`. No remote is configured; no push, PR creation or hosted CI watch was attempted. The controller owns publication and the remaining campaign gates.
