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
        
        # Create mapping from gene symbols to Pathway Commons targets
        # The risk_targets column contains gene symbols that match OpenTargets targets
        mapping_data = []
        
        for idx, row in network_df.iterrows():
            pc_target = row['target1']
            risk_targets_str = row['risk_targets']
            
            if pd.notna(risk_targets_str):
                # Split the semicolon-separated gene symbols
                gene_symbols = risk_targets_str.split(';')
                
                for gene_symbol in gene_symbols:
                    gene_symbol = gene_symbol.strip()
                    if gene_symbol:  # Skip empty strings
                        mapping_data.append({
                            'pc_target': pc_target,
                            'gene_symbol': gene_symbol,
                            'n_risk_targets': row['n_risk_targets']
                        })
        
        # Create mapping DataFrame
        mapping_df = pd.DataFrame(mapping_data)
        
        # Save both the original network and the mapping
        network_output_path = self.processed_dir / "target_network.parquet"
        mapping_output_path = self.processed_dir / "target_mapping.parquet"
        
        # Keep only essential columns for network analysis
        network_cols = ['target1', 'risk_targets', 'n_risk_targets']
        available_cols = [col for col in network_cols if col in network_df.columns]
        
        if available_cols:
            network_df = network_df[available_cols]
        
        network_df.to_parquet(network_output_path, index=False)
        mapping_df.to_parquet(mapping_output_path, index=False)
        
        logger.info(f"Saved target network with {len(network_df)} records")
        logger.info(f"Saved target mapping with {len(mapping_df)} gene symbol mappings")
        
        return network_df 