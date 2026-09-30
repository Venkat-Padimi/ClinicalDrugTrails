"""Unit tests for PatientScreeningAgent."""

import pytest
from src.providers.synthetic_data_generator import SyntheticDataGenerator
from src.agents.patient_screening_agent import PatientScreeningAgent
from src.domain.models import EligibilityStatus

def test_patient_screening_agent_cohort():
    gen = SyntheticDataGenerator(seed=42)
    trials = gen.generate_trials()
    onc_trial = trials[0]
    sites = gen.generate_sites()
    patients = gen.generate_patients(count=50, sites=sites)

    agent = PatientScreeningAgent()
    results, summary = agent.screen_cohort(onc_trial, patients)

    assert len(results) == 50
    assert summary.total_screened == 50
    assert summary.eligible_count + summary.ineligible_count + summary.uncertain_count == 50
    assert 0.0 <= summary.eligibility_rate <= 1.0
    assert summary.is_synthetic is True

    # Test site breakdown
    site_breakdown = agent.get_candidate_breakdown_by_site(patients, results)
    assert len(site_breakdown) > 0
    total_in_sites = sum(data["total"] for data in site_breakdown.values())
    assert total_in_sites == 50

    # Test geo breakdown
    geo_breakdown = agent.get_geographic_distribution(patients, results)
    assert len(geo_breakdown) > 0
    total_geo = sum(data["screened"] for data in geo_breakdown.values())
    assert total_geo == 50
