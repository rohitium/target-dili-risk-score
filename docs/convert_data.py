#!/usr/bin/env python3
"""
Convert parquet data to JSON for the web app.
"""

import pandas as pd
import json
from pathlib import Path

def convert_data():
    """Convert parquet data to JSON for web app."""
    
    # Read the risk scores data
    data_path = Path("../data/processed/dili_risk_scores.parquet")
    
    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        return
    
    df = pd.read_parquet(data_path)
    
    # Convert to JSON format
    data = []
    for _, row in df.iterrows():
        data.append({
            'target_symbol': row['target_symbol'],
            'drug_count': int(row['drug_count']),
            'total_dili_weight': float(row['total_dili_weight']),
            'high_risk_drug_count': int(row['high_risk_drug_count']) if pd.notna(row['high_risk_drug_count']) else 0,
            'dili_risk_ratio': float(row['dili_risk_ratio']),
            'avg_dili_weight': float(row['avg_dili_weight']),
            'network_dili_score': float(row['network_dili_score']),
            'dili_risk_score': float(row['dili_risk_score']),
            'risk_category': row['risk_category']
        })
    
    # Save to JSON file
    output_path = Path("data.json")
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Converted {len(data)} records to {output_path}")
    
    # Print some statistics
    print(f"\nStatistics:")
    print(f"Total targets: {len(data)}")
    print(f"Risk categories: {df['risk_category'].value_counts().to_dict()}")
    print(f"Score range: {df['dili_risk_score'].min():.4f} - {df['dili_risk_score'].max():.4f}")

if __name__ == "__main__":
    convert_data() 