"""Validate the example data against the schema.

Structural validation (linkml-validate) runs offline. Ontology-binding
validation (linkml-term-validator) queries the EBI Ontology Lookup Service and
is marked `network`; skip it with `-m "not network"`.
"""

import shutil
import sys
import subprocess
from pathlib import Path

import pytest
from linkml.validator import validate_file

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "src" / "rapid_registry_schema" / "schema" / "rapid_registry.yaml"
OAK_CONFIG = ROOT / "conf" / "oak_config.yaml"
TARGET = "RegistryDataset"

VALID = sorted((ROOT / "examples" / "valid").glob("*.yaml"))
INVALID = sorted((ROOT / "examples" / "invalid").glob("*.yaml"))
INVALID_TERMS = sorted((ROOT / "examples" / "invalid_terms").glob("*.yaml"))


@pytest.mark.parametrize("path", VALID, ids=lambda p: p.name)
def test_valid_examples_pass(path):
    report = validate_file(path, SCHEMA, TARGET)
    assert not report.results, [r.message for r in report.results]


@pytest.mark.parametrize("path", INVALID, ids=lambda p: p.name)
def test_invalid_examples_fail(path):
    report = validate_file(path, SCHEMA, TARGET)
    assert report.results, f"{path.name} was expected to fail validation"


@pytest.mark.parametrize("path", INVALID_TERMS, ids=lambda p: p.name)
def test_term_invalid_examples_pass_structural_validation(path):
    report = validate_file(path, SCHEMA, TARGET)
    assert not report.results, [r.message for r in report.results]


def _term_validate(path, tmp_path):
    exe = shutil.which("linkml-term-validator")
    if exe is None:
        pytest.skip("linkml-term-validator is not installed")
    return subprocess.run(
        [exe, "validate-data", str(path), "-s", str(SCHEMA), "-t", TARGET,
         "-c", str(OAK_CONFIG), "--cache-dir", str(tmp_path / "cache")],
        capture_output=True, text=True, timeout=900,
    )


@pytest.mark.network
@pytest.mark.parametrize("path", VALID, ids=lambda p: p.name)
def test_valid_examples_pass_term_bindings(path, tmp_path):
    result = _term_validate(path, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.network
@pytest.mark.parametrize("path", INVALID_TERMS, ids=lambda p: p.name)
def test_term_invalid_examples_fail_term_bindings(path, tmp_path):
    result = _term_validate(path, tmp_path)
    assert result.returncode != 0, f"{path.name} was expected to fail term validation"


@pytest.mark.network
@pytest.mark.parametrize("path", VALID, ids=lambda p: p.name)
def test_valid_examples_pass_code_check(path):
    """LOINC, RxNorm, HGNC and UCUM codes resolve and carry their source label."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_codes.py"), str(path)],
        capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr
