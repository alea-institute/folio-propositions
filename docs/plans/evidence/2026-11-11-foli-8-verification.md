# Maintenance landing verification — 2026-11-11

This is fresh local evidence for `foli-8`. The controller's replacement PR
supersedes **PR #10**. No remote, push, PR creation, merge, or deployment was
attempted in this lane. Hosted CI and campaign Astra/Fable reviews remain the
controller's responsibility.

## Source and scope

- Supplied lane base: `6729ace779b610b8c4081990e496dfdc56b48073`.
- Local `main`: `90f94bea43ce6f63176cd6271c7006c72f528dd3` (older than the lane).
- Committed build plan: [maintenance landing plan](../2026-11-11-0253-chore-land-maintenance-assurance-plan.md).
- Source PR head: `a714cb1708d5bfa74bd68841ef9ffd3a6ba68eb4`.
- Tested implementation snapshot: `55d17aeae5247e8376b55059e396e448e224d2b3`,
  tree `22ccde340231181be18fe6bcc85537daf1ea8469`.

All five requested source commits were cherry-picked, in order:

| Source | Restored commit |
|---|---|
| `5e2c12c` | `f52459d` |
| `2e29892` | `ae6e3fc` |
| `c5cf3e7` | `9571b8e` |
| `c520761` | `805472b` |
| `a714cb1` | `1b7ad89` |

No commits were skipped. Conflicts in `README.md` and `pyproject.toml` were
resolved by retaining current lifecycle actions, conformance guidance, consumer
links and `jsonschema`, alongside the maintenance documentation and `coverage`.
The lifecycle test comment change was already present; that file is unchanged.
The restored auditor's hardcoded accepted 0.4.0 wheel failed as predicted. The
fixture now obtains its accepted version from project metadata; stale 0.4.0 and
misplaced current-version wheels are additional rejection cases. Assertions
and original tests remain intact.

Both `git diff main` and `git diff 6729ace` contain substantive tooling and test
changes. The latter is this item's scope: no runtime source, conformance asset,
consumer fixture, lifecycle test, schema version, or package version changed.
The broader `main` diff includes pre-existing lane work and is not a claim about
the controller's publication base. Version remains 0.5.0; schema and signing
payload remain 4. No release, migration, outside service, or frontend was added.

The chief repository and its campaign plan were unavailable. The controller must
compare the supplied campaign Goal Capsule and cited rules, its real publication
base, and resulting integration tree before accepting the replacement PR.

## Fresh checks

Fresh environments used `.[dev,signing]`; all three resolved the same 25 public
dependencies listed below. The baseline environment included the same coverage
tool for comparison, and its public dependency pins match those final inventories.

| Check | Result |
|---|---|
| Before restoration, Python 3.11.14 | 323 tests passed; Ruff and mypy passed |
| Restored focused interchange, signing and audit tests | 63 passed |
| Full suite, Python 3.11.14 | 361 passed |
| Full suite, Python 3.12.12 | 361 passed |
| Full suite, Python 3.13.11 | 361 passed |
| Ruff and mypy, all three environments | Passed; six source modules type checked |
| Generated conformance check, all three environments | Passed |
| YAML and embedded Bash | YAML parsed; nine shell steps and audit script parsed |
| Workflow protections | Matrix, read-only permission, timeouts, cancellation and action refs retained; no `continue-on-error` |
| Documentation links and diff whitespace | Passed |

Commands were `pytest -q`, `ruff check .`, `mypy src`, and
`python scripts/generate_conformance.py --check`, through each environment.
Python 3.11 additionally ran `coverage run -m pytest -q`, `coverage report`, and
`coverage json`. Combined statement/branch coverage rose from **96.09%**
(498/510 statements and 165/180 branches) to **97.83%** (505/510 statements and
170/180 branches). The unchanged 97% floor passes. A 99% threshold failed with
exit 2 as expected. Existing exclusions were unchanged; none were added.

The verification tree was copied from the committed tree into fresh storage.
An initial lint attempt found generated virtual-environment activation scripts:
Ruff does not honor `.gitignore` without Git metadata. The README recipe now
initializes a local temporary Git repository; the identical `ruff check .`
command passes. Two extra matrix-environment directories were ignored locally
in that temporary repository only. No source/test lint exclusion was added.
The README-only correction was copied into the verification tree, with all
other tracked inputs unchanged, before the final wheel was built.

## Installed wheel

The build backend was inventoried before and after `uv build --wheel
--no-build-isolation`; inventories matched. Earlier artifacts were preserved
outside `dist/` before the final build, leaving that directory empty.

- Wheel: `dist/folio_propositions-0.5.0-py3-none-any.whl`.
- SHA-256: `2c67c66949458aaefc5587afc767da8d3fe2bd7814ecc435da8022f4813af115`.
- A separate fresh core environment installed that exact wheel.
- `python -I tests/core_smoke.py`: all six checks passed, including wheel
  provenance, typing marker, absent cryptography, serialization, migration,
  stamping, verifier protocol and ordered history replay.
- Separate editable-core and wheel-with-signing environments each failed the
  provenance/isolation check with exit 1; the five functional checks passed.

The smoke's verifier is synthetic and proves protocol behavior. Real Ed25519
verification is exercised by the development suite. Documentation changes in
this receipt do not alter package build inputs.

## Live dependency audits

Tool versions: uv 0.9.22, pip-audit 2.10.1, coverage 7.17.2, pytest 9.2.0,
Ruff 0.17.4, mypy 2.4.1. YAML validation used PyYAML 6.0.3 separately.

The restored `scripts/audit-dependencies.sh` ran with an isolated auditor for
all three development environments (25 pins each), the build backend (6 pins),
and the exact final installed wheel's core environment (5 pins). Every run
passed compatibility checks and complete matching advisory results with zero
skipped packages and zero known vulnerabilities. The original core environment
was also audited successfully before the documentation-only wheel rebuild.

The live missing-package control failed with exit 1 and an explicit collection
error. Offline fixtures also retain rejection of malformed/incomplete/duplicate,
skipped, version-mismatched and vulnerable reports, unexpected origins and a
nonzero auditor exit despite clean-looking JSON. No advisory failure was
suppressed. Audits describe these resolutions at scan time, not every allowed
version or future advisory state. Raw freezes and reports remain untracked;
only public package pins appear below.

### Development and signing — same inventory on all three versions

```text
annotated-types==0.8.0
ast-serialize==0.13.1
attrs==26.1.0
cffi==2.1.1
coverage==7.17.2
cryptography==50.0.2
iniconfig==2.3.1
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
librt==0.16.0
mypy==2.4.1
mypy-extensions==1.2.0
packaging==26.3
pathspec==1.1.1
pluggy==1.7.0
pycparser==3.12
pydantic==2.14.3
pydantic-core==2.50.4
pygments==2.21.0
pytest==9.2.0
referencing==0.37.0
rpds-py==2026.9.1
ruff==0.17.4
typing-extensions==4.16.0
typing-inspection==0.4.5
```

### Build backend

```text
hatchling==1.33.0
packaging==26.3
pathspec==1.1.1
pluggy==1.7.0
tomlkit==0.15.2
trove-classifiers==2026.9.21.13
```

### Installed core wheel dependencies

```text
annotated-types==0.8.0
pydantic==2.14.3
pydantic-core==2.50.4
typing-extensions==4.16.0
typing-inspection==0.4.5
```

The local `folio-propositions` distribution was 0.5.0 in development and core
environments and was excluded only under the auditor's exact local-origin rule.

## Delivery boundary

All required local maintenance checks passed. The repository has no frontend,
so browser screenshots do not apply. The controller owns the campaign authority
comparison, hosted matrix, Astra/Fable reviews, publication-base comparison,
and replacement PR that supersedes #10. No user-only blocker was found.
