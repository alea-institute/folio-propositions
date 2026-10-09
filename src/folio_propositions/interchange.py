"""Per-document interchange records and schema migration hooks."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .identity import content_iri
from .models import SCHEMA_VERSION, Proposition


class GeneratorInfo(BaseModel):
    tool: str
    version: str


class PropositionDocumentRecord(BaseModel):
    document_id: str
    schema_version: int = Field(default=SCHEMA_VERSION, ge=1)
    propositions: list[Proposition] = Field(default_factory=list)
    document_metadata: dict[str, Any] | None = None
    generator: GeneratorInfo | None = None
    source_uri: str | None = None

    @model_validator(mode="after")
    def validate_record_contract(self) -> PropositionDocumentRecord:
        for proposition in self.propositions:
            if proposition.schema_version != self.schema_version:
                raise ValueError(
                    f"proposition {proposition.id} schema_version "
                    f"{proposition.schema_version} does not match the record "
                    f"schema_version {self.schema_version}"
                )
        if self.source_uri is not None:
            for proposition in self.propositions:
                if proposition.text is None or proposition.content_iri is None:
                    continue
                expected = content_iri(self.source_uri, proposition.text)
                if proposition.content_iri != expected:
                    raise ValueError(
                        f"proposition {proposition.id} content_iri does not match "
                        "content_iri(source_uri, text)"
                    )
        return self


def stamp_content_iris(record: PropositionDocumentRecord) -> PropositionDocumentRecord:
    """Return a copy with ``content_iri`` computed for every proposition with text.

    Requires ``record.source_uri``; the input record is not modified.
    """

    source_uri = record.source_uri
    if source_uri is None:
        raise ValueError("stamp_content_iris requires record.source_uri")
    propositions = [
        proposition.model_copy(
            update={"content_iri": content_iri(source_uri, proposition.text)}
        )
        if proposition.text is not None
        else proposition.model_copy()
        for proposition in record.propositions
    ]
    return record.model_copy(update={"propositions": propositions})


MigrationStep = Callable[[dict[str, Any]], dict[str, Any]]
MIGRATIONS: dict[tuple[int, int], MigrationStep] = {}

_V2_WORKING_TAXONOMY = frozenset(
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


def register_migration(version_from: int, version_to: int):
    """Register a single, consecutive schema migration step."""

    if version_to != version_from + 1:
        raise ValueError("migration steps must advance exactly one version")

    def decorator(function: MigrationStep) -> MigrationStep:
        MIGRATIONS[(version_from, version_to)] = function
        return function

    return decorator


@register_migration(1, 2)
def _migrate_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
    """Apply cycle-1 taxonomy decisions and advance proposition stamps."""

    def migrate_proposition(proposition: dict[str, Any]) -> None:
        type_rewrites = {
            "dissenting judicial proposition": "judicial proposition of law",
            "hypothetical party claim": "hypothetical illustration",
        }
        stored_type = proposition.get("proposition_type")
        proposition_type = (
            type_rewrites.get(stored_type, stored_type)
            if isinstance(stored_type, str)
            else stored_type
        )
        proposition["proposition_type"] = proposition_type
        if proposition_type in _V2_WORKING_TAXONOMY:
            proposition["is_new_type"] = False
        elif proposition_type == "definitional proposition":
            proposition["is_new_type"] = True
        proposition["schema_version"] = 2

    propositions = data.get("propositions")
    if isinstance(propositions, list):
        for proposition in propositions:
            if isinstance(proposition, dict):
                migrate_proposition(proposition)
    else:
        migrate_proposition(data)

    data["schema_version"] = 2
    return data


@register_migration(2, 3)
def _migrate_v2_to_v3(data: dict[str, Any]) -> dict[str, Any]:
    """Align the four matched proposition types to canonical FOLIO metadata."""

    def migrate_proposition(proposition: dict[str, Any]) -> None:
        type_rewrites = {
            "party proposition of law": "Legal Proposition",
            "party proposition of fact": "Factual Statement",
            "judicial proposition of law": "Judicial Legal Conclusion",
            "judicial proposition of fact": "Judicial Finding of Fact",
        }
        stored_type = proposition.get("proposition_type")
        proposition_type = (
            type_rewrites.get(stored_type, stored_type)
            if isinstance(stored_type, str)
            else stored_type
        )
        proposition["proposition_type"] = proposition_type
        if stored_type in type_rewrites:
            proposition["is_new_type"] = False
        proposition["schema_version"] = 3

    propositions = data.get("propositions")
    if isinstance(propositions, list):
        for proposition in propositions:
            if isinstance(proposition, dict):
                migrate_proposition(proposition)
    else:
        migrate_proposition(data)

    data["schema_version"] = 3
    return data


@register_migration(3, 4)
def _migrate_v3_to_v4(data: dict[str, Any]) -> dict[str, Any]:
    """Add the signed-lifecycle history; content IRIs need a source URI."""

    def migrate_proposition(proposition: dict[str, Any]) -> None:
        history = proposition.get("axiom_history")
        if not history:
            status = proposition.get("axiom_status", "proposition")
            if status is not None and status != "proposition":
                history = [
                    {
                        "from_status": "proposition",
                        "to_status": status,
                        "action": "migrate",
                        "actor_did": None,
                        "at": None,
                        "reason": "pre-v4 status without recorded transition",
                        "signature": None,
                    }
                ]
            else:
                history = []
        proposition["axiom_history"] = history
        proposition["schema_version"] = 4

    propositions = data.get("propositions")
    if isinstance(propositions, list):
        for proposition in propositions:
            if isinstance(proposition, dict):
                migrate_proposition(proposition)
    else:
        migrate_proposition(data)

    data["schema_version"] = 4
    return data


def migrate_record(
    data: dict[str, Any], target_version: int = SCHEMA_VERSION
) -> dict[str, Any]:
    """Return a migrated copy of a stored interchange record."""

    migrated = deepcopy(data)
    current_version = migrated.get("schema_version")
    if not isinstance(current_version, int):
        # Preserve the v0.2 public error contract for migration callers.
        raise ValueError("record schema_version must be an integer")  # noqa: TRY004
    if target_version < current_version:
        raise ValueError("schema downgrades are not supported")
    _check_proposition_versions(migrated, current_version)
    while current_version < target_version:
        next_version = current_version + 1
        try:
            step = MIGRATIONS[(current_version, next_version)]
        except KeyError as error:
            raise ValueError(
                f"no migration registered for v{current_version} to v{next_version}"
            ) from error
        migrated = step(migrated)
        current_version = next_version
    _check_proposition_versions(migrated, target_version, require=True)
    return migrated


def _check_proposition_versions(
    data: dict[str, Any], version: int, *, require: bool = False
) -> None:
    """Reject nested propositions stamped with a different schema version.

    Before migrating, an absent proposition stamp is tolerated (each step
    writes one); after migrating, every nested proposition must carry it.
    """

    propositions = data.get("propositions")
    if not isinstance(propositions, list):
        return
    for proposition in propositions:
        if not isinstance(proposition, dict):
            continue
        if not require and "schema_version" not in proposition:
            continue
        if proposition.get("schema_version") != version:
            raise ValueError(
                "proposition schema_version must match the record schema_version"
            )
