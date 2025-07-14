"""
Drug Name Utilities.

Provides utilities for normalizing and matching drug names
across different data sources.
"""

import re
import logging

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
    # Convert to lowercase, remove extra spaces, remove common suffixes
    normalized = name.lower().strip()
    normalized = re.sub(r'\s+', ' ', normalized)  # Multiple spaces to single
    normalized = re.sub(r'\b(hcl|hydrochloride|sulfate|citrate|phosphate|acetate|sodium|potassium|calcium|magnesium)\b', '', normalized)
    normalized = normalized.strip()
    return normalized 