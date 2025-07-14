"""
ETL for Target DILI Risk Score.

This module builds the core data tables needed for DILI risk assessment:
- Drug-target associations with DILIrank data and OpenFDA approval status
- Target-target network from Pathway Commons
"""

from .etl import ETL

__all__ = ['ETL'] 