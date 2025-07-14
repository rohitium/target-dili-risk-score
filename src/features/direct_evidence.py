"""
Direct DILI Evidence Computation.

Computes direct DILI evidence for each target based on drug-target associations
and FDA DILIrank data.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DirectEvidenceComputer:
    """Computes direct DILI evidence for each target."""
    
    def compute_direct_dili_evidence(self, drug_target_df: pd.DataFrame) -> pd.DataFrame:
        """Compute direct DILI evidence for each target.
        
        Args:
            drug_target_df: Drug-target table with DILI severity weights
            
        Returns:
            DataFrame with direct DILI evidence per target
        """
        logger.info("Computing direct DILI evidence...")
        
        # Aggregate DILI evidence per target
        direct_evidence = drug_target_df.groupby('ot_target_symbol').agg({
            'fda_drug_name': 'count',  # Number of drugs targeting this target
            'dili_severity_weight': 'sum',  # Sum of DILI severity weights
            'fda_dili_concern': lambda x: (x == 'Most-DILI-Concern').sum()  # High-risk drug count
        }).rename(columns={
            'fda_drug_name': 'drug_count',
            'dili_severity_weight': 'total_dili_weight',
            'fda_dili_concern': 'high_risk_drug_count'
        })
        
        # Add derived features
        direct_evidence['dili_risk_ratio'] = (
            direct_evidence['high_risk_drug_count'] / direct_evidence['drug_count']
        ).fillna(0)
        
        direct_evidence['avg_dili_weight'] = (
            direct_evidence['total_dili_weight'] / direct_evidence['drug_count']
        ).fillna(0)
        
        logger.info(f"Computed direct DILI evidence for {len(direct_evidence)} targets")
        return direct_evidence 