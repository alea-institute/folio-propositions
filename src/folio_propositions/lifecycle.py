"""Signed axiom lifecycle for propositions.

A proposition starts as a plain ``proposition``. Promotion, demotion, and
supersession are recorded as an append-only history of
:class:`AxiomTransition` entries, each signed by the acting identity (a DID).
:func:`apply_transition` is the only sanctioned way to advance
``Proposition.axiom_status``; it checks the transition table and verifies the
signature through a caller-supplied :class:`TransitionVerifier`.

The ``migrate`` action is reserved for schema migrations that must record a
pre-v4 status for which no signed transition exists. It is never accepted by
:func:`apply_transition` and carries no signature.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, Protocol

from pydantic import BaseModel, model_validator

if TYPE_CHECKING:
    from .models import Proposition

# The signing payload is a frozen wire format. It stays at 4 even if the
# record SCHEMA_VERSION later advances, so existing signatures keep verifying.
SIGNING_PAYLOAD_VERSION = 4


class AxiomStatus(str, Enum):
    PROPOSITION = "proposition"
    PROMOTED = "promoted"
    DEMOTED = "demoted"
    SUPERSEDED = "superseded"


class AxiomAction(str, Enum):
    PROMOTE = "promote"
    DEMOTE = "demote"
    SUPERSEDE = "supersede"
    MIGRATE = "migrate"


AXIOM_TRANSITIONS: Mapping[tuple[AxiomStatus, AxiomStatus], AxiomAction] = (
    MappingProxyType(
        {
            (AxiomStatus.PROPOSITION, AxiomStatus.PROMOTED): AxiomAction.PROMOTE,
            (AxiomStatus.PROMOTED, AxiomStatus.DEMOTED): AxiomAction.DEMOTE,
            (AxiomStatus.DEMOTED, AxiomStatus.PROMOTED): AxiomAction.PROMOTE,
            (AxiomStatus.PROPOSITION, AxiomStatus.SUPERSEDED): AxiomAction.SUPERSEDE,
            (AxiomStatus.PROMOTED, AxiomStatus.SUPERSEDED): AxiomAction.SUPERSEDE,
            (AxiomStatus.DEMOTED, AxiomStatus.SUPERSEDED): AxiomAction.SUPERSEDE,
        }
    )
)


class IllegalAxiomTransition(ValueError):
    """The requested status change is not in the transition table."""


class AxiomSignatureError(ValueError):
    """A transition signature is missing or does not verify."""


class TransitionSignature(BaseModel):
    algorithm: Literal["ed25519"]
    key_id: str
    value: str


def _check_legal(
    from_status: AxiomStatus, to_status: AxiomStatus, action: AxiomAction
) -> str | None:
    """Return a reason the triple is illegal, or ``None`` when it is legal."""

    if action is AxiomAction.MIGRATE:
        if from_status == to_status:
            return "a migrate entry must change the status"
        return None
    expected = AXIOM_TRANSITIONS.get((from_status, to_status))
    if expected is None:
        return f"illegal axiom transition {from_status.value} -> {to_status.value}"
    if expected is not action:
        return (
            f"transition {from_status.value} -> {to_status.value} requires action "
            f"{expected.value}, not {action.value}"
        )
    return None


class _TransitionBody(BaseModel):
    from_status: AxiomStatus
    to_status: AxiomStatus
    action: AxiomAction
    actor_did: str | None
    at: datetime | None
    reason: str | None = None

    def _validate_body(self) -> None:
        if self.at is not None and self.at.utcoffset() is None:
            raise ValueError("transition timestamp must be timezone-aware")
        if self.action is not AxiomAction.MIGRATE and (
            self.actor_did is None or self.at is None
        ):
            raise ValueError("signed transitions require actor_did and at")
        problem = _check_legal(self.from_status, self.to_status, self.action)
        if problem is not None:
            raise ValueError(problem)


class AxiomTransitionDraft(_TransitionBody):
    """An unsigned transition: the input to :func:`sign_transition`."""

    @model_validator(mode="after")
    def validate_draft(self) -> AxiomTransitionDraft:
        self._validate_body()
        return self


class AxiomTransition(_TransitionBody):
    """One recorded, signed (or legacy ``migrate``) status change."""

    signature: TransitionSignature | None = None

    @model_validator(mode="after")
    def validate_transition(self) -> AxiomTransition:
        self._validate_body()
        if self.action is AxiomAction.MIGRATE:
            if self.signature is not None:
                raise ValueError("migrate entries must not carry a signature")
        elif self.signature is None:
            raise ValueError("signed transitions require a signature")
        return self


def _format_at(at: datetime | None) -> str | None:
    if at is None:
        return None
    return at.astimezone(UTC).isoformat().replace("+00:00", "Z")


def transition_signing_payload(
    proposition_id: str,
    content_iri: str | None,
    transition: AxiomTransition | AxiomTransitionDraft,
) -> bytes:
    """Return the canonical bytes a transition signature covers.

    The payload is ``json.dumps(..., sort_keys=True, separators=(",", ":"),
    ensure_ascii=False)`` encoded as UTF-8 over the proposition id, content
    IRI, from/to status, action, actor DID, UTC timestamp (ISO-8601 with
    ``Z``), reason, and ``schema_version`` 4. The signature itself is
    excluded. For these value types (strings, ``null``, and one small
    integer) this output equals RFC 8785 JSON Canonicalization Scheme output.
    """

    obj: dict[str, Any] = {
        "proposition_id": proposition_id,
        "content_iri": content_iri,
        "from_status": transition.from_status.value,
        "to_status": transition.to_status.value,
        "action": transition.action.value,
        "actor_did": transition.actor_did,
        "at": _format_at(transition.at),
        "reason": transition.reason,
        "schema_version": SIGNING_PAYLOAD_VERSION,
    }
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


class TransitionVerifier(Protocol):
    def verify(
        self, payload: bytes, signature: TransitionSignature, actor_did: str
    ) -> bool: ...


def _verify_entry(
    proposition_id: str,
    content_iri: str | None,
    transition: AxiomTransition,
    verifier: TransitionVerifier,
) -> None:
    if transition.signature is None or transition.actor_did is None:
        raise AxiomSignatureError("transition is not signed")
    payload = transition_signing_payload(proposition_id, content_iri, transition)
    if not verifier.verify(payload, transition.signature, transition.actor_did):
        raise AxiomSignatureError(
            f"signature does not verify for proposition {proposition_id}"
        )


def apply_transition(
    proposition: Proposition,
    transition: AxiomTransition,
    verifier: TransitionVerifier,
) -> Proposition:
    """Return a new proposition with ``transition`` appended and applied.

    Raises :class:`IllegalAxiomTransition` when the transition does not start
    from the proposition's current status, uses ``migrate``, or is not in
    :data:`AXIOM_TRANSITIONS`; raises :class:`AxiomSignatureError` when the
    signature is missing or does not verify. The input is never modified.
    """

    if transition.action is AxiomAction.MIGRATE:
        raise IllegalAxiomTransition("migrate transitions are reserved for migrations")
    if transition.from_status != proposition.axiom_status:
        raise IllegalAxiomTransition(
            f"transition starts from {transition.from_status.value} but proposition "
            f"{proposition.id} is {proposition.axiom_status.value}"
        )
    problem = _check_legal(
        transition.from_status, transition.to_status, transition.action
    )
    if problem is not None:
        raise IllegalAxiomTransition(problem)
    _verify_entry(proposition.id, proposition.content_iri, transition, verifier)
    return proposition.model_copy(
        update={
            "axiom_history": [*proposition.axiom_history, transition],
            "axiom_status": transition.to_status,
        }
    )


def verify_history(proposition: Proposition, verifier: TransitionVerifier) -> None:
    """Re-verify every signed entry of ``proposition.axiom_history``."""

    for transition in proposition.axiom_history:
        if transition.action is AxiomAction.MIGRATE:
            continue
        _verify_entry(proposition.id, proposition.content_iri, transition, verifier)
