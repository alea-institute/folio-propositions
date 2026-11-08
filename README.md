# folio-propositions

[![CI](https://github.com/alea-institute/folio-propositions/actions/workflows/ci.yml/badge.svg)](https://github.com/alea-institute/folio-propositions/actions/workflows/ci.yml)

`folio-propositions` defines the shared, typed Proposition ledger schema used by
`folio-enrich` and `folio-insights`. Each proposition records an asserter side and
a validator side; either side may be null when that is the legally accurate state.

Install the package with:

```bash
pip install folio-propositions
```

```python
from folio_propositions import Proposition, WORKING_TAXONOMY

open_position = Proposition(
    id="p-1",
    proposition_type="Legal Proposition",
    asserter={"role": "party", "name": "Appellant"},
    validator=None,
    disposition="unresolved",
)

folio_iri = WORKING_TAXONOMY[open_position.proposition_type]
```

`SHAPES` names the ledger configurations: `litigation`, `disputatio`, and
`normative` (statutes, regulations, court rules, and rule-stating holdings,
asserted by a `legislature`, `agency`, or `court` and validated by a court or
an automated `system` verifier).

`WORKING_TAXONOMY` maps canonical labels to optional FOLIO IRIs. Library-local
working types remain valid entries with a `None` IRI until FOLIO gains an exact
class for them.

## Content identity

`content_iri(source_uri, span)` returns the same `urn:folio:shard/…` IRI that
folio-insights mints for a shard drawn from that span of that source, so the two
products can match a proposition to a corpus shard. The identity is per
`(source, span)`: URIs and spans are normalized (case, trailing slash, NFC,
newlines, surrounding whitespace) before hashing. Set `source_uri` on a
`PropositionDocumentRecord` and call `stamp_content_iris(record)` to fill every
proposition's `content_iri`; `document_source_uri(text)` gives a deterministic
URI when a document has none.

Consumer developers can check their implementation against the portable
[shared shard identity fixtures](docs/consumer-compatibility.md), including
literal normalization outputs and fixture-backed proposition-to-shard joins.

## Axiom lifecycle

Use `apply_transition` to advance `axiom_status`: it checks the legal
transition table (`proposition → promoted ⇄ demoted`, `proposition → demoted`
by `reject`, any of them → `superseded`, which is terminal) and verifies the
actor's signature. Between `promoted` and `demoted` an authorized person may
use `override` instead of `demote` or `promote` to record that they overturned
an automated status; `reject` and `override` require a `reason`. Every accepted
change is appended to the returned copy's `axiom_history` with its sequence
number, and the
signature binds the proposition id, its stamped `content_iri` and that sequence.
A `did:key` signature is self-certifying, so check `actor_did` against your own
authorized signers. Models are mutable; direct assignment and `model_copy(update=...)`
can bypass validation. Constructing a `Proposition` checks history structure,
but does not verify signatures. Call `verify_history` on a validated incoming
proposition to check every recorded signature with your verifier; `apply_transition`
checks only the new entry. Neither operation supplies your authorization policy.
Unsigned legacy `migrate` entries are rejected by `verify_history` unless you
explicitly opt in to trusting them. Install
`folio-propositions[signing]` for the `did:key` Ed25519 verifier and the
`sign_transition` helper. See the [v0.5.0](docs/migration-0.5.0.md) and
[v0.4.0](docs/migration-0.4.0.md) migration notes.
For a runnable walkthrough of caller-owned signer policy, saved-history replay,
and explicit legacy trust, see the
[consumer migration examples](docs/migration-0.4.0.md#run-the-consumer-examples).

## Conformance files for other languages

`conformance/identity-vectors.json` holds content-identity vectors with every
intermediate value (normalized URI and span, hashed payload bytes, provenance
hash, IRI), so a port in another language can check each step of the recipe.
`conformance/proposition.schema.json` and
`conformance/document-record.schema.json` are JSON Schemas (draft 2020-12)
generated from the pydantic models. `scripts/generate_conformance.py` writes
all three, and the test suite fails if they drift from the implementation. See
[conformance](docs/conformance.md).

## Development checks

From the repository root, install and run the same checks as CI:

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -e '.[dev,signing]'
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/mypy src
.venv/bin/python scripts/generate_conformance.py --check
.venv/bin/coverage run -m pytest -q
.venv/bin/coverage report
```

CI runs the full pytest, Ruff and mypy suites on Python 3.11, 3.12, and 3.13.
The 3.11 leg measures every package module's statements and branches and enforces
a 97% combined coverage floor. Run the commands from the repository root.
The test suite uses fixed ontology IRIs and content-identity golden vectors;
it does not fetch an ontology or require sibling repositories.

To reproduce the separate wheel check, create fresh build and core environments:

```bash
mkdir -p .audit
uv venv --python 3.11 .venv-build
.venv-build/bin/python -I -c 'import tomllib; print("\n".join(tomllib.load(open("pyproject.toml", "rb"))["build-system"]["requires"]))' > .audit/build-requirements.txt
uv pip install --python .venv-build/bin/python -r .audit/build-requirements.txt
uv pip freeze --python .venv-build/bin/python > .audit/build-before.freeze
uv build --python .venv-build/bin/python --wheel --no-build-isolation
uv pip freeze --python .venv-build/bin/python > .audit/build-after.freeze
cmp .audit/build-before.freeze .audit/build-after.freeze
sha256sum dist/*.whl
uv venv --python 3.11 .venv-core
uv pip install --python .venv-core/bin/python dist/*.whl
.venv-core/bin/python -I tests/core_smoke.py
```

The smoke script requires a non-editable wheel installation, its typing marker,
and no `cryptography`. It checks serialization, migration, identity stamping and
the custom-verifier protocol. Its recording verifier is synthetic; the signing
suite separately exercises real Ed25519 signatures.

Audit the exact installed dependencies with an isolated auditor (Bash and GNU
`timeout` are required, as on CI's Ubuntu runners):

```bash
uv venv --python 3.11 .venv-audit
uv pip install --python .venv-audit/bin/python pip-audit
for environment in .venv .venv-build .venv-core; do
  bash scripts/audit-dependencies.sh "$environment/bin/python" ".audit/$environment" .venv-audit/bin/pip-audit || exit "$?"
done
```

CI also audits each development matrix environment. The script exports exact
transitive pins and excludes only this checkout's local package or its versioned
wheel. Unexpected URLs/editables, vulnerabilities, skipped packages, incomplete
reports and service failures fail the check. Only validated third-party pins go
to PyPI's advisory service; local freeze files stay in the ignored `.audit/`
directory. Audits cover the tested resolutions at the time of the scan, not every
version permitted by dependency ranges. See the dated [verification](docs/plans/evidence/foli-3-verification.md)
and [dependency/source audit](docs/plans/evidence/foli-3-audit.md) receipts.

## Docs

See the [documentation index](docs/README.md) for the folio-insights shard
mapping, v2.0 ledger rationale, review-disposition template, gold-cycle
learnings template, and Phase A exit-record template.
