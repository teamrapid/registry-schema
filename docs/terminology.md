# Terminologies and how codes are checked

Every coded value in the schema is a `Concept`: an `id` (a CURIE such as
`MONDO:0010726`) and the `label` the vocabulary gives it. This page explains
which vocabulary each kind of value uses, how a code is checked, and what is
needed to check codes from vocabularies outside the OBO Foundry.

## Two kinds of vocabulary

**OBO Foundry ontologies** (MONDO, HPO, UBERON, SO, GENO, ECO, NCBITaxon,
NCIT, DUO) are published openly and served by the EBI Ontology Lookup Service
(OLS). The schema binds each slot to a branch of the ontology with a LinkML
`bindings` block, for example "a diagnosis must be a descendant of
`MONDO:0700096` human disease". `linkml-term-validator` checks both that the
code is in that branch and that the label matches.

**Other clinical vocabularies** (LOINC, RxNorm, SNOMED CT, CVX, HGNC, UCUM,
ICD-10-CM, OMIM, Orphanet) are not OBO ontologies, and
`linkml-term-validator` has no way to look them up. The schema handles these
in two steps:

1. A Concept subclass per vocabulary (`LoincConcept`, `RxNormConcept`,
   `SnomedCtConcept`, `CvxConcept`, `HgncGeneConcept`, `UcumUnitConcept`, and
   the mixed `SymptomConcept`, `SubstanceConcept`, `ObservationCodeConcept`)
   has a regular expression on `id`. Plain `linkml-validate` then rejects a
   code from the wrong vocabulary, such as a MONDO ID in a medication slot.
2. `scripts/check_codes.py` looks each code up in an authoritative service
   and compares the label. This catches a well-formed code that does not
   exist or names something else.

A pattern alone cannot tell a real code from an invented one. Run the
checker on any data that will be shared.

## Which vocabulary goes where

| Slot | Vocabulary | Checked by |
|---|---|---|
| `Diagnosis.condition_concept`, `Registry.disease_focus`, `GeneticFinding.associated_condition`, `Consent.disease_restriction` | MONDO, under `MONDO:0700096` | term validator |
| `Condition.condition_concept`, cause of death, family-history conditions | MONDO or HPO | term validator |
| `PhenotypicFeature.phenotype` | HPO, under `HP:0000118` | term validator |
| onset, severity, temporal pattern, modifiers | HPO, under `HP:0003674`, `HP:0012824`, `HP:0011008`, `HP:0012823` | term validator |
| body sites | UBERON, under `UBERON:0001062` | term validator |
| variant type, zygosity | SO, GENO | term validator |
| phenotype evidence | ECO, under `ECO:0000000` | term validator |
| causal organism | NCBITaxon | term validator |
| labs, vital signs, device measures, instruments, question codes | LOINC | pattern + checker (NLM Clinical Tables) |
| medications and supplements | RxNorm | pattern + checker (RxNav) |
| genes | HGNC | pattern + checker (genenames.org) |
| units | UCUM | pattern + checker (NLM Clinical Tables) |
| procedures, diary symptoms, allergens | SNOMED CT (symptoms may also be HPO) | pattern + checker (BioPortal) |
| vaccines | CVX | pattern + checker (BioPortal) |
| other disease codings (`Diagnosis.equivalent_codings`) | Orphanet, OMIM, ICD-10-CM, ICD-11 | checker for OMIM and ICD-10-CM (BioPortal) |

Original EHR codes go in `source_codings` and are kept as received; they are
not required to pass any check.

## Fixed value sets

Enumerations such as `DataUseEnum` or `ACMGClassificationEnum` give each value
a `meaning`, which is an ontology term, and sometimes `exact_mappings` to
codes other models use. The `meaning` terms (DUO, NCIT, EDAM, OMOP) were
looked up when they were written, and `linkml-term-validator validate-schema`
re-checks the NCIT and DUO ones against OLS. The `exact_mappings` to SNOMED
CT and LOINC answer codes were copied from RareLink 2.0.7 (see
[rarelink-alignment.md](rarelink-alignment.md)) and still need checking; see
the next section.

## BioPortal

[BioPortal](https://bioportal.bioontology.org) hosts SNOMED CT, CVX,
ICD-10-CM, OMIM, LOINC answer codes and many other vocabularies that are not
in the OBO Foundry. `scripts/check_codes.py` uses its REST API
(`data.bioontology.org`) for the vocabularies that have no free lookup service
and as a fallback for LOINC and RxNorm.

BioPortal needs an API key, which comes with a free BioPortal account; it is
shown on <https://bioportal.bioontology.org/account>. The API expects it in
the header `Authorization: apikey token=<key>`.

**Running locally:** export the key and the checker sends it in that header.

```bash
export BIOPORTAL_API_KEY=...    # your own key; never commit it
uv run python scripts/check_codes.py examples/valid/*.yaml
```

**Running in a Claude Code cloud session:** save the key as a network secret
for host `data.bioontology.org` in the environment's settings, with header
`Authorization` and value `apikey token=<key>`. The session's proxy then adds
it to every request to that host, and no environment variable is needed.

This is unrelated to the BioPortal MCP servers (`ncbo/bioportal-mcp`,
`metadatacenter/bioportal-term-mcp`). Those let an assistant search
BioPortal interactively and have their own configuration; the checker here
calls the REST API directly.

**Current status:** the key saved for this project's cloud environment is
rejected by BioPortal (HTTP 401), so SNOMED CT, CVX, OMIM, ICD-10-CM and
LOINC answer codes are currently reported as `UNCHECKED`. `UNCHECKED` is not
a failure; once a valid key is in place, re-run:

```bash
uv run python scripts/check_codes.py --schema-mappings src/rapid_registry_schema/schema/rapid_registry.yaml
```

to check the 69 SNOMED CT and LOINC codes in the schema's `exact_mappings`.

## Checker output

```
LABEL_MISMATCH  RXNORM:114477   label 'aspirin', source says 'levetiracetam'
NOT_FOUND       HGNC:99999999   not found in genenames.org
UNCHECKED       LOINC:LA30202-8 no service reachable (HTTP 401)
summary: LABEL_MISMATCH=1, NOT_FOUND=1, OK=1
```

The exit status is 1 when anything is `NOT_FOUND` or `LABEL_MISMATCH`.
Labels are compared ignoring case. For LOINC the expected label is the Long
Common Name, for RxNorm the RxNorm name, for HGNC the approved symbol, and for
UCUM the unit's name (e.g. `kilogram`).
