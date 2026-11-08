# Foli-5 build prerequisite verification

Date: 2026-11-08

Status: **Blocked before implementation.** This is a fresh prerequisite receipt,
not evidence that PR #6 has been repaired or that any acceptance check passed.

Work source: `docs/plans/2026-11-08-1605-fix-foli-5-migration-ci-plan.md`.

## Verified checkout

| Check | Result |
| --- | --- |
| `git status --short` at entry | Empty; the working tree was clean. |
| `git branch --show-current` | `drawdown/foli-5`. |
| `git show-ref` | Repair branch at `6edd04bc6bae9e43c101d41aca99b195939e9916`; `main` at `90f94bea43ce6f63176cd6271c7006c72f528dd3`; neither `drawdown/foli-2` nor `origin/drawdown/foli-2` exists. |
| `git log -6 --oneline` | The repair plan follows v0.5.0 merge `be8db76172f3e5a792bf19823b709db2a4512eea`. |
| `git remote` | Empty, as required by the sandbox delivery contract. |
| `git ls-tree -r --name-only HEAD` | Neither `examples/migration_v4.py` nor `tests/test_migration_examples.py` is in the supplied checkout. No repository `AGENTS.md`, `CLAUDE.md`, handoff directory, or `.planning/` is present. |
| `git cat-file -t 37ad3b828b0112ac52366985f3fcb590b989ecf4` | The historical candidate remains available as a commit object. |
| `git log -5` at that candidate | The five-commit migration-example chain recorded in the plan remains inspectable. |
| `git branch --contains` that candidate | Empty; no local branch contains it. |
| Candidate tree inspection | Contains the migration example, its tests, and `docs/plans/evidence/foli-2-verification.md`. This does not establish PR #6's authoritative head. |

Local inspection did not locate the chief repository's campaign plan or
`ops/drawdown/mandates/_common.md`. The supplied lane rules remain available,
but the independent authority reconciliation required by P2 is still missing.
No remote was added, no account lookup was attempted, and no credentials were
read.

## Unresolved prerequisites

1. **P1 — authoritative source and branch provisioning.** The required source
   ref is absent. Candidate `37ad3b8` is historical evidence, not a confirmed
   PR #6 head. Restoring its files onto the v0.5.0 tree would not meet the
   mandate's branch-origin requirement or the plan's explicit build entry.
2. **P2 — campaign authority.** The chief plan's Goal Capsule and R11, R15,
   R16, R17, R19, and R20, plus the applicable common mandate, were not supplied
   in the local repository material.

These are controller provisioning requirements. Neither requires a product
decision, account login, credential, or security-setting change from Damien.

## Execution and verification status

The `lfg` plan route stopped at work-source readiness after `ce-plan` resume
revalidation. The existing plan remains unchanged; further planning cannot
confirm a missing source ref or supply the absent authority excerpts.

U1, U2, and U3 are **not completed**. No defect has been reproduced, no regression
test added, and no implementation changed. Python 3.11, 3.12, and 3.13 test runs,
lint, type checking, example execution, and the isolated core import were not
run. Testing the supplied v0.5.0 tree would not verify the missing PR #6 change.
Simplification, implementation review, browser tests, and publication were not
reached. No front-end change or screenshot applies.

The only build-stage change is this receipt. `git diff --check` verifies its
whitespace before the local commit; that check is not acceptance evidence for
the repair. There is no replacement PR yet, and no push or merge was attempted.

## Controller recovery

1. Confirm PR #6's authoritative head against candidate `37ad3b8` and provision
   the corresponding `drawdown/foli-2` source ref in the clone.
2. Preserve the existing plan, this receipt, and the supplied v0.5.0 history in
   reachable references. Provision `drawdown/foli-5` from the confirmed source
   and carry the plan and receipt forward, recording the old and new bases.
3. Supply the chief Goal Capsule, the cited campaign R-IDs, and applicable
   common-mandate guidance so P2 can be reconciled.
4. Resume `lfg` on the same plan. Reproduce the failing CI command at the
   confirmed head before selecting a repair; retain all original tests and
   complete the three-version verification contract.
5. After a verified local repair, the controller publishes a replacement that
   explicitly supersedes PR #6 and runs the campaign review and merge gates.
