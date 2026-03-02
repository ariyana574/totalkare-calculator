"""
TotalKare Service Contract Pricing Tables
Now reads from Google Sheets instead of hardcoded values
"""
import streamlit as st
from config.sheets_config import get_sheet_data

@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_pricing(price_list="new"):
    """
    Get pricing from Google Sheets based on price list selection
    
    Args:
        price_list: "new" (2025 prices) or "old" (2023/24 prices)
        
    Returns:
        dict: Contains all pricing dictionaries for the selected price list
    """
    # Lift base rates
    lift_df = get_sheet_data("LiftRates")
    lift_rates = {}
    if lift_df is not None:
        for contract_type in ['standard_service', 'extra_service', 'fixed_labour']:
            row = lift_df[(lift_df['price_list'] == price_list) & 
                         (lift_df['contract_type'] == contract_type)]
            if not row.empty:
                lift_rates[contract_type] = {
                    "one_lift": float(row.iloc[0]['one_lift']),
                    "multi_sets": float(row.iloc[0]['multi_sets']),
                    "national_accounts": float(row.iloc[0]['national_accounts'])
                }
    
    # Brake tester rates
    brake_df = get_sheet_data("BrakeTesterRates")
    brake_rates = {}
    if brake_df is not None:
        row = brake_df[brake_df['price_list'] == price_list]
        if not row.empty:
            brake_rates = {
                "one_lift": float(row.iloc[0]['one_lift']),
                "multi_sets": float(row.iloc[0]['multi_sets']),
                "national_accounts": float(row.iloc[0]['national_accounts'])
            }
    
    # ROTE rates
    rote_df = get_sheet_data("ROTERates")
    rote_rates = {"1_visit": {}, "2_visits": {}}
    if rote_df is not None:
        for visits in [1, 2]:
            row = rote_df[(rote_df['price_list'] == price_list) & 
                         (rote_df['visits'] == visits)]
            if not row.empty:
                key = f"{visits}_visit" if visits == 1 else "2_visits"
                rote_rates[key] = {
                    "one_lift": float(row.iloc[0]['one_lift']),
                    "multi_sets": float(row.iloc[0]['multi_sets']),
                    "national_accounts": float(row.iloc[0]['national_accounts'])
                }
    
    # Add-ons
    addons_df = get_sheet_data("AddonsRates")
    addon_rates = {}
    if addons_df is not None:
        rows = addons_df[addons_df['price_list'] == price_list]
        for _, row in rows.iterrows():
            addon_rates[row['addon_name']] = float(row['price'])
    
    # Ancillary
    ancillary_df = get_sheet_data("AncillaryRates")
    ancillary_rates = {}
    if ancillary_df is not None:
        rows = ancillary_df[ancillary_df['price_list'] == price_list]
        for _, row in rows.iterrows():
            ancillary_rates[row['equipment_type']] = float(row['price'])
    
    # Labour rates
    labour_df = get_sheet_data("LabourRates")
    labour_rates = {}
    if labour_df is not None:
        for contract_type in ['standard_service', 'extra_service', 'fixed_labour', 'brake_tester']:
            row = labour_df[(labour_df['price_list'] == price_list) & 
                           (labour_df['contract_type'] == contract_type)]
            if not row.empty:
                labour_rates[contract_type] = {
                    "callout_first_hour": float(row.iloc[0]['callout_first_hour']),
                    "additional_hours": float(row.iloc[0]['additional_hours']),
                    "travel": float(row.iloc[0]['travel']),
                    "misuse_damage": float(row.iloc[0]['misuse_damage'])
                }
    
    # Intro offers
    intro_df = get_sheet_data("IntroOffers")
    intro_offers = {}
    if intro_df is not None:
        rows = intro_df[intro_df['price_list'] == price_list]
        for _, row in rows.iterrows():
            intro_offers[row['offer_type']] = float(row['price'])
    
    # PRO-2 Warranty
    pro2_df = get_sheet_data("PRO2Warranty")
    pro2_rates = {}
    if pro2_df is not None:
        rows = pro2_df[pro2_df['price_list'] == price_list]
        for _, row in rows.iterrows():
            pro2_rates[row['warranty_type']] = float(row['price'])
    
    # Parts discounts (fixed - not in sheets)
    parts_discounts = {
        "standard_service": 10,
        "extra_service": 30,
        "fixed_labour": 35,
        "brake_tester": 30
    }
    
    return {
        "lift_base_rates": lift_rates,
        "brake_tester_base_rates": brake_rates,
        "rote_rates": rote_rates,
        "addon_rates": addon_rates,
        "ancillary_rates": ancillary_rates,
        "labour_rates": labour_rates,
        "introductory_offers": intro_offers,
        "pro2_warranty_rates": pro2_rates,
        "parts_discounts": parts_discounts
    }


# Keep these for reference
TIER_OPTIONS = ["one_lift", "multi_sets", "national_accounts"]
CONTRACT_TYPES = ["standard_service", "extra_service", "fixed_labour", "brake_tester"]