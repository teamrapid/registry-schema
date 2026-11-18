# Governance metadata

RAPID data move between organizations under the RAPID Associate Performer
Agreement (APA). The APA requires a **Data Inventory** entry before any
dataset is transferred, tracks consent centrally, and links participants
across contributors with a pseudonymous program-wide identifier. This page
describes how the schema carries that information. The APA itself is not in
this repository; the fields below follow its Data Inventory minimum fields
(Annex B) and its consent and linkage provisions.

## Dataset level: `DataInventoryEntry`

Every `RegistryDataset` (one delivered batch) can carry an `inventory_entry`.
It describes the dataset, never a participant.

| Data Inventory field | Schema slot(s) |
|---|---|
| Contribution and source | `id`, `description`, `data_contributor`, `provenance`, `data_type_category`, `version`, `persistent_identifier` |
| Permitted access and use | `permitted_recipients`, `permitted_uses` (DUO), `permitted_uses_description` |
| Access mode and safeguards | `access_mode`, `safeguards` |
| Regulatory status | `hipaa_status` (not PHI / identifiable / limited data set / de-identified), `deidentification_method` (Safe Harbor / Expert Determination), `contains_non_us_data`, `contains_bulk_sensitive_personal_data` |
| Restrictions | `restrictions`, `retention_period` |
| Governing instruments | `governing_instruments` (type + reference: DUA, DTA, ISA, licence, consent, IRB, source terms) |
| Access approval | `access_approval_contact` |
| Inventory maintenance | `inventory_maintenance_contact` |
| Participant recontact | `recontact` (originating organization, authorized pathway, consent restrictions, coordination contact) |
| Data return and attribution | `data_return` (contributing organization, authorized outputs, delivery mechanism, frequency, attribution) |
| Combined-data privacy review | `privacy_risk_assessment` |

`data_type_category` uses the data types the APA's data rights table assigns
rights to: tokenized, structured, harmonized, de-identified linked, and
versioned datasets.

Contacts are recorded as a role and an organization (`ContactRole`), with an
optional functional mailbox, rather than as named people. Governing
instruments are referenced by identifier; their text does not belong in the
data.

## Participant level

- **`Person.mspi`** holds the Master Study Patient Index, the program-wide
  pseudonymous identifier minted by the Linkage Honest Broker. Linkage
  tokens themselves are never stored in this model: the APA keeps them with
  the Linkage Honest Broker, separate from clinical data.
- **`Consent`** carries what the Consent Steward communicates downstream:
  `consent_status` (including `SUPERSEDED` for re-consent and `WITHDRAWN`),
  `consent_version`, effective dates (`valid_from`, `valid_to`),
  `withdrawal_date`, `consent_steward`, `recontact_permitted` and
  `recontact_pathway`, `linkage_permitted`, and DUO `data_use_permission`.
  Assent and legally authorized representative consent are `consent_type`
  values. Full consent documents are optional (`consent_document`) because
  the APA exchanges them only when authorized and necessary.
- **`DataFile.deidentification_status`** gives the HIPAA status of an
  individual file, and **`MediaFile.retained_at_source`** marks inherently
  identifiable media (faces, voice, video) that stays with the contributor
  while only its metadata is shared.

## Not modelled

- Linkage tokens and crosswalks (held by the Linkage Honest Broker).
- Access logs, incident reports and the change-notification workflow; these
  are operational records, not registry data.
- The rights terms of the data rights table, which are contractual and
  differ by party.
