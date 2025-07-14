#!/usr/bin/env python3
"""
Test script for the web app functionality.
"""

import json
import requests
from pathlib import Path

def test_webapp():
    """Test the web app functionality."""
    
    print("🧪 Testing DILI Risk Score Checker Web App")
    print("=" * 50)
    
    # Check if data.json exists
    data_file = Path("docs/data.json")
    if not data_file.exists():
        print("❌ Error: data.json not found")
        print("Run: python docs/convert_data.py")
        return False
    
    # Load and validate data
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        print(f"✅ Loaded {len(data)} targets from data.json")
        
        # Check data structure
        if not data:
            print("❌ Error: No data found")
            return False
        
        sample = data[0]
        required_fields = ['target_symbol', 'drug_count', 'dili_risk_score', 'risk_category']
        
        for field in required_fields:
            if field not in sample:
                print(f"❌ Error: Missing field '{field}' in data")
                return False
        
        print("✅ Data structure is valid")
        
        # Test some sample targets
        test_targets = ['CYP3A4', 'ACE', 'ACHE', 'ADORA1', 'ADRA1A']
        found_targets = []
        
        for target in test_targets:
            found = any(t['target_symbol'] == target for t in data)
            if found:
                found_targets.append(target)
                print(f"✅ Found target: {target}")
            else:
                print(f"⚠️  Target not found: {target}")
        
        # Show statistics
        risk_categories = {}
        for target in data:
            category = target['risk_category']
            risk_categories[category] = risk_categories.get(category, 0) + 1
        
        print(f"\n📊 Risk Category Distribution:")
        for category, count in risk_categories.items():
            percentage = (count / len(data)) * 100
            print(f"  {category}: {count} targets ({percentage:.1f}%)")
        
        # Show score range
        scores = [t['dili_risk_score'] for t in data]
        print(f"\n📈 Score Range: {min(scores):.4f} - {max(scores):.4f}")
        
        print(f"\n🎉 Web app test completed successfully!")
        print(f"Found {len(found_targets)}/{len(test_targets)} test targets")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing web app: {e}")
        return False

if __name__ == "__main__":
    success = test_webapp()
    exit(0 if success else 1) 