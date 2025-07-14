"""
Simple validation for DILI risk scores.

Validates DILI risk scores against drug approval rates from OpenFDA
to assess the biological relevance of the risk scores.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)


class ApprovalValidator:
    """Simple validator for DILI risk scores against approval rates."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize approval validator.
        
        Args:
            data_dir: Path to data directory
        """
        self.data_dir = Path(data_dir)
        self.processed_dir = self.data_dir / "processed"
        self.results_dir = Path("results")
        
        # Ensure results directory exists
        self.results_dir.mkdir(exist_ok=True)
    
    def compute_approval_rates(self, drug_target_df: pd.DataFrame) -> pd.DataFrame:
        """Compute approval rates for each target.
        
        Args:
            drug_target_df: Drug-target table with approval status
            
        Returns:
            DataFrame with approval rates per target
        """
        logger.info("Computing approval rates per target...")
        
        # Check if approval status column exists
        if 'approval_status' not in drug_target_df.columns:
            logger.warning("No approval status data available. Using DILI concern as proxy for approval.")
            
            # Use DILI concern as a proxy for approval (negative correlation expected)
            approval_stats = drug_target_df.groupby('ot_target_symbol').agg({
                'fda_drug_name': 'count',  # Total drugs per target
                'fda_dili_concern': lambda x: (x == 'No-DILI-Concern').sum()  # Safe drugs per target
            }).rename(columns={
                'fda_drug_name': 'total_drugs',
                'fda_dili_concern': 'safe_drugs'
            })
            
            # Compute "approval rate" as ratio of safe drugs
            approval_stats['approval_rate'] = (
                approval_stats['safe_drugs'] / approval_stats['total_drugs']
            ).fillna(0)
            
        else:
            # Use actual approval status if available
            approval_stats = drug_target_df.groupby('ot_target_symbol').agg({
                'fda_drug_name': 'count',  # Total drugs per target
                'approval_status': lambda x: (x == 'approved').sum()  # Approved drugs per target
            }).rename(columns={
                'fda_drug_name': 'total_drugs',
                'approval_status': 'approved_drugs'
            })
            
            # Compute approval rate
            approval_stats['approval_rate'] = (
                approval_stats['approved_drugs'] / approval_stats['total_drugs']
            ).fillna(0)
        
        # Only keep targets with at least one drug
        approval_stats = approval_stats[approval_stats['total_drugs'] > 0]
        
        logger.info(f"Computed approval rates for {len(approval_stats)} targets")
        logger.info(f"Approval rate range: {approval_stats['approval_rate'].min():.3f} - {approval_stats['approval_rate'].max():.3f}")
        
        return approval_stats
    
    def compute_withdrawal_rates(self, drug_target_df: pd.DataFrame) -> pd.DataFrame:
        """Compute withdrawal rates for each target."""
        logger.info("Computing withdrawal rates per target...")
        if 'withdrawn' not in drug_target_df.columns:
            logger.warning("No withdrawn status data available. Skipping withdrawal rate computation.")
            return pd.DataFrame()
        withdrawal_stats = drug_target_df.groupby('ot_target_symbol').agg({
            'fda_drug_name': 'count',
            'withdrawn': 'sum'
        }).rename(columns={
            'fda_drug_name': 'total_drugs',
            'withdrawn': 'withdrawn_drugs'
        })
        withdrawal_stats['withdrawal_rate'] = (
            withdrawal_stats['withdrawn_drugs'] / withdrawal_stats['total_drugs']
        ).fillna(0)
        withdrawal_stats = withdrawal_stats[withdrawal_stats['total_drugs'] > 0]
        logger.info(f"Computed withdrawal rates for {len(withdrawal_stats)} targets")
        return withdrawal_stats

    def validate_risk_scores(self, risk_scores: pd.DataFrame, approval_rates: pd.DataFrame, withdrawal_rates: pd.DataFrame) -> pd.DataFrame:
        """Validate DILI risk scores against approval and withdrawal rates."""
        logger.info("Validating DILI risk scores against approval and withdrawal rates...")
        validation_df = risk_scores.merge(
            approval_rates, left_index=True, right_index=True, how='inner'
        )
        if not withdrawal_rates.empty:
            validation_df = validation_df.merge(
                withdrawal_rates[['withdrawal_rate']], left_index=True, right_index=True, how='left'
            )
        # Correlation with approval
        correlation_approval = validation_df['dili_risk_score'].corr(validation_df['approval_rate'])
        validation_df['correlation_with_approval'] = correlation_approval
        # Correlation with withdrawal
        if 'withdrawal_rate' in validation_df.columns:
            correlation_withdrawal = validation_df['dili_risk_score'].corr(validation_df['withdrawal_rate'])
            validation_df['correlation_with_withdrawal'] = correlation_withdrawal
        else:
            correlation_withdrawal = None
        logger.info(f"Correlation between DILI risk score and approval rate: {correlation_approval:.3f}")
        if correlation_withdrawal is not None:
            logger.info(f"Correlation between DILI risk score and withdrawal rate: {correlation_withdrawal:.3f}")
        return validation_df
    
    def generate_validation_report(self, validation_df: pd.DataFrame) -> None:
        """Generate validation report.
        
        Args:
            validation_df: Validation results DataFrame
        """
        logger.info("Generating validation report...")
        
        report_lines = []
        report_lines.append("Target DILI Risk Score - Validation Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Summary statistics
        report_lines.append("SUMMARY STATISTICS")
        report_lines.append("-" * 20)
        report_lines.append(f"Total targets analyzed: {len(validation_df)}")
        
        if 'dili_risk_score' in validation_df.columns:
            report_lines.append(f"Mean DILI risk score: {validation_df['dili_risk_score'].mean():.3f}")
            report_lines.append(f"Risk score range: {validation_df['dili_risk_score'].min():.3f} - {validation_df['dili_risk_score'].max():.3f}")
        
        if 'approval_rate' in validation_df.columns:
            report_lines.append(f"Mean approval rate: {validation_df['approval_rate'].mean():.3f}")
        
        if 'withdrawal_rate' in validation_df.columns:
            report_lines.append(f"Mean withdrawal rate: {validation_df['withdrawal_rate'].mean():.3f}")
        
        # Correlation
        if 'correlation_with_approval' in validation_df.columns:
            correlation = validation_df['correlation_with_approval'].iloc[0]
            report_lines.append("")
            report_lines.append("VALIDATION RESULTS")
            report_lines.append("-" * 20)
            report_lines.append(f"DILI risk score vs approval rate correlation: {correlation:.3f}")
            
            if correlation < 0:
                report_lines.append("✓ Negative correlation: Higher DILI risk targets have lower approval rates")
            else:
                report_lines.append("⚠ Positive correlation: Higher DILI risk targets have higher approval rates")
        
        if 'correlation_with_withdrawal' in validation_df.columns:
            correlation = validation_df['correlation_with_withdrawal'].iloc[0]
            report_lines.append(f"DILI risk score vs withdrawal rate correlation: {correlation:.3f}")
            if correlation > 0:
                report_lines.append("✓ Positive correlation: Higher DILI risk targets have higher withdrawal rates")
            else:
                report_lines.append("⚠ Negative correlation: Higher DILI risk targets have lower withdrawal rates")
        
        # Risk category distribution
        if 'risk_category' in validation_df.columns:
            report_lines.append("")
            report_lines.append("RISK CATEGORY DISTRIBUTION")
            report_lines.append("-" * 30)
            category_counts = validation_df['risk_category'].value_counts()
            for category, count in category_counts.items():
                report_lines.append(f"{category} risk: {count} targets")
        
        # Top risk targets
        if 'dili_risk_score' in validation_df.columns:
            report_lines.append("")
            report_lines.append("TOP 10 HIGHEST DILI RISK TARGETS")
            report_lines.append("-" * 30)
            top_risk = validation_df.nlargest(10, 'dili_risk_score')[
                ['dili_risk_score', 'risk_category', 'approval_rate', 'total_drugs']
            ]
            for idx, row in top_risk.iterrows():
                report_lines.append(f"{idx}: {row['dili_risk_score']:.3f} ({row['risk_category']}) - Approval: {row['approval_rate']:.3f} ({row['total_drugs']} drugs)")
        
        # Write report
        report_path = self.results_dir / "validation_report.txt"
        with open(report_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"Validation report saved to {report_path}")
    
    def plot_risk_vs_approval(self, validation_df: pd.DataFrame) -> None:
        """Matplotlib: Plot DILI risk score vs approval rate (log-scale), color by risk score, label one target at each order of magnitude."""
        import matplotlib.pyplot as plt
        import numpy as np
        import matplotlib as mpl
        from matplotlib.cm import ScalarMappable
        logger.info("Plotting DILI risk score vs approval rate (matplotlib, log-scale, color-coded)...")
        x = validation_df['dili_risk_score'].values
        y = validation_df['approval_rate'].values
        c = validation_df['dili_risk_score'].values
        fig, ax = plt.subplots(figsize=(8, 6))
        # Ensure ot_target_symbol is a column in validation_df for labeling
        if 'ot_target_symbol' not in validation_df.columns:
            validation_df = validation_df.reset_index()
        # Use log normalization for color if there are positive values
        if np.any(c > 0):
            norm = mpl.colors.LogNorm(vmin=np.min(c[c > 0]), vmax=np.max(c))
        else:
            norm = mpl.colors.Normalize(vmin=np.min(c), vmax=np.max(c))
        cmap = plt.get_cmap('coolwarm')
        sc = ax.scatter(x, y, c=c, cmap=cmap, norm=norm, s=50, edgecolor='k', alpha=0.8)
        ax.set_xscale('log')
        ax.set_xlabel('DILI Risk Score')
        ax.set_ylabel('Approval Rate')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        mags = [1e-4, 1e-3, 1e-2, 1e-1, 1.0]
        offsets = [(0, 15), (0, -20), (30, 0), (-30, 0), (0, 25)]
        for i, mag in enumerate(mags):
            idx = (np.abs(x - mag)).argmin()
            row = validation_df.iloc[idx]
            label = row['ot_target_symbol'] if 'ot_target_symbol' in row else str(idx)
            dx, dy = offsets[i % len(offsets)]
            ax.annotate(f"{label}\n({row['dili_risk_score']:.1e})",
                        (row['dili_risk_score'], row['approval_rate']),
                        textcoords="offset points", xytext=(dx, dy), ha='center', fontsize=9,
                        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", lw=0, alpha=0.8),
                        arrowprops=dict(arrowstyle="->", color="blue", lw=1, alpha=0.7))
        plt.tight_layout()
        out_path = 'results/risk_vs_approval.png'
        plt.savefig(out_path, dpi=150)
        plt.close()
        logger.info(f"Saved risk vs approval plot to {out_path}")
    
    def plot_risk_vs_withdrawal(self, validation_df: pd.DataFrame) -> None:
        import matplotlib.pyplot as plt
        import numpy as np
        import matplotlib as mpl
        logger = logging.getLogger(__name__)
        logger.info("Plotting DILI risk score vs withdrawal rate (matplotlib, log-scale, color-coded)...")
        if 'withdrawal_rate' not in validation_df.columns:
            logger.warning("No withdrawal_rate column in validation_df. Skipping plot.")
            return
        x = validation_df['dili_risk_score'].values
        y = validation_df['withdrawal_rate'].values
        c = validation_df['dili_risk_score'].values
        fig, ax = plt.subplots(figsize=(8, 6))
        if np.any(c > 0):
            norm = mpl.colors.LogNorm(vmin=np.min(c[c > 0]), vmax=np.max(c))
        else:
            norm = mpl.colors.Normalize(vmin=np.min(c), vmax=np.max(c))
        cmap = plt.get_cmap('coolwarm')
        sc = ax.scatter(x, y, c=c, cmap=cmap, norm=norm, s=50, edgecolor='k', alpha=0.8)
        ax.set_xscale('log')
        ax.set_xlabel('DILI Risk Score')
        ax.set_ylabel('Withdrawal Rate')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        mags = [1e-4, 1e-3, 1e-2, 1e-1, 1.0]
        offsets = [(0, 15), (0, -20), (30, 0), (-30, 0), (0, 25)]
        # Ensure ot_target_symbol is a column in validation_df for labeling
        if 'ot_target_symbol' not in validation_df.columns:
            validation_df = validation_df.reset_index()
        for i, mag in enumerate(mags):
            idx = (np.abs(x - mag)).argmin()
            row = validation_df.iloc[idx]
            label = row['ot_target_symbol'] if 'ot_target_symbol' in row else str(idx)
            dx, dy = offsets[i % len(offsets)]
            ax.annotate(f"{label}\n({row['dili_risk_score']:.1e})",
                        (row['dili_risk_score'], row['withdrawal_rate']),
                        textcoords="offset points", xytext=(dx, dy), ha='center', fontsize=9,
                        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", lw=0, alpha=0.8),
                        arrowprops=dict(arrowstyle="->", color="blue", lw=1, alpha=0.7))
        plt.tight_layout()
        out_path = 'results/risk_vs_withdrawal.png'
        plt.savefig(out_path, dpi=150)
        plt.close()
        logger.info(f"Saved risk vs withdrawal plot to {out_path}")
    
    def run_validation(self) -> pd.DataFrame:
        """Run complete validation pipeline.
        
        Returns:
            DataFrame with validation results
        """
        logger.info("=== Running DILI Risk Score Validation ===")
        
        # Load drug-target table
        drug_target_path = self.processed_dir / "drug_target_table.parquet"
        if not drug_target_path.exists():
            logger.error("Drug-target table not found. Run ETL first.")
            return pd.DataFrame()
        
        drug_target_df = pd.read_parquet(drug_target_path)
        
        # Load risk scores
        risk_scores_path = self.processed_dir / "dili_risk_scores.parquet"
        if not risk_scores_path.exists():
            logger.error("DILI risk scores not found. Run risk scoring first.")
            return pd.DataFrame()
        
        risk_scores = pd.read_parquet(risk_scores_path)
        risk_scores = risk_scores.set_index('ot_target_symbol')
        
        # Compute approval rates
        approval_rates = self.compute_approval_rates(drug_target_df)
        # Compute withdrawal rates
        withdrawal_rates = self.compute_withdrawal_rates(drug_target_df)
        # Validate risk scores
        validation_results = self.validate_risk_scores(risk_scores, approval_rates, withdrawal_rates)
        
        # Generate report
        self.generate_validation_report(validation_results)
        
        # Save validation results
        output_path = self.processed_dir / "validation_results.parquet"
        validation_results.to_parquet(output_path, index=False)
        logger.info(f"Saved validation results to {output_path}")
        
        # Plot risk vs approval
        self.plot_risk_vs_approval(validation_results)
        # Plot risk vs withdrawal
        self.plot_risk_vs_withdrawal(validation_results)
        logger.info("=== Validation Complete ===")
        
        return validation_results 