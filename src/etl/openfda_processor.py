"""
OpenFDA Data Processor.

Processes OpenFDA bulk data and matches drug names to approval status.
"""

import json
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List

from .drug_utils import normalize_drug_name

logger = logging.getLogger(__name__)


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