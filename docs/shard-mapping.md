# folio-insights shard mapping

The folio-insights shard vocabulary maps onto the shared Proposition ledger as
shown below; these mappings remain design hypotheses until annotation testing.

| insights shard type | Proposition-model configuration | Status |
|---|---|---|
| `simple_assertion` | Proposition with a plain balanced entry | design-only |
| `hypothesis` | Asserter role `system` (generated), validator null | design-only |
| `gloss` | Asserter `secondary_source`; citation edge type `interprets`/`elaborates` | design-only |
| `disputed_proposition` | A thread of propositions linked by stance edges | design-only |
| `conflicting_authorities` | **Cross-document composite — stays application-level in folio-insights**, built from library propositions; not a single-model configuration | design-only |

Completion and annotation-tested status updates happen in U7.

