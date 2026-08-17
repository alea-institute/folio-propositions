"""Pydantic models for the double-entry Proposition ledger."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field, model_validator

SCHEMA_VERSION = 2

WORKING_TAXONOMY = frozenset(
    {
        "party proposition of law",
        "party proposition of fact",
        "judicial proposition of law",
        "judicial proposition of fact",
        "stipulation",
        "arguendo assumption",
        "judicial notice",
        "cited-authority proposition",
        "hypothetical illustration",
        "policy proposition",
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


class AxiomStatus(str, Enum):
    PROPOSITION = "proposition"
    PROMOTED = "promoted"
    DEMOTED = "demoted"
    SUPERSEDED = "superseded"


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

    @model_validator(mode="after")
    def validate_model_contract(self) -> Proposition:
        span_fields = (self.start_char, self.end_char, self.text)
        if any(value is not None for value in span_fields) and not all(
            value is not None for value in span_fields
        ):
            raise ValueError("start_char, end_char, and text must be supplied together")
        if self.start_char is not None and self.end_char is not None:
            if self.end_char < self.start_char:
                raise ValueError("end_char must not precede start_char")
        if not self.is_new_type and self.proposition_type not in WORKING_TAXONOMY:
            raise ValueError("proposition_type is not in the working taxonomy")
        if self.shape not in SHAPES:
            raise ValueError(f"unregistered proposition shape: {self.shape}")
        return self
