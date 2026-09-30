"""Synthetic data generator and fixtures provider.

Generates realistic clinical trials, candidate sites, patient populations,
and protocol deviation logs. All generated data is purely synthetic.
"""

import json
import os
import random
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

from src.domain.models import (
    Trial,
    Patient,
    TrialSite,
    ProtocolDeviation,
    EligibilityCriterion,
    CriterionType,
    CriterionCategory,
    DeviationSeverity,
    DeviationCategory,
)
from src.config import config


class SyntheticDataGenerator:
    """Deterministic generator for synthetic clinical trials and cohorts."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_trials(self) -> List[Trial]:
        """Generates representative clinical trial protocols across key therapeutic areas."""
        trials = [
            Trial(
                trial_id="TRIAL-ONC-001",
                trial_name="LUNG-ADVANCE: Phase III Trial in Metastatic Non-Small Cell Lung Cancer (NSCLC)",
                therapeutic_area="Oncology",
                phase="Phase III",
                target_population="Adults with Stage IIIB/IV EGFR-mutated non-small cell lung cancer",
                target_enrollment=120,
                enrollment_deadline="2027-06-30",
                protocol_version="v2.1",
                inclusion_criteria=[
                    EligibilityCriterion(
                        criterion_id="INC-AGE-01",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.AGE,
                        field_name="age",
                        operator="between",
                        target_value=[18, 80],
                        description="Age between 18 and 80 years at screening",
                    ),
                    EligibilityCriterion(
                        criterion_id="INC-STAGE-01",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.DISEASE_STAGE,
                        field_name="disease_stage",
                        operator="in",
                        target_value=["Stage IIIB", "Stage IV"],
                        description="Histologically confirmed Stage IIIB or Stage IV NSCLC",
                    ),
                    EligibilityCriterion(
                        criterion_id="INC-BIO-01",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.BIOMARKER,
                        field_name="EGFR_mutation",
                        operator="in",
                        target_value=["Exon 19 del", "L858R", "Positive"],
                        description="Documented EGFR sensitizing mutation (Exon 19 del or L858R)",
                    ),
                    EligibilityCriterion(
                        criterion_id="INC-LAB-EGFR",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.LAB_VALUE,
                        field_name="eGFR",
                        operator=">=",
                        target_value=45.0,
                        description="Adequate renal function: estimated GFR >= 45 mL/min/1.73m2",
                    ),
                    EligibilityCriterion(
                        criterion_id="INC-LAB-PLT",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.LAB_VALUE,
                        field_name="platelets",
                        operator=">=",
                        target_value=100000.0,
                        description="Adequate bone marrow function: Platelets >= 100,000 /mcL",
                    ),
                    EligibilityCriterion(
                        criterion_id="INC-LAB-ALT",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.LAB_VALUE,
                        field_name="ALT",
                        operator="<=",
                        target_value=120.0,
                        description="Adequate hepatic function: ALT <= 120 U/L (<= 3x ULN)",
                    ),
                    EligibilityCriterion(
                        criterion_id="INC-CONSENT-01",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.CONSENT,
                        field_name="consent_status",
                        operator="is_true",
                        target_value=True,
                        description="Signed written informed consent provided prior to study procedures",
                    ),
                ],
                exclusion_criteria=[
                    EligibilityCriterion(
                        criterion_id="EXC-COMORB-01",
                        criterion_type=CriterionType.EXCLUSION,
                        category=CriterionCategory.COMORBIDITY,
                        field_name="comorbidities",
                        operator="contains_any",
                        target_value=["Untreated Brain Metastases", "Interstitial Lung Disease", "Active Severe Hepatitis"],
                        description="History of untreated brain metastases, interstitial lung disease, or active viral hepatitis",
                    ),
                    EligibilityCriterion(
                        criterion_id="EXC-MED-01",
                        criterion_type=CriterionType.EXCLUSION,
                        category=CriterionCategory.MEDICATION,
                        field_name="medications",
                        operator="contains_any",
                        target_value=["Strong CYP3A4 Inducers", "Live Attenuated Vaccines"],
                        description="Concurrent therapy with potent CYP3A4 inducers or live vaccines",
                    ),
                    EligibilityCriterion(
                        criterion_id="EXC-PRIOR-01",
                        criterion_type=CriterionType.EXCLUSION,
                        category=CriterionCategory.PRIOR_TREATMENT,
                        field_name="prior_treatment",
                        operator="contains_any",
                        target_value=["Prior 3rd-Gen EGFR TKI", "Investigational ADC within 28 days"],
                        description="Prior exposure to third-generation EGFR TKI or novel ADC within 28 days",
                    ),
                ],
            ),
            Trial(
                trial_id="TRIAL-CARD-002",
                trial_name="PRESERVE-HF: Phase III Trial in Heart Failure with Preserved Ejection Fraction",
                therapeutic_area="Cardiology",
                phase="Phase III",
                target_population="Patients aged 45-85 with symptomatic HFpEF and elevated NT-proBNP",
                target_enrollment=150,
                enrollment_deadline="2027-09-30",
                protocol_version="v1.4",
                inclusion_criteria=[
                    EligibilityCriterion(
                        criterion_id="INC-CARD-AGE",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.AGE,
                        field_name="age",
                        operator="between",
                        target_value=[45, 85],
                        description="Age between 45 and 85 years",
                    ),
                    EligibilityCriterion(
                        criterion_id="INC-CARD-EF",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.LAB_VALUE,
                        field_name="ejection_fraction",
                        operator=">=",
                        target_value=50.0,
                        description="Left ventricular ejection fraction (LVEF) >= 50%",
                    ),
                    EligibilityCriterion(
                        criterion_id="INC-CARD-BNP",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.LAB_VALUE,
                        field_name="NT_proBNP",
                        operator=">=",
                        target_value=300.0,
                        description="Elevated NT-proBNP >= 300 pg/mL (or >= 600 if atrial fibrillation)",
                    ),
                    EligibilityCriterion(
                        criterion_id="INC-CARD-GFR",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.LAB_VALUE,
                        field_name="eGFR",
                        operator=">=",
                        target_value=30.0,
                        description="Renal function: eGFR >= 30 mL/min/1.73m2",
                    ),
                    EligibilityCriterion(
                        criterion_id="INC-CARD-CONSENT",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.CONSENT,
                        field_name="consent_status",
                        operator="is_true",
                        target_value=True,
                        description="Voluntary signed informed consent",
                    ),
                ],
                exclusion_criteria=[
                    EligibilityCriterion(
                        criterion_id="EXC-CARD-MI",
                        criterion_type=CriterionType.EXCLUSION,
                        category=CriterionCategory.COMORBIDITY,
                        field_name="comorbidities",
                        operator="contains_any",
                        target_value=["Acute Myocardial Infarction within 90 days", "Severe Aortic Stenosis", "End-Stage Renal Disease on Dialysis"],
                        description="Recent acute MI within 90 days, hemodynamically significant valvular stenosis, or dialysis",
                    ),
                    EligibilityCriterion(
                        criterion_id="EXC-CARD-MED",
                        criterion_type=CriterionType.EXCLUSION,
                        category=CriterionCategory.MEDICATION,
                        field_name="medications",
                        operator="contains_any",
                        target_value=["Inotropic Agents", "Investigational SGLT2 Inhibitor"],
                        description="Current IV inotropes or concurrent investigational cardioprotective therapies",
                    ),
                ],
            ),
            Trial(
                trial_id="TRIAL-IMM-003",
                trial_name="CROHN-TARGET: Phase IIb Trial in Moderate-to-Severe Active Crohn's Disease",
                therapeutic_area="Immunology",
                phase="Phase IIb",
                target_population="Adults with moderate-to-severe Crohn's disease with inadequate response to biologics",
                target_enrollment=90,
                enrollment_deadline="2027-04-15",
                protocol_version="v2.0",
                inclusion_criteria=[
                    EligibilityCriterion(
                        criterion_id="INC-IMM-AGE",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.AGE,
                        field_name="age",
                        operator="between",
                        target_value=[18, 75],
                        description="Age between 18 and 75 years",
                    ),
                    EligibilityCriterion(
                        criterion_id="INC-IMM-CRP",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.LAB_VALUE,
                        field_name="CRP",
                        operator=">=",
                        target_value=5.0,
                        description="C-reactive protein (CRP) >= 5.0 mg/L indicating active mucosal inflammation",
                    ),
                    EligibilityCriterion(
                        criterion_id="INC-IMM-PRIOR",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.PRIOR_TREATMENT,
                        field_name="prior_treatment",
                        operator="contains_any",
                        target_value=["Anti-TNF Therapy", "Corticosteroids", "Immunomodulators"],
                        description="Documented history of inadequate response, loss of response, or intolerance to prior therapy",
                    ),
                    EligibilityCriterion(
                        criterion_id="INC-IMM-CONSENT",
                        criterion_type=CriterionType.INCLUSION,
                        category=CriterionCategory.CONSENT,
                        field_name="consent_status",
                        operator="is_true",
                        target_value=True,
                        description="Signed informed consent",
                    ),
                ],
                exclusion_criteria=[
                    EligibilityCriterion(
                        criterion_id="EXC-IMM-COMORB",
                        criterion_type=CriterionType.EXCLUSION,
                        category=CriterionCategory.COMORBIDITY,
                        field_name="comorbidities",
                        operator="contains_any",
                        target_value=["Active Bowel Obstruction", "Active Tuberculosis", "Toxic Megacolon", "Active Sepsis"],
                        description="Symptomatic stricture/obstruction, active tuberculosis, toxic megacolon, or untreated systemic infection",
                    ),
                ],
            ),
        ]
        return trials

    def generate_sites(self) -> List[TrialSite]:
        """Generates realistic clinical trial sites with varied performance profiles."""
        site_templates = [
            ("SITE-101", "Midwest Academic Comprehensive Cancer Center", "Chicago", "IL", "USA", 16.0, 18.0, 42, 580, 5.2, 0.14, 0.05, 0.35, 1.1, 55, 7, 10, 520),
            ("SITE-102", "Boston Oncology & Biologics Institute", "Boston", "MA", "USA", 14.5, 15.0, 36, 490, 4.6, 0.16, 0.06, 0.40, 1.2, 60, 10, 8, 480),
            ("SITE-103", "Texas Health Sciences Trial Network", "Houston", "TX", "USA", 12.0, 14.0, 28, 410, 4.1, 0.20, 0.08, 0.60, 1.4, 68, 14, 7, 430),
            ("SITE-104", "Pacific Northwest Research Hospital", "Seattle", "WA", "USA", 10.0, 11.5, 22, 310, 3.4, 0.22, 0.09, 0.75, 1.6, 75, 15, 6, 360),
            ("SITE-105", "Southeastern Cardiovascular & Clinical Center", "Atlanta", "GA", "USA", 15.0, 16.0, 38, 520, 4.8, 0.15, 0.07, 0.45, 1.3, 62, 8, 9, 500),
            ("SITE-106", "Rocky Mountain Clinical Therapeutics", "Denver", "CO", "USA", 7.0, 8.5, 14, 180, 2.2, 0.28, 0.12, 1.10, 2.1, 92, 24, 4, 210),
            ("SITE-107", "Mid-Atlantic Community Health Alliance", "Philadelphia", "PA", "USA", 8.5, 9.0, 16, 220, 2.7, 0.26, 0.11, 0.95, 1.9, 85, 20, 5, 260),
            ("SITE-108", "Southwest Clinical Innovation Center", "Phoenix", "AZ", "USA", 5.0, 6.0, 10, 130, 1.8, 0.32, 0.15, 1.45, 2.6, 105, 30, 3, 170),
            ("SITE-109", "Great Lakes University Medical Center", "Cleveland", "OH", "USA", 13.0, 13.5, 30, 390, 3.8, 0.19, 0.07, 0.50, 1.3, 70, 12, 7, 390),
            ("SITE-110", "California Premier Clinical Consortium", "San Francisco", "CA", "USA", 15.5, 17.0, 40, 560, 5.0, 0.15, 0.06, 0.38, 1.15, 58, 9, 9, 510),
            ("SITE-111", "Sunshine State Trial Investigators", "Miami", "FL", "USA", 6.5, 7.0, 12, 160, 2.0, 0.30, 0.14, 1.30, 2.4, 98, 28, 4, 190),
            ("SITE-112", "Carolinas Integrated Health Clinical Hub", "Charlotte", "NC", "USA", 9.0, 10.0, 18, 250, 3.0, 0.24, 0.10, 0.80, 1.7, 80, 18, 5, 290),
        ]
        sites = []
        for s in site_templates:
            sites.append(
                TrialSite(
                    site_id=s[0],
                    site_name=s[1],
                    city=s[2],
                    state=s[3],
                    country=s[4],
                    therapeutic_area_experience_years=s[5],
                    investigator_experience_years=s[6],
                    historical_trials_completed=s[7],
                    historical_enrollment=s[8],
                    average_monthly_enrollment=s[9],
                    screen_failure_rate=s[10],
                    dropout_rate=s[11],
                    protocol_deviation_rate=s[12],
                    data_query_rate=s[13],
                    activation_time_days=s[14],
                    recruitment_start_delay_days=s[15],
                    staff_capacity=s[16],
                    patient_pool_estimate=s[17],
                )
            )
        return sites

    def generate_patients(self, count: int = 300, sites: List[TrialSite] = None) -> List[Patient]:
        """Generates realistic synthetic patient population."""
        if sites is None:
            sites = self.generate_sites()
        site_ids = [s.site_id for s in sites]

        regions = ["Midwest", "Northeast", "South", "West", "Mid-Atlantic", "Pacific"]
        disease_stages = ["Stage IIIA", "Stage IIIB", "Stage IV", "Stage IIB", "Stage IA"]
        egfr_variants = ["Exon 19 del", "L858R", "Positive", "Wild-Type", "T790M", "Negative"]
        prior_tx_pool = [
            "Platinum-doublet", "Carboplatin + Pemetrexed", "Radiation",
            "Anti-TNF Therapy", "Corticosteroids", "Immunomodulators",
            "Prior 3rd-Gen EGFR TKI", "ACE Inhibitor", "Beta Blocker"
        ]
        meds_pool = [
            "Amlodipine", "Metformin", "Atorvastatin", "Omeprazole", "Lisinopril",
            "Strong CYP3A4 Inducers", "Live Attenuated Vaccines", "Inotropic Agents", "Aspirin"
        ]
        comorbidities_pool = [
            "Hypertension", "Type 2 Diabetes", "Hyperlipidemia", "GERD", "Osteoarthritis",
            "Untreated Brain Metastases", "Interstitial Lung Disease",
            "Acute Myocardial Infarction within 90 days", "Active Bowel Obstruction"
        ]

        patients = []
        for i in range(1, count + 1):
            pt_id = f"SYN-PT-{i:04d}"
            age = self.rng.randint(22, 88)
            sex = self.rng.choice(["Female", "Male"])
            region = self.rng.choice(regions)
            stage = self.rng.choice(disease_stages)
            assigned_site = self.rng.choice(site_ids)

            # Biomarkers
            egfr_val = self.rng.choice(egfr_variants)
            pdl1_val = round(self.rng.uniform(0.0, 95.0), 1)
            kras_val = self.rng.choice(["G12C", "G12D", "Wild-Type", "Negative"])
            her2_val = self.rng.choice(["0", "1+", "2+", "3+"])

            # Labs: Introduce deliberate ranges and rare missing values
            include_egfr_lab = self.rng.random() > 0.05  # 5% missing to test missing-data handling
            include_alt_lab = self.rng.random() > 0.03
            include_bnp_lab = self.rng.random() > 0.08
            include_ef_lab = self.rng.random() > 0.08

            lab_vals: Dict[str, float] = {}
            if include_egfr_lab:
                lab_vals["eGFR"] = round(self.rng.gauss(65.0, 18.0), 1)
            lab_vals["platelets"] = round(max(40000.0, self.rng.gauss(190000.0, 50000.0)), 0)
            if include_alt_lab:
                lab_vals["ALT"] = round(max(10.0, self.rng.gauss(55.0, 35.0)), 1)
            lab_vals["bilirubin"] = round(max(0.2, self.rng.gauss(1.1, 0.5)), 2)
            lab_vals["CRP"] = round(max(0.5, self.rng.gauss(8.0, 6.0)), 1)
            if include_bnp_lab:
                lab_vals["NT_proBNP"] = round(max(40.0, self.rng.gauss(420.0, 250.0)), 1)
            if include_ef_lab:
                lab_vals["ejection_fraction"] = round(min(75.0, max(25.0, self.rng.gauss(54.0, 10.0))), 1)

            # Prior treatments (0 to 3)
            prior_count = self.rng.randint(0, 3)
            pt_prior = self.rng.sample(prior_tx_pool, prior_count)

            # Meds (0 to 4)
            med_count = self.rng.randint(0, 4)
            pt_meds = self.rng.sample(meds_pool, med_count)

            # Comorbidities (0 to 3)
            comorb_count = self.rng.randint(0, 3)
            pt_comorbs = self.rng.sample(comorbidities_pool, comorb_count)

            # Consent status: 96% consented, 4% refusal/missing
            consent = self.rng.random() > 0.04

            # Relevant conditions
            conditions = ["Non-Small Cell Lung Cancer"] if stage.startswith("Stage") else ["Cardiomyopathy"]
            if "Hypertension" in pt_comorbs:
                conditions.append("Hypertension")

            days_ago = self.rng.randint(1, 180)
            scr_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            patients.append(
                Patient(
                    synthetic_patient_id=pt_id,
                    age=age,
                    sex=sex,
                    region=region,
                    relevant_conditions=conditions,
                    disease_stage=stage,
                    biomarkers={
                        "EGFR_mutation": egfr_val,
                        "PD_L1": pdl1_val,
                        "KRAS": kras_val,
                        "HER2": her2_val,
                    },
                    medications=pt_meds,
                    lab_values=lab_vals,
                    prior_treatment=pt_prior,
                    comorbidities=pt_comorbs,
                    consent_status=consent,
                    screening_date=scr_date,
                    assigned_site_id=assigned_site,
                )
            )

        return patients

    def generate_deviations(
        self,
        sites: List[TrialSite],
        trial_id: str = "TRIAL-ONC-001",
        count: int = 48
    ) -> List[ProtocolDeviation]:
        """Generates realistic protocol deviations distributed across candidate sites."""
        dev_templates = [
            (DeviationCategory.VISIT_WINDOW, DeviationSeverity.LOW, "Patient visit conducted 3 days outside protocol-defined +/- 2 day window due to weather.", False),
            (DeviationCategory.INFORMED_CONSENT, DeviationSeverity.HIGH, "Subject re-consent on protocol amendment v2.0 completed 4 days after first amendment visit.", True),
            (DeviationCategory.INVESTIGATIONAL_PRODUCT, DeviationSeverity.CRITICAL, "Study drug storage temperature excursion: -2°C below validated range for 4 hours; quarantined.", True),
            (DeviationCategory.LAB_PROTOCOL, DeviationSeverity.LOW, "PK blood sample centrifuged 15 minutes past target schedule; sample integrity maintained.", False),
            (DeviationCategory.INCLUSION_VIOLATION, DeviationSeverity.CRITICAL, "Subject enrolled with baseline eGFR 42 mL/min (protocol threshold >= 45 mL/min); reported to IRB.", True),
            (DeviationCategory.SAFETY_REPORTING, DeviationSeverity.HIGH, "Non-serious grade 2 rash reported 48 hours after sponsor notification window.", False),
            (DeviationCategory.DOCUMENTATION, DeviationSeverity.LOW, "Concomitant medication dose change not reconciled in eCRF prior to interim monitoring visit.", False),
            (DeviationCategory.LAB_PROTOCOL, DeviationSeverity.MEDIUM, "Local laboratory chemistry panel used instead of central laboratory without sponsor waiver.", False),
            (DeviationCategory.VISIT_WINDOW, DeviationSeverity.LOW, "Week 12 CT imaging scan rescheduled 5 days later due to hospital scanner maintenance.", False),
            (DeviationCategory.INVESTIGATIONAL_PRODUCT, DeviationSeverity.MEDIUM, "Dose accountability log had 2 unverified returned tablet blisters reconciled with pharmacy log.", False),
        ]

        site_ids = [s.site_id for s in sites]
        # Some sites have higher risk / more deviations to test risk differentiation
        high_risk_sites = ["SITE-106", "SITE-108", "SITE-111"]
        weights = [3 if sid in high_risk_sites else 1 for sid in site_ids]

        deviations = []
        for i in range(1, count + 1):
            dev_id = f"DEV-{i:03d}"
            template = self.rng.choice(dev_templates)
            chosen_site = self.rng.choices(site_ids, weights=weights, k=1)[0]
            days_ago = self.rng.randint(5, 300)
            occ_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            resolved = self.rng.random() > 0.25  # 25% unresolved

            # Recurrence likelihood higher for high risk sites
            recurrence = template[3] or (chosen_site in high_risk_sites and self.rng.random() > 0.4)

            deviations.append(
                ProtocolDeviation(
                    deviation_id=dev_id,
                    site_id=chosen_site,
                    trial_id=trial_id,
                    category=template[0],
                    severity=template[1],
                    occurrence_date=occ_date,
                    resolved=resolved,
                    recurrence=recurrence,
                    description=template[2],
                    site_impact=(
                        "Requires root cause corrective action (CAPA) and investigator re-training."
                        if template[1] in [DeviationSeverity.HIGH, DeviationSeverity.CRITICAL]
                        else "Documented in site master file with monitoring verification."
                    ),
                )
            )

        return deviations


class SyntheticDataProvider:
    """Manages cached access to synthetic datasets and disk fixtures."""

    def __init__(self, data_dir: str = None, seed: int = 42):
        self.data_dir = data_dir or config.synthetic_data_dir
        self.generator = SyntheticDataGenerator(seed=seed)
        self._cached_trials: List[Trial] = []
        self._cached_sites: List[TrialSite] = []
        self._cached_patients: List[Patient] = []
        self._cached_deviations: List[ProtocolDeviation] = []

    def ensure_fixtures_on_disk(self) -> None:
        """Saves synthetic datasets to disk if not already present."""
        os.makedirs(self.data_dir, exist_ok=True)
        trials_path = os.path.join(self.data_dir, "trials.json")
        sites_path = os.path.join(self.data_dir, "sites.json")
        patients_path = os.path.join(self.data_dir, "patients.json")
        deviations_path = os.path.join(self.data_dir, "deviations.json")

        if not os.path.exists(trials_path):
            trials = self.generator.generate_trials()
            with open(trials_path, "w", encoding="utf-8") as f:
                json.dump([t.model_dump() for t in trials], f, indent=2)

        sites_list = None
        if not os.path.exists(sites_path):
            sites_list = self.generator.generate_sites()
            with open(sites_path, "w", encoding="utf-8") as f:
                json.dump([s.model_dump() for s in sites_list], f, indent=2)

        if not os.path.exists(patients_path):
            if sites_list is None:
                with open(sites_path, "r", encoding="utf-8") as f:
                    sites_list = [TrialSite(**item) for item in json.load(f)]
            patients = self.generator.generate_patients(count=350, sites=sites_list)
            with open(patients_path, "w", encoding="utf-8") as f:
                json.dump([p.model_dump() for p in patients], f, indent=2)

        if not os.path.exists(deviations_path):
            if sites_list is None:
                with open(sites_path, "r", encoding="utf-8") as f:
                    sites_list = [TrialSite(**item) for item in json.load(f)]
            deviations = self.generator.generate_deviations(sites=sites_list, count=55)
            with open(deviations_path, "w", encoding="utf-8") as f:
                json.dump([d.model_dump() for d in deviations], f, indent=2)

    def get_trials(self) -> List[Trial]:
        if not self._cached_trials:
            self.ensure_fixtures_on_disk()
            trials_path = os.path.join(self.data_dir, "trials.json")
            with open(trials_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                self._cached_trials = [Trial(**item) for item in raw]
        return self._cached_trials

    def get_sites(self) -> List[TrialSite]:
        if not self._cached_sites:
            self.ensure_fixtures_on_disk()
            sites_path = os.path.join(self.data_dir, "sites.json")
            with open(sites_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                self._cached_sites = [TrialSite(**item) for item in raw]
        return self._cached_sites

    def get_patients(self) -> List[Patient]:
        if not self._cached_patients:
            self.ensure_fixtures_on_disk()
            patients_path = os.path.join(self.data_dir, "patients.json")
            with open(patients_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                self._cached_patients = [Patient(**item) for item in raw]
        return self._cached_patients

    def get_deviations(self, trial_id: str = "TRIAL-ONC-001") -> List[ProtocolDeviation]:
        if not self._cached_deviations:
            self.ensure_fixtures_on_disk()
            deviations_path = os.path.join(self.data_dir, "deviations.json")
            with open(deviations_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                self._cached_deviations = [ProtocolDeviation(**item) for item in raw]
        return [d for d in self._cached_deviations if d.trial_id == trial_id]

# Singleton instance
data_provider = SyntheticDataProvider()
