"""
Simple validation for DILI risk scores.

Validates DILI risk scores against drug approval rates from OpenFDA
to assess the biological relevance of the risk scores.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

from .metrics import compute_approval_rates, compute_withdrawal_rates
from .report import generate_validation_report
from .plots import plot_risk_vs_approval, plot_risk_vs_withdrawal

logger = logging.getLogger(__name__)


class Validator:
    """Simple validator for DILI risk scores against approval rates."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize approval validator.
        
        Args:
            data_dir: Path to data directory
        """
        self.data_dir = Path(data_dir)
        self.processed_dir = self.data_dir / "processed"
        self.results_dir = Path("results")
        
        # Ensure results directory exists
        self.results_dir.mkdir(exist_ok=True)
    
    def run_validation(self) -> pd.DataFrame:
        """Run complete validation pipeline.
        
        Returns:
            DataFrame with validation results
        """
        logger = logging.getLogger(__name__)
        logger.info("=== Running DILI Risk Score Validation ===")
        
        # Load drug-target table
        drug_target_path = self.processed_dir / "drug_target_table.parquet"
        if not drug_target_path.exists():
            logger.error("Drug-target table not found. Run ETL first.")
            return pd.DataFrame()
        
        drug_target_df = pd.read_parquet(drug_target_path)
        
        # Load risk scores
        risk_scores_path = self.processed_dir / "dili_risk_scores.parquet"
        if not risk_scores_path.exists():
            logger.error("DILI risk scores not found. Run risk scoring first.")
            return pd.DataFrame()
        
        risk_scores = pd.read_parquet(risk_scores_path)
        risk_scores = risk_scores.set_index('ot_target_symbol')
        
        # Compute approval rates
        approval_rates = compute_approval_rates(drug_target_df)
        # Compute withdrawal rates
        withdrawal_rates = compute_withdrawal_rates(drug_target_df)
        # Validate risk scores
        validation_df = risk_scores.merge(approval_rates, left_index=True, right_index=True, how='inner')
        if not withdrawal_rates.empty:
            validation_df = validation_df.merge(
                withdrawal_rates[['withdrawal_rate']], left_index=True, right_index=True, how='left'
            )
        # Correlation with approval
        validation_df['correlation_with_approval'] = validation_df['dili_risk_score'].corr(validation_df['approval_rate'])
        # Correlation with withdrawal
        if 'withdrawal_rate' in validation_df.columns:
            validation_df['correlation_with_withdrawal'] = validation_df['dili_risk_score'].corr(validation_df['withdrawal_rate'])
        # Report
        report_path = self.results_dir / "validation_report.txt"
        generate_validation_report(validation_df, report_path)
        # Save validation results
        output_path = self.processed_dir / "validation_results.parquet"
        validation_df.to_parquet(output_path, index=False)
        logger.info(f"Saved validation results to {output_path}")
        # Plots
        plot_risk_vs_approval(validation_df)
        plot_risk_vs_withdrawal(validation_df)
        logger.info("=== Validation Complete ===")
        
        return validation_df 