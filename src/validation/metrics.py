import logging
import pandas as pd

def compute_approval_rates(drug_target_df: pd.DataFrame) -> pd.DataFrame:
    logger = logging.getLogger(__name__)
    logger.info("Computing approval rates per target...")
    
    # Deduplicate drug-target pairs to match risk scoring process
    drug_target_dedup = drug_target_df.drop_duplicates(
        subset=['fda_drug_name', 'ot_target_symbol'], 
        keep='first'
    )
    logger.info(f"Deduplicated from {len(drug_target_df)} to {len(drug_target_dedup)} unique drug-target pairs for validation")
    
    if 'approval_status' not in drug_target_dedup.columns:
        logger.warning("No approval status data available. Using DILI concern as proxy for approval.")
        approval_stats = drug_target_dedup.groupby('ot_target_symbol').agg({
            'fda_drug_name': 'count',
            'fda_dili_concern': lambda x: (x == 'No-DILI-Concern').sum()
        }).rename(columns={
            'fda_drug_name': 'total_drugs',
            'fda_dili_concern': 'safe_drugs'
        })
        approval_stats['approval_rate'] = (
            approval_stats['safe_drugs'] / approval_stats['total_drugs']
        ).fillna(0)
    else:
        approval_stats = drug_target_dedup.groupby('ot_target_symbol').agg({
            'fda_drug_name': 'count',
            'approval_status': lambda x: (x == 'approved').sum()
        }).rename(columns={
            'fda_drug_name': 'total_drugs',
            'approval_status': 'approved_drugs'
        })
        approval_stats['approval_rate'] = (
            approval_stats['approved_drugs'] / approval_stats['total_drugs']
        ).fillna(0)
    approval_stats = approval_stats[approval_stats['total_drugs'] > 0]
    logger.info(f"Computed approval rates for {len(approval_stats)} targets")
    logger.info(f"Approval rate range: {approval_stats['approval_rate'].min():.3f} - {approval_stats['approval_rate'].max():.3f}")
    return approval_stats

def compute_withdrawal_rates(drug_target_df: pd.DataFrame) -> pd.DataFrame:
    logger = logging.getLogger(__name__)
    logger.info("Computing withdrawal rates per target...")
    
    # Deduplicate drug-target pairs to match risk scoring process
    drug_target_dedup = drug_target_df.drop_duplicates(
        subset=['fda_drug_name', 'ot_target_symbol'], 
        keep='first'
    )
    
    if 'withdrawn' not in drug_target_dedup.columns:
        logger.warning("No withdrawn status data available. Skipping withdrawal rate computation.")
        return pd.DataFrame()
    withdrawal_stats = drug_target_dedup.groupby('ot_target_symbol').agg({
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