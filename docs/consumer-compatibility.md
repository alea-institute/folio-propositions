# Shared shard identity fixtures

Use the [version 1 corpus](../tests/fixtures/shared_shard_identity_v1.json) to
check whether a consumer produces the same shard IRI as `folio-propositions`
for a source URI and text span. It contains 29 successful examples with fixed
expected values, including Unicode, newline, URI, and whitespace boundaries.

Copy the JSON file from a **pinned repository commit** and record that commit
alongside your copy. The file is a repository asset; installing the package
does not provide a fixture loader or promise to include the corpus in the wheel.
Consumers in any language can read it without importing Python test code.

## Format

The top-level object contains `fixture_version: 1` and a nonempty `cases` array.
The fixture version describes this data format, independently of the package
version and the proposition `SCHEMA_VERSION`. Reject unsupported fixture versions
and malformed cases rather than skipping them. Case IDs are unique.

| Field | Meaning |
|---|---|
| `id` | Stable case name for test output and mismatch reports. |
| `source_uri` | Raw source URI to pass to the consumer. |
| `span` | Raw text to pass to the consumer. |
| `normalized_source_uri` | Literal expected source normalization output. |
| `normalized_span` | Literal expected text normalization output. |
| `provenance_hash` | Full 64-character lowercase SHA-256 hex digest. |
| `iri` | `urn:folio:shard/` followed by the digest's first 32 hex characters. |

All fields are nonempty strings. Decode the file as UTF-8 JSON: escapes such as
`\r\n`, `\t`, and `\u0301` represent characters, not literal backslashes.
Each portable span remains nonempty after normalization.

## Run the cases

Feed **raw** `source_uri` and `span` into your implementation. Pre-normalizing
them would hide normalization bugs. Compare any normalization outputs your API
exposes, then the full hash and IRI. If it exposes only the IRI, compare that
field; the intermediate values help diagnose a mismatch.

This reference reader runs from this repository's root with the development
dependencies installed. Replace the `folio_propositions` calls with your
consumer's equivalent operations when porting it:

```python
import json
from pathlib import Path

from folio_propositions import (
    content_identity,
    normalize_source_uri,
    normalize_span,
)

path = Path("tests/fixtures/shared_shard_identity_v1.json")
corpus = json.loads(path.read_text(encoding="utf-8"))
assert type(corpus["fixture_version"]) is int and corpus["fixture_version"] == 1
assert corpus["cases"]
for case in corpus["cases"]:
    identity = content_identity(case["source_uri"], case["span"])
    actual = {
        "normalized_source_uri": normalize_source_uri(case["source_uri"]),
        "normalized_span": normalize_span(case["span"]),
        "provenance_hash": identity.provenance_hash,
        "iri": identity.iri,
    }
    for field, value in actual.items():
        assert value == case[field], (
            f"{case['id']} {field}: expected {case[field]!r}, got {value!r}"
        )
print(f"{len(corpus['cases'])} shared-shard cases matched")
```

The frozen recipe in [identity.py](../src/folio_propositions/identity.py) hashes
the UTF-8 bytes of `normalized_source_uri + "\n" + normalized_span`. Source
normalization lowercases the scheme and NFC-normalized authority, NFC-normalizes
and percent-encodes the path, removes trailing slashes from non-root paths, and
NFC-normalizes the query and fragment. Existing percent escapes remain intact.
Text normalization converts CRLF and bare CR to LF, applies NFC, and strips
surrounding whitespace.

The corpus pins both equivalence and distinctions:

- `scheme-host-case-trailing-slash` and `canonical-a` share an identity.
- `nfc-path`, `nfd-path`, and `encoded-path` share an identity, as do `nfc-span`
  and `nfd-span`.
- `crlf-span`, `lf-span`, and `bare-cr-span` agree; `surrounding-whitespace`
  agrees with `unpadded-span`.
- Changing the source, span, query, or fragment changes the identity.
- Root slash presence, path case, interior spaces/tabs, and percent-escape
  spelling remain significant. In particular, `%2F` is not decoded to `/`,
  and existing `%` characters are not double-encoded.

## Proposition-to-shard joins

[The local consumer tests](../tests/test_consumer_compatibility.py) stamp two
propositions with different IDs, types, and asserters for each fixture. Both
stamps equal the fixture's literal `iri` after JSON serialization and validation.
The tests also check that extraction IDs, offsets, generator information, and
document metadata do not affect that join key. Stamping preserves raw text and
metadata, leaves the input record unchanged, and is idempotent on these unsigned
records.

Empty inputs are deliberately outside the portable corpus. This library rejects
an empty source URI or a span that normalizes to empty when computing identity.
`stamp_content_iris` requires a source and leaves missing or normalized-empty
text unstamped. The stamping contract notes that folio-insights can hash empty
spans; consumers should not infer a shared empty-input error policy from these
fixtures.

A record without `source_uri` can carry a syntactically valid stamp, but cannot
verify it. With source and nonempty text available, record validation rejects a
stamp that does not match their identity.

## Provenance and verification

The first eight cases preserve the IDs, raw inputs, and hashes in
[the original golden vectors](../tests/test_identity.py). Those vectors are
documented there as computed with the frozen folio-insights recipe. Additional
cases use explicitly reviewed normalized strings and independently calculated
SHA-256 payload hashes. Expected values are committed constants; tests never
regenerate them with the implementation under test.

Run local fixture, identity, and interchange checks with:

```bash
.venv/bin/pytest -q tests/test_consumer_compatibility.py tests/test_identity.py tests/test_interchange.py
```

These are local conformance checks. They do not establish that a current
folio-enrich or folio-insights checkout has run this corpus, or replace the
pending cross-product evidence recorded in [shard mapping](shard-mapping.md).

For a mismatch, report the pinned repository revision, fixture version, case ID,
output field, expected value, actual value, and consumer version. Investigate
the first differing stage before proposing a change; do not regenerate the
expected values to make a failing implementation pass. Changes to normalization
or identity belong to a separately named scheme, as the frozen recipe requires.
