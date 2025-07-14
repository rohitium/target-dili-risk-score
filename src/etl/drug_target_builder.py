"""
Drug-Target Table Builder.

Builds the core drug-target table with DILIrank severity data
and OpenFDA approval status.
"""

import pandas as pd
import logging
from pathlib import Path

from .openfda_processor import fetch_openfda_approval_status

logger = logging.getLogger(__name__)


class DrugTargetBuilder:
    """Builds drug-target table with DILIrank data and approval status."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize drug-target builder.
        
        Args:
            data_dir: Path to data directory
        """
        self.data_dir = Path(data_dir)
        self.interim_dir = self.data_dir / "interim"
        self.processed_dir = self.data_dir / "processed"
        
        # Ensure directories exist
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def build_drug_target_table(self) -> pd.DataFrame:
        """Build drug-target table with DILIrank severity data and OpenFDA approval status.
        
        Returns:
            DataFrame with drug-target associations, DILI severity, and approval status
        """
        logger.info("Building drug-target table with DILIrank data and OpenFDA approval status...")
        
        # Load clean drug-target mapping (new source)
        mapping_path = self.interim_dir / "drug_target_mapping_clean.parquet"
        if not mapping_path.exists():
            logger.error("Clean drug-target mapping not found. Run acquisition first.")
            return pd.DataFrame()
        
        drug_target_df = pd.read_parquet(mapping_path)
        logger.info(f"Loaded {len(drug_target_df)} clean drug-target mappings")
        
        # Add DILI severity weights (already included in clean mapping)
        if 'dili_severity_weight' not in drug_target_df.columns:
            severity_weights = {
                'Most-DILI-Concern': 2.0,
                'Less-DILI-Concern': 1.0, 
                'No-DILI-Concern': 0.0,
                'Ambiguous-DILI-Concern': 0.5
            }
            
            drug_target_df['dili_severity_weight'] = drug_target_df['fda_dili_concern'].map(
                severity_weights
            ).fillna(0)
        
        # Fetch OpenFDA approval status and merge
        unique_drugs = drug_target_df['fda_drug_name'].dropna().unique().tolist()
        logger.info(f"Fetching OpenFDA approval status for {len(unique_drugs)} unique drugs...")
        approval_df = fetch_openfda_approval_status(unique_drugs)
        logger.info(f"Fetched approval status for {len(approval_df)} drugs")
        
        # Merge approval status into drug_target_df
        drug_target_df = drug_target_df.merge(
            approval_df.rename(columns={'drug_name': 'fda_drug_name'}),
            on='fda_drug_name', how='left'
        )
        
        # Add withdrawn status column (after merge)
        drug_target_df['withdrawn'] = drug_target_df['approval_status'] == 'withdrawn'
        
        # Save drug-target table
        output_path = self.processed_dir / "drug_target_table.parquet"
        drug_target_df.to_parquet(output_path, index=False)
        logger.info(f"Saved drug-target table with {len(drug_target_df)} records")
        
        return drug_target_df 