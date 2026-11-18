# Alignment with RareLink and the RD-CDM

## What they are

**RD-CDM**, the ontology-based Rare Disease Common Data Model, is a list of
79 data elements (version 2.1.0) for rare disease registries. Each element
has a code (SNOMED CT, LOINC, HPO, NCIT, or an HL7 FHIR or GA4GH element
name), a value set, and its location in FHIR R4 and in the GA4GH Phenopacket
Schema v2. It is published as a LinkML instance file in the
[`rd-cdm`](https://github.com/BIH-CEI/rd-cdm) package and was described in
*Scientific Data* (2025).

**RareLink** implements the RD-CDM as REDCap instruments, with a LinkML
schema of the same sections, and exports REDCap records to HL7 FHIR
(International Patient Summary and Genomics Reporting profiles) and to GA4GH
Phenopackets. It is described in *npj Genomic Medicine*
([doi:10.1038/s41525-025-00534-z](https://www.nature.com/articles/s41525-025-00534-z);
preprint on [medRxiv](https://www.medrxiv.org/content/10.1101/2025.05.09.25327342)).
Code: <https://github.com/BIH-CEI/RareLink>; documentation:
<https://rarelink.readthedocs.io>.

This alignment was made against `rd-cdm` 2.1.0 and `rarelink` 2.0.7, read
from their PyPI releases.

## How RAPID relates to them

They do different jobs. RD-CDM says which facts a rare disease registry
should record about one patient. The RAPID schema describes the data RAPID
aggregates from several registry platforms, which includes RD-CDM's facts
but also surveys, wearables, files, EEGs, media, biospecimens and care teams,
and records where each fact came from.

So RAPID does not adopt RareLink's structure (one REDCap record per patient,
data elements named after their codes, such as `loinc_53034_5`). It keeps the
BDCHM-style separate records, and instead makes sure **every RD-CDM element
has a home** in the RAPID schema. That means a RareLink registry can be
loaded into RAPID without losing anything, and a RAPID record can be exported
to RD-CDM.

The element-by-element crosswalk is
[`mappings/rd_cdm_to_rapid.sssom.tsv`](../mappings/rd_cdm_to_rapid.sssom.tsv),
in SSSOM format: each RD-CDM element (`rdcdm:6.1.11`), its code, the RAPID
`Class.slot` that holds it, and whether the match is exact or close.
`tests/test_rd_cdm_crosswalk.py` checks that all 79 elements are mapped
exactly once and that every target slot exists.

## What was added to RAPID for RD-CDM

| RD-CDM section | Added to RAPID |
|---|---|
| 2 Personal information | `Person.date_of_birth` (YYYY, YYYY-MM or YYYY-MM-DD); `Demography.sex_at_birth`, `karyotypic_sex`, `gender_identity`, `country_of_birth` |
| 3 Patient status | `Person.gestational_age_at_birth`; `Participant.age_category`, `undiagnosed_rare_disease` |
| 4 Care pathway | `Encounter.encounter_status`; a rare disease specialist centre value in `EncounterClassEnum` |
| 5 Disease | `Diagnosis.diagnosis_status` is now the FHIR verification status; `equivalent_codings` for Orphanet/OMIM/ICD; `onset_date`, `diagnosis_date` |
| 6.1 Genetic findings | `GeneticTest.interpretation_progress`, `structural_variant_method`; `GeneticFinding.variant_description`, `interpretation_status`, `therapeutic_actionability`, `acmg_evidence_level`; more genomic source classes |
| 6.2 Phenotypic features | HPO-bound `severity`, `temporal_pattern`, `modifiers`; ECO `evidence`; `causal_organism`; `age_at_resolution` |
| 6.4 Family history | `FamilyHistory` class for relatives who are not enrolled; `Family.consanguinity`; `Participant.relationship_to_proband` |
| 7 Consent | `policy_references`, `contact_for_research`, `data_reuse`, `biospecimen_available`, `biobank_link` |
| 8 Disability | `DisabilityAssessment` with ICF codes |

## Where RAPID and RD-CDM code things differently

These are deliberate, and each is recorded as `skos:closeMatch` in the
crosswalk.

| Element | RD-CDM | RAPID | Why |
|---|---|---|---|
| Sex, vital status, severity | SNOMED CT | OMOP concepts (from BDCHM), with RareLink's SNOMED CT codes as `exact_mappings` | Shared codes with BDCHM; the mappings make conversion mechanical |
| Zygosity | LOINC answer codes | GENO | GENO is an OBO ontology the term validator can check |
| DNA change type | LOINC answer codes | Sequence Ontology | as above |
| Body site | SNOMED CT body structure | UBERON | as above |
| Units | Units of Measurement Ontology (UO) | UCUM codes | UCUM is what labs and FHIR use |
| Times | dates | age in days, with optional dates | BDCHM convention; registries often share only offsets |

Where RAPID enumerations correspond to RD-CDM value sets, the RAPID value
carries the RareLink code in `exact_mappings` (for example `ACMGClassificationEnum.PATHOGENIC`
→ `LOINC:LA6668-3`). These codes were copied from RareLink's schema and then
checked in BioPortal: 67 of 69 resolve, and the one SNOMED CT code that does
not (`SNOMEDCT:184115007`, "sex unknown", used twice) was removed; see
[terminology.md](terminology.md#bioportal).

## What RAPID covers that RD-CDM does not

Instruments and custom surveys, diaries, journals, digital health
technologies, EEG/EKG/ERG recordings, media files, documents, genomic data
files, biospecimen details, care teams, addresses, medications, allergies,
immunizations, and per-record data provenance. These come from the RAPID TA1
data inventory.

## Decisions

- **Sex.** RAPID keeps both BDCHM's administrative `sex` (OMOP) and RD-CDM's
  `sex_at_birth` (SNOMED CT). A registry fills whichever it collects.
- **Vital status.** `VitalStatusEnum` adds RD-CDM's `LOST_TO_FOLLOW_UP` and
  `OPTED_OUT`, which BDCHM's OMOP value set lacks. RareLink's SNOMED CT code
  for "lost to follow-up" (`SNOMEDCT:399307001`) checks out; its code for
  "opted out" (`SNOMEDCT:185924006`) is not in SNOMED CT, so that value has no
  mapping.
- **Export.** A RAPID → RD-CDM/RareLink export, so RAPID data can use
  RareLink's FHIR and Phenopackets converters, is a planned follow-up. The
  crosswalk already defines the mapping it would implement.
