import logging
from datetime import datetime

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
        report_lines.append(f"Mean DILI risk score: {validation_df['dili_risk_score'].mean():.3f}")
        report_lines.append(f"Risk score range: {validation_df['dili_risk_score'].min():.3f} - {validation_df['dili_risk_score'].max():.3f}")
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
        top_risk = validation_df.nlargest(10, 'dili_risk_score')[
            ['dili_risk_score', 'risk_category', 'approval_rate', 'total_drugs']
        ]
        for idx, row in top_risk.iterrows():
            report_lines.append(f"{idx}: {row['dili_risk_score']:.3f} ({row['risk_category']}) - Approval: {row['approval_rate']:.3f} ({row['total_drugs']} drugs)")
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    logger.info(f"Validation report saved to {output_path}") 