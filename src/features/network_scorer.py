"""
Network Guilt-by-Association Scoring.

Computes network-based DILI risk scores using guilt-by-association
from target-target network data.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


class NetworkScorer:
    """Computes network guilt-by-association for each target."""
    
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
        
        # Load target mapping to connect OpenTargets to Pathway Commons
        from pathlib import Path
        mapping_path = Path("data/processed/target_mapping.parquet")
        
        if not mapping_path.exists():
            logger.warning("Target mapping not found, using zero network scores")
            network_scores = direct_evidence.copy()
            network_scores['network_dili_score'] = 0
            return network_scores
        
        mapping_df = pd.read_parquet(mapping_path)
        logger.info(f"Loaded target mapping with {len(mapping_df)} gene symbol mappings")
        
        # For each target, find its network neighbors and sum their DILI evidence
        network_scores = []
        
        for target in direct_evidence.index:
            # Find Pathway Commons targets that contain this gene symbol
            pc_targets = mapping_df[mapping_df['gene_symbol'] == target]['pc_target'].unique()
            
            if len(pc_targets) > 0:
                # Get the network data for these Pathway Commons targets
                target_network = network_df[network_df['target1'].isin(pc_targets)]
                
                if not target_network.empty:
                    # Sum the n_risk_targets as a proxy for network guilt-by-association
                    neighbor_dili_score = target_network['n_risk_targets'].sum()
                else:
                    neighbor_dili_score = 0
            else:
                neighbor_dili_score = 0
            
            network_scores.append({
                'target_symbol': target,
                'network_dili_score': neighbor_dili_score
            })
        
        network_df_scores = pd.DataFrame(network_scores).set_index('target_symbol')
        
        # Merge with direct evidence
        combined_scores = direct_evidence.merge(network_df_scores, left_index=True, right_index=True, how='left')
        combined_scores['network_dili_score'] = combined_scores['network_dili_score'].fillna(0)
        
        # Log some statistics
        non_zero_network = combined_scores[combined_scores['network_dili_score'] > 0]
        logger.info(f"Computed network guilt-by-association for {len(combined_scores)} targets")
        logger.info(f"Targets with non-zero network contribution: {len(non_zero_network)}")
        
        return combined_scores 