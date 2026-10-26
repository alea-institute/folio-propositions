# foli-2 build verification

Plan: [Authorized Signer and Lifecycle Migration Examples](../2026-10-26-1342-feat-foli-2-migration-examples-plan.md)

Branch: `drawdown/foli-2`. Item kind: expansion. Verified on 2026-10-26.

## Delivered

- `examples/migration_v4.py` demonstrates caller-owned signer authorization,
  native signed-history reconstruction, obsolete-event rejection, and explicit
  trust for an unsigned legacy migration anchor.
- `tests/test_migration_examples.py` adds 19 integration cases using the shipped
  helpers and real ephemeral signatures, including the script entry point.
- `docs/migration-0.4.0.md` supplies runnable instructions, expected output, and
  the trust boundaries. `README.md` links to the walkthrough.
- Library source, existing tests, dependencies, schemas, CI, and deployment
  configuration are unchanged.

## Verification results

Environment: Python 3.13.11, pytest 9.1.1, Ruff 0.17.2, mypy 2.4.0.

| Check | Result |
| --- | --- |
| Baseline `.venv/bin/pytest -q` | 118 passed. |
| Final `.venv/bin/pytest -q` | 137 passed. |
| Focused example, lifecycle, and interchange suites | 85 passed. |
| `.venv/bin/mypy src examples/migration_v4.py` | Passed for all seven files. |
| Ruff on the new example and test file | Passed. |
| Repository-wide `.venv/bin/ruff check .` | Same baseline RUF100 finding at `tests/test_lifecycle.py:341`: unused `noqa: DTZ001`. Existing test left unchanged; this is not a regression from foli-2. |
| `.venv/bin/python examples/migration_v4.py` | Both demonstrations completed with the documented output. |
| Signed-transition Python fragment in the migration guide | Executed successfully from the checkout. |
| Core-only isolated import | Passed in a separate environment with no `cryptography` installed. |
| Documentation links and `git diff --check` | Passed. |

The native walkthrough test first failed because the example file did not exist.
The legacy walkthrough test first failed because `legacy_demo` did not exist.
Both passed after implementation. The entry-point test characterizes the real
script through a subprocess. No existing test was deleted, changed, or weakened.

## Review and controller follow-through

Simplification removed one redundant comment and preserved the proof tests.
Six local review lenses completed: correctness, testing, security,
maintainability, reliability, and adversarial. They reported no findings;
requirements R1–R7 and implementation units U1–U3 were checked as met.

The checkout disables the external cross-model review. The controller retains
the campaign's Astra/Fable review gates and Python 3.11/3.12 CI verification.
The pre-existing Ruff finding remains for the separate hygiene item, `foli-3`.

The chief campaign plan was unavailable in this sandbox, consistent with plan
assumption A4. The supplied lane rules governed the build; the controller must
reconcile the named campaign excerpts.

There is no front-end change, so browser testing and screenshot evidence do not
apply. There is no held schema/data change, release, outside service, or user
decision. Commits are local; this clone has no remote. The controller owns push,
PR creation, and the campaign merge gate.
