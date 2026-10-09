"""Pydantic models for the double-entry Proposition ledger."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from pydantic import BaseModel, Field, model_validator

from .identity import CONTENT_IRI_HEX_LEN, CONTENT_IRI_PREFIX
from .lifecycle import AxiomAction, AxiomStatus, AxiomTransition

SCHEMA_VERSION = 4

_CONTENT_IRI_PATTERN = re.compile(
    re.escape(CONTENT_IRI_PREFIX) + "[0-9a-f]{" + str(CONTENT_IRI_HEX_LEN) + "}"
)

# Canonical FOLIO labels carry their ontology IRIs. Library-local working types
# remain closed taxonomy entries with no IRI until FOLIO grows an exact home.
WORKING_TAXONOMY: Mapping[str, str | None] = MappingProxyType(
    {
        "Legal Proposition": (
            "https://folio.openlegalstandard.org/RNICD9MDcFQJJX6nxX11Vt"
        ),
        "Factual Statement": (
            "https://folio.openlegalstandard.org/RnKWv1E6U2Ssc5SRsG14NO"
        ),
        "Judicial Legal Conclusion": (
            "https://folio.openlegalstandard.org/RKTUVhpkOGaH53JFNJ4X4s"
        ),
        "Judicial Finding of Fact": (
            "https://folio.openlegalstandard.org/R7ZrWzdAOf6mXVtcQ49gWat"
        ),
        "stipulation": None,
        "arguendo assumption": None,
        "judicial notice": None,
        "cited-authority proposition": None,
        "hypothetical illustration": None,
        "policy proposition": None,
    }
)


class ActorRole(str, Enum):
    PARTY = "party"
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    APPELLANT = "appellant"
    APPELLEE = "appellee"
    PETITIONER = "petitioner"
    RESPONDENT = "respondent"
    BOTH_PARTIES = "both_parties"
    COURT = "court"
    SECONDARY_SOURCE = "secondary_source"
    SYSTEM = "system"


class AdjudicationMode(str, Enum):
    RULED = "ruled"
    PRO_FORMA = "pro_forma"
    DECLINED = "declined"


class Disposition(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVISED = "revised"
    UNRESOLVED = "unresolved"
    ASSUMED_ARGUENDO = "assumed-arguendo"


class CitationEdgeType(str, Enum):
    SUPPORTS = "supports"
    DISTINGUISHES = "distinguishes"
    OVERRULES = "overrules"
    FOLLOWS = "follows"
    CITES_RECORD_EVIDENCE = "cites_record_evidence"
    INTERPRETS = "interprets"
    ELABORATES = "elaborates"
    CITES = "cites"


class ActorRef(BaseModel):
    role: ActorRole
    individual_id: str | None = None
    name: str | None = None
    assumed: bool = False


class AdjudicatorRef(BaseModel):
    role: ActorRole
    individual_id: str | None = None
    name: str | None = None
    mode: AdjudicationMode = AdjudicationMode.RULED


class CitationEdge(BaseModel):
    edge_type: CitationEdgeType
    authority_individual_id: str
    authority_text: str | None = None


@dataclass(frozen=True)
class PropositionShape:
    """A named ontology configuration and its expected actor vocabulary."""

    name: str
    expected_roles: frozenset[ActorRole]
    description: str


SHAPES: dict[str, PropositionShape] = {
    "litigation": PropositionShape(
        name="litigation",
        expected_roles=frozenset(
            {
                ActorRole.PARTY,
                ActorRole.PLAINTIFF,
                ActorRole.DEFENDANT,
                ActorRole.APPELLANT,
                ActorRole.APPELLEE,
                ActorRole.PETITIONER,
                ActorRole.RESPONDENT,
                ActorRole.BOTH_PARTIES,
                ActorRole.COURT,
            }
        ),
        description="Adversarial legal assertion and adjudication ledger.",
    ),
    "disputatio": PropositionShape(
        name="disputatio",
        expected_roles=frozenset(
            {ActorRole.PARTY, ActorRole.SECONDARY_SOURCE, ActorRole.SYSTEM}
        ),
        description="Dialectical proposition and response configuration.",
    ),
}


class Proposition(BaseModel):
    id: str
    schema_version: int = Field(default=SCHEMA_VERSION, ge=1)
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, ge=0)
    text: str | None = None
    proposition_type: str
    is_new_type: bool = False
    asserter: ActorRef | None
    validator: AdjudicatorRef | None
    disposition: Disposition
    citation_edges: list[CitationEdge] = Field(default_factory=list)
    triple_ids: list[str] = Field(default_factory=list)
    shape: str = "litigation"
    axiom_status: AxiomStatus = AxiomStatus.PROPOSITION
    content_iri: str | None = None
    axiom_history: list[AxiomTransition] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_model_contract(self) -> Proposition:
        span_fields = (self.start_char, self.end_char, self.text)
        if any(value is not None for value in span_fields) and not all(
            value is not None for value in span_fields
        ):
            raise ValueError("start_char, end_char, and text must be supplied together")
        if (
            self.start_char is not None
            and self.end_char is not None
            and self.end_char < self.start_char
        ):
            raise ValueError("end_char must not precede start_char")
        if not self.is_new_type and self.proposition_type not in WORKING_TAXONOMY:
            raise ValueError("proposition_type is not in the working taxonomy")
        if self.shape not in SHAPES:
            raise ValueError(f"unregistered proposition shape: {self.shape}")
        if self.content_iri is not None and not _CONTENT_IRI_PATTERN.fullmatch(
            self.content_iri
        ):
            raise ValueError(
                f"content_iri must be {CONTENT_IRI_PREFIX} followed by "
                f"{CONTENT_IRI_HEX_LEN} lowercase hex characters"
            )
        self._validate_axiom_history()
        return self

    def _validate_axiom_history(self) -> None:
        previous = AxiomStatus.PROPOSITION
        for index, entry in enumerate(self.axiom_history):
            if entry.from_status != previous:
                raise ValueError(
                    f"axiom_history[{index}] starts from {entry.from_status.value}, "
                    f"expected {previous.value}"
                )
            if entry.action is AxiomAction.MIGRATE and index != 0:
                raise ValueError(
                    "only the first axiom_history entry may be a migrate entry"
                )
            previous = entry.to_status
        if self.axiom_status != previous:
            raise ValueError(
                f"axiom_status {self.axiom_status.value} does not match the "
                f"axiom_history end state {previous.value}"
            )
