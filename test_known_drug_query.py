#!/usr/bin/env python3
"""
Test script to query OpenTargets known_drug table.
"""

import yaml
import pandas as pd
from google.cloud import bigquery
from google.auth import default
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_known_drug_query():
    """Test querying the known_drug table."""
    
    # Load config
    with open("config/config.yml", "r") as f:
        config = yaml.safe_load(f)
    
    project_id = config['bigquery']['project_id']
    dataset = config['bigquery']['dataset']
    
    logger.info(f"Testing BigQuery connection to project: {project_id}")
    
    # Initialize BigQuery client
    try:
        credentials, default_project = default()
        logger.info(f"Using credentials for project: {default_project}")
        
        client = bigquery.Client(project=project_id, credentials=credentials)
        logger.info("BigQuery client initialized successfully")
        
        # Test 1: List tables
        logger.info("Testing table listing...")
        tables_query = f"""
        SELECT table_name
        FROM `{dataset}.INFORMATION_SCHEMA.TABLES`
        WHERE table_name = 'known_drug'
        """
        
        tables_df = client.query(tables_query).to_dataframe()
        logger.info(f"Found known_drug table: {len(tables_df)} rows")
        
        # Test 2: Check schema
        logger.info("Testing schema inspection...")
        schema_query = f"""
        SELECT column_name, data_type
        FROM `{dataset}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = 'known_drug'
        ORDER BY ordinal_position
        """
        
        schema_df = client.query(schema_query).to_dataframe()
        logger.info(f"Schema columns: {schema_df['column_name'].tolist()}")
        
        # Test 3: Simple query without LIMIT
        logger.info("Testing simple query...")
        simple_query = f"""
        SELECT COUNT(*) as total_rows
        FROM `{dataset}.known_drug`
        """
        
        count_df = client.query(simple_query).to_dataframe()
        total_rows = count_df['total_rows'].iloc[0]
        logger.info(f"Total rows in known_drug: {total_rows}")
        
        # Test 4: Query with LIMIT
        logger.info("Testing query with LIMIT...")
        limit_query = f"""
        SELECT drugId, prefName, targetId, approvedSymbol
        FROM `{dataset}.known_drug`
        LIMIT 5
        """
        
        result_df = client.query(limit_query).to_dataframe()
        logger.info(f"Query with LIMIT successful: {len(result_df)} rows")
        print("\nSample data:")
        print(result_df)
        
        return result_df
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_known_drug_query() 