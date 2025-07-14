# Target DILI Risk Score Pipeline

A fully automated, biologically informed pipeline for assessing drug target liver injury (DILI) risk. Integrates OpenTargets, FDA DILIrank, Pathway Commons, and OpenFDA data to produce interpretable risk scores, robust validation, and publication-ready plots.

## What It Does
- **Acquires** all required data (OpenTargets, DILIrank, Pathway Commons, OpenFDA)
- **Builds** unified drug-target and network tables
- **Scores** targets for DILI risk (direct evidence + network guilt-by-association)
- **Validates** risk scores against drug approval and withdrawal rates
- **Outputs** clean tables, a validation report, and high-quality plots

## Quick Start
```bash
git clone <repo-url>
cd target-dili-risk-score
pip install -r requirements.txt
# Or: conda env create -f environment.yml && conda activate dili-risk-score
# Download OpenFDA bulk JSON to data/raw/drug-drugsfda-0001-of-0001.json
python main.py
```

## Outputs
- `data/processed/drug_target_table.parquet` — Drug-target associations with DILI and approval/withdrawal data
- `data/processed/dili_risk_scores.parquet` — Final risk scores and categories
- `data/processed/validation_results.parquet` — Validation metrics
- `results/validation_report.txt` — Summary report (correlations, risk categories, top targets)
- `results/risk_vs_approval.png` — Approval rate vs. DILI risk score plot
- `results/risk_vs_withdrawal.png` — Withdrawal rate vs. DILI risk score plot

## Rationale
- **Direct DILI evidence:** Targets with more high-risk drugs (from FDA DILIrank) are scored higher
- **Network guilt-by-association:** Targets connected to high-risk neighbors (from Pathway Commons) are upweighted
- **Validation:** Risk scores are correlated with both drug approval and withdrawal rates (withdrawal is a more specific metric for DILI)

## Configuration
Edit `config/config.yml` for:
- BigQuery project info (for OpenTargets)
- Disease IDs (for liver injury)
- Output settings

## License
MIT 