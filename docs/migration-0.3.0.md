# Migrating to v0.3.0

v0.3.0 aligns four working proposition types with canonical FOLIO labels and
IRIs. It does not add, remove, or rearrange fields in the Proposition ledger.

| v0.2 label | v0.3 canonical label | FOLIO IRI |
|---|---|---|
| `party proposition of law` | `Legal Proposition` | `https://folio.openlegalstandard.org/RNICD9MDcFQJJX6nxX11Vt` |
| `judicial proposition of law` | `Judicial Legal Conclusion` | `https://folio.openlegalstandard.org/RKTUVhpkOGaH53JFNJ4X4s` |
| `party proposition of fact` | `Factual Statement` | `https://folio.openlegalstandard.org/RnKWv1E6U2Ssc5SRsG14NO` |
| `judicial proposition of fact` | `Judicial Finding of Fact` | `https://folio.openlegalstandard.org/R7ZrWzdAOf6mXVtcQ49gWat` |

The six unmatched working types retain their v0.2 labels and map to `None` in
`WORKING_TAXONOMY`. Consumers should migrate stored v2 records before model
validation:

```python
from folio_propositions import PropositionDocumentRecord, migrate_record

migrated = migrate_record(stored_record)
record = PropositionDocumentRecord.model_validate(migrated)
```

`migrate_record` also supports bare proposition dictionaries. Historical
v1→v2 semantics are frozen inside that migration step, so chained v1→v3
migration remains reproducible.
