# Synthetic Data Dictionary

All fields and records described herein are purely synthetic demonstration models.

---

## 1. `Trial`
| Field | Type | Description |
| :--- | :--- | :--- |
| `trial_id` | `str` | Unique trial identifier (e.g. `TRIAL-ONC-001`) |
| `trial_name` | `str` | Full protocol title |
| `therapeutic_area` | `str` | Oncology, Cardiology, Immunology, Neurology |
| `phase` | `str` | Development phase (Phase IIb, Phase III) |
| `target_population`| `str` | Target disease and stage description |
| `target_enrollment`| `int` | Required evaluable patient count |
| `enrollment_deadline`| `str` | Target completion date (YYYY-MM-DD) |
| `inclusion_criteria` | `List[EligibilityCriterion]` | Mandatory inclusion requirements |
| `exclusion_criteria` | `List[EligibilityCriterion]` | Disqualifying exclusion requirements |

---

## 2. `Patient`
| Field | Type | Description |
| :--- | :--- | :--- |
| `synthetic_patient_id` | `str` | Unique synthetic identifier (e.g. `SYN-PT-0001`) |
| `age` | `int` | Age at screening (years) |
| `sex` | `str` | Male, Female |
| `region` | `str` | Geographic region (Midwest, Northeast, etc.) |
| `relevant_conditions` | `List[str]` | Documented primary conditions |
| `disease_stage` | `str` | Clinical stage (Stage IIIB, Stage IV, etc.) |
| `biomarkers` | `Dict[str, Any]` | Biomarkers (EGFR, PD-L1, KRAS, HER2) |
| `medications` | `List[str]` | Concurrent medications |
| `lab_values` | `Dict[str, float]` | Chemistry and hematology (eGFR, platelets, ALT, etc.) |
| `prior_treatment` | `List[str]` | Prior therapies |
| `comorbidities` | `List[str]` | Active comorbidities |
| `consent_status` | `bool` | Informed consent signature status |

---

## 3. `TrialSite`
| Field | Type | Description |
| :--- | :--- | :--- |
| `site_id` | `str` | Unique site code (e.g. `SITE-101`) |
| `site_name` | `str` | Institution name |
| `therapeutic_area_experience_years` | `float` | Investigator team experience in disease area |
| `investigator_experience_years` | `float` | Principal Investigator career experience |
| `historical_trials_completed` | `int` | Prior clinical trials completed |
| `average_monthly_enrollment` | `float` | Historical recruitment velocity |
| `screen_failure_rate` | `float` | Proportion of screened patients failing eligibility |
| `dropout_rate` | `float` | Proportion of enrolled patients withdrawing early |
| `protocol_deviation_rate` | `float` | Deviations per 10 enrolled subjects |
| `data_query_rate` | `float` | Electronic data queries per CRF |
| `activation_time_days` | `int` | Days from site selection to first patient in |
| `staff_capacity` | `int` | Number of certified study coordinators |
| `patient_pool_estimate` | `int` | Estimated local patient catchment |

---

## 4. `ProtocolDeviation`
| Field | Type | Description |
| :--- | :--- | :--- |
| `deviation_id` | `str` | Deviation identifier (e.g. `DEV-001`) |
| `site_id` | `str` | Associated trial site |
| `category` | `DeviationCategory` | Consent, Drug Accountability, Visit Window, Lab, etc. |
| `severity` | `DeviationSeverity` | LOW, MEDIUM, HIGH, CRITICAL |
| `occurrence_date` | `str` | Date of incident (YYYY-MM-DD) |
| `resolved` | `bool` | Corrective action completed status |
| `recurrence` | `bool` | Indicates recurring operational issue |
