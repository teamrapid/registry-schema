"""Check codes from vocabularies that linkml-term-validator cannot reach.

linkml-term-validator checks the OBO ontologies (MONDO, HPO, UBERON, SO, GENO,
ECO, NCBITaxon) through the EBI Ontology Lookup Service. This script covers
the rest: it finds every {id, label} Concept in a data file whose prefix is
LOINC, RXNORM, SNOMEDCT, CVX, HGNC, UCUM, ICD10CM or OMIM, looks the code up,
and compares the label.

Lookup sources, in order:

* LOINC  - NLM Clinical Table Search Service, then BioPortal (answer codes LA...)
* RXNORM - NLM RxNav, then BioPortal
* HGNC   - genenames.org REST API
* UCUM   - NLM Clinical Table Search Service
* SNOMEDCT, CVX, ICD10CM, OMIM - BioPortal only

BioPortal needs an API key. Set BIOPORTAL_API_KEY, or in a Claude Code cloud
session save it as a network secret for data.bioontology.org and the proxy
adds it. Without a working key the BioPortal-only codes are reported as
UNCHECKED, which is not a failure.

    python scripts/check_codes.py examples/valid/*.yaml
    python scripts/check_codes.py --schema-mappings src/rapid_registry_schema/schema/rapid_registry.yaml

Exit status is 1 if any code is NOT_FOUND or has a LABEL_MISMATCH.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import yaml

CHECKED_PREFIXES = {"LOINC", "RXNORM", "SNOMEDCT", "CVX", "HGNC", "UCUM", "ICD10CM", "OMIM"}

# BioPortal acronym and class-IRI base for each prefix (UMLS-derived ontologies).
BIOPORTAL = {
    "SNOMEDCT": ("SNOMEDCT", "http://purl.bioontology.org/ontology/SNOMEDCT/"),
    "RXNORM": ("RXNORM", "http://purl.bioontology.org/ontology/RXNORM/"),
    "LOINC": ("LOINC", "http://purl.bioontology.org/ontology/LNC/"),
    "CVX": ("CVX", "http://purl.bioontology.org/ontology/CVX/"),
    "ICD10CM": ("ICD10CM", "http://purl.bioontology.org/ontology/ICD10CM/"),
    "OMIM": ("OMIM", "http://purl.bioontology.org/ontology/OMIM/"),
}


class Unreachable(Exception):
    """The service could not be asked (network error, or 401/403 from BioPortal)."""


@dataclass
class Result:
    curie: str
    given_label: str | None
    status: str  # OK, LABEL_MISMATCH, NOT_FOUND, UNCHECKED
    found_label: str | None = None
    source: str = ""
    where: str = ""


def _get_json(url: str, headers: dict[str, str] | None = None):
    req = urllib.request.Request(url, headers={"Accept": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        if e.code in (401, 403):
            raise Unreachable(f"HTTP {e.code}") from e
        raise Unreachable(f"HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise Unreachable(str(e.reason)) from e


def bioportal(prefix: str, code: str) -> str | None:
    acronym, base = BIOPORTAL[prefix]
    iri = urllib.parse.quote(base + code, safe="")
    headers = {}
    key = os.environ.get("BIOPORTAL_API_KEY")
    if key:
        headers["Authorization"] = f"apikey token={key}"
    d = _get_json(f"https://data.bioontology.org/ontologies/{acronym}/classes/{iri}", headers)
    return d.get("prefLabel") if d else None


def loinc(code: str) -> tuple[str | None, str]:
    if not code.startswith(("LA", "LP", "LG")):
        url = ("https://clinicaltables.nlm.nih.gov/api/loinc_items/v3/search?"
               + urllib.parse.urlencode({"terms": code, "df": "LOINC_NUM,LONG_COMMON_NAME", "maxList": 20}))
        d = _get_json(url)
        for num, name in (d[3] if d else []) or []:
            if num == code:
                return name, "NLM Clinical Tables"
    return bioportal("LOINC", code), "BioPortal"


def rxnorm(code: str) -> tuple[str | None, str]:
    d = _get_json(f"https://rxnav.nlm.nih.gov/REST/rxcui/{urllib.parse.quote(code)}/properties.json")
    props = (d or {}).get("properties")
    return (props["name"] if props else None), "RxNav"


def hgnc(code: str) -> tuple[str | None, str]:
    d = _get_json(f"https://rest.genenames.org/fetch/hgnc_id/{urllib.parse.quote(code)}")
    docs = ((d or {}).get("response") or {}).get("docs") or []
    return (docs[0]["symbol"] if docs else None), "genenames.org"


def ucum(code: str) -> tuple[str | None, str]:
    url = ("https://clinicaltables.nlm.nih.gov/api/ucum/v3/search?"
           + urllib.parse.urlencode({"terms": code, "df": "cs_code,name", "maxList": 50}))
    d = _get_json(url)
    for cs, name in (d[3] if d else []) or []:
        if cs == code:
            return name, "NLM Clinical Tables"
    return None, "NLM Clinical Tables"


def lookup(curie: str) -> tuple[str | None, str]:
    prefix, code = curie.split(":", 1)
    if prefix == "LOINC":
        return loinc(code)
    if prefix == "RXNORM":
        try:
            return rxnorm(code)
        except Unreachable:
            return bioportal("RXNORM", code), "BioPortal"
    if prefix == "HGNC":
        return hgnc(curie)
    if prefix == "UCUM":
        return ucum(code)
    return bioportal(prefix, code), "BioPortal"


def check(curie: str, label: str | None, where: str, cache: dict) -> Result:
    if curie not in cache:
        try:
            cache[curie] = lookup(curie)
        except Unreachable as e:
            cache[curie] = (Unreachable(str(e)), "")
    found, source = cache[curie]
    if isinstance(found, Unreachable):
        return Result(curie, label, "UNCHECKED", source=str(found), where=where)
    if found is None:
        return Result(curie, label, "NOT_FOUND", source=source, where=where)
    if label is not None and label.casefold() != found.casefold():
        return Result(curie, label, "LABEL_MISMATCH", found, source, where)
    return Result(curie, label, "OK", found, source, where)


def concepts_in_data(obj, path="$"):
    if isinstance(obj, dict):
        cid = obj.get("id")
        if isinstance(cid, str) and cid.split(":", 1)[0] in CHECKED_PREFIXES:
            yield cid, obj.get("label"), path
        for k, v in obj.items():
            yield from concepts_in_data(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from concepts_in_data(v, f"{path}[{i}]")


def mappings_in_schema(schema: dict):
    for ename, enum in (schema.get("enums") or {}).items():
        for pv_name, pv in ((enum or {}).get("permissible_values") or {}).items():
            for curie in (pv or {}).get("exact_mappings") or []:
                if curie.split(":", 1)[0] in CHECKED_PREFIXES:
                    yield curie, None, f"{ename}.{pv_name}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--schema-mappings", action="store_true",
                    help="treat the files as schemas and check enum exact_mappings (existence only)")
    args = ap.parse_args(argv)

    cache: dict = {}
    results: list[Result] = []
    for f in args.files:
        doc = yaml.safe_load(f.read_text())
        found = mappings_in_schema(doc) if args.schema_mappings else concepts_in_data(doc)
        for curie, label, where in found:
            results.append(check(curie, label, f"{f.name}:{where}", cache))

    counts: dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
        if r.status != "OK":
            detail = {"LABEL_MISMATCH": f"label {r.given_label!r}, source says {r.found_label!r}",
                      "NOT_FOUND": f"not found in {r.source}",
                      "UNCHECKED": f"no service reachable ({r.source})"}[r.status]
            print(f"{r.status:15} {r.curie:28} {detail}  [{r.where}]")
    print("summary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) if counts else "summary: no codes")
    return 1 if counts.get("NOT_FOUND") or counts.get("LABEL_MISMATCH") else 0


if __name__ == "__main__":
    sys.exit(main())
