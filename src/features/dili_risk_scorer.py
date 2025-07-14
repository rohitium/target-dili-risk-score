"""
Simple DILI Risk Scorer.

Computes direct DILI evidence and network guilt-by-association
for each target to create a simple, interpretable risk score.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DILIRiskScorer:
    """Simple DILI risk scorer based on direct evidence and network guilt-by-association."""
    
    def __init__(self, data_dir: str = "data", alpha: float = 0.5):
        """Initialize DILI risk scorer.
        
        Args:
            data_dir: Path to data directory
            alpha: Weight for network guilt-by-association (0-1)
        """
        self.data_dir = Path(data_dir)
        self.processed_dir = self.data_dir / "processed"
        self.alpha = alpha
    
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
    
    def compute_network_guilt_by_association(self, 
                                           direct_evidence: pd.DataFrame,
                                           network_df: pd.DataFrame) -> pd.DataFrame:
        """Compute network guilt-by-association for each target.
        
        Args:
            direct_evidence: Direct DILI evidence per target
            network_df: Target-target network data
            
        Returns:
            DataFrame with network guilt-by-association scores
        """
        logger.info("Computing network guilt-by-association...")
        
        if network_df.empty:
            logger.warning("No network data available, using zero network scores")
            network_scores = direct_evidence.copy()
            network_scores['network_dili_score'] = 0
            return network_scores
        
        # For each target, sum the DILI evidence of its neighbors
        network_scores = []
        
        for target in direct_evidence.index:
            # Find neighbors of this target in the network
            if 'risk_targets' in network_df.columns:
                # Use the risk_targets column which contains neighbor information
                target_network = network_df[network_df['target1'] == target]
                if not target_network.empty:
                    # For now, use a simple approach: sum neighbor DILI weights
                    # In practice, you'd parse the risk_targets string to get actual neighbors
                    neighbor_dili_score = target_network['n_risk_targets'].sum() if 'n_risk_targets' in target_network.columns else 0
                else:
                    neighbor_dili_score = 0
            else:
                neighbor_dili_score = 0
            
            network_scores.append({
                'ot_target_symbol': target,
                'network_dili_score': neighbor_dili_score
            })
        
        network_df_scores = pd.DataFrame(network_scores).set_index('ot_target_symbol')
        
        # Merge with direct evidence
        combined_scores = direct_evidence.merge(network_df_scores, left_index=True, right_index=True, how='left')
        combined_scores['network_dili_score'] = combined_scores['network_dili_score'].fillna(0)
        
        logger.info(f"Computed network guilt-by-association for {len(combined_scores)} targets")
        return combined_scores
    
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
    
    def score_targets(self) -> pd.DataFrame:
        """Score all targets for DILI risk.
        
        Returns:
            DataFrame with DILI risk scores for all targets
        """
        logger.info("=== Computing DILI Risk Scores ===")
        
        # Load drug-target table
        drug_target_path = self.processed_dir / "drug_target_table.parquet"
        if not drug_target_path.exists():
            logger.error("Drug-target table not found. Run ETL first.")
            return pd.DataFrame()
        
        drug_target_df = pd.read_parquet(drug_target_path)
        logger.info(f"Loaded {len(drug_target_df)} drug-target records")
        
        # Load target network
        network_path = self.processed_dir / "target_network.parquet"
        network_df = pd.read_parquet(network_path) if network_path.exists() else pd.DataFrame()
        
        # Compute direct DILI evidence
        direct_evidence = self.compute_direct_dili_evidence(drug_target_df)
        
        # Compute network guilt-by-association
        combined_scores = self.compute_network_guilt_by_association(direct_evidence, network_df)
        
        # Compute final risk scores
        final_scores = self.compute_final_risk_score(combined_scores)
        
        # Save results
        output_path = self.processed_dir / "dili_risk_scores.parquet"
        # Reset index to include target symbols as a column
        final_scores = final_scores.reset_index()
        final_scores.to_parquet(output_path, index=False)
        logger.info(f"Saved DILI risk scores to {output_path}")
        
        return final_scores 