"""Content identity shared by folio-enrich and folio-insights.

This module reproduces, byte for byte, the folio-insights shard IRI recipe
(``folio_insights.shards.minting.mint_shard_iri``). That recipe is a frozen
cross-product contract: a proposition stamped by folio-enrich and a shard
minted by folio-insights for the same normalized ``(source_uri, span)`` pair
carry the same IRI, which is what lets the two products match each other.

The identity is per ``(source, span)``, not per proposition type, asserter, or
job. Two propositions of different types drawn from the same span of the same
source share one content IRI; job-scoped proposition ``id`` values remain the
place for per-extraction identity.

Changing any normalization step, the payload layout, the hash, the prefix, or
the hex length breaks every IRI already minted by either product. Do not
"improve" this module; add a new, separately named scheme instead.
"""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass
from urllib.parse import quote, urlsplit, urlunsplit

CONTENT_IRI_PREFIX = "urn:folio:shard/"
CONTENT_IRI_HEX_LEN = 32
DOCUMENT_URI_PREFIX = "urn:sha256:"


@dataclass(frozen=True)
class ContentIdentity:
    """A content IRI and the full SHA-256 provenance hash it was cut from."""

    iri: str
    provenance_hash: str


def normalize_source_uri(uri: str) -> str:
    """Normalize a source URI exactly as folio-insights does before hashing."""

    parts = urlsplit(uri)
    scheme = parts.scheme.lower()
    netloc = unicodedata.normalize("NFC", parts.netloc).lower()
    path = quote(unicodedata.normalize("NFC", parts.path), safe="/%:@")
    if path.endswith("/") and path != "/":
        path = path.rstrip("/")
    query = unicodedata.normalize("NFC", parts.query)
    fragment = unicodedata.normalize("NFC", parts.fragment)
    return urlunsplit((scheme, netloc, path, query, fragment))


def normalize_span(span: str) -> str:
    """Normalize newlines to LF, apply NFC, and strip surrounding whitespace."""

    lf = span.replace("\r\n", "\n").replace("\r", "\n")
    return unicodedata.normalize("NFC", lf).strip()


def content_identity(source_uri: str, span: str) -> ContentIdentity:
    """Return the content identity for one span of one source.

    Raises ``ValueError`` when ``source_uri`` is empty or ``span`` normalizes
    to the empty string.
    """

    if not source_uri:
        raise ValueError("source_uri must be a non-empty string")
    span_n = normalize_span(span)
    if not span_n:
        raise ValueError("span must not normalize to an empty string")
    uri_n = normalize_source_uri(source_uri)
    payload = (uri_n + "\n" + span_n).encode("utf-8")
    hash_hex = hashlib.sha256(payload).hexdigest()
    return ContentIdentity(
        iri=f"{CONTENT_IRI_PREFIX}{hash_hex[:CONTENT_IRI_HEX_LEN]}",
        provenance_hash=hash_hex,
    )


def content_iri(source_uri: str, span: str) -> str:
    """Return only the content IRI for one span of one source."""

    return content_identity(source_uri, span).iri


def document_source_uri(text: str) -> str:
    """Return the default deterministic source URI for an unnamed document.

    The URI is ``urn:sha256:`` followed by the SHA-256 hex digest of the
    document text after :func:`normalize_span`. The same canonical text
    (identical after LF/NFC/strip normalization) always yields the same URI,
    so two runs over one document without a caller-supplied URI mint the same
    content IRIs. Prefer a real, caller-supplied source URI when one exists.
    """

    normalized = normalize_span(text)
    if not normalized:
        raise ValueError("document text must not normalize to an empty string")
    return DOCUMENT_URI_PREFIX + hashlib.sha256(normalized.encode("utf-8")).hexdigest()
