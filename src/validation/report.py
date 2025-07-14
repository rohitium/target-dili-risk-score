import logging
from datetime import datetime
import numpy as np

def format_sig(x, sig=1):
    if x == 0:
        return "0"
    from math import log10, floor
    return f"{round(x, -int(floor(log10(abs(x)))) + (sig - 1))}"

def generate_validation_report(validation_df, output_path):
    logger = logging.getLogger(__name__)
    report_lines = []
    report_lines.append("Target DILI Risk Score - Validation Report")
    report_lines.append("=" * 50)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("SUMMARY STATISTICS")
    report_lines.append("-" * 20)
    report_lines.append(f"Total targets analyzed: {len(validation_df)}")
    if 'dili_risk_score' in validation_df.columns:
        report_lines.append(f"Mean DILI risk score: {format_sig(validation_df['dili_risk_score'].mean())}")
        report_lines.append(f"Risk score range: {format_sig(validation_df['dili_risk_score'].min())} - {format_sig(validation_df['dili_risk_score'].max())}")
    if 'approval_rate' in validation_df.columns:
        report_lines.append(f"Mean approval rate: {validation_df['approval_rate'].mean():.3f}")
    if 'withdrawal_rate' in validation_df.columns:
        report_lines.append(f"Mean withdrawal rate: {validation_df['withdrawal_rate'].mean():.3f}")
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
    if 'risk_category' in validation_df.columns:
        report_lines.append("")
        report_lines.append("RISK CATEGORY DISTRIBUTION")
        report_lines.append("-" * 30)
        category_counts = validation_df['risk_category'].value_counts()
        for category, count in category_counts.items():
            report_lines.append(f"{category} risk: {count} targets")
    if 'dili_risk_score' in validation_df.columns:
        report_lines.append("")
        report_lines.append("TOP 10 HIGHEST DILI RISK TARGETS")
        report_lines.append("-" * 30)
        top_risk = validation_df.nlargest(10, 'dili_risk_score').copy()

        # Compute number of approved and withdrawn drugs if not present
        if 'approved_drugs' not in top_risk.columns or 'withdrawn_drugs' not in top_risk.columns:
            # Try to infer from available columns
            if 'approval_rate' in top_risk.columns and 'total_drugs' in top_risk.columns:
                top_risk['approved_drugs'] = np.round(top_risk['approval_rate'] * top_risk['total_drugs']).astype(int)
            else:
                top_risk['approved_drugs'] = np.nan
            if 'withdrawal_rate' in top_risk.columns and 'total_drugs' in top_risk.columns:
                top_risk['withdrawn_drugs'] = np.round(top_risk['withdrawal_rate'] * top_risk['total_drugs']).astype(int)
            else:
                top_risk['withdrawn_drugs'] = np.nan

        for idx, row in top_risk.iterrows():
            target_name = row['target_symbol'] if 'target_symbol' in row else (idx if isinstance(idx, str) else f"Target_{idx}")
            line = f"{target_name}: {format_sig(row['dili_risk_score'])} ({row['risk_category']})"
            line += f" | Direct: {row.get('total_dili_weight_normalized', 'N/A'):.3f}"
            line += f" | Network: {row.get('network_dili_score_normalized', 'N/A'):.3f}"
            line += f" | Approved: {row['approved_drugs']}"
            line += f" | Withdrawn: {row['withdrawn_drugs']}"
            line += f" | Approval: {row['approval_rate']:.3f}"
            line += f" | Withdrawal: {row['withdrawal_rate']:.3f}"
            line += f" | Drugs: {row['total_drugs']}"
            report_lines.append(line)

    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    logger.info(f"Validation report saved to {output_path}") 