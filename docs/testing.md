# Testing Strategy & Verification Report

## Automated Test Coverage

The platform contains a test suite built using **pytest**, verifying deterministic reproducibility, model validation, edge-case criteria parsing, risk calculations, human-in-the-loop workflows, and export formats.

---

## Test Inventory

| Test Module | Coverage Scope | Status |
| :--- | :--- | :--- |
| `tests/unit/test_models.py` | Pydantic domain models, serialization, synthetic labeling | ✅ Passed (5/5) |
| `tests/unit/test_synthetic_data.py` | Random seed determinism, disk fixture creation | ✅ Passed (2/2) |
| `tests/unit/test_eligibility.py` | Inclusion/exclusion evaluation, operators, missing data triggers | ✅ Passed (4/4) |
| `tests/unit/test_screening.py` | Population screening, site & regional cohort breakdowns | ✅ Passed (1/1) |
| `tests/unit/test_screening_audit.py`| Patient audit across 6 clinical edge cases & explanations | ✅ Passed (6/6) |
| `tests/unit/test_site_intelligence.py`| Operational metrics, velocity & experience scoring | ✅ Passed (1/1) |
| `tests/unit/test_recruitment_forecast.py`| Multi-scenario projections (P10, P50, P90), friction impact | ✅ Passed (2/2) |
| `tests/unit/test_recruitment_audit.py`| Extreme rate boundary tests & division-by-zero prevention | ✅ Passed (4/4) |
| `tests/unit/test_protocol_deviations.py`| Severity scoring, outlier detection, facts vs interpretations | ✅ Passed (3/3) |
| `tests/unit/test_protocol_deviations_audit.py`| Comprehensive site deviation profiles & backlog detection | ✅ Passed (1/1) |
| `tests/unit/test_risk.py` | Multi-dimensional weighting, formula disclosures | ✅ Passed (2/2) |
| `tests/unit/test_site_ranking.py` | MCDA priority ranking, confidence, strengths/weaknesses | ✅ Passed (1/1) |
| `tests/unit/test_site_ranking_audit.py`| Exact mathematical verification of ranking formula & rationale | ✅ Passed (1/1) |
| `tests/unit/test_human_review.py` | APPROVE, MODIFY, REJECT, REQUEST_MORE_EVIDENCE transitions | ✅ Passed (3/3) |
| `tests/unit/test_audit.py` | Immutable audit logging, latency tracking, provenance & errors | ✅ Passed (2/2) |
| `tests/unit/test_reporting.py` | Markdown report generation, JSON schema validation, CSVs | ✅ Passed (3/3) |
| `tests/unit/test_workflow.py` | Multi-agent LangGraph execution, state transitions | ✅ Passed (1/1) |
| `tests/integration/test_end_to_end.py`| Full pipeline execution across all 11 agent nodes to export | ✅ Passed (1/1) |
| **Total Automated Tests** | **Comprehensive Unit & Integration Test Suite** | **✅ 43 / 43 Passed** |

---

## Running the Automated Test Suite

To run all automated tests:

```bash
python -m pytest tests/
```

To run with verbose output and timing:

```bash
python -m pytest -v --durations=10 tests/
```
