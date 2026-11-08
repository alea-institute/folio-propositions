"""Exercise the audit gate's input and exit boundaries without network access."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLEAN = {"dependencies": [{"name": "pydantic", "version": "2.14.1", "vulns": []}]}


@pytest.fixture
def audit_gate(tmp_path, monkeypatch):
    freeze = tmp_path / "freeze"
    report = tmp_path / "report"
    called = tmp_path / "called"
    uv = tmp_path / "uv"
    uv.write_text('#!/bin/sh\nif [ "$2" = freeze ]; then cat "$AUDIT_TEST_FREEZE"; fi\n')
    uv.chmod(0o755)
    auditor = tmp_path / "auditor"
    auditor.write_text(
        f"#!{sys.executable}\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        "Path(os.environ['AUDIT_TEST_CALLED']).touch()\n"
        "Path(sys.argv[sys.argv.index('--output') + 1]).write_text(\n"
        "    Path(os.environ['AUDIT_TEST_REPORT']).read_text())\n"
        "sys.exit(int(os.environ.get('AUDIT_TEST_EXIT', '0')))\n"
    )
    auditor.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("AUDIT_TEST_FREEZE", str(freeze))
    monkeypatch.setenv("AUDIT_TEST_REPORT", str(report))
    monkeypatch.setenv("AUDIT_TEST_CALLED", str(called))

    def run(inventory="pydantic==2.14.1\n", result=CLEAN):
        freeze.write_text(inventory)
        report.write_text(json.dumps(result))
        completed = subprocess.run(
            [
                "bash", "scripts/audit-dependencies.sh", sys.executable,
                str(tmp_path / "audit"), str(auditor),
            ],
            cwd=ROOT, capture_output=True, text=True, timeout=10, check=False,
        )
        return completed, called.exists()

    return run


@pytest.mark.parametrize(
    "local",
    [
        f"-e {ROOT.as_uri()}\n",
        f"folio-propositions @ {ROOT.as_uri()}/dist/folio_propositions-0.4.0-py3-none-any.whl\n",
        "",
    ],
)
def test_audit_accepts_complete_pins_and_only_known_local_origins(audit_gate, local):
    result, called = audit_gate(local + "pydantic==2.14.1\n")
    assert result.returncode == 0, result.stderr
    assert called
    assert "Audited 1 pinned dependencies" in result.stdout


@pytest.mark.parametrize(
    "inventory",
    [
        "-e file:///unexpected\n",
        "pydantic @ https://example.com/private.whl\n",
        "pydantic>=2\n",
        "folio-propositions==0.4.0\n",
        "",
    ],
)
def test_audit_rejects_unexpected_inventory_before_contacting_service(audit_gate, inventory):
    result, called = audit_gate(inventory)
    assert result.returncode != 0
    assert not called


@pytest.mark.parametrize(
    "report",
    [
        {},
        {"dependencies": []},
        {"dependencies": CLEAN["dependencies"] * 2},
        {"dependencies": [{"name": "pydantic", "skip_reason": "unavailable"}]},
        {"dependencies": [{"name": "pydantic", "version": "2.14.1", "vulns": [{}]}]},
        {"dependencies": [{"name": "pydantic", "version": "2.14.0", "vulns": []}]},
    ],
)
def test_audit_rejects_incomplete_skipped_malformed_or_vulnerable_reports(audit_gate, report):
    result, called = audit_gate(result=report)
    assert result.returncode != 0
    assert called


def test_audit_preserves_auditor_failure_even_with_clean_report(audit_gate, monkeypatch):
    monkeypatch.setenv("AUDIT_TEST_EXIT", "7")
    result, called = audit_gate()
    assert result.returncode == 7
    assert called
