"""
Google Sheets Configuration and Helper Functions
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st

# Google Sheets configuration
SHEET_ID = "1FIC9gWYdTqPWjsewEcXUAJbffcr73M_qzA4L-9cgeG8"
SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]


@st.cache_resource(ttl=3600)
def get_sheets_client():
    """Get authenticated Google Sheets client (cached)"""
    try:
        # Check if running on Streamlit Cloud (has secrets)
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            # Running on Streamlit Cloud - use secrets
            import json
            from oauth2client.service_account import ServiceAccountCredentials
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                dict(st.secrets["gcp_service_account"]),
                SCOPES
            )
        else:
            # Running locally - use JSON file
            from oauth2client.service_account import ServiceAccountCredentials
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                'service-account.json',
                SCOPES
            )
        
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {str(e)}")
        return None

@st.cache_data(ttl=300)
def get_sheet_data(sheet_name):
    """Get all data from a specific sheet as DataFrame"""
    try:
        client = get_sheets_client()
        if client is None:
            return None
        
        spreadsheet = client.open_by_key(SHEET_ID)
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error reading {sheet_name}: {str(e)}")
        return None


def update_sheet_data(sheet_name, dataframe):
    """Update entire sheet with DataFrame data"""
    try:
        client = get_sheets_client()
        if client is None:
            return False
        
        spreadsheet = client.open_by_key(SHEET_ID)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Clear existing data
        worksheet.clear()
        
        # Write headers
        headers = dataframe.columns.tolist()
        worksheet.append_row(headers)
        
        # Write data
        for _, row in dataframe.iterrows():
            worksheet.append_row(row.tolist())
        
        return True
    except Exception as e:
        st.error(f"Error updating {sheet_name}: {str(e)}")
        return False


def add_ancillary_item(equipment_type, price_new, price_old):
    """Add new ancillary equipment to sheet"""
    try:
        df = get_sheet_data("AncillaryRates")
        if df is None:
            return False
        
        # Add new rows
        new_rows = pd.DataFrame([
            {"price_list": "new", "equipment_type": equipment_type, "price": price_new},
            {"price_list": "old", "equipment_type": equipment_type, "price": price_old}
        ])
        
        df = pd.concat([df, new_rows], ignore_index=True)
        
        return update_sheet_data("AncillaryRates", df)
    except Exception as e:
        st.error(f"Error adding ancillary item: {str(e)}")
        return False