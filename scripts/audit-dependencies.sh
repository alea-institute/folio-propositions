#!/usr/bin/env bash
set -euo pipefail

audited_python=${1:?usage: audit-dependencies.sh PYTHON REPORT_PREFIX PIP_AUDIT}
report_prefix=${2:?report prefix required}
auditor=${3:?isolated pip-audit executable required}
mkdir -p "$(dirname "$report_prefix")"
uv pip check --python "$audited_python"
uv pip freeze --python "$audited_python" > "$report_prefix.freeze"

"$audited_python" -I - "$report_prefix" <<'PY'
import re
import sys
import tomllib
from pathlib import Path

prefix = sys.argv[1]
root = Path.cwd().resolve()
version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
wheel = root / "dist" / f"folio_propositions-{version}-py3-none-any.whl"
local = {f"-e {root.as_uri()}", f"folio-propositions @ {wheel.as_uri()}"}
pins = []
for line in Path(prefix + ".freeze").read_text().splitlines():
    if line in local:
        continue
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*==[A-Za-z0-9][A-Za-z0-9.!_-]*", line):
        raise SystemExit("Audit refused an unexpected editable, URL, or unpinned requirement")
    if re.sub(r"[-_.]+", "-", line.split("==")[0]).lower() == "folio-propositions":
        raise SystemExit("Audit refused an unexpected local distribution origin")
    pins.append(line)
if not pins:
    raise SystemExit("Audit refused an empty dependency inventory")
Path(prefix + ".requirements.txt").write_text("\n".join(pins) + "\n")
PY

timeout 120 "$auditor" --requirement "$report_prefix.requirements.txt" \
  --vulnerability-service pypi --no-deps --disable-pip --strict \
  --timeout 15 --progress-spinner off --format json --output "$report_prefix.json"

"$audited_python" -I - "$report_prefix" <<'PY'
import json
import re
import sys
from pathlib import Path

prefix = sys.argv[1]


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


expected = {
    (normalize(name), version)
    for name, version in (
        line.split("==")
        for line in Path(prefix + ".requirements.txt").read_text().splitlines()
    )
}
dependencies = json.loads(Path(prefix + ".json").read_text())["dependencies"]
actual = set()
for entry in dependencies:
    if "skip_reason" in entry or entry["vulns"] != []:
        raise SystemExit("Dependency audit has skipped packages or vulnerabilities")
    actual.add((normalize(entry["name"]), entry["version"]))
if actual != expected or len(dependencies) != len(expected):
    raise SystemExit("Dependency audit did not cover the complete inventory")
print(f"Audited {len(expected)} pinned dependencies; no skips or known vulnerabilities")
PY
