"""
Simple DILI Risk Scorer.

Computes direct DILI evidence and network guilt-by-association
for each target to create a simple, interpretable risk score.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Optional

from .direct_evidence import DirectEvidenceComputer
from .network_scorer import NetworkScorer
from .risk_calculator import RiskCalculator

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
        
        # Initialize components
        self.direct_evidence_computer = DirectEvidenceComputer()
        self.network_scorer = NetworkScorer()
        self.risk_calculator = RiskCalculator(alpha=alpha)
    
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
        direct_evidence = self.direct_evidence_computer.compute_direct_dili_evidence(drug_target_df)
        
        # Compute network guilt-by-association
        combined_scores = self.network_scorer.compute_network_guilt_by_association(direct_evidence, network_df)
        
        # Compute final risk scores
        final_scores = self.risk_calculator.compute_final_risk_score(combined_scores)
        
        # Save results
        output_path = self.processed_dir / "dili_risk_scores.parquet"
        # Reset index to include target symbols as a column
        final_scores = final_scores.reset_index()
        final_scores.to_parquet(output_path, index=False)
        logger.info(f"Saved DILI risk scores to {output_path}")
        
        return final_scores 