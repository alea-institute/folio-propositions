# Dependency and source audit — 2026-11-08

Scope: the exact environments used for the [maintenance verification](foli-3-verification.md), on Linux x86_64. This is a dated advisory scan and focused source review, not a guarantee about every version permitted by dependency ranges or the absence of undiscovered vulnerabilities.

## Method and outcomes

uv **0.9.22** exported each environment after `uv pip check`. Isolated pip-audit **2.10.1**, running on CPython **3.11.14**, queried the existing PyPI advisory service with `--no-deps --disable-pip --strict --timeout 15`, JSON output, and a 120-second outer timeout. Only validated exact third-party pins were transmitted. The auditor's own dependencies were kept outside the application inventories. The validation environment also had PyYAML 6.0.3 for the local workflow parse. See [pip-audit's documented options and limits](https://github.com/pypa/pip-audit#usage).

| Environment | Interpreter | Third-party pins | Exit | Known vulnerabilities | Skips |
|---|---|---:|---:|---:|---:|
| Development + signing | 3.11.14 | 20 | 0 | 0 | 0 |
| Development + signing | 3.12.12 | 20 | 0 | 0 | 0 |
| Development + signing | 3.13.11 | 20 | 0 | 0 | 0 |
| Actual wheel backend | 3.11.14 | 6 | 0 | 0 | 0 |
| Installed core wheel | 3.11.14 | 5 | 0 | 0 | 0 |

Every report matched its complete expected inventory. There were no advisory IDs, collection failures, unexplained skips or suppressions to disposition. No dependency-bound correction was required. pip-audit emitted its expected recommendation to hash pinned requirements; this scan uses complete resolved pins and performs no dependency resolution or installation. A lockfile/hash policy remains outside this maintenance change.

The only distribution excluded was local **folio-propositions 0.4.0**, from this checkout or its exact versioned wheel. Unexpected editable origins, URLs and unpinned requirements fail before calling the advisory tool. Vulnerabilities, missing/duplicate report entries, skipped dependencies, malformed reports and service failures fail the gate. Freeze files with local paths stay ignored; this receipt contains public pins only.

## Exact inventories

All three development/signing environments resolved the same pins:

```text
annotated-types==0.8.0
ast-serialize==0.13.1
cffi==2.1.1
coverage==7.17.2
cryptography==50.0.2
iniconfig==2.3.1
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
ruff==0.17.4
typing-extensions==4.16.0
typing-inspection==0.4.5
```

Actual build environment, unchanged before/after the build:

```text
hatchling==1.33.0
packaging==26.3
pathspec==1.1.1
pluggy==1.7.0
tomlkit==0.15.2
trove-classifiers==2026.9.21.13
```

Core-only wheel environment:

```text
annotated-types==0.8.0
pydantic==2.14.3
pydantic-core==2.50.4
typing-extensions==4.16.0
typing-inspection==0.4.5
```

Wheel: `folio_propositions-0.4.0-py3-none-any.whl`.

SHA-256: `326c0dd386db85b598c79e71551ba19681a22c2ebf30be5b1b5de11ac07fa53b`.

The wheel was built without isolation in the inventoried backend environment and installed into a new core environment. No build hook added a dependency. Documentation metadata is part of the wheel; a future documentation edit can change this hash without changing package source.

## Focused source and workflow review

| Surface | Evidence | Consequence and disposition |
|---|---|---|
| `src/folio_propositions/signing.py`: Base58 and DID parsing | Length bound precedes big-integer decoding; codec and exact key length are checked. Added cases exercise valid Base58 with invalid codec/length. | Bounded parsing remains intact; no behavior change needed. |
| `DidKeyEd25519Verifier.verify` | Actor/key-id binding and signature length precede decoding; decoding errors and invalid signatures return false. Negative cases are paired with a real valid signature. | Bad inputs cannot satisfy an always-false verifier test. Existing self-certifying DID semantics remain explicit; authorization belongs to the consumer. |
| `src/folio_propositions/lifecycle.py`: `transition_signing_payload`, `apply_transition`, `verify_history` | Signed payload includes proposition id, content IRI, sequence and transition fields; apply checks legal transition, next index and increasing signed timestamp. Existing replay/tamper tests remain active. History verification rejects unsigned legacy claims by default. | Signature binding and replay checks remain unchanged. Consumers must validate incoming structure and authorize actors before trusting their actions. |
| `src/folio_propositions/models.py`: `Proposition` | Construction validates history structure; models are mutable and assignment/copy updates can bypass validation. `apply_transition` verifies only the new entry. | README overstatement corrected. No new immutability or authorization policy introduced. |
| `src/folio_propositions/interchange.py`: migration and stamping | Migration deep-copies nested inputs; new mutation assertions prove ownership. Stamping refuses identity changes bound to signed history; existing tests cover that protection. | No stored-data operation or migration added. Stamping/lifecycle model copies remain shallow for existing nested objects; the docs do not promise detached ownership for them. |
| `.github/workflows/ci.yml` | Ordinary pull-request/push triggers, read-only token permission, no secrets or PR text interpolated into shell; suites and job timeouts preserved. | Added commands run repository code under the existing unprivileged CI context. No credential, security-setting or deployment change. |
| `scripts/audit-dependencies.sh` | Exact allowlist of local origins, strict public pins, isolated auditor, bounded runtime and complete-result comparison. Offline tests exercise failure propagation. | Audits fail closed on incomplete evidence. The small shared script keeps validation identical across five audited environments; it is not a general audit framework. |

The source review found no compatible source correction necessary for this item's scope. Mutable models, shallow model copies and consumer authorization remain existing contract limits documented above. No secrets, private records, external message sends or production data were used. Hosted workflow execution and campaign PR reviews remain separate controller gates.
