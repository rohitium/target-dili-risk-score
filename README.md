# Target DILI Risk Score Pipeline

A fully automated, biologically informed pipeline for assessing drug target liver injury (DILI) risk. Integrates OpenTargets, FDA DILIrank, Pathway Commons, and OpenFDA data to produce interpretable risk scores, robust validation, and publication-ready plots.

## What It Does
- **Acquires** all required data (OpenTargets, DILIrank, Pathway Commons, OpenFDA)
- **Builds** clean, deduplicated drug-target mappings with optimized drug name matching
- **Scores** targets for DILI risk (direct evidence + network guilt-by-association)
- **Validates** risk scores against drug withdrawal and approval rates with detailed breakdowns
- **Outputs** clean tables, comprehensive validation reports, and high-quality plots

## 🌐 Web Application

**Live Demo**: [DILI Risk Score Checker](https://rohitium.github.io/target-dili-risk-score/)

An interactive web app for checking DILI risk scores for any drug target:
- **Search** any target by symbol (e.g., CYP3A4, ABCB1, SLC22A1)
- **View** detailed risk scores, categories, and metrics
- **Explore** interactive charts and visualizations
- **Mobile-friendly** responsive design

The web app automatically updates when the pipeline runs, providing real-time access to the latest risk scores.

## Quick Start
```bash
git clone <repo-url>
cd target-dili-risk-score
pip install -r requirements.txt
# Or: conda env create -f environment.yml && conda activate dili-risk-score
# Download OpenFDA bulk JSON to data/raw/drug-drugsfda-0001-of-0001.json
python main.py
```

## Project Structure
```
├── main.py                 # Main pipeline entry point
├── src/                    # Source code modules
│   ├── acquisition/        # Data acquisition modules
│   ├── etl/              # ETL pipeline modules
│   ├── features/          # Risk scoring modules
│   ├── validation/        # Validation modules
│   └── utils/             # Utility functions (drug matching, etc.)
├── docs/                  # Web application files
├── scripts/               # Utility and test scripts
├── data/                  # Data files (raw, interim, processed)
├── results/               # Output plots and reports
└── config/                # Configuration files
```

## Outputs
- `data/processed/drug_target_table.parquet` — Clean, deduplicated drug-target associations with DILI and approval/withdrawal data
- `data/processed/dili_risk_scores.parquet` — Final risk scores and categories with direct/network subscores
- `data/processed/validation_results.parquet` — Validation metrics
- `results/validation_report.txt` — Comprehensive report with top 10 targets breakdown
- `results/risk_vs_withdrawal.png` — Withdrawal rate vs. DILI risk score plot
- `results/risk_vs_approval.png` — Approval rate vs. DILI risk score plot

## Key Features
- **Optimized Drug Matching**: Fast, parallel drug name matching with exact and fuzzy matching
- **Clean Data Pipeline**: Deduplicated drug-target mappings with proper normalization
- **Enhanced Validation**: Detailed breakdown of direct vs. network evidence for top targets
- **Comprehensive Logging**: Full pipeline logging with progress tracking

## Rationale
- **Direct DILI evidence:** Targets with more high-risk drugs (from FDA DILIrank) are scored higher
- **Network guilt-by-association:** Targets connected to high-risk neighbors (from Pathway Commons) are upweighted
- **Validation:** Risk scores are validated against drug withdrawal/approval rates with detailed metrics

## Configuration
Edit `config/config.yml` for:
- BigQuery project info (for OpenTargets)
- Disease IDs (for liver injury)
- Output settings

## License
MIT 