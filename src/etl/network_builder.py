"""
Target Network Builder.

Builds target-target network from Pathway Commons data
for guilt-by-association analysis.
"""

import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class NetworkBuilder:
    """Builds target-target network from Pathway Commons."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize network builder.
        
        Args:
            data_dir: Path to data directory
        """
        self.data_dir = Path(data_dir)
        self.interim_dir = self.data_dir / "interim"
        self.processed_dir = self.data_dir / "processed"
        
        # Ensure directories exist
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def build_target_network(self) -> pd.DataFrame:
        """Build target-target network from Pathway Commons.
        
        Returns:
            DataFrame with target-target associations
        """
        logger.info("Building target-target network...")
        
        # Load Pathway Commons data
        pc_path = self.interim_dir / "guilt_by_association_targets.parquet"
        if not pc_path.exists():
            logger.warning("Pathway Commons data not found, creating empty network")
            return pd.DataFrame()
        
        network_df = pd.read_parquet(pc_path)
        logger.info(f"Loaded {len(network_df)} target-target associations")
        
        # Standardize column names
        if 'implicated_target' in network_df.columns:
            network_df = network_df.rename(columns={'implicated_target': 'target1'})
        
        # Keep only essential columns for network analysis
        network_cols = ['target1', 'risk_targets', 'n_risk_targets']
        available_cols = [col for col in network_cols if col in network_df.columns]
        
        if available_cols:
            network_df = network_df[available_cols]
        
        # Save target network
        output_path = self.processed_dir / "target_network.parquet"
        network_df.to_parquet(output_path, index=False)
        logger.info(f"Saved target network with {len(network_df)} records")
        
        return network_df 