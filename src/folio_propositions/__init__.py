"""Public API for the folio-propositions schema library."""

from .interchange import (
    MIGRATIONS,
    GeneratorInfo,
    PropositionDocumentRecord,
    migrate_record,
    register_migration,
)
from .models import (
    SCHEMA_VERSION,
    SHAPES,
    WORKING_TAXONOMY,
    ActorRef,
    ActorRole,
    AdjudicationMode,
    AdjudicatorRef,
    AxiomStatus,
    CitationEdge,
    CitationEdgeType,
    Disposition,
    Proposition,
    PropositionShape,
)

__version__ = "0.2.0"

__all__ = [
    "MIGRATIONS",
    "SCHEMA_VERSION",
    "SHAPES",
    "WORKING_TAXONOMY",
    "ActorRef",
    "ActorRole",
    "AdjudicationMode",
    "AdjudicatorRef",
    "AxiomStatus",
    "CitationEdge",
    "CitationEdgeType",
    "Disposition",
    "GeneratorInfo",
    "Proposition",
    "PropositionDocumentRecord",
    "PropositionShape",
    "migrate_record",
    "register_migration",
]
