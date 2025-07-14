#!/usr/bin/env python3
"""
Target DILI Risk Score Pipeline - Main Script

A simple, biologically relevant pipeline for computing liver injury risk scores
for drug targets based on direct DILI evidence and network guilt-by-association.
"""

import logging
import sys
from pathlib import Path
import yaml
from src.acquisition.acquire_all import acquire_all

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from etl.etl import ETL
from features.dili_risk_scorer import DILIRiskScorer
from validation.validator import Validator


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pipeline.log')
        ]
    )


def main():
    """Run the complete DILI risk score pipeline."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=== Target DILI Risk Score Pipeline ===")
    logger.info("Simple, biologically relevant risk scoring for drug targets")

    # Load config
    with open("config/config.yml", "r") as f:
        config = yaml.safe_load(f)

    try:
        # Step 0: Data Acquisition
        logger.info("\n--- Step 0: Data Acquisition ---")
        acquire_all(config)

        # Step 1: ETL - Build drug-target and target-target tables
        logger.info("\n--- Step 1: ETL Pipeline ---")
        etl = ETL()
        etl_results = etl.run_etl()
        
        if etl_results['drug_target_table'].empty:
            logger.error("ETL failed - no drug-target data available")
            return
        
        # Step 2: Risk Scoring - Compute DILI risk scores
        logger.info("\n--- Step 2: Risk Scoring ---")
        risk_scorer = DILIRiskScorer(alpha=0.5)  # 50% weight to network evidence
        risk_scores = risk_scorer.score_targets()
        
        if risk_scores.empty:
            logger.error("Risk scoring failed - no risk scores computed")
            return
        
        # Step 3: Validation - Validate against approval rates
        logger.info("\n--- Step 3: Validation ---")
        validator = Validator()
        validation_results = validator.run_validation()
        
        if validation_results.empty:
            logger.error("Validation failed - no validation results")
            return
        
        # Pipeline complete
        logger.info("\n=== Pipeline Complete ===")
        logger.info("Results saved to:")
        logger.info("  - data/processed/dili_risk_scores.parquet")
        logger.info("  - data/processed/validation_results.parquet")
        logger.info("  - results/validation_report.txt")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        raise


if __name__ == "__main__":
    main() 