# Draft issue for linkml/valuesets: meanings that name a different concept

*To be filed at https://github.com/linkml/valuesets/issues. Checked against
valuesets 0.4.2 (PyPI) and NCIT labels from the EBI Ontology Lookup Service on
2026-11-18.*

---

**Title:** Some `meaning` mappings name a different concept from the value

While reusing value sets in a rare disease registry schema we checked each
`meaning` against the label of the term it points to. These point to a
related but different concept:

| Enum | Value | `meaning` | Label of that term | Problem |
|---|---|---|---|---|
| `KaryotypicSexEnum` | `XXYY` | `NCIT:C89801` | XXYY Syndrome | A disease, not a karyotype. The other values use karyotype terms (e.g. `NCIT:C176784` 47,XXY Karyotype). |
| `InterpretationProgressEnum` | `SOLVED` | `NCIT:C20826` | Molecular Diagnosis | Not a progress status. |
| `InterpretationProgressEnum` | `UNSOLVED` | `NCIT:C125009` | Clinical Interpretation | Not a progress status; also not "unsolved". |
| `InterpretationProgressEnum` | `COMPLETED` | `NCIT:C216251` | Procedure Completed | A procedure status, not an interpretation status. |
| `InterpretationProgressEnum` | `IN_PROGRESS` | `NCIT:C25630` | Progress | Generic. |
| `EducationalAttainmentEnum` | `ASSOCIATE_DEGREE` | `NCIT:C71344` | Associate of Science | One specific associate degree. |
| `EducationalAttainmentEnum` | `BACHELORS_DEGREE` | `NCIT:C71345` | Bachelor of Arts | One specific bachelor's degree. |
| `EducationalAttainmentEnum` | `MASTERS_DEGREE` | `NCIT:C39452` | Master of Science | One specific master's degree. |
| `EducationalAttainmentEnum` | `DOCTORAL_DEGREE` | `NCIT:C39387` | Doctor of Philosophy | Excludes professional doctorates. |

Suggested fix: remove these meanings (an absent meaning is better than one
that names another concept), or replace them with terms for the level or
status itself where NCIT has one.

---
