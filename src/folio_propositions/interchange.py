"""Per-document interchange records and schema migration hooks."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from pydantic import BaseModel, Field

from .models import Proposition, SCHEMA_VERSION, WORKING_TAXONOMY


class GeneratorInfo(BaseModel):
    tool: str
    version: str


class PropositionDocumentRecord(BaseModel):
    document_id: str
    schema_version: int = Field(default=SCHEMA_VERSION, ge=1)
    propositions: list[Proposition] = Field(default_factory=list)
    document_metadata: dict[str, Any] | None = None
    generator: GeneratorInfo | None = None


MigrationStep = Callable[[dict[str, Any]], dict[str, Any]]
MIGRATIONS: dict[tuple[int, int], MigrationStep] = {}


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
        proposition_type = type_rewrites.get(
            proposition.get("proposition_type"), proposition.get("proposition_type")
        )
        proposition["proposition_type"] = proposition_type
        if proposition_type in WORKING_TAXONOMY:
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


def migrate_record(
    data: dict[str, Any], target_version: int = SCHEMA_VERSION
) -> dict[str, Any]:
    """Return a migrated copy of a stored interchange record."""

    migrated = deepcopy(data)
    current_version = migrated.get("schema_version")
    if not isinstance(current_version, int):
        raise ValueError("record schema_version must be an integer")
    if target_version < current_version:
        raise ValueError("schema downgrades are not supported")
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
    return migrated
