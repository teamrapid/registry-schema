# Terminologies and how codes are checked

Every coded value in the schema is a `Concept`: an `id` (a CURIE such as
`MONDO:0010726`) and the `label` the vocabulary gives it. This page explains
which vocabulary each kind of value uses, how a code is checked, and what is
needed to check codes from vocabularies outside the OBO Foundry.

## Two kinds of vocabulary

**OBO Foundry ontologies** (MONDO, HPO, UBERON, SO, GENO, ECO, NCBITaxon,
OBA, NCIT, DUO) are published openly and served by the EBI Ontology Lookup Service
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
| `Condition.condition_concept` | MONDO or HPO preferred; ICD-10-CM or SNOMED CT accepted | pattern + checker (OLS, BioPortal) |
| cause of death | MONDO | term validator |
| family-history conditions | MONDO or HPO | term validator |
| `PhenotypicFeature.phenotype` | HPO, under `HP:0000118` | term validator |
| onset, severity, temporal pattern, modifiers | HPO, under `HP:0003674`, `HP:0012824`, `HP:0011008`, `HP:0012823` | term validator |
| body sites | UBERON, under `UBERON:0001062` | term validator |
| variant type, zygosity | SO, GENO | term validator |
| phenotype evidence | ECO, under `ECO:0000000` | term validator |
| causal organism | NCBITaxon | term validator |
| `Observation.measured_attribute`, `DeviceObservationSeries.measured_attribute` | OBA, under `OBA:0000001` biological attribute | term validator |
| labs, vital signs, device measures, instruments, question codes | LOINC | pattern + checker (NLM Clinical Tables) |
| medications and supplements | RxNorm | pattern + checker (RxNav) |
| genes | HGNC | pattern + checker (genenames.org) |
| units | UCUM | pattern + checker (NLM Clinical Tables) |
| procedures | SNOMED CT or CPT | pattern + checker (BioPortal for SNOMED CT; CPT format only) |
| diary symptoms, allergens | SNOMED CT (symptoms may also be HPO) | pattern + checker (BioPortal) |
| family relationships | OMOP concepts, mapped to the GA4GH Kinship Ontology (KIN) | fixed value set |
| document type | LOINC Document Ontology (FHIR DocumentReference.type) | pattern + checker |
| vaccines | CVX | pattern only (CVX is not in BioPortal) |
| other disease codings (`Diagnosis.equivalent_codings`) | Orphanet, OMIM, ICD-10-CM, ICD-11 | checker for OMIM and ICD-10-CM (BioPortal) |

Original EHR codes go in `source_codings` and are kept as received; they are
not required to pass any check.

## OBA: what a measurement measures

A LOINC code identifies a *test*: there are many LOINC codes for body weight
(measured, stated, by device…). The Ontology of Biological Attributes (OBA),
from the Monarch Initiative, identifies the *trait* being measured, so
`measured_attribute: OBA:VT0001259` (body mass) lets results from different
tests of the same trait be grouped. BDCHM uses OBA the same way. The slot is
optional and sits beside the LOINC code, not instead of it.

### Why `Condition.condition_concept` has no binding

`linkml-term-validator` checks every binding as if it were required,
whatever its `obligation_level` says. A binding to MONDO/HPO would therefore
reject the ICD-10-CM and SNOMED CT codes this slot accepts. The slot instead
relies on its id pattern plus `scripts/check_codes.py`, which looks up all
four vocabularies (MONDO and HPO in OLS, ICD-10-CM and SNOMED CT in
BioPortal). `Diagnosis` keeps a required MONDO binding.

CPT is licensed by the AMA and BioPortal holds only a summary of it, so CPT
codes are format-checked only.

## Fixed value sets

Enumerations such as `DataUseEnum` or `ACMGClassificationEnum` give each value
a `meaning`, which is an ontology term, and sometimes `exact_mappings` to
codes other models use. The `meaning` terms (DUO, NCIT, EDAM, OMOP) were
looked up when they were written, and `linkml-term-validator validate-schema`
re-checks the NCIT and DUO ones against OLS. The `exact_mappings` to SNOMED
CT and LOINC answer codes were copied from RareLink 2.0.7 (see
[rarelink-alignment.md](rarelink-alignment.md)) and were checked through
BioPortal; see the next section.

### Value sets from LinkML valuesets

Where RAPID needed a value set that neither BDCHM nor RD-CDM supplies, it
reuses the [LinkML common value sets](https://linkml.io/valuesets/) (in OLS as
`valuesets`), and the RAPID enum records the source with `exact_mappings:
valuesets:<EnumName>`. Their `meaning` terms were checked one by one, and
only those that name the value itself were kept:

| RAPID enum | From valuesets | Kept | Not used, and why |
|---|---|---|---|
| `DataUseEnum` | `DataUseModifierEnum` | NRES, NPO, NCU, NMDS, RS (DUO) | — |
| `TherapeuticActionabilityEnum` | same name | ACTIONABLE, NOT_ACTIONABLE (NCIT) | — |
| `KaryotypicSexEnum` | same name | XX, XY, X0, XXY, XXX, XXXY, XXXX, XYY (NCIT) | XXYY: `NCIT:C89801` is "XXYY Syndrome", a disease |
| `EducationalAttainmentEnum` | same name | two high-school levels (NCIT) | degree levels: the NCIT terms are specific degrees ("Bachelor of Arts", "Master of Science", "Doctor of Philosophy") |
| `InterpretationProgressStatusEnum` | `InterpretationProgressEnum` | none | SOLVED is "Molecular Diagnosis", UNSOLVED "Clinical Interpretation", COMPLETED "Procedure Completed" |

A draft issue reporting the rejected mappings is in
[upstream/linkml-valuesets-meanings.md](upstream/linkml-valuesets-meanings.md).

## BioPortal

[BioPortal](https://bioportal.bioontology.org) hosts SNOMED CT,
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

**Key handling.** The checker sends `BIOPORTAL_API_KEY` as the `apikey` query
parameter rather than the `Authorization` header. A Claude Code cloud
session's proxy replaces any `Authorization` header with its saved network
secret, so a header sent by the script would be overwritten if that secret is
wrong. The query parameter is not touched.

BioPortal's `/ontologies/{acronym}/classes/{iri}` endpoint returns 404 for
SNOMED CT classes that exist, so the checker uses the search endpoint with
`require_exact_match` and keeps the hit whose IRI is the code's own.

CVX is not in BioPortal and has no lookup service, so CVX codes are always
reported as `UNCHECKED`.

**Result of the first full check (2026-11-18):** of the 69 SNOMED CT and
LOINC codes copied from RareLink 2.0.7 into the schema's `exact_mappings`, 67
resolved in BioPortal. One, `SNOMEDCT:184115007` (used for "sex unknown"), is
not in the SNOMED CT US edition BioPortal serves, so it was removed from
`SexEnum` and `SexAtBirthEnum` and a comment records why. Re-run with:

```bash
uv run python scripts/check_codes.py --schema-mappings src/rapid_registry_schema/schema/rapid_registry.yaml
```

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
