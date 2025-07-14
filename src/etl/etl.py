"""
ETL for Target DILI Risk Score.

Builds the core data tables needed for DILI risk assessment:
- Drug-target associations with DILIrank data and OpenFDA approval status
- Target-target network from Pathway Commons
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict

from .drug_target_builder import DrugTargetBuilder
from .network_builder import NetworkBuilder

logger = logging.getLogger(__name__)


class ETL:
    """ETL for DILI risk assessment."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize ETL.
        
        Args:
            data_dir: Path to data directory
        """
        self.data_dir = Path(data_dir)
        self.interim_dir = self.data_dir / "interim"
        self.processed_dir = self.data_dir / "processed"
        
        # Initialize components
        self.drug_target_builder = DrugTargetBuilder(data_dir)
        self.network_builder = NetworkBuilder(data_dir)
        
        # Ensure directories exist
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def run_etl(self) -> Dict[str, pd.DataFrame]:
        """Run complete ETL pipeline.
        
        Returns:
            Dictionary with ETL outputs
        """
        logger.info("=== Running ETL Pipeline ===")
        
        # Build drug-target table
        drug_target_df = self.drug_target_builder.build_drug_target_table()
        
        # Build target network
        network_df = self.network_builder.build_target_network()
        
        logger.info("=== ETL Pipeline Complete ===")
        
        return {
            'drug_target_table': drug_target_df,
            'target_network': network_df
        } 