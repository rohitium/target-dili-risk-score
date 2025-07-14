"""
Orchestrate all data acquisition for the Target DILI Risk Score pipeline.
Downloads/queries all raw data needed for a full pipeline run.
"""
import logging
from pathlib import Path

def acquire_opentargets(config):
    from .opentargets_bigquery import OpenTargetsBigQuery
    project_id = config['bigquery']['project_id']
    dataset = config['bigquery']['dataset']
    disease_ids = config['liver_injury']['disease_ids']
    client = OpenTargetsBigQuery(project_id, dataset)
    df = client.query_liver_injury_evidence(disease_ids)
    out_path = Path('data/interim/liver_injury_evidence.parquet')
    df.to_parquet(out_path, index=False)
    logging.info(f"Saved OpenTargets evidence to {out_path}")
    return out_path

def acquire_pathway_commons():
    from .pathway_commons_local import build_all
    build_all()  # Downloads and processes SIF/mapping files
    logging.info("Downloaded and processed Pathway Commons data")

def acquire_fda_dilirank():
    from .fda_dilirank_scraper import download_and_parse_dilirank
    download_and_parse_dilirank()
    out_path = Path('data/interim/fda_dilirank.parquet')
    if out_path.exists():
        logging.info(f"Downloaded and processed FDA DILIrank to {out_path}")
    else:
        logging.warning(f"FDA DILIrank output not found at {out_path}")
    return out_path

def acquire_openfda():
    # User must download OpenFDA bulk JSON manually due to TOS
    # Place at data/raw/drug-drugsfda-0001-of-0001.json
    path = Path('data/raw/drug-drugsfda-0001-of-0001.json')
    if not path.exists():
        logging.warning(f"OpenFDA bulk JSON not found at {path}. Please download manually from https://open.fda.gov/data/downloads/")
    else:
        logging.info(f"OpenFDA bulk JSON found at {path}")
    return path

def acquire_drug_target_associations(config):
    """Acquire drug-target associations from OpenTargets and create clean mapping."""
    from .opentargets_bigquery import OpenTargetsBigQuery
    import sys
    sys.path.append('src/utils')
    from drug_matching import match_fda_to_opentargets_drugs, validate_drug_matches, create_drug_target_mapping
    import pandas as pd
    
    project_id = config['bigquery']['project_id']
    dataset = config['bigquery']['dataset']
    client = OpenTargetsBigQuery(project_id, dataset)
    
    # Load FDA DILIrank data
    fda_dilirank_path = Path('data/interim/fda_dilirank.parquet')
    if not fda_dilirank_path.exists():
        logging.error("FDA DILIrank data not found. Run acquire_fda_dilirank() first.")
        return None
    
    fda_dilirank_df = pd.read_parquet(fda_dilirank_path)
    fda_drugs = fda_dilirank_df['Compound Name'].unique().tolist()
    logging.info(f"Loaded {len(fda_drugs)} FDA DILIrank drugs")
    
    # Query OpenTargets drugs
    ot_drugs_df = client.query_drugs()
    if ot_drugs_df.empty:
        logging.error("Failed to query OpenTargets drugs")
        return None
    
    ot_drugs = ot_drugs_df['drug_name'].unique().tolist()
    logging.info(f"Retrieved {len(ot_drugs)} OpenTargets drugs")
    
    # Match FDA drugs to OpenTargets drugs
    matches = match_fda_to_opentargets_drugs(fda_drugs, ot_drugs, threshold=0.8)
    validate_drug_matches(matches)
    
    # Query drug-target associations for matched drugs
    matched_ot_drugs = list(matches.values())
    ot_drug_target_df = client.query_drug_target_associations_for_drugs(matched_ot_drugs)
    
    if ot_drug_target_df.empty:
        logging.error("Failed to query drug-target associations")
        return None
    
    # Create clean drug-target mapping
    clean_mapping_df = create_drug_target_mapping(fda_dilirank_df, ot_drug_target_df, matches)
    
    # Save clean mapping
    out_path = Path('data/interim/drug_target_mapping_clean.parquet')
    clean_mapping_df.to_parquet(out_path, index=False)
    logging.info(f"Saved clean drug-target mapping to {out_path}")
    
    return out_path

def acquire_all(config):
    acquire_opentargets(config)
    acquire_pathway_commons()
    acquire_fda_dilirank()
    acquire_openfda()
    acquire_drug_target_associations(config)
    logging.info("All acquisition steps complete.") 