"""
Drug Name Matching Utilities.

Provides utilities for normalizing and matching drug names
between FDA DILIrank and OpenTargets datasets.
"""

import re
import logging
import pandas as pd
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
import multiprocessing as mp
from functools import partial

logger = logging.getLogger(__name__)


def normalize_drug_name(name: str) -> str:
    """Normalize drug name for matching.
    
    Args:
        name: Raw drug name
        
    Returns:
        Normalized drug name
    """
    if not name:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = name.lower().strip()
    
    # Remove common drug suffixes and salts
    suffixes = [
        r'\b(hcl|hydrochloride|sulfate|citrate|phosphate|acetate|sodium|potassium|calcium|magnesium)\b',
        r'\b(hydrochloride|sulfate|citrate|phosphate|acetate)\b',
        r'\b(sodium|potassium|calcium|magnesium)\b',
        r'\b(monohydrate|dihydrate|trihydrate)\b',
        r'\b(hemihydrate|sesquihydrate)\b'
    ]
    
    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized)
    
    # Remove extra spaces and punctuation
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = normalized.strip()
    
    return normalized


def create_drug_name_variations(drug_name: str) -> List[str]:
    """Create variations of a drug name for matching.
    
    Args:
        drug_name: Drug name
        
    Returns:
        List of drug name variations
    """
    variations = [drug_name]
    
    # Add normalized version
    normalized = normalize_drug_name(drug_name)
    if normalized != drug_name.lower():
        variations.append(normalized)
    
    # Add common abbreviations
    common_abbrevs = {
        'acetaminophen': 'paracetamol',
        'paracetamol': 'acetaminophen',
        'aspirin': 'acetylsalicylic acid',
        'acetylsalicylic acid': 'aspirin',
        'ibuprofen': 'advil',
        'advil': 'ibuprofen'
    }
    
    if drug_name.lower() in common_abbrevs:
        variations.append(common_abbrevs[drug_name.lower()])
    
    return list(set(variations))


def fuzzy_match_drug_names(drug1: str, drug2: str, threshold: float = 0.8) -> float:
    """Calculate fuzzy match score between two drug names.
    
    Args:
        drug1: First drug name
        drug2: Second drug name
        threshold: Minimum similarity threshold
        
    Returns:
        Similarity score (0-1)
    """
    if not drug1 or not drug2:
        return 0.0
    
    # Normalize both names
    norm1 = normalize_drug_name(drug1)
    norm2 = normalize_drug_name(drug2)
    
    # Exact match after normalization
    if norm1 == norm2:
        return 1.0
    
    # Calculate similarity using SequenceMatcher
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    return similarity


def match_fda_to_opentargets_drugs_parallel(fda_drugs: List[str], ot_drugs: List[str], 
                                           threshold: float = 0.8, n_jobs: int = -1) -> Dict[str, str]:
    """Match FDA DILIrank drug names to OpenTargets drug names using parallel processing.
    
    Args:
        fda_drugs: List of FDA DILIrank drug names
        ot_drugs: List of OpenTargets drug names
        threshold: Minimum similarity threshold for matching
        n_jobs: Number of parallel jobs (-1 for all CPUs)
        
    Returns:
        Dictionary mapping FDA drug names to OpenTargets drug names
    """
    logger.info(f"Matching {len(fda_drugs)} FDA drugs to {len(ot_drugs)} OpenTargets drugs (parallel)")
    
    # Pre-compute all OpenTargets drug variations for fast lookup
    logger.info("Pre-computing OpenTargets drug variations...")
    ot_variations_dict = {}
    ot_normalized_dict = {}
    
    for ot_drug in ot_drugs:
        variations = create_drug_name_variations(ot_drug)
        normalized = normalize_drug_name(ot_drug)
        
        # Store all variations
        for var in variations:
            ot_variations_dict[var.lower()] = ot_drug
            ot_normalized_dict[normalized] = ot_drug
    
    # Process in parallel using a simpler approach
    logger.info(f"Processing with {n_jobs} parallel jobs...")
    
    # Split FDA drugs into chunks for parallel processing
    chunk_size = max(1, len(fda_drugs) // n_jobs)
    fda_chunks = [fda_drugs[i:i + chunk_size] for i in range(0, len(fda_drugs), chunk_size)]
    
    def process_chunk(fda_chunk: List[str]) -> List[Tuple[str, str, float]]:
        """Process a chunk of FDA drugs."""
        results = []
        for fda_drug in fda_chunk:
            best_match = None
            best_score = 0.0
            
            # Create variations of FDA drug name
            fda_variations = create_drug_name_variations(fda_drug)
            fda_normalized = normalize_drug_name(fda_drug)
            
            # First, try exact matches (fastest)
            for fda_var in fda_variations:
                if fda_var.lower() in ot_variations_dict:
                    best_match = ot_variations_dict[fda_var.lower()]
                    best_score = 1.0
                    break
            
            # If no exact match, try normalized exact match
            if best_score == 0.0 and fda_normalized in ot_normalized_dict:
                best_match = ot_normalized_dict[fda_normalized]
                best_score = 1.0
            
            # If still no match, try fuzzy matching (slower)
            if best_score == 0.0:
                for ot_drug in ot_drugs:
                    # Skip if we already have a perfect match
                    if best_score >= 0.99:
                        break
                        
                    ot_normalized = normalize_drug_name(ot_drug)
                    
                    # Quick check: if normalized names are very different, skip
                    if abs(len(fda_normalized) - len(ot_normalized)) > 5:
                        continue
                    
                    # Calculate similarity
                    similarity = SequenceMatcher(None, fda_normalized, ot_normalized).ratio()
                    
                    if similarity > best_score:
                        best_score = similarity
                        best_match = ot_drug
                        
                        # Early termination for very good matches
                        if similarity >= 0.95:
                            break
            
            results.append((fda_drug, best_match, best_score))
        
        return results
    
    # Set number of jobs
    if n_jobs == -1:
        n_jobs = mp.cpu_count()
    
    # Process in parallel
    with mp.Pool(n_jobs) as pool:
        chunk_results = pool.map(process_chunk, fda_chunks)
    
    # Flatten results
    results = []
    for chunk_result in chunk_results:
        results.extend(chunk_result)
    
    # Collect results
    matches = {}
    matched_count = 0
    exact_matches = 0
    fuzzy_matches = 0
    
    for fda_drug, best_match, best_score in results:
        if best_score >= threshold:
            matches[fda_drug] = best_match
            matched_count += 1
            if best_score == 1.0:
                exact_matches += 1
            else:
                fuzzy_matches += 1
        else:
            logger.debug(f"No match found for '{fda_drug}' (best score: {best_score:.3f})")
    
    logger.info(f"Matched {matched_count}/{len(fda_drugs)} FDA drugs to OpenTargets drugs")
    logger.info(f"  Exact matches: {exact_matches}")
    logger.info(f"  Fuzzy matches: {fuzzy_matches}")
    return matches


def match_fda_to_opentargets_drugs(fda_drugs: List[str], ot_drugs: List[str], 
                                  threshold: float = 0.8, use_parallel: bool = False) -> Dict[str, str]:
    """Match FDA DILIrank drug names to OpenTargets drug names.
    
    Args:
        fda_drugs: List of FDA DILIrank drug names
        ot_drugs: List of OpenTargets drug names
        threshold: Minimum similarity threshold for matching
        use_parallel: Whether to use parallel processing (disabled for now)
        
    Returns:
        Dictionary mapping FDA drug names to OpenTargets drug names
    """
    # Use optimized serial version for now
    return match_fda_to_opentargets_drugs_serial(fda_drugs, ot_drugs, threshold)


def match_fda_to_opentargets_drugs_serial(fda_drugs: List[str], ot_drugs: List[str], 
                                         threshold: float = 0.8) -> Dict[str, str]:
    """Match FDA DILIrank drug names to OpenTargets drug names.
    
    Args:
        fda_drugs: List of FDA DILIrank drug names
        ot_drugs: List of OpenTargets drug names
        threshold: Minimum similarity threshold for matching
        
    Returns:
        Dictionary mapping FDA drug names to OpenTargets drug names
    """
    logger.info(f"Matching {len(fda_drugs)} FDA drugs to {len(ot_drugs)} OpenTargets drugs")
    
    # Pre-compute all OpenTargets drug variations for fast lookup
    logger.info("Pre-computing OpenTargets drug variations...")
    ot_variations_dict = {}
    ot_normalized_dict = {}
    
    for ot_drug in ot_drugs:
        variations = create_drug_name_variations(ot_drug)
        normalized = normalize_drug_name(ot_drug)
        
        # Store all variations
        for var in variations:
            ot_variations_dict[var.lower()] = ot_drug
            ot_normalized_dict[normalized] = ot_drug
    
    matches = {}
    matched_count = 0
    exact_matches = 0
    fuzzy_matches = 0
    
    for fda_drug in fda_drugs:
        best_match = None
        best_score = 0.0
        
        # Create variations of FDA drug name
        fda_variations = create_drug_name_variations(fda_drug)
        fda_normalized = normalize_drug_name(fda_drug)
        
        # First, try exact matches (fastest)
        for fda_var in fda_variations:
            if fda_var.lower() in ot_variations_dict:
                best_match = ot_variations_dict[fda_var.lower()]
                best_score = 1.0
                exact_matches += 1
                break
        
        # If no exact match, try normalized exact match
        if best_score == 0.0 and fda_normalized in ot_normalized_dict:
            best_match = ot_normalized_dict[fda_normalized]
            best_score = 1.0
            exact_matches += 1
        
        # If still no match, try fuzzy matching (slower)
        if best_score == 0.0:
            for ot_drug in ot_drugs:
                # Skip if we already have a perfect match
                if best_score >= 0.99:
                    break
                    
                ot_normalized = normalize_drug_name(ot_drug)
                
                # Quick check: if normalized names are very different, skip
                if abs(len(fda_normalized) - len(ot_normalized)) > 5:
                    continue
                
                # Calculate similarity
                similarity = SequenceMatcher(None, fda_normalized, ot_normalized).ratio()
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = ot_drug
                    
                    # Early termination for very good matches
                    if similarity >= 0.95:
                        break
        
        if best_score >= threshold:
            matches[fda_drug] = best_match
            matched_count += 1
            if best_score < 1.0:
                fuzzy_matches += 1
        else:
            logger.debug(f"No match found for '{fda_drug}' (best score: {best_score:.3f})")
    
    logger.info(f"Matched {matched_count}/{len(fda_drugs)} FDA drugs to OpenTargets drugs")
    logger.info(f"  Exact matches: {exact_matches}")
    logger.info(f"  Fuzzy matches: {fuzzy_matches}")
    return matches


def validate_drug_matches(matches: Dict[str, str], sample_size: int = 10) -> None:
    """Validate drug name matches by showing sample matches.
    
    Args:
        matches: Dictionary of FDA to OpenTargets drug matches
        sample_size: Number of sample matches to show
    """
    logger.info("Validating drug name matches:")
    
    # Show sample matches
    sample_matches = list(matches.items())[:sample_size]
    for fda_drug, ot_drug in sample_matches:
        logger.info(f"  {fda_drug} -> {ot_drug}")
    
    # Show statistics
    total_matches = len(matches)
    logger.info(f"Total matches: {total_matches}")
    
    # Show some unmatched drugs if any
    if total_matches < 100:  # If we have few matches, show unmatched
        logger.info("Sample unmatched FDA drugs:")
        # This would need to be implemented based on the full FDA drug list


def create_drug_target_mapping(fda_dilirank_df, ot_drug_target_df, 
                              matches: Dict[str, str]) -> pd.DataFrame:
    """Create clean drug-target mapping using matched drug names.
    
    Args:
        fda_dilirank_df: FDA DILIrank DataFrame
        ot_drug_target_df: OpenTargets drug-target DataFrame
        matches: Dictionary mapping FDA drug names to OpenTargets drug names
        
    Returns:
        DataFrame with clean drug-target associations
    """
    logger.info("Creating clean drug-target mapping")
    
    # Create reverse mapping (OpenTargets -> FDA)
    reverse_matches = {v: k for k, v in matches.items()}
    
    # Filter OpenTargets data to only include matched drugs
    matched_ot_drugs = set(matches.values())
    filtered_ot_df = ot_drug_target_df[ot_drug_target_df['drug_name'].isin(matched_ot_drugs)].copy()
    
    # Add FDA drug names
    filtered_ot_df['fda_drug_name'] = filtered_ot_df['drug_name'].map(reverse_matches)
    
    # Prepare FDA DILIrank data for merge
    fda_df = fda_dilirank_df[['Compound Name', 'vDILIConcern', 'Severity Class']].copy()
    fda_df = fda_df.rename(columns={
        'Compound Name': 'fda_drug_name',
        'vDILIConcern': 'fda_dili_concern',
        'Severity Class': 'fda_severity_class'
    })
    
    # Merge with FDA DILIrank data
    merged_df = filtered_ot_df.merge(
        fda_df,
        on='fda_drug_name',
        how='left'
    )
    
    # Add severity weights
    severity_weights = {
        'Most-DILI-Concern': 2.0,
        'Less-DILI-Concern': 1.0, 
        'No-DILI-Concern': 0.0,
        'Ambiguous-DILI-Concern': 0.5
    }
    
    merged_df['dili_severity_weight'] = merged_df['fda_dili_concern'].map(
        severity_weights
    ).fillna(0)
    
    # Ensure unique column names
    if 'drugId' in merged_df.columns:
        merged_df = merged_df.rename(columns={'drugId': 'ot_drug_id'})
    if 'targetId' in merged_df.columns:
        merged_df = merged_df.rename(columns={'targetId': 'ot_target_id'})
    
    # Deduplicate to unique drug-target pairs for downstream use
    dedup_cols = ['fda_drug_name', 'target_symbol']
    merged_df = merged_df.drop_duplicates(subset=dedup_cols, keep='first').reset_index(drop=True)
    logger.info(f"Deduplicated to {len(merged_df)} unique drug-target pairs")
    logger.info(f"Covering {merged_df['fda_drug_name'].nunique()} unique FDA drugs")
    logger.info(f"Covering {merged_df['target_symbol'].nunique()} unique targets")
    
    return merged_df 