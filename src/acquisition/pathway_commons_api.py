"""
Pathway Commons API client for network data.

This module provides functionality to query Pathway Commons for protein-protein
interaction networks and pathway data.
"""

import logging
import json
from typing import Dict, List, Optional, Set
import pandas as pd
import requests
import networkx as nx

logger = logging.getLogger(__name__)


class PathwayCommonsAPI:
    """Client for Pathway Commons API."""

    def __init__(self, base_url: str = "https://www.pathwaycommons.org/pc2/"):
        """Initialize the API client.
        
        Args:
            base_url: Pathway Commons API base URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Target-DILI-Risk-Score/1.0'
        })
    
    def get_interactions(self, source_ids: List[str], target_ids: Optional[List[str]] = None) -> pd.DataFrame:
        """Get protein-protein interactions.
        
        Args:
            source_ids: List of source protein IDs (UniProt)
            target_ids: Optional list of target protein IDs
            
        Returns:
            DataFrame with interaction data
        """
        endpoint = f"{self.base_url}graph"
        
        params = {
            'source': ','.join(source_ids),
            'kind': 'PATHSBETWEEN',
            'format': 'json'
        }
        
        if target_ids:
            params['target'] = ','.join(target_ids)
        
        logger.info(f"Querying interactions for {len(source_ids)} source proteins")
        
        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            interactions = self._parse_interactions(data)
            
            df = pd.DataFrame(interactions)
            logger.info(f"Retrieved {len(df)} interactions")
            
            return df
            
        except Exception as e:
            logger.error(f"Error querying Pathway Commons: {e}")
            return pd.DataFrame()
    
    def _parse_interactions(self, data: Dict) -> List[Dict]:
        """Parse interaction data from API response.
        
        Args:
            data: API response data
            
        Returns:
            List of interaction dictionaries
        """
        interactions = []
        
        if 'graph' not in data:
            return interactions
        
        graph = data['graph']
        
        if 'edges' in graph:
            for edge in graph['edges']:
                interaction = {
                    'source_id': edge.get('source', ''),
                    'target_id': edge.get('target', ''),
                    'interaction_type': edge.get('interactionType', ''),
                    'data_source': edge.get('dataSource', ''),
                    'score': edge.get('score', 0.0)
                }
                interactions.append(interaction)
        
        return interactions
    
    def build_protein_network(self, protein_ids: List[str]) -> nx.Graph:
        """Build a protein interaction network.
        
        Args:
            protein_ids: List of protein IDs
            
        Returns:
            NetworkX graph object
        """
        logger.info(f"Building network for {len(protein_ids)} proteins")
        
        # Get interactions
        interactions_df = self.get_interactions(protein_ids)
        
        if interactions_df.empty:
            logger.warning("No interactions found, returning empty graph")
            return nx.Graph()
        
        # Build NetworkX graph
        G = nx.Graph()
        
        for _, row in interactions_df.iterrows():
            source = row['source_id']
            target = row['target_id']
            weight = row.get('score', 1.0)
            
            G.add_edge(source, target, weight=weight)
        
        logger.info(f"Built network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        
        return G
    
    def get_network_metrics(self, G: nx.Graph) -> pd.DataFrame:
        """Calculate network metrics for proteins.
        
        Args:
            G: NetworkX graph
            
        Returns:
            DataFrame with network metrics per protein
        """
        if G.number_of_nodes() == 0:
            return pd.DataFrame()
        
        metrics = []
        
        for node in G.nodes():
            # Centrality measures
            degree_cent = nx.degree_centrality(G).get(node, 0.0)
            betweenness_cent = nx.betweenness_centrality(G).get(node, 0.0)
            closeness_cent = nx.closeness_centrality(G).get(node, 0.0)
            eigenvector_cent = nx.eigenvector_centrality_numpy(G).get(node, 0.0)
            
            # Clustering coefficient
            clustering_coef = nx.clustering(G, node)
            
            # Average shortest path length to other nodes
            try:
                avg_path_length = nx.average_shortest_path_length(G, source=node)
            except nx.NetworkXError:
                avg_path_length = float('inf')
            
            metrics.append({
                'protein_id': node,
                'degree_centrality': degree_cent,
                'betweenness_centrality': betweenness_cent,
                'closeness_centrality': closeness_cent,
                'eigenvector_centrality': eigenvector_cent,
                'clustering_coefficient': clustering_coef,
                'avg_path_length': avg_path_length
            })
        
        df = pd.DataFrame(metrics)
        logger.info(f"Calculated metrics for {len(df)} proteins")
        
        return df
    
    def get_pathways(self, protein_ids: List[str]) -> pd.DataFrame:
        """Get pathway information for proteins.
        
        Args:
            protein_ids: List of protein IDs
            
        Returns:
            DataFrame with pathway data
        """
        endpoint = f"{self.base_url}graph"
        
        params = {
            'source': ','.join(protein_ids),
            'kind': 'NEIGHBORHOOD',
            'format': 'json'
        }
        
        logger.info(f"Querying pathways for {len(protein_ids)} proteins")
        
        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            pathways = self._parse_pathways(data)
            
            df = pd.DataFrame(pathways)
            logger.info(f"Retrieved {len(df)} pathway associations")
            
            return df
            
        except Exception as e:
            logger.error(f"Error querying pathways: {e}")
            return pd.DataFrame()
    
    def _parse_pathways(self, data: Dict) -> List[Dict]:
        """Parse pathway data from API response.
        
        Args:
            data: API response data
            
        Returns:
            List of pathway dictionaries
        """
        pathways = []
        
        if 'graph' not in data:
            return pathways
        
        graph = data['graph']
        
        if 'nodes' in graph:
            for node in graph['nodes']:
                if 'pathway' in node.get('type', ''):
                    pathway = {
                        'pathway_id': node.get('id', ''),
                        'pathway_name': node.get('name', ''),
                        'data_source': node.get('dataSource', ''),
                        'pathway_type': node.get('type', '')
                    }
                    pathways.append(pathway)
        
        return pathways

    def query_neighborhood_v2(self, ids: List[str], format: str = "BINARY_SIF", limit: int = 100) -> pd.DataFrame:
        """Query Pathway Commons v2 /neighborhood endpoint (POST).
        Args:
            ids: List of gene/protein IDs (HGNC, UniProt, etc.)
            format: Output format (default: BINARY_SIF)
            limit: Max number of neighbors
        Returns:
            DataFrame with interaction data
        """
        endpoint = f"{self.base_url}v2/neighborhood"
        payload = {
            "source": ids,
            "format": format,
            "limit": limit
        }
        try:
            resp = self.session.post(endpoint, json=payload, timeout=60)
            resp.raise_for_status()
            if format == "BINARY_SIF":
                return self._parse_binary_sif(resp.text)
            else:
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error in /v2/neighborhood: {e}")
            return pd.DataFrame()

    def query_pathbetween_v2(self, source_ids: List[str], target_ids: List[str], format: str = "BINARY_SIF") -> pd.DataFrame:
        """Query Pathway Commons v2 /pathbetween endpoint (POST).
        Args:
            source_ids: List of source gene/protein IDs
            target_ids: List of target gene/protein IDs
            format: Output format (default: BINARY_SIF)
        Returns:
            DataFrame with interaction data
        """
        endpoint = f"{self.base_url}v2/pathbetween"
        payload = {
            "source": source_ids,
            "target": target_ids,
            "format": format
        }
        try:
            resp = self.session.post(endpoint, json=payload, timeout=60)
            resp.raise_for_status()
            if format == "BINARY_SIF":
                return self._parse_binary_sif(resp.text)
            else:
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error in /v2/pathbetween: {e}")
            return pd.DataFrame()

    def _parse_binary_sif(self, sif_text: str) -> pd.DataFrame:
        """Parse BINARY_SIF format into DataFrame.
        Args:
            sif_text: SIF string
        Returns:
            DataFrame with columns: source, interaction, target
        """
        rows = []
        for line in sif_text.strip().split("\n"):
            parts = line.strip().split("\t")
            if len(parts) == 3:
                rows.append({
                    "source": parts[0],
                    "interaction": parts[1],
                    "target": parts[2]
                })
        return pd.DataFrame(rows)


if __name__ == "__main__":
    # Example usage
    import yaml
    
    with open("config/config.yml", "r") as f:
        config = yaml.safe_load(f)
    
    api = PathwayCommonsAPI(base_url=config["apis"]["pathway_commons"]["base_url"])
    
    # Example protein IDs (UniProt)
    protein_ids = ["P04637", "P53_HUMAN", "Q9Y6K9"]  # p53, NFKB1
    
    # Get network
    network = api.build_protein_network(protein_ids)
    
    # Calculate metrics
    metrics_df = api.get_network_metrics(network)
    
    # Save to interim data
    metrics_df.to_parquet("data/interim/network_metrics.parquet", index=False)
    print(f"Saved network metrics for {len(metrics_df)} proteins") 