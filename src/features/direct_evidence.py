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
        
        # Deduplicate drug-target pairs to prevent inflated weights
        # Keep the first occurrence of each unique drug-target pair
        drug_target_dedup = drug_target_df.drop_duplicates(
            subset=['fda_drug_name', 'ot_target_symbol'], 
            keep='first'
        )
        
        logger.info(f"Deduplicated from {len(drug_target_df)} to {len(drug_target_dedup)} unique drug-target pairs")
        
        # Aggregate DILI evidence per target
        direct_evidence = drug_target_dedup.groupby('ot_target_symbol').agg({
            'fda_drug_name': 'nunique',  # Number of unique drugs targeting this target
            'dili_severity_weight': 'sum',  # Sum of DILI severity weights (now from unique drugs only)
        }).rename(columns={
            'fda_drug_name': 'drug_count',
            'dili_severity_weight': 'total_dili_weight',
        })
        
        # Calculate high-risk drug count (unique drugs that are high-risk)
        high_risk_counts = drug_target_dedup[
            drug_target_dedup['fda_dili_concern'] == 'Most-DILI-Concern'
        ].groupby('ot_target_symbol')['fda_drug_name'].nunique()
        
        direct_evidence['high_risk_drug_count'] = high_risk_counts.fillna(0)
        
        # Add derived features
        direct_evidence['dili_risk_ratio'] = (
            direct_evidence['high_risk_drug_count'] / direct_evidence['drug_count']
        ).fillna(0)
        
        direct_evidence['avg_dili_weight'] = (
            direct_evidence['total_dili_weight'] / direct_evidence['drug_count']
        ).fillna(0)
        
        logger.info(f"Computed direct DILI evidence for {len(direct_evidence)} targets")
        return direct_evidence 