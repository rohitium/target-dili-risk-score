"""
ETL for Target DILI Risk Score.

Builds the core data tables needed for DILI risk assessment:
- Drug-target associations with DILIrank data and OpenFDA approval status
- Target-target network from Pathway Commons
"""

import json
import pandas as pd
import logging
import re
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


def normalize_drug_name(name: str) -> str:
    """Normalize drug name for matching."""
    if not name:
        return ""
    # Convert to lowercase, remove extra spaces, remove common suffixes
    normalized = name.lower().strip()
    normalized = re.sub(r'\s+', ' ', normalized)  # Multiple spaces to single
    normalized = re.sub(r'\b(hcl|hydrochloride|sulfate|citrate|phosphate|acetate|sodium|potassium|calcium|magnesium)\b', '', normalized)
    normalized = normalized.strip()
    return normalized


def parse_openfda_bulk_data(json_path: str) -> pd.DataFrame:
    """
    Parse OpenFDA bulk data and extract drug approval information.
    
    Args:
        json_path: Path to the OpenFDA JSON file
        
    Returns:
        DataFrame with columns: ['drug_name', 'normalized_name', 'brand_name', 'generic_name', 'marketing_status', 'approval_status']
    """
    logger.info(f"Parsing OpenFDA bulk data from {json_path}...")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    results = []
    total_records = len(data['results'])
    logger.info(f"Processing {total_records} drug records...")
    
    for i, record in enumerate(data['results']):
        if i % 1000 == 0:
            logger.info(f"Processed {i}/{total_records} records...")
        
        products = record.get('products', [])
        for product in products:
            brand_name = product.get('brand_name', '').strip()
            active_ingredients = product.get('active_ingredients', [])
            marketing_status = product.get('marketing_status', '').strip()
            
            # Extract generic names from active ingredients
            generic_names = []
            for ingredient in active_ingredients:
                generic_name = ingredient.get('name', '').strip()
                if generic_name:
                    generic_names.append(generic_name)
            
            # Create entries for brand name and generic names
            drug_names = [brand_name] + generic_names if brand_name else generic_names
            
            for drug_name in drug_names:
                if drug_name:  # Skip empty names
                    normalized = normalize_drug_name(drug_name)
                    
                    # Determine approval status from marketing status
                    if marketing_status:
                        status_lower = marketing_status.lower()
                        if 'discontinued' in status_lower or 'withdrawn' in status_lower:
                            approval_status = 'withdrawn'
                        elif 'approved' in status_lower or 'prescription' in status_lower:
                            approval_status = 'approved'
                        elif 'otc' in status_lower or 'over-the-counter' in status_lower:
                            approval_status = 'approved'
                        else:
                            approval_status = 'other'
                    else:
                        approval_status = 'unknown'
                    
                    results.append({
                        'drug_name': drug_name,
                        'normalized_name': normalized,
                        'brand_name': brand_name,
                        'generic_name': '; '.join(generic_names) if generic_names else '',
                        'marketing_status': marketing_status,
                        'approval_status': approval_status
                    })
    
    df = pd.DataFrame(results)
    logger.info(f"Extracted {len(df)} drug entries from OpenFDA data")
    
    return df


def create_drug_approval_lookup(openfda_df: pd.DataFrame) -> Dict[str, str]:
    """
    Create a lookup dictionary mapping drug names to approval status.
    
    Args:
        openfda_df: DataFrame from parse_openfda_bulk_data
        
    Returns:
        Dictionary mapping drug names to approval status
    """
    logger.info("Creating drug approval lookup...")
    
    # Create lookup with both original and normalized names
    lookup = {}
    
    for _, row in openfda_df.iterrows():
        drug_name = row['drug_name']
        normalized = row['normalized_name']
        approval_status = row['approval_status']
        
        # Add both original and normalized names to lookup
        if drug_name:
            lookup[drug_name.lower()] = approval_status
        if normalized:
            lookup[normalized] = approval_status
    
    logger.info(f"Created lookup with {len(lookup)} unique drug names")
    return lookup


def match_drugs_to_approval_status(drug_names: List[str], openfda_df: pd.DataFrame) -> pd.DataFrame:
    """
    Match a list of drug names to their approval status from OpenFDA data.
    
    Args:
        drug_names: List of drug names to match
        openfda_df: DataFrame from parse_openfda_bulk_data
        
    Returns:
        DataFrame with columns: ['drug_name', 'approval_status', 'matched_name']
    """
    logger.info(f"Matching {len(drug_names)} drugs to OpenFDA approval status...")
    
    # Create lookup
    lookup = create_drug_approval_lookup(openfda_df)
    
    results = []
    matched_count = 0
    
    for drug_name in drug_names:
        if not drug_name:
            continue
            
        # Try exact match first
        normalized = normalize_drug_name(drug_name)
        approval_status = None
        matched_name = None
        
        # Try multiple matching strategies
        if drug_name.lower() in lookup:
            approval_status = lookup[drug_name.lower()]
            matched_name = drug_name
        elif normalized in lookup:
            approval_status = lookup[normalized]
            matched_name = drug_name
        else:
            # Try partial matching
            for openfda_name, status in lookup.items():
                if (drug_name.lower() in openfda_name or 
                    openfda_name in drug_name.lower() or
                    normalized in openfda_name or 
                    openfda_name in normalized):
                    approval_status = status
                    matched_name = openfda_name
                    break
        
        if approval_status:
            matched_count += 1
        else:
            approval_status = 'not_found'
            matched_name = drug_name
        
        results.append({
            'drug_name': drug_name,
            'approval_status': approval_status,
            'matched_name': matched_name
        })
    
    df = pd.DataFrame(results)
    logger.info(f"Matched {matched_count}/{len(drug_names)} drugs to approval status")
    
    return df


def fetch_openfda_approval_status(drug_names: List[str]) -> pd.DataFrame:
    """
    Fetch approval status for drugs using bulk OpenFDA data.
    
    Args:
        drug_names: List of drug names to match
        
    Returns:
        DataFrame with columns: ['drug_name', 'approval_status']
    """
    # Path to the OpenFDA JSON file
    json_path = Path("data/raw/drug-drugsfda-0001-of-0001.json")
    
    if not json_path.exists():
        logger.error(f"OpenFDA JSON file not found at {json_path}")
        # Return empty DataFrame with expected columns
        return pd.DataFrame({'drug_name': drug_names, 'approval_status': ['not_found'] * len(drug_names)})
    
    # Parse bulk data
    openfda_df = parse_openfda_bulk_data(str(json_path))
    
    # Match drugs to approval status
    result_df = match_drugs_to_approval_status(drug_names, openfda_df)
    
    # Return in expected format
    return result_df[['drug_name', 'approval_status']]


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
        
        # Ensure directories exist
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def build_drug_target_table(self) -> pd.DataFrame:
        """Build drug-target table with DILIrank severity data and OpenFDA approval status.
        
        Returns:
            DataFrame with drug-target associations, DILI severity, and approval status
        """
        logger.info("Building drug-target table with DILIrank data and OpenFDA approval status...")
        
        # Load drug-target mapping (primary source)
        mapping_path = self.interim_dir / "drug_target_mapping.parquet"
        if not mapping_path.exists():
            logger.error("Drug-target mapping not found. Run acquisition first.")
            return pd.DataFrame()
        
        drug_target_df = pd.read_parquet(mapping_path)
        logger.info(f"Loaded {len(drug_target_df)} drug-target mappings")
        
        # Add DILI severity weights
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
    
    def run_etl(self) -> Dict[str, pd.DataFrame]:
        """Run complete ETL pipeline.
        
        Returns:
            Dictionary with ETL outputs
        """
        logger.info("=== Running ETL Pipeline ===")
        
        # Build drug-target table
        drug_target_df = self.build_drug_target_table()
        
        # Build target network
        network_df = self.build_target_network()
        
        logger.info("=== ETL Pipeline Complete ===")
        
        return {
            'drug_target_table': drug_target_df,
            'target_network': network_df
        } 