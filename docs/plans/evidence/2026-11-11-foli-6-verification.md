# Shared shard consumer fixture landing verification

The consumer fixture payload from PR #5 is restored on `drawdown/foli-6`.
The controller's new PR supersedes #5 and #8.

## Scope and provenance

- Execution plan: `docs/plans/2026-11-11-0157-feat-land-shard-consumer-fixtures-plan.md`.
- Supplied lane base: `be8db76172f3e5a792bf19823b709db2a4512eea`.
- Source PR head: `8cf35db6898175590593ae8f81dffd40db5161ce`.
- Verified implementation head: `a8f345c947ee89dbd18e6844a9f6bba3aec3031e`.
- Four source commits cherry-picked without conflicts: `d5dc789`, `a11b63a`,
  `c73eb21`, and `a8f345c`.

The restored fixture, tests, guide, README links, and historical plan retain
the source PR's content. All 29 literal cases and eight original golden anchors
remain intact. No compatibility repair was needed in the tested environments.
The current runtime, existing tests, generated conformance assets, dependencies,
package version, and CI configuration are unchanged from the supplied lane base.

The fixture, test module, and guide appear in both the lane-base delta and the
diff against local `main`. Local `main` is `90f94be`; the supplied lane already
includes newer v0.5.0 work. That pre-existing work is not attributed to this item.

## Verification observed

Each development environment was created fresh and installed with
`uv pip install --python <venv>/bin/python -e '.[dev,signing]'`.
Commands below used the corresponding environment's executables.

| Check | Python 3.11.14 | Python 3.12.12 | Python 3.13.11 |
|---|---|---|---|
| `pytest -q` | 323 passed | 323 passed | 323 passed |
| `ruff check .` | Passed | Passed | Passed |
| `mypy src` | Passed, 6 files | Passed, 6 files | Passed, 6 files |
| `python scripts/generate_conformance.py --check` | Passed | Passed | Passed |

Before restoration, Python 3.12 ran the full baseline: 221 tests passed,
with Ruff and mypy also passing. After restoration, the focused command
`pytest -q tests/test_consumer_compatibility.py tests/test_identity.py tests/test_interchange.py`
passed all 157 tests. The restored module adds 102 passing cases.

All three development environments resolved pytest 9.2.0, Pydantic 2.14.3,
cryptography 50.0.2, Ruff 0.17.4, mypy 2.4.1, and jsonschema 4.26.0.
These are the observed versions, not new dependency constraints.

Additional checks:

- A separate Python 3.11 environment installed only the core package.
  `python -I` confirmed `cryptography` was absent and imported
  `folio_propositions` successfully.
- Executing the guide's Python reader verbatim reported
  `29 shared-shard cases matched`.
- Relative links and named case IDs in the consumer guidance were verified.
- The restored payload was compared with the source PR head, and protected
  runtime, generated assets, and existing tests were compared with the lane base.
- `git diff --check` passed.

## Review and acceptance boundary

The combined simplification review found no eligible changes. It preserved
all proof tests and the independent fixture corpus. Its focused verification
passed 222 tests across consumer, identity, interchange, and conformance modules,
plus Ruff and mypy.

The subsequent correctness review checked the item delta and execution-plan
requirements and found no actionable issues. The browser-test scope contained
no frontend routes; no screenshot was required. No held change or user decision
was identified.

All commits remain local. No remote is configured, and no push, PR creation,
hosted CI, or campaign Astra/Fable review ran in this lane. The controller must
verify the campaign Goal Capsule and cited requirements in the chief repository,
compare against its current publication base, and complete the campaign review
and merge gates. Repeat integration checks if the publication tree changes.

These results establish local conformance only. Neither folio-enrich nor
folio-insights was executed against the corpus in this run.
