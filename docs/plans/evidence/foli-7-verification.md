# foli-7 build verification

Plan: [Land Authorized Signer and Lifecycle Migration Examples](../2026-11-11-0216-feat-foli-7-land-migration-examples-plan.md)

Branch: `drawdown/foli-7`. Item kind: expansion. Verified on 2026-11-11.
The replacement PR supersedes #6 and #9.

## Restoration and comparison bases

- Frozen build starting tip: `9872740c4fa73844272b0927332ab0d05301e4da`.
- Supplied implementation baseline: `be8db76172f3e5a792bf19823b709db2a4512eea`.
- Local `main`: `90f94bea43ce6f63176cd6271c7006c72f528dd3`, an older ancestor
  of the supplied baseline. The controller must compare against its current
  publication target; this lane preserved the newer checkout.
- Original PR head: `37ad3b828b0112ac52366985f3fcb590b989ecf4`.
- Checked code commit: `127c0c5381437c82fec4abfa5384bdad67696905`.

The mandate's merge-base-to-source-head cherry-pick range restored all five
commits. The only conflict was in `README.md`; its resolution retains the
v0.5.0 lifecycle guidance, both migration links, normative shape, conformance
section, and generator command, and adds the consumer-example link.

| Original commit | Restored commit | Contribution |
| --- | --- | --- |
| `53a5970` | `593586e` | Historical migration-example plan. |
| `c7576b7` | `c47cf99` | Authorized native lifecycle example and tests. |
| `366df2e` | `b74f4e0` | Explicit legacy trust example and tests. |
| `00637b8` | `3cad5a4` | Runnable guide, README link, and console-output test. |
| `37ad3b8` | `127c0c5` | Historical verification receipt and comment cleanup. |

Both `git diff main..HEAD` and `git diff 9872740..HEAD` include
`examples/migration_v4.py` and `tests/test_migration_examples.py`. The example,
all 19 restored test cases, migration guide, original plan, and historical
receipt match the original PR head byte for byte. The historical receipt's
results are not evidence for this landing.

No library source, existing test, dependency declaration, schema, CI workflow,
generator, or deployment configuration changed relative to the frozen build
starting tip. No existing or restored test was removed or weakened.

## Fresh environment and baseline

Fresh environments were created with `uv 0.9.22`. For each suffix `311`, `312`,
and `313`, the corresponding interpreter was selected with `uv venv --python`
and installed with:

```bash
uv pip install --python .venv/foli7-py311/bin/python -e '.[dev,signing]'
```

The same command was used with the matching environment suffix for the other
two interpreters. Installed versions were pytest 9.2.0, Ruff 0.17.4,
mypy 2.4.1, pydantic 2.14.3, and cryptography 50.0.2 on all three.

Before cherry-picking, Python 3.11.14 passed all 221 existing tests,
`ruff check .`, `mypy src`, and
`python scripts/generate_conformance.py --check`. The example source and
test file were absent. This restoration used the original integration tests
and the passing baseline as characterization; it did not recreate or alter
the implementation through a new red/green cycle.

## Verification results

Commands below use the matching environment's executable. Tests use the
console `pytest` entry point from CI, including the real script subprocess.

| Check | Python 3.11.14 | Python 3.12.12 | Python 3.13.11 |
| --- | --- | --- | --- |
| `pytest -q` | 240 passed | 240 passed | 240 passed |
| `ruff check .` | Passed | Passed | Passed |
| `mypy src examples/migration_v4.py` | Passed, 7 files | Passed, 7 files | Passed, 7 files |
| `python scripts/generate_conformance.py --check` | Passed | Passed | Passed |
| `python examples/migration_v4.py` | Exact documented output | Exact documented output | Exact documented output |

Additional Python 3.11.14 checks:

- `pytest -q tests/test_migration_examples.py`: 19 passed.
- `pytest -q tests/test_migration_examples.py tests/test_lifecycle.py tests/test_interchange.py`:
  118 passed.
- Executed the Python fragment under “Applying a signed transition” directly
  from `docs/migration-0.4.0.md`; it promotes the new proposition and leaves
  the original unchanged.
- Installed only `-e .` in a separate fresh `.venv/foli7-core` environment;
  CI's isolated import command passed:
  `python -I -c "import importlib.util; assert importlib.util.find_spec('cryptography') is None; import folio_propositions"`.
- Verified all local file links and heading anchors in the README and migration
  guide, plus `git diff --check`.

The restored tests exercise native replay using unchanged signed events,
authorization on append and every saved entry, obsolete and cross-identity
replay rejection, malformed record rejection before signature verification,
default rejection of the unsigned legacy opener, explicit caller trust, and
authorization/signature checks on the signed legacy suffix. They use real,
ephemeral signatures and no persistent keys or stored records.

## Controller follow-through

The chief campaign plan and common mandate file are unavailable in this
sandbox, as recorded in the landing plan. The supplied lane rules govern this
build; the controller must reconcile the named campaign Goal Capsule and
rule excerpts. Controller CI and campaign Astra/Fable reviews still apply.

There is no front-end change, so browser tests and screenshot evidence do not
apply. No schema migration, stored-data rewrite, package release, new service,
or user decision is needed. Commits remain local because the clone has no
remote; the controller owns push and PR creation, and the campaign merge gate
owns merging.
