"""
Simple feature engineering for Target DILI Risk Score.

This module computes direct DILI evidence and network guilt-by-association
for each target to create a simple, interpretable risk score.
"""

from .dili_risk_scorer import DILIRiskScorer

__all__ = ['DILIRiskScorer'] 