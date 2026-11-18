# RAPID Registry Schema

A [LinkML](https://linkml.io) data model for the rare disease patient-registry
data aggregated under RAPID Technical Area 1. It is built from the data
inventory in [`RAPID_TA1_Registries_Data_Inventory.xlsx`](RAPID_TA1_Registries_Data_Inventory.xlsx)
and modelled on two existing LinkML models:

- the [BioData Catalyst Harmonized Model](https://rtiinternational.github.io/NHLBI-BDC-DMC-HM/)
  (BDCHM), and
- the [LinkML Core Model for Clinical Data Collection](https://linkml.io/cmdr) (CMDR).

It is also aligned element by element with the rare disease common data model
([RD-CDM](https://github.com/BIH-CEI/rd-cdm)) used by
[RareLink](https://github.com/BIH-CEI/RareLink); see
[docs/rarelink-alignment.md](docs/rarelink-alignment.md).

## Documentation

- [docs/terminology.md](docs/terminology.md) — which vocabulary each value
  uses, how codes are checked, and setting up BioPortal.
- [docs/rarelink-alignment.md](docs/rarelink-alignment.md) — how the schema
  relates to RareLink and RD-CDM, and the crosswalk in
  [`mappings/rd_cdm_to_rapid.sssom.tsv`](mappings/rd_cdm_to_rapid.sssom.tsv).

The schema is [`src/rapid_registry_schema/schema/rapid_registry.yaml`](src/rapid_registry_schema/schema/rapid_registry.yaml).

## Status

Draft, version 0.1.0, for review by the RAPID TA1 teams. The schema `id`
(`https://w3id.org/rapid/registry-schema`) is a placeholder: no w3id redirect
has been registered yet.

## What comes from where

| Pattern | Taken from |
|---|---|
| `Person` (the individual) / `Participant` (their enrolment in one registry) / `Demography` split | BDCHM |
| `Condition`, `Procedure`, `DrugExposure`, `Observation`, `MeasurementObservation`, `Encounter` (BDCHM `Visit`), `Questionnaire*`, `Specimen`, `DataFile` (BDCHM `File`) | BDCHM |
| Timing as age in days since birth (`age_at_*`, UCUM `d`) | BDCHM |
| OMOP-coded sex, race, ethnicity, vital status, severity, family relationship and route value sets | BDCHM (copied, so data harmonised to either model shares codes) |
| DUO data-use permissions on `Consent` | BDCHM |
| `Family` with `members`, `probands` and pairwise `FamilyRelationship` | CMDR |
| `Entity` base, `Organization` | CMDR / BDCHM |

Every class carries `exact_mappings` / `close_mappings` to its BDCHM and CMDR
counterpart, and a `class_uri` or mapping to the corresponding HL7 FHIR
resource and OMOP CDM table where one exists.

Added for RAPID:

- **Provenance on every participant record.** `data_provenance`
  (self-reported, manually entered health information, abstracted EHR, raw
  EHR, curator-abstracted, device-generated…) and `reported_by_role`
  (patient, caregiver, parent, guardian, clinician, researcher, curator,
  third-party observer). The inventory shows the same data type arriving by
  several routes, so this is per record rather than per table.
- **`source_codings`** keeps the code exactly as the source system sent it
  (ICD-10-CM, SNOMED CT, local codes) next to the harmonised concept.
- **Rare disease specifics:** `Diagnosis` (status including `UNDIAGNOSED`,
  basis, confirming genetic test), `PhenotypicFeature` (HPO, with onset and
  exclusion), `GeneticTest` / `GeneticFinding` (HGVS, zygosity, allele origin,
  ACMG class), `GenomicDataFile` (BAM/CRAM/VCF with the phenotypes recorded at
  sequencing). These follow the GA4GH Phenopackets elements of the same names.
- Classes for the inventory rows neither reference model covers: diaries,
  journals, digital health technologies, EEG/EKG/ERG recordings, media
  (images, video, voice) and care teams.

## Semantic bindings

Coded values are `Concept` objects (`{id, label}`). Which vocabulary a slot
accepts is enforced in one of two ways:

| Vocabulary | Used for | Enforced by |
|---|---|---|
| MONDO (under `MONDO:0700096` human disease) | diagnoses, disease focus, consent disease restriction, care-team qualification | `bindings` → linkml-term-validator |
| HPO (under `HP:0000118`; onset under `HP:0003674`) | phenotypic features, conditions, onset | `bindings` → linkml-term-validator |
| UBERON (under `UBERON:0001062`) | body sites | `bindings` → linkml-term-validator |
| SO (under `SO:0001060`), GENO (under `GENO:0000133`) | variant type, zygosity | `bindings` → linkml-term-validator |
| LOINC | labs, vital signs, device measures, instrument panels, question codes | `LoincConcept` id pattern |
| RxNorm | medications and supplements | `RxNormConcept` id pattern |
| SNOMED CT | procedures, diary symptoms, allergens | `SnomedCtConcept` / `SymptomConcept` / `SubstanceConcept` id pattern |
| CVX | vaccines | `CvxConcept` id pattern |
| HGNC | genes | `HgncGeneConcept` id pattern |
| UCUM | units | `UcumUnitConcept` id pattern |

LOINC, RxNorm, SNOMED CT, CVX, HGNC and UCUM are not OBO ontologies, so the
term validator cannot look them up. The schema's id patterns reject codes from
the wrong vocabulary, and `scripts/check_codes.py` looks each code up (NLM
Clinical Tables, RxNav, genenames.org, and BioPortal for SNOMED CT, OMIM,
ICD-10-CM and LOINC answer codes)
and compares its label. Details in [docs/terminology.md](docs/terminology.md).

Static enumerations bind their values with `meaning`: DUO for data use, NCIT
for reporter roles, consent types, genetic test types, ACMG classes and signal
modalities, EDAM for file formats, OMOP for the value sets copied from BDCHM.
Every `meaning` was checked against the ontology when written, and
`linkml-term-validator validate-schema` re-checks the NCIT and DUO ones.

## Inventory row → schema class

| Inventory data type | Class |
|---|---|
| Standard Instruments | `Questionnaire` (`instrument_type: STANDARD_INSTRUMENT`, LOINC panel), `QuestionnaireResponse` |
| Custom Surveys/Forms | `Questionnaire` (`CUSTOM_SURVEY_FORM`), `QuestionnaireResponse` |
| Health Information | `Condition`, `DrugExposure`, `Procedure`, `AllergyIntolerance`, `Immunization`, `MeasurementObservation`, `Encounter` with `data_provenance: MANUALLY_ENTERED_HEALTH_INFORMATION` |
| Abstracted EHR | the same classes with `data_provenance: EHR_ABSTRACTED` |
| Raw EHR (FHIR/C-CDA) | `DocumentFile` (`file_format: FHIR_JSON` or `CCDA`, `data_category: RAW_EHR`) |
| Digital Health Technologies | `Device`, `DeviceObservationSeries` |
| Genetic Test (Curated) | `GeneticTest` with `findings`, `is_curated: true` |
| Genetic Test (Raw) | `DocumentFile` (PDF), linked as `GeneticTest.report_file` |
| General Information (Demographics +) | `Demography` (income, education and insurance optional) |
| Diary (Symptoms/Activities) | `DiaryEntry` (SNOMED CT or HPO) |
| EEG, EKG, Retinal ERG | `PhysiologicalSignalRecording` |
| Documents/Files | `DocumentFile` |
| Consent | `Consent` (+ signed form as `DocumentFile`) |
| Biospecimen / Biobank Information | `Specimen` |
| Pedigree | `Family`, `FamilyRelationship` (enrolled relatives), `FamilyHistory` (relatives who are not enrolled) |
| Journal | `JournalEntry` (+ source audio as `MediaFile`) |
| Care Team | `CareTeam`, `CareTeamMember`, `Organization` |
| Genomic (BAM/VCF) | `GenomicDataFile` |
| Mortality | `Death`, `Person.vital_status` |
| Address | `Address` (country + 3-digit ZIP) |
| Diagnosis | `Diagnosis` |
| Medications/Treatments | `DrugExposure` (RxNorm) |
| Voice, Images, Video | `MediaFile` |
| *(RD-CDM section 8)* Disability | `DisabilityAssessment` (ICF codes) |

## Open questions from the inventory

- **Voice, Images, Video, EKG, Retinal ERG** have no registry listed yet.
- **Genomic** standards are marked "?"; the schema assumes BAM/CRAM/VCF with a
  stated reference genome.
- **Medications** are marked "RxNorm?"; the schema requires RxNorm for the
  harmonised code and keeps the patient's own wording in
  `drug_name_as_reported`.
- **Mortality**: whether cause of death is captured varies, so
  `cause_of_death_known` records that explicitly.
- **General Information**: the socioeconomic fields are free text until the
  registries agree on bands.

## Using it

```bash
uv sync
```

Validate a data file's structure:

```bash
uv run linkml-validate -s src/rapid_registry_schema/schema/rapid_registry.yaml -C RegistryDataset examples/valid/RegistryDataset-rett-example.yaml
```

Validate its ontology bindings (queries the EBI Ontology Lookup Service):

```bash
uv run linkml-term-validator validate-data examples/valid/RegistryDataset-rett-example.yaml -s src/rapid_registry_schema/schema/rapid_registry.yaml -t RegistryDataset -c conf/oak_config.yaml
```

Check LOINC, RxNorm, HGNC, UCUM and SNOMED CT codes against their sources
(SNOMED CT needs a BioPortal key in `BIOPORTAL_API_KEY`; see docs/terminology.md):

```bash
uv run python scripts/check_codes.py examples/valid/RegistryDataset-rett-example.yaml
```

Run the tests (add `-m "not network"` to skip the ones that call OLS and the
code lookup services):

```bash
uv run pytest
```

Generate other representations, e.g. JSON Schema, Pydantic or OWL:

```bash
uv run gen-json-schema src/rapid_registry_schema/schema/rapid_registry.yaml > rapid_registry.schema.json
```

## Examples

- `examples/valid/` — a synthetic Rett syndrome participant covering
  demographics, consent, family, diagnosis, phenotypes, medication, a vital
  sign, a curated genetic test with its raw report, and an EEG.
- `examples/invalid/` — files that fail structural validation.
- `examples/invalid_terms/` — files that pass structural validation but fail
  the ontology bindings.

## License

MIT
