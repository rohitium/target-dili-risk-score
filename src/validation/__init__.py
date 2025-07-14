"""
Simple validation for Target DILI Risk Score.

This module validates DILI risk scores against drug approval rates
from OpenFDA to assess the biological relevance of the risk scores.
"""

from .validator import Validator

__all__ = ['Validator'] 