# folio-propositions

`folio-propositions` defines the shared, typed Proposition ledger schema used by
`folio-enrich` and `folio-insights`. Each proposition records an asserter side and
a validator side; either side may be null when that is the legally accurate state.

Install the package with:

```bash
pip install folio-propositions
```

```python
from folio_propositions import Proposition, WORKING_TAXONOMY

open_position = Proposition(
    id="p-1",
    proposition_type="Legal Proposition",
    asserter={"role": "party", "name": "Appellant"},
    validator=None,
    disposition="unresolved",
)

folio_iri = WORKING_TAXONOMY[open_position.proposition_type]
```

`WORKING_TAXONOMY` maps canonical labels to optional FOLIO IRIs. Library-local
working types remain valid entries with a `None` IRI until FOLIO gains an exact
class for them.

## Docs

See the [documentation index](docs/README.md) for the folio-insights shard
mapping, v2.0 ledger rationale, review-disposition template, gold-cycle
learnings template, and Phase A exit-record template.
