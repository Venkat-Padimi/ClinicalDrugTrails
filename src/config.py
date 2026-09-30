"""Configuration management for Clinical Trial Site Selection & Recruitment Agent.

Contains system settings, default scoring weights, thresholds, and mandatory disclaimers.
All data is strictly synthetic for demonstration purposes.
"""

from dataclasses import dataclass, field
from typing import Dict
import os

DISCLAIMER_TEXT = (
    "DISCLAIMER: Synthetic demonstration data — not real clinical trial data. "
    "This system is an AI-assisted clinical trial decision-support demonstration. "
    "It does not provide medical advice, does not replace investigators or ethics "
    "committees, and must not be used for real patient eligibility or clinical "
    "decisions without appropriate clinical, regulatory, and human review."
)

@dataclass
class RiskScoringWeights:
    """Configurable weights for the Site Risk Engine (must sum to 1.0)."""
    recruitment_weight: float = 0.25
    compliance_weight: float = 0.20
    data_quality_weight: float = 0.15
    investigator_experience_weight: float = 0.15
    operational_weight: float = 0.15
    capacity_activation_weight: float = 0.10

    def validate(self) -> bool:
        total = (
            self.recruitment_weight
            + self.compliance_weight
            + self.data_quality_weight
            + self.investigator_experience_weight
            + self.operational_weight
            + self.capacity_activation_weight
        )
        return abs(total - 1.0) < 1e-4


@dataclass
class SiteRankingWeights:
    """Configurable weights for composite Multi-Criteria Site Ranking."""
    recruitment_score_weight: float = 0.30
    operational_score_weight: float = 0.20
    experience_score_weight: float = 0.20
    data_quality_weight: float = 0.15
    compliance_score_weight: float = 0.15

    def validate(self) -> bool:
        total = (
            self.recruitment_score_weight
            + self.operational_score_weight
            + self.experience_score_weight
            + self.data_quality_weight
            + self.compliance_score_weight
        )
        return abs(total - 1.0) < 1e-4


@dataclass
class AppConfig:
    """Global Application Configuration."""
    app_name: str = "Clinical Trial Site Selection & Recruitment Agent"
    version: str = "1.0.0"
    is_demo_mode: bool = True
    synthetic_label: str = "SYNTHETIC DEMO DATA"
    disclaimer: str = DISCLAIMER_TEXT
    default_random_seed: int = 42
    
    # Workflow constraints
    max_workflow_steps: int = 25
    human_review_confidence_threshold: float = 0.70
    high_risk_deviation_threshold: int = 5
    
    # Scoring configurations
    risk_weights: RiskScoringWeights = field(default_factory=RiskScoringWeights)
    ranking_weights: SiteRankingWeights = field(default_factory=SiteRankingWeights)
    
    # Storage / paths
    data_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    synthetic_data_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "synthetic")

config = AppConfig()
