"""
OpenTargets BigQuery client for querying liver injury data.

This module provides functionality to query OpenTargets data from BigQuery
to extract target-disease associations for liver injury endpoints.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
from google.cloud import bigquery
from google.auth import default

logger = logging.getLogger(__name__)


class OpenTargetsBigQuery:
    """
    Client for querying OpenTargets data from BigQuery.
    """
    
    def __init__(self, project_id: str, dataset: str):
        self.project_id = project_id
        self.dataset = dataset
        
        # Set up BigQuery client with proper authentication
        try:
            # Try to get default credentials
            credentials, default_project = default()
            
            # If no project ID was determined, use the one from config
            if not default_project:
                os.environ['GOOGLE_CLOUD_PROJECT'] = project_id
                logger.info(f"Set GOOGLE_CLOUD_PROJECT to {project_id}")
            
            self.client = bigquery.Client(
                project=project_id,
                credentials=credentials
            )
            logger.info(f"BigQuery client initialized for project: {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            raise
    
    def query_liver_injury_evidence(self, disease_ids: List[str], disease_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Query liver injury evidence from OpenTargets.
        
        Args:
            disease_ids: List of disease IDs to query
            disease_names: Optional list of disease names for logging
            
        Returns:
            DataFrame with liver injury evidence
        """
        if disease_names is None:
            disease_names = [f"Disease_{i}" for i in range(len(disease_ids))]
        
        logger.info(f"Querying liver injury evidence for diseases: {list(zip(disease_ids, disease_names))}")
        
        # Build the query
        disease_conditions = " OR ".join([f"e.diseaseId = '{disease_id}'" for disease_id in disease_ids])
        
        query = f"""
        SELECT 
            e.targetId,
            t.approvedSymbol as target_name,
            e.diseaseId as disease_id,
            d.name as disease_name,
            e.score,
            e.datatypeId as datatype,
            e.literature
        FROM `{self.dataset}.evidence` e
        JOIN `{self.dataset}.target` t ON e.targetId = t.id
        JOIN `{self.dataset}.disease` d ON e.diseaseId = d.id
        WHERE ({disease_conditions})
        AND e.score > 0
        ORDER BY e.score DESC
        LIMIT 10000
        """
        
        try:
            df = self.client.query(query).to_dataframe()
            logger.info(f"Retrieved {len(df)} evidence records")
            return df
        except Exception as e:
            logger.error(f"Failed to query liver injury evidence: {e}")
            return pd.DataFrame()
    
    def query_all_targets(self) -> pd.DataFrame:
        """Query all targets from OpenTargets.
        
        Returns:
            DataFrame with target information
        """
        query = f"""
        SELECT 
            id,
            approvedSymbol,
            approvedName,
            biotype,
            functionDescriptions,
            subcellularLocations
        FROM `{self.dataset}.target`
        WHERE approvedSymbol IS NOT NULL
        """
        
        logger.info("Querying all targets")
        df = self.client.query(query).to_dataframe()
        logger.info(f"Retrieved {len(df)} targets")
        
        return df
    
    def query_target_disease_associations(self, target_ids: List[str]) -> pd.DataFrame:
        """Query disease associations for specific targets.
        
        Args:
            target_ids: List of target IDs
            
        Returns:
            DataFrame with target-disease associations
        """
        query = f"""
        SELECT 
            e.targetId,
            e.diseaseId,
            e.score,
            e.datatypeId,
            d.name as disease_name,
            d.therapeuticAreas
        FROM `{self.dataset}.evidence` e
        JOIN `{self.dataset}.disease` d 
            ON e.diseaseId = d.id
        WHERE e.targetId IN ({','.join([f"'{t}'" for t in target_ids])})
        AND e.score > 0.1
        """
        
        logger.info(f"Querying disease associations for {len(target_ids)} targets")
        df = self.client.query(query).to_dataframe()
        logger.info(f"Retrieved {len(df)} associations")
        
        return df
    
    def query_drug_target_associations(self) -> pd.DataFrame:
        """
        Query drug-target associations from OpenTargets.
        
        Returns:
            DataFrame with drug-target associations
        """
        logger.info("Querying drug-target associations")
        
        query = f"""
        SELECT 
            e.targetId,
            t.approvedSymbol as target_name,
            e.diseaseId as disease_id,
            d.name as disease_name,
            e.score,
            e.datatypeId as datatype,
            e.literature
        FROM `{self.dataset}.evidence` e
        JOIN `{self.dataset}.target` t ON e.targetId = t.id
        JOIN `{self.dataset}.disease` d ON e.diseaseId = d.id
        WHERE e.datatypeId IN ('known_drug', 'clinical_trial')
        AND e.score > 0
        ORDER BY e.score DESC
        LIMIT 100000
        """
        
        try:
            df = self.client.query(query).to_dataframe()
            logger.info(f"Retrieved {len(df)} drug-target associations")
            return df
        except Exception as e:
            logger.error(f"Failed to query drug-target associations: {e}")
            return pd.DataFrame()


if __name__ == "__main__":
    # Example usage
    import yaml
    
    with open("config/config.yml", "r") as f:
        config = yaml.safe_load(f)
    
    client = OpenTargetsBigQuery(
        project_id=config["bigquery"]["project_id"],
        dataset=config["bigquery"]["dataset"]
    )
    
    # Query liver injury evidence
    liver_evidence = client.query_liver_injury_evidence(
        config["liver_injury"]["disease_ids"]
    )
    
    # Save to interim data
    liver_evidence.to_parquet("data/interim/liver_injury_evidence.parquet", index=False)
    print(f"Saved {len(liver_evidence)} liver injury evidence records") 