#!/usr/bin/env python3
"""
Setup script for GitHub Pages deployment.
"""

import subprocess
import sys
from pathlib import Path

def setup_github_pages():
    """Setup GitHub Pages for the web app."""
    
    print("🚀 Setting up GitHub Pages for DILI Risk Score Checker")
    print("=" * 60)
    
    # Check if we're in a git repository
    try:
        subprocess.run(["git", "status"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ Error: Not in a git repository")
        print("Please run: git init")
        return False
    
    # Check if docs directory exists
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("❌ Error: docs/ directory not found")
        return False
    
    # Check if required files exist
    required_files = ["index.html", "styles.css", "script.js", "data.json"]
    missing_files = []
    
    for file in required_files:
        if not (docs_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Error: Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files found")
    
    # Convert data if needed
    print("\n📊 Converting data for web app...")
    try:
        subprocess.run(["python", "docs/convert_data.py"], check=True)
        print("✅ Data conversion successful")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error converting data: {e}")
        return False
    
    # Check if GitHub Pages is enabled
    print("\n🌐 Checking GitHub Pages setup...")
    print("To enable GitHub Pages:")
    print("1. Go to your repository on GitHub")
    print("2. Click Settings > Pages")
    print("3. Set Source to 'Deploy from a branch'")
    print("4. Select 'main' branch and '/docs' folder")
    print("5. Click Save")
    
    # Check if GitHub Actions workflow exists
    workflow_file = Path(".github/workflows/deploy.yml")
    if workflow_file.exists():
        print("✅ GitHub Actions workflow found")
        print("The web app will automatically deploy when you push to main")
    else:
        print("⚠️  GitHub Actions workflow not found")
        print("The workflow file should be created automatically")
    
    print("\n🎉 Setup complete!")
    print("Your web app will be available at:")
    print("https://your-username.github.io/target-dili-risk-score/")
    print("\nTo update the web app:")
    print("1. Run: python main.py")
    print("2. Run: python docs/convert_data.py")
    print("3. Commit and push changes")
    
    return True

if __name__ == "__main__":
    success = setup_github_pages()
    sys.exit(0 if success else 1) 