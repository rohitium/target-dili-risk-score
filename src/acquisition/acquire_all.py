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

def acquire_all(config):
    acquire_opentargets(config)
    acquire_pathway_commons()
    acquire_fda_dilirank()
    acquire_openfda()
    logging.info("All acquisition steps complete.") 