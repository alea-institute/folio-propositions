# folio-propositions

`folio-propositions` defines the shared, typed Proposition ledger schema used by
`folio-enrich` and `folio-insights`. Each proposition records an asserter side and
a validator side; either side may be null when that is the legally accurate state.

Install the package with:

```bash
pip install folio-propositions
```

```python
from folio_propositions import Proposition

open_position = Proposition(
    id="p-1",
    proposition_type="party proposition of law",
    asserter={"role": "party", "name": "Appellant"},
    validator=None,
    disposition="unresolved",
)
```

