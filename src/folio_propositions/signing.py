"""Optional did:key Ed25519 signing and verification for axiom transitions.

Requires the ``signing`` extra (``pip install folio-propositions[signing]``),
which installs ``cryptography``. The import is deferred until a key is
actually used, so the core library depends only on pydantic.
"""

from __future__ import annotations

import base64
import binascii
from typing import TYPE_CHECKING

from .lifecycle import (
    AxiomTransition,
    AxiomTransitionDraft,
    TransitionSignature,
    transition_signing_payload,
)

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_B58_INDEX = {char: index for index, char in enumerate(_B58_ALPHABET)}
_ED25519_MULTICODEC = b"\xed\x01"
_DID_KEY_PREFIX = "did:key:z"
# An Ed25519 did:key multibase body is 48 characters; anything far longer is
# rejected before decoding so hostile input cannot force big-integer work.
MAX_MULTIBASE_LENGTH = 128
_MAX_SIGNATURE_LENGTH = 128


def base58btc_encode(data: bytes) -> str:
    """Encode bytes with the Bitcoin base58 alphabet."""

    number = int.from_bytes(data, "big")
    encoded = ""
    while number:
        number, remainder = divmod(number, 58)
        encoded = _B58_ALPHABET[remainder] + encoded
    leading_zeros = len(data) - len(data.lstrip(b"\x00"))
    return "1" * leading_zeros + encoded


def base58btc_decode(text: str, max_length: int = MAX_MULTIBASE_LENGTH) -> bytes:
    """Decode Bitcoin-alphabet base58; raises ``ValueError`` on bad input.

    Input longer than ``max_length`` characters is rejected before decoding.
    """

    if len(text) > max_length:
        raise ValueError(f"base58 input exceeds {max_length} characters")
    number = 0
    for char in text:
        if char not in _B58_INDEX:
            raise ValueError(f"invalid base58 character: {char!r}")
        number = number * 58 + _B58_INDEX[char]
    leading_ones = len(text) - len(text.lstrip("1"))
    body = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    return b"\x00" * leading_ones + body


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    padded = text + "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def did_key_from_public_bytes(raw: bytes) -> str:
    """Return the ``did:key`` for a raw 32-byte Ed25519 public key."""

    if len(raw) != 32:
        raise ValueError("Ed25519 public keys are 32 bytes")
    return _DID_KEY_PREFIX + base58btc_encode(_ED25519_MULTICODEC + raw)


def public_bytes_from_did_key(did: str) -> bytes:
    """Return the raw Ed25519 public key encoded in a ``did:key``."""

    if not did.startswith(_DID_KEY_PREFIX):
        raise ValueError("not a base58btc did:key")
    if len(did) - len(_DID_KEY_PREFIX) > MAX_MULTIBASE_LENGTH:
        raise ValueError("did:key multibase part is too long")
    decoded = base58btc_decode(did[len(_DID_KEY_PREFIX) :])
    if not decoded.startswith(_ED25519_MULTICODEC) or len(decoded) != 34:
        raise ValueError("did:key does not encode an Ed25519 public key")
    return decoded[len(_ED25519_MULTICODEC) :]


class DidKeyEd25519Verifier:
    """Verify Ed25519 transition signatures whose actor is a ``did:key``.

    ``did:key`` is self-certifying: this proves only that the key encoded in
    ``actor_did`` signed the payload. Callers must separately check
    ``actor_did`` against their own set of authorized signers.
    """

    def verify(
        self, payload: bytes, signature: TransitionSignature, actor_did: str
    ) -> bool:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PublicKey,
        )

        if signature.algorithm != "ed25519":
            return False
        if not signature.key_id.startswith(actor_did + "#"):
            return False
        fragment = signature.key_id[len(actor_did) + 1 :]
        if len(fragment) > MAX_MULTIBASE_LENGTH:
            return False
        if len(signature.value) > _MAX_SIGNATURE_LENGTH:
            return False
        try:
            public_key = Ed25519PublicKey.from_public_bytes(
                public_bytes_from_did_key(actor_did)
            )
            signature_bytes = _b64url_decode(signature.value)
        except (ValueError, binascii.Error):
            return False
        try:
            public_key.verify(signature_bytes, payload)
        except InvalidSignature:
            return False
        return True


def sign_transition(
    proposition_id: str,
    content_iri: str | None,
    transition_without_signature: AxiomTransitionDraft,
    private_key: Ed25519PrivateKey,
    key_id: str,
) -> AxiomTransition:
    """Sign a draft transition and return the signed :class:`AxiomTransition`.

    Raises ``ValueError`` when ``content_iri`` is ``None``: stamp the
    proposition's content IRI before signing any lifecycle transition.
    """

    payload = transition_signing_payload(
        proposition_id, content_iri, transition_without_signature
    )
    signature = TransitionSignature(
        algorithm="ed25519",
        key_id=key_id,
        value=_b64url_encode(private_key.sign(payload)),
    )
    return AxiomTransition(
        **transition_without_signature.model_dump(), signature=signature
    )
