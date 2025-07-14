import os
import gzip
import requests
import pandas as pd
import networkx as nx
from tqdm import tqdm
import pickle

DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data/raw')
SIF_URL = 'https://download.baderlab.org/PathwayCommons/PC2/v14/pc-hgnc.sif.gz'
SIF_PATH = os.path.join(DATA_DIR, 'pc-hgnc.sif.gz')
MAPPING_URL = 'https://download.baderlab.org/PathwayCommons/PC2/v14/pc-hgnc.txt.gz'
MAPPING_PATH = os.path.join(DATA_DIR, 'pc-hgnc.txt.gz')
UNIPROT_URL = 'https://download.baderlab.org/PathwayCommons/PC2/v14/uniprot.txt'
UNIPROT_PATH = os.path.join(DATA_DIR, 'uniprot.txt')
GRAPH_PICKLE = os.path.join(DATA_DIR, 'pc-hgnc_graph.pkl')
MAP_PICKLE = os.path.join(DATA_DIR, 'pc-hgnc_map.pkl')
GMT_PATH = os.path.join(DATA_DIR, 'pc-hgnc.gmt.gz')

os.makedirs(DATA_DIR, exist_ok=True)

def download_file(url, path):
    if not os.path.exists(path):
        print(f"Downloading {url} ...")
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in tqdm(r.iter_content(1024*1024), desc=f"{os.path.basename(path)}", unit='MB'):
                f.write(chunk)
    else:
        print(f"{path} already exists.")

def parse_sif(path):
    print(f"Parsing SIF: {path}")
    G = nx.Graph()
    with gzip.open(path, 'rt') as f:
        for line in tqdm(f, desc="SIF lines"):
            parts = line.strip().split('\t')
            if len(parts) == 3:
                a, interaction, b = parts
                G.add_edge(a, b, interaction=interaction)
    return G

def parse_mapping(path):
    print(f"Parsing mapping: {path}")
    with gzip.open(path, 'rt') as f:
        df = pd.read_csv(f, sep='\t', dtype=str)
    return df

def parse_uniprot(path):
    print(f"Parsing UniProt mapping: {path}")
    df = pd.read_csv(path, sep='\t', dtype=str)
    return df

def build_all():
    download_file(SIF_URL, SIF_PATH)
    download_file(MAPPING_URL, MAPPING_PATH)
    download_file(UNIPROT_URL, UNIPROT_PATH)
    G = parse_sif(SIF_PATH)
    mapping_df = parse_mapping(MAPPING_PATH)
    uniprot_df = parse_uniprot(UNIPROT_PATH)
    with open(GRAPH_PICKLE, 'wb') as f:
        pickle.dump(G, f)
    with open(MAP_PICKLE, 'wb') as f:
        pickle.dump({'mapping': mapping_df, 'uniprot': uniprot_df}, f)
    print(f"Saved graph to {GRAPH_PICKLE} and mapping to {MAP_PICKLE}")

def load_graph():
    with open(GRAPH_PICKLE, 'rb') as f:
        return pickle.load(f)

def load_mapping():
    with open(MAP_PICKLE, 'rb') as f:
        return pickle.load(f)

def get_neighbors(g, node):
    return list(g.neighbors(node)) if node in g else []

def get_degree(g, node):
    return g.degree[node] if node in g else 0

def shortest_path(g, source, target):
    try:
        return nx.shortest_path(g, source, target)
    except Exception:
        return None

def map_gene(mapping, query):
    # Try symbol, HGNC, UniProt, Ensembl
    df = mapping['mapping']
    hits = df[(df['NAME'] == query) | (df['HGNC_ID'] == query) | (df['UNIPROT'] == query) | (df['ENSEMBL'] == query)]
    if not hits.empty:
        return hits.iloc[0].to_dict()
    return None

def main():
    build_all()
    G = load_graph()
    mapping = load_mapping()
    print(f"Graph nodes: {len(G.nodes())}, edges: {len(G.edges())}")
    # Example: get neighbors for ALB
    print("Neighbors of ALB:", get_neighbors(G, 'ALB'))
    print("Degree of ALB:", get_degree(G, 'ALB'))
    print("Shortest path ALB <-> CYP2E1:", shortest_path(G, 'ALB', 'CYP2E1'))
    print("Mapping for ALB:", map_gene(mapping, 'ALB'))

if __name__ == "__main__":
    main() 