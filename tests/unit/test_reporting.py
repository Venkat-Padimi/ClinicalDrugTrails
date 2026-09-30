"""Unit tests for ExecutiveReportGenerator."""

import pytest
import json
import csv
import io
from src.providers.synthetic_data_generator import SyntheticDataGenerator
from src.workflow.orchestrator import TrialWorkflowOrchestrator
from src.reporting.report_generator import ExecutiveReportGenerator

@pytest.fixture
def sample_analysis():
    gen = SyntheticDataGenerator(seed=42)
    trial = gen.generate_trials()[0]
    sites = gen.generate_sites()[:4]
    patients = gen.generate_patients(count=30, sites=sites)
    deviations = gen.generate_deviations(sites=sites, count=10)

    orchestrator = TrialWorkflowOrchestrator()
    return orchestrator.run(trial, patients, sites, deviations)

def test_markdown_report_generation(sample_analysis):
    generator = ExecutiveReportGenerator()
    md = generator.generate_markdown_report(sample_analysis)

    assert "MANDATORY SAFETY DISCLAIMER" in md
    assert "Synthetic demonstration data" in md
    assert sample_analysis.trial.trial_name in md
    assert "Executive Summary" in md
    assert "Candidate Trial Site Prioritization & Ranking" in md
    assert "Protocol Deviation & Compliance Monitoring" in md
    assert "Limitations & Scope of Demonstration" in md

def test_json_report_generation(sample_analysis):
    generator = ExecutiveReportGenerator()
    json_str = generator.generate_json_report(sample_analysis)

    parsed = json.loads(json_str)
    assert parsed["trial"]["trial_id"] == sample_analysis.trial.trial_id
    assert parsed["is_synthetic"] is True
    assert len(parsed["site_rankings"]) == 4

def test_csv_exports(sample_analysis):
    generator = ExecutiveReportGenerator()

    # Patients CSV
    pt_csv = generator.generate_patients_csv(sample_analysis)
    reader = csv.reader(io.StringIO(pt_csv))
    rows = list(reader)
    assert len(rows) == 31  # Header + 30 patients
    assert rows[0][0] == "patient_id"

    # Sites CSV
    site_csv = generator.generate_sites_csv(sample_analysis)
    reader = csv.reader(io.StringIO(site_csv))
    rows = list(reader)
    assert len(rows) == 5  # Header + 4 sites
    assert rows[0][0] == "rank"

    # Deviations CSV
    dev_csv = generator.generate_deviations_csv(sample_analysis)
    reader = csv.reader(io.StringIO(dev_csv))
    rows = list(reader)
    assert len(rows) == 11  # Header + 10 deviations
    assert rows[0][0] == "deviation_id"
