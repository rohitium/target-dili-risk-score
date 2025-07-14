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