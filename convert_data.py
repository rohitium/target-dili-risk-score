#!/usr/bin/env python3
"""
Convert parquet data to JSON for the web app.
Works from both root and docs/ directories.
"""

import pandas as pd
import json
from pathlib import Path

def convert_data():
    """Convert parquet data to JSON for web app."""
    
    # Try different possible paths for the data file
    possible_paths = [
        Path("data/processed/dili_risk_scores.parquet"),  # From root
        Path("../data/processed/dili_risk_scores.parquet"),  # From docs/
        Path("../../data/processed/dili_risk_scores.parquet")  # From subdir
    ]
    
    data_path = None
    for path in possible_paths:
        if path.exists():
            data_path = path
            break
    
    if not data_path:
        print("❌ Error: Could not find dili_risk_scores.parquet")
        print("Please run the pipeline first: python main.py")
        return False
    
    print(f"📊 Found data at: {data_path}")
    
    # Read the risk scores data
    df = pd.read_parquet(data_path)
    
    # Convert to JSON format
    data = []
    for _, row in df.iterrows():
        data.append({
            'target_symbol': row['ot_target_symbol'],
            'drug_count': int(row['drug_count']),
            'total_dili_weight': float(row['total_dili_weight']),
            'high_risk_drug_count': int(row['high_risk_drug_count']),
            'dili_risk_ratio': float(row['dili_risk_ratio']),
            'avg_dili_weight': float(row['avg_dili_weight']),
            'network_dili_score': float(row['network_dili_score']),
            'dili_risk_score': float(row['dili_risk_score']),
            'risk_category': row['risk_category']
        })
    
    # Save to JSON files in both locations
    output_paths = [
        Path("data.json"),  # Root directory
        Path("docs/data.json")  # Docs directory
    ]
    
    for output_path in output_paths:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Saved {len(data)} records to {output_path}")
    
    # Print some statistics
    print(f"\n📊 Statistics:")
    print(f"Total targets: {len(data)}")
    print(f"Risk categories: {df['risk_category'].value_counts().to_dict()}")
    print(f"Score range: {df['dili_risk_score'].min():.4f} - {df['dili_risk_score'].max():.4f}")
    
    return True

if __name__ == "__main__":
    success = convert_data()
    exit(0 if success else 1) 