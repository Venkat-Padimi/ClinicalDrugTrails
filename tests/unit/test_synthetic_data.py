"""Unit tests for synthetic data generation and disk persistence."""

import pytest
import os
import shutil
import tempfile
from src.providers.synthetic_data_generator import SyntheticDataGenerator, SyntheticDataProvider

def test_synthetic_data_generator_determinism():
    gen1 = SyntheticDataGenerator(seed=123)
    trials1 = gen1.generate_trials()
    patients1 = gen1.generate_patients(count=20)

    gen2 = SyntheticDataGenerator(seed=123)
    trials2 = gen2.generate_trials()
    patients2 = gen2.generate_patients(count=20)

    assert len(trials1) == len(trials2)
    assert len(patients1) == len(patients2)
    assert patients1[0].synthetic_patient_id == patients2[0].synthetic_patient_id
    assert patients1[0].age == patients2[0].age
    assert patients1[0].lab_values == patients2[0].lab_values

def test_synthetic_data_provider_disk_fixtures():
    temp_dir = tempfile.mkdtemp()
    try:
        provider = SyntheticDataProvider(data_dir=temp_dir, seed=999)
        trials = provider.get_trials()
        sites = provider.get_sites()
        patients = provider.get_patients()
        deviations = provider.get_deviations()

        assert len(trials) >= 3
        assert len(sites) >= 10
        assert len(patients) >= 100
        assert len(deviations) >= 10

        assert os.path.exists(os.path.join(temp_dir, "trials.json"))
        assert os.path.exists(os.path.join(temp_dir, "sites.json"))
        assert os.path.exists(os.path.join(temp_dir, "patients.json"))
        assert os.path.exists(os.path.join(temp_dir, "deviations.json"))

        for p in patients:
            assert p.is_synthetic is True
        for s in sites:
            assert s.is_synthetic is True
        for d in deviations:
            assert d.is_synthetic is True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
