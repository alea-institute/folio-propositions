# Conformance files

The `conformance/` directory publishes this library's contracts in a form that
consumers in other languages can test against. Every file is generated from the
Python implementation by `scripts/generate_conformance.py`; never edit one by
hand. `tests/test_conformance.py` regenerates each file and fails when the
committed copy differs, so the files cannot drift from the code.

```bash
.venv/bin/python scripts/generate_conformance.py          # rewrite after a change
.venv/bin/python scripts/generate_conformance.py --check  # fail on drift
```

## `identity-vectors.json`

Content-identity vectors for `content_identity`, `content_iri`, and
`document_source_uri`. The file is ASCII-only JSON: every non-ASCII or control
character appears as a `\uXXXX` escape, and each string input also appears as
UTF-8 hex, so no editor or transport can silently normalize a vector.

Top-level fields:

| Field | Meaning |
|---|---|
| `format` | Always `folio-propositions/identity-vectors`. |
| `format_version` | Layout version of this file (currently `1`). Bumped only when the JSON layout changes. |
| `recipe` | Identity recipe the vectors exercise (`folio-content-iri-v1`). The recipe is frozen; a new recipe would ship as a separately named file. |
| `generated_by` | Library version that generated the file. |
| `spec` | IRI prefix, hex length, document-URI prefix, and the recipe steps in prose. |
| `content_identity` | Vectors that mint an IRI. |
| `content_identity_errors` | Inputs that must be refused. |
| `document_source_uri` | Vectors for the default document URI. |

A `content_identity` vector:

```json
{
  "id": "span-leading-u001c",
  "description": "U+001C FILE SEPARATOR is stripped by Python str.strip() but NOT by Rust str::trim(); a port must strip it.",
  "input": {
    "source_uri": "https://example.com/doc",
    "source_uri_utf8_hex": "68747470733a2f2f6578616d706c652e636f6d2f646f63",
    "span": "\u001cspan",
    "span_utf8_hex": "1c7370616e"
  },
  "expected": {
    "normalized_source_uri": "https://example.com/doc",
    "normalized_span": "span",
    "normalized_span_utf8_hex": "7370616e",
    "payload_utf8_hex": "68747470733a2f2f6578616d706c652e636f6d2f646f630a7370616e",
    "provenance_hash": "5cf42353ce439b2d52c664b670fdc4bc3ccbcd467ac986182255dea68512628a",
    "iri": "urn:folio:shard/5cf42353ce439b2d52c664b670fdc4bc"
  }
}
```

A port should check each step in order: `normalized_source_uri`,
`normalized_span`, `payload_utf8_hex` (the exact bytes hashed),
`provenance_hash`, then `iri`. An error vector's `expected` is
`{"error": "ValueError", "message": "..."}`; a port must refuse the input with
its own error type. A `document_source_uri` vector's `expected` holds
`normalized_text`, its UTF-8 hex, and `uri`.

### Edges a port must reproduce

- **Python `str.strip()`, not Unicode `White_Space`.** `normalize_span` strips
  every character for which Python's `str.isspace()` is true. That set equals
  Unicode `White_Space` plus U+001C-U+001F (file, group, record, and unit
  separators). Rust's `str::trim()` and most other languages' trims use
  `White_Space` alone, so a direct port leaves those four characters in place
  and mints a different IRI, or mints one for a span that Python refuses as
  empty. The `span-*-u001*` and `error-separators-only-span` vectors cover
  this.
- **NFC, not NFKC.** Compatibility characters such as ligatures and full-width
  digits survive.
- **CRLF before CR.** CRLF becomes LF first, then any lone CR becomes LF.
- **`urllib.parse.urlsplit`.** It strips leading C0 controls and spaces and
  removes every tab, CR, and LF before splitting. Trailing spaces stay and
  percent-encode as `%20`.
- **Path quoting.** `quote(safe="/%:@")`: unreserved characters plus `/`, `%`,
  `:`, and `@` stay literal; existing escapes keep their case; new escapes use
  uppercase hex. Trailing slashes go unless the path is exactly `/`.
- **Host.** NFC then lowercase; no IDNA encoding.
- **Query and fragment.** NFC only; no case change or encoding.

## `proposition.schema.json` and `document-record.schema.json`

JSON Schemas (draft 2020-12) for one `Proposition` and one
`PropositionDocumentRecord`, generated with pydantic's `model_json_schema`.
They carry `x-folio-schema-version` (the record `SCHEMA_VERSION`) and
`x-folio-invariants`, a list of cross-field rules that JSON Schema cannot
express (span fields supplied together, the history chain, the transition
table, signature verification). A document that validates against the schema
has the right shape; a consumer must still enforce the listed invariants, or
round-trip through this library, before treating it as valid.
