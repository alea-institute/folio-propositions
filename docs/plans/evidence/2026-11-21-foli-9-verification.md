# Additive CI maintenance verification

Plan: [Preserve CI Steps While Landing Maintenance](../2026-11-21-1429-fix-foli-9-preserve-ci-steps-plan.md).

This receipt records fresh checks for `foli-9` on 2026-11-21 (2026-11-22 UTC).
The controller's new PR supersedes #13 and #10. No remote is configured in this
lane; publication, hosted CI, campaign reviews, and merging belong to the
controller. Earlier receipts are historical evidence only.

## Restored scope

All ten commits after the merge base through
`814cb5078b070e75bd7a7111e26854c9ac03380a` were cherry-picked in order without
conflicts. Their script, tests, tooling, documentation, and historical receipts
are present. The complete 15-file source payload was retained; the subsequent
correction changes CI and development instructions, not the restored tests.

The lane baseline was `92a30ab2ee5b206ecd688d88938fae76208ba8ce`; the committed
item plan was `8be65a3`. Local `main`, `90f94bea43ce6f63176cd6271c7006c72f528dd3`,
is older than that baseline, so the full diff against `main` includes work that
predates this item. Both comparisons were inspected. No runtime package source,
package version, schema/signing version, conformance asset, consumer fixture, or
migration example was changed by this item.

AST comparison confirmed that every test function from the lane baseline is
unchanged. No existing test or assertion was removed or weakened.

## CI preservation

The workflow at `main` and the lane baseline is identical. Parsed workflow
comparison against each reference verified that:

- All six original named steps remain, with their exact command blocks and
  conditions, in the same jobs and relative order.
- `Install core dependencies only` and `Verify isolated core import` remain
  verbatim, before the three appended wheel and audit steps.
- `Test` still runs `pytest -q` unconditionally on 3.11, 3.12, and 3.13.
  Python 3.11 additionally runs the separate branch-coverage step.
- Original unnamed action steps, action pins, job identities, timeouts, matrix,
  permissions, triggers, and concurrency settings are unchanged.
- `git diff main -- .github/workflows/ci.yml` contains no removed `- name:` line.
  The workflow delta is entirely additive.

The YAML parsed successfully, `bash -n scripts/audit-dependencies.sh` passed,
and every workflow `run` block passed `bash -n`. The actual command blocks were
then executed in fresh environments as described below; this is local execution,
not a claim that GitHub Actions itself ran.

## Tested snapshot and isolation

- Commit: `ec2fd3455541feeb1de7074a48835d2cc2a08808`.
- Tree: `281b1e04cd95d26010c13fdf63d006871b154827`.
- Toolchain: CPython 3.11.14, 3.12.12, and 3.13.11.

Four fresh copies came from `git archive` of that commit, each initialized with
temporary Git metadata so Ruff honored `.gitignore`. The three development
copies installed `-e '.[dev,signing]'` into their own `.venv`. A fourth copy ran
the separate core-import job. No pre-existing environment or artifact was
overwritten or deleted.

Each job's `run` blocks were extracted from the committed YAML and executed
under `bash` with error checking. `UV_PYTHON` selected the matrix interpreter;
the local runner supplied `GITHUB_WORKSPACE`, a scratch `GITHUB_PATH`, and the
job's `.venv/bin` on `PATH`. The 3.11 coverage condition was honored. This ran
both original core command blocks exactly, including their path export.

Later receipt/index changes affect documentation only. The wheel hash below
identifies the tested snapshot, not a later rebuild with updated README metadata.

## Fresh results

| Check | Python 3.11.14 | Python 3.12.12 | Python 3.13.11 |
|---|---|---|---|
| `pytest -q` | 380 passed | 380 passed | 380 passed |
| `ruff check .` | Passed | Passed | Passed |
| `mypy src` | Passed, 6 files | Passed, 6 files | Passed, 6 files |
| `python scripts/generate_conformance.py --check` | Passed | Passed | Passed |
| Exact development/signing audit | 25 pins, clean | 25 pins, clean | 25 pins, clean |

Python 3.11 additionally passed:

- `pytest -q tests/test_interchange.py tests/test_signing.py tests/test_dependency_audit.py`:
  **63 passed**.
- `coverage run -m pytest -q`: **380 passed**.
- `coverage report`: **97.83%**, above the unchanged **97%** floor; 510 statements,
  5 missed statements, 180 branches, and 10 partial branches. All package modules
  were measured without new exclusions.

The isolated core job passed both the original editable import and the six
standalone `tests/core_smoke.py` methods against the installed wheel, with
`cryptography` absent. These verify wheel provenance and `py.typed`, JSON/null
round trips, migration/stamping input ownership, independent schema-4 payload
bytes, rejected-signature input ownership, and ordered history replay. Its
synthetic verifier checks protocol; real Ed25519 coverage remains in pytest.

The inventoried backend did not change across the build (`cmp` passed).
Wheel: `dist/folio_propositions-0.5.0-py3-none-any.whl`.
SHA-256: `0c2f17b9d25571fff891042dc2d0b91e4fda104ef58b5402a2164587bc24a55f`.

## Exact dependency audits

All five audits passed `uv pip check` and the script's complete-inventory
validation. Isolated `pip-audit` 2.10.1 queried PyPI advisory data with no skipped
packages or known vulnerabilities. Only validated third-party pins were sent;
local package origins and raw freeze files remain outside committed evidence.

The 25 development/signing pins were identical on all three interpreters:

```text
annotated-types==0.8.0
ast-serialize==0.13.1
attrs==26.1.0
cffi==2.1.1
coverage==7.17.4
cryptography==50.0.2
iniconfig==2.3.1
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
librt==0.17.0
mypy==2.4.1
mypy-extensions==1.2.0
packaging==26.3
pathspec==1.1.1
pluggy==1.7.0
pycparser==3.12
pydantic==2.14.4
pydantic-core==2.50.5
pygments==2.21.0
pytest==9.2.0
referencing==0.37.0
rpds-py==2026.9.1
ruff==0.17.6
typing-extensions==4.16.0
typing-inspection==0.4.5
```

The six actual build-backend pins were:

```text
hatchling==1.33.0
packaging==26.3
pathspec==1.1.1
pluggy==1.7.0
tomlkit==0.15.2
trove-classifiers==2026.9.21.13
```

The five installed core-wheel dependency pins were:

```text
annotated-types==0.8.0
pydantic==2.14.4
pydantic-core==2.50.5
typing-extensions==4.16.0
typing-inspection==0.4.5
```

The advisory result applies to these exact resolutions at scan time, not every
version allowed by the dependency ranges. The auditor warns that fully hashed
pins provide stronger artifact integrity; these exact-version advisory checks
do not claim to provide that guarantee. Existing refusal-path tests cover
unexpected origins, stale/wrong-location wheels, empty or malformed inventories,
incomplete or vulnerable reports, and nonzero auditor exits.

## Local review

The five simplification reviews covered reuse, code quality, efficiency, test
value, and comments. They found no actionable changes; all proof tests remain
unchanged. The subsequent `ce-code-review` correctness pass covered commit
`60b60450d52d20ed23b333d4cf0cd4a1d70ed92d` against the lane baseline, including
plan completeness, workflow preservation, audit refusal behavior, and test
sufficiency. It found no actionable issues or unsettled-decision conflicts.
The skill selected its inline review path; no independent cross-model
correctness review ran locally. The campaign reviews remain controller checks.

Final inspection confirmed that all restored payload files are byte-identical
to the supplied source head except the intended workflow and documentation
adjustments. Documentation links resolve, the item diff passes `git diff --check`,
and no machine-local paths appear in added or changed Markdown artifacts.
This review addendum changes only the receipt.

## Delivery limits

The chief repository's campaign Goal Capsule and cited campaign requirements
remain unavailable in this isolated lane. The controller must reconcile them,
compare its actual publication base, run hosted CI and the campaign's Astra and
Fable reviews, and repeat verification if integration changes executable content.

There is no frontend or browser route, so browser testing and a Playwright
screenshot do not apply. No schema migration, data rewrite, package release,
new outside service, deploy change, credential access, spend, or send was needed.
No user-only decision or held change was identified.
