"""
ETL module for Target DILI Risk Score.

This module contains the components for data extraction, transformation, and loading:
- Drug name utilities
- OpenFDA data processing
- Drug-target table building
- Network building
"""

from .etl import ETL
from .drug_utils import normalize_drug_name
from .openfda_processor import (
    parse_openfda_bulk_data,
    create_drug_approval_lookup,
    match_drugs_to_approval_status,
    fetch_openfda_approval_status
)
from .drug_target_builder import DrugTargetBuilder
from .network_builder import NetworkBuilder

__all__ = [
    'ETL',
    'normalize_drug_name',
    'parse_openfda_bulk_data',
    'create_drug_approval_lookup',
    'match_drugs_to_approval_status',
    'fetch_openfda_approval_status',
    'DrugTargetBuilder',
    'NetworkBuilder'
] 