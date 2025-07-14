"""
Risk Score Calculator.

Computes final DILI risk scores by combining direct and network evidence,
and assigns risk categories.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


class RiskCalculator:
    """Computes final DILI risk scores and categories."""
    
    def __init__(self, alpha: float = 0.5):
        """Initialize risk calculator.
        
        Args:
            alpha: Weight for network guilt-by-association (0-1)
        """
        self.alpha = alpha
    
    def compute_final_risk_score(self, combined_scores: pd.DataFrame) -> pd.DataFrame:
        """Compute final DILI risk score combining direct and network evidence.
        
        Args:
            combined_scores: DataFrame with direct and network DILI evidence
            
        Returns:
            DataFrame with final risk scores
        """
        logger.info("Computing final DILI risk scores...")
        
        # Normalize features to [0,1] range
        features_to_normalize = ['total_dili_weight', 'high_risk_drug_count', 'network_dili_score']
        
        for feature in features_to_normalize:
            if feature in combined_scores.columns:
                max_val = combined_scores[feature].max()
                if max_val > 0:
                    combined_scores[f'{feature}_normalized'] = combined_scores[feature] / max_val
                else:
                    combined_scores[f'{feature}_normalized'] = 0
        
        # Compute final risk score: direct evidence + alpha * network evidence
        combined_scores['dili_risk_score'] = (
            combined_scores['total_dili_weight_normalized'] + 
            self.alpha * combined_scores['network_dili_score_normalized']
        )
        
        # Normalize final score to [0,1]
        max_score = combined_scores['dili_risk_score'].max()
        if max_score > 0:
            combined_scores['dili_risk_score'] = combined_scores['dili_risk_score'] / max_score
        
        # Add risk categories with equal distribution (tertiles)
        try:
            combined_scores['risk_category'] = pd.qcut(
                combined_scores['dili_risk_score'],
                q=3,
                labels=['Low', 'Medium', 'High'],
                duplicates='drop'
            )
        except ValueError:
            # Fallback to cut if qcut fails due to duplicate values
            combined_scores['risk_category'] = pd.cut(
                combined_scores['dili_risk_score'],
                bins=3,
                labels=['Low', 'Medium', 'High'],
                include_lowest=True
            )
        
        logger.info(f"Computed final risk scores for {len(combined_scores)} targets")
        logger.info(f"Risk score range: {combined_scores['dili_risk_score'].min():.3f} - {combined_scores['dili_risk_score'].max():.3f}")
        
        # Show risk distribution
        risk_dist = combined_scores['risk_category'].value_counts()
        logger.info(f"Risk category distribution:\n{risk_dist}")
        
        return combined_scores 