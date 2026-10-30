"""Generate the cross-language conformance files in ``conformance/``.

The files are derived from this library, never written by hand:

- ``conformance/identity-vectors.json``: content-identity vectors computed by
  :mod:`folio_propositions.identity`, with every intermediate value, so a port
  in another language can check each step of the recipe.
- ``conformance/proposition.schema.json`` and
  ``conformance/document-record.schema.json``: JSON Schemas generated from the
  pydantic models.

Run ``python scripts/generate_conformance.py`` to rewrite them after a change,
or ``python scripts/generate_conformance.py --check`` to fail when the committed
files drift from the implementation (``tests/test_conformance.py`` does the
same check).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from folio_propositions import (
    SCHEMA_VERSION,
    PropositionDocumentRecord,
    __version__,
)
from folio_propositions.identity import (
    CONTENT_IRI_HEX_LEN,
    CONTENT_IRI_PREFIX,
    DOCUMENT_URI_PREFIX,
    content_identity,
    document_source_uri,
    normalize_source_uri,
    normalize_span,
)
from folio_propositions.models import Proposition

CONFORMANCE_DIR = ROOT / "conformance"
IDENTITY_VECTORS = CONFORMANCE_DIR / "identity-vectors.json"
PROPOSITION_SCHEMA = CONFORMANCE_DIR / "proposition.schema.json"
RECORD_SCHEMA = CONFORMANCE_DIR / "document-record.schema.json"

# Bump when the JSON layout of identity-vectors.json changes. The recipe itself
# is frozen (see identity.py); new recipes get a new, separately named file.
IDENTITY_VECTORS_FORMAT_VERSION = 1
IDENTITY_RECIPE = "folio-content-iri-v1"

URI = "https://example.com/doc"
CAFE_NFC = unicodedata.normalize("NFC", "caf\u00e9")
CAFE_NFD = unicodedata.normalize("NFD", "caf\u00e9")

# (id, description, source_uri, span)
CONTENT_IDENTITY_CASES: list[tuple[str, str, str, str]] = [
    (
        "plain-ascii",
        "Plain ASCII source and span; no normalization applies.",
        "https://example.com/opinions/palsgraf",
        "The risk reasonably to be perceived defines the duty to be obeyed.",
    ),
    (
        "span-nfc",
        "Precomposed (NFC) span.",
        URI,
        f"{CAFE_NFC} holding",
    ),
    (
        "span-nfd",
        "Decomposed (NFD) span; must equal span-nfc.",
        URI,
        f"{CAFE_NFD} holding",
    ),
    (
        "span-nfd-reordered-marks",
        "Combining marks in non-canonical order; NFC reorders and composes.",
        URI,
        "s\u0307\u0323",
    ),
    (
        "span-nfc-singleton",
        "U+212B ANGSTROM SIGN; NFC maps it to U+00C5.",
        URI,
        "\u212b rule",
    ),
    (
        "span-compatibility-not-folded",
        "NFC, not NFKC: the U+FB01 ligature and full-width digits survive.",
        URI,
        "\ufb01le \uff11\uff12",
    ),
    (
        "span-crlf",
        "CRLF line endings become LF.",
        URI,
        "line one\r\nline two",
    ),
    (
        "span-lone-cr",
        "A lone CR becomes LF.",
        URI,
        "line one\rline two",
    ),
    (
        "span-cr-cr-lf",
        "CR CR LF becomes two LFs (CRLF is replaced before lone CR).",
        URI,
        "a\r\r\nb",
    ),
    (
        "span-surrounding-ascii-whitespace",
        "Leading and trailing spaces, tabs and newlines are stripped.",
        URI,
        " \t\n padded span \r\n\t ",
    ),
    (
        "span-interior-whitespace-kept",
        "Interior runs of whitespace are kept verbatim.",
        URI,
        "a  \t b\n\nc",
    ),
    (
        "span-surrounding-unicode-whitespace",
        (
            "NBSP, NEL, ideographic space, line and paragraph separators are "
            "stripped (Unicode White_Space; Rust trim() agrees)."
        ),
        URI,
        "\u00a0\u0085\u3000\u2028span\u2029\u2003\u00a0",
    ),
    (
        "span-zero-width-and-bom-not-stripped",
        "U+200B and U+FEFF are not whitespace and are kept.",
        URI,
        "\ufeff\u200bspan\u200b",
    ),
    (
        "span-leading-u001c",
        (
            "U+001C FILE SEPARATOR is stripped by Python str.strip() but NOT by "
            "Rust str::trim(); a port must strip it."
        ),
        URI,
        "\u001cspan",
    ),
    (
        "span-trailing-u001d",
        "U+001D GROUP SEPARATOR is stripped (Python strip, not Rust trim).",
        URI,
        "span\u001d",
    ),
    (
        "span-surrounding-u001e",
        "U+001E RECORD SEPARATOR is stripped on both ends.",
        URI,
        "\u001espan\u001e",
    ),
    (
        "span-surrounding-u001f",
        "U+001F UNIT SEPARATOR is stripped on both ends.",
        URI,
        "\u001fspan\u001f",
    ),
    (
        "span-mixed-separators-and-spaces",
        "U+001C-U+001F mixed with ordinary whitespace are all stripped.",
        URI,
        " \u001c\t\u001d span \u001e\n\u001f ",
    ),
    (
        "span-interior-separators-kept",
        "U+001C-U+001F inside the span are kept.",
        URI,
        "a\u001cb\u001dc\u001ed\u001fe",
    ),
    (
        "span-other-c0-controls-not-stripped",
        "Other C0 controls (U+0000, U+0001, U+001B) are not whitespace and stay.",
        URI,
        "\u0000\u0001span\u001b",
    ),
    (
        "span-vertical-tab-form-feed",
        "U+000B and U+000C are whitespace in both languages and are stripped.",
        URI,
        "\u000b\u000cspan\u000c\u000b",
    ),
    (
        "span-astral",
        "Characters outside the BMP hash as their UTF-8 bytes.",
        URI,
        "\U0001d4d0 \U0001f600 \u00a7 504B.178",
    ),
    (
        "uri-scheme-and-host-case",
        "Scheme and host are lowercased; path case is kept.",
        "HTTPS://Example.COM/Doc",
        "span",
    ),
    (
        "uri-trailing-slash",
        "A trailing slash on a non-root path is removed.",
        "https://example.com/a/",
        "span",
    ),
    (
        "uri-multiple-trailing-slashes",
        "All trailing slashes on a non-root path are removed.",
        "https://example.com/a///",
        "span",
    ),
    (
        "uri-root-slash-kept",
        "The root path '/' is kept.",
        "https://example.com/",
        "span",
    ),
    (
        "uri-path-nfc",
        "A precomposed non-ASCII path is NFC-normalized, then percent-encoded.",
        f"https://example.com/{CAFE_NFC}",
        "span",
    ),
    (
        "uri-path-nfd",
        "A decomposed non-ASCII path; must equal uri-path-nfc.",
        f"https://example.com/{CAFE_NFD}",
        "span",
    ),
    (
        "uri-existing-percent-escapes-kept",
        "Existing percent escapes are kept verbatim, including lowercase hex.",
        "https://example.com/caf%c3%a9/a%2Fb",
        "span",
    ),
    (
        "uri-path-space-and-reserved",
        (
            "In the path only unreserved characters and '/', '%', ':' and '@' "
            "stay literal; space and other reserved characters are percent-encoded."
        ),
        "https://example.com/a b;c=d,e+f!g~h",
        "span",
    ),
    (
        "uri-query-and-fragment-kept",
        "Query and fragment are kept (NFC only, not lowercased or encoded).",
        f"https://example.com/doc?Page=2&q={CAFE_NFD}#Para-7",
        "span",
    ),
    (
        "uri-host-nfc",
        "A non-ASCII host is NFC-normalized and lowercased, not IDNA-encoded.",
        f"https://{CAFE_NFD.upper()}.example/doc",
        "span",
    ),
    (
        "uri-userinfo-and-port",
        "Userinfo and port are part of the lowercased netloc.",
        "https://User:Pass@Example.com:8443/doc",
        "span",
    ),
    (
        "uri-urn",
        "A URN has no netloc; its body is the path.",
        "urn:sha256:ABC123",
        "span",
    ),
    (
        "uri-leading-space-and-c0-stripped",
        "Python urlsplit (WHATWG) strips leading C0 controls and spaces.",
        " \u001f\u0001https://example.com/doc",
        "span",
    ),
    (
        "uri-tab-and-newline-removed",
        "Python urlsplit removes every tab, CR and LF anywhere in the URI.",
        "https://exa\tmple.com/d\noc\r",
        "span",
    ),
    (
        "uri-trailing-space-encoded",
        "Trailing spaces are not stripped; they percent-encode as %20.",
        "https://example.com/doc ",
        "span",
    ),
]

# (id, description, source_uri, span); each must raise ValueError.
CONTENT_IDENTITY_ERRORS: list[tuple[str, str, str, str]] = [
    ("error-empty-source-uri", "An empty source URI is refused.", "", "span"),
    ("error-empty-span", "An empty span is refused.", URI, ""),
    (
        "error-whitespace-only-span",
        "A span that normalizes to empty is refused.",
        URI,
        " \r\n\t\u3000 ",
    ),
    (
        "error-separators-only-span",
        (
            "A span of only U+001C-U+001F normalizes to empty and is refused; "
            "a port using Rust trim() would wrongly mint an IRI."
        ),
        URI,
        "\u001c\u001d\u001e\u001f",
    ),
]

# (id, description, text)
DOCUMENT_SOURCE_URI_CASES: list[tuple[str, str, str]] = [
    ("doc-plain", "Plain ASCII document text.", "Opinion text"),
    (
        "doc-crlf-and-padding",
        "Document text uses the span normalization (LF, NFC, strip).",
        "  Opinion text\r\nsecond line\u001f ",
    ),
    ("doc-nfd", "Decomposed text hashes as its NFC form.", f"{CAFE_NFD} opinion"),
]


def _hex(data: bytes) -> str:
    return data.hex()


def _identity_vector(
    vector_id: str, description: str, source_uri: str, span: str
) -> dict[str, Any]:
    uri_n = normalize_source_uri(source_uri)
    span_n = normalize_span(span)
    payload = (uri_n + "\n" + span_n).encode("utf-8")
    identity = content_identity(source_uri, span)
    if hashlib.sha256(payload).hexdigest() != identity.provenance_hash:
        raise AssertionError(f"{vector_id}: payload does not reproduce the hash")
    return {
        "id": vector_id,
        "description": description,
        "input": {
            "source_uri": source_uri,
            "source_uri_utf8_hex": _hex(source_uri.encode("utf-8")),
            "span": span,
            "span_utf8_hex": _hex(span.encode("utf-8")),
        },
        "expected": {
            "normalized_source_uri": uri_n,
            "normalized_span": span_n,
            "normalized_span_utf8_hex": _hex(span_n.encode("utf-8")),
            "payload_utf8_hex": _hex(payload),
            "provenance_hash": identity.provenance_hash,
            "iri": identity.iri,
        },
    }


def _error_vector(
    vector_id: str, description: str, source_uri: str, span: str
) -> dict[str, Any]:
    try:
        content_identity(source_uri, span)
    except ValueError as error:
        message = str(error)
    else:
        raise AssertionError(f"{vector_id}: expected ValueError")
    return {
        "id": vector_id,
        "description": description,
        "input": {
            "source_uri": source_uri,
            "source_uri_utf8_hex": _hex(source_uri.encode("utf-8")),
            "span": span,
            "span_utf8_hex": _hex(span.encode("utf-8")),
        },
        "expected": {"error": "ValueError", "message": message},
    }


def _document_vector(vector_id: str, description: str, text: str) -> dict[str, Any]:
    normalized = normalize_span(text)
    return {
        "id": vector_id,
        "description": description,
        "input": {"text": text, "text_utf8_hex": _hex(text.encode("utf-8"))},
        "expected": {
            "normalized_text": normalized,
            "normalized_text_utf8_hex": _hex(normalized.encode("utf-8")),
            "uri": document_source_uri(text),
        },
    }


def build_identity_vectors() -> dict[str, Any]:
    """Return the identity conformance document computed from this library."""

    return {
        "format": "folio-propositions/identity-vectors",
        "format_version": IDENTITY_VECTORS_FORMAT_VERSION,
        "recipe": IDENTITY_RECIPE,
        "generated_by": f"folio-propositions {__version__}",
        "generator": "scripts/generate_conformance.py",
        "spec": {
            "content_iri_prefix": CONTENT_IRI_PREFIX,
            "content_iri_hex_len": CONTENT_IRI_HEX_LEN,
            "document_uri_prefix": DOCUMENT_URI_PREFIX,
            "steps": [
                "source_uri must be non-empty (checked before normalization).",
                (
                    "normalized_span: replace CRLF with LF, then lone CR with LF; "
                    "apply Unicode NFC; strip leading and trailing characters for "
                    "which Python str.isspace() is true (Unicode White_Space plus "
                    "U+001C-U+001F). The result must be non-empty."
                ),
                (
                    "normalized_source_uri: split with Python urllib.parse.urlsplit "
                    "(which first strips leading C0 controls and spaces and removes "
                    "every tab, CR and LF); lowercase the scheme; NFC then lowercase "
                    "the netloc; NFC the path then percent-encode it with "
                    "urllib.parse.quote(safe='/%:@'), uppercase hex, UTF-8; drop "
                    "trailing slashes unless the path is exactly '/'; NFC the query "
                    "and fragment; reassemble with urlunsplit."
                ),
                "payload = UTF-8(normalized_source_uri + '\\n' + normalized_span).",
                "provenance_hash = lowercase hex SHA-256(payload).",
                "iri = content_iri_prefix + provenance_hash[:content_iri_hex_len].",
                (
                    "document_source_uri(text) = document_uri_prefix + lowercase hex "
                    "SHA-256(UTF-8(normalized_span(text))); text must normalize to "
                    "non-empty."
                ),
            ],
        },
        "content_identity": [
            _identity_vector(*case) for case in CONTENT_IDENTITY_CASES
        ],
        "content_identity_errors": [
            _error_vector(*case) for case in CONTENT_IDENTITY_ERRORS
        ],
        "document_source_uri": [
            _document_vector(*case) for case in DOCUMENT_SOURCE_URI_CASES
        ],
    }


_INVARIANTS = [
    "start_char, end_char and text are all null or all non-null.",
    "end_char >= start_char when both are set.",
    "proposition_type is a key of WORKING_TAXONOMY unless is_new_type is true.",
    "shape is a key of SHAPES.",
    "content_iri, when set, is 'urn:folio:shard/' plus 32 lowercase hex characters.",
    (
        "axiom_history[i].sequence == i; entries chain from 'proposition' "
        "(each from_status equals the previous to_status); axiom_status equals the "
        "last to_status, or 'proposition' when the history is empty."
    ),
    (
        "Only axiom_history[0] may use the 'migrate' action; migrate entries are "
        "unsigned, and every other entry has actor_did, a timezone-aware at, and a "
        "signature."
    ),
    "Signed entries have strictly increasing at.",
    (
        "(from_status, to_status, action) is in AXIOM_TRANSITION_ACTIONS; "
        "'reject' and 'override' carry a non-blank reason."
    ),
    (
        "Signatures verify over transition_signing_payload (signing payload "
        "version 4); this cannot be checked by JSON Schema."
    ),
]


def _with_header(
    schema: dict[str, Any], schema_id: str, title: str, invariants: list[str]
) -> dict[str, Any]:
    header: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": schema_id,
        "title": title,
        "x-folio-schema-version": SCHEMA_VERSION,
        "x-folio-generated-by": f"folio-propositions {__version__}",
        "x-folio-invariants": invariants,
    }
    body = {key: value for key, value in schema.items() if key != "title"}
    return {**header, **body}


def build_proposition_schema() -> dict[str, Any]:
    """Return the normative JSON Schema for one proposition."""

    return _with_header(
        Proposition.model_json_schema(mode="validation"),
        f"urn:folio-propositions:schema:proposition:v{SCHEMA_VERSION}",
        "Proposition",
        _INVARIANTS,
    )


def build_record_schema() -> dict[str, Any]:
    """Return the normative JSON Schema for a per-document record."""

    return _with_header(
        PropositionDocumentRecord.model_json_schema(mode="validation"),
        f"urn:folio-propositions:schema:document-record:v{SCHEMA_VERSION}",
        "PropositionDocumentRecord",
        [
            "Every proposition's schema_version equals the record's.",
            (
                "When source_uri is set, every proposition with text and content_iri "
                "has content_iri == content_iri(source_uri, text), and its text is "
                "non-empty after normalization."
            ),
            "Each proposition satisfies the Proposition invariants.",
        ],
    )


def render(document: dict[str, Any]) -> str:
    """Serialize deterministically; ASCII-only so every code point is explicit."""

    return json.dumps(document, indent=2, ensure_ascii=True, sort_keys=False) + "\n"


def outputs() -> dict[Path, str]:
    return {
        IDENTITY_VECTORS: render(build_identity_vectors()),
        PROPOSITION_SCHEMA: render(build_proposition_schema()),
        RECORD_SCHEMA: render(build_record_schema()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if a committed file differs from the generated one",
    )
    args = parser.parse_args(argv)
    stale = []
    for path, text in outputs().items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == text:
            continue
        if args.check:
            stale.append(path.relative_to(ROOT))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")
    if stale:
        for path in stale:
            print(f"stale: {path}", file=sys.stderr)
        print("run: python scripts/generate_conformance.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
