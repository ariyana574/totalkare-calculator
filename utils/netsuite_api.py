"""
NetSuite RESTlet API integration
Fetches saved search results from NetSuite
"""

import requests
import streamlit as st
import pandas as pd
from requests_oauthlib import OAuth1
from datetime import datetime


def get_netsuite_credentials():
    """Get NetSuite credentials from Streamlit secrets"""
    if 'netsuite' in st.secrets:
        return {
            'account_id': st.secrets['netsuite']['account_id'],
            'restlet_url': st.secrets['netsuite']['restlet_url'],
            'consumer_key': st.secrets['netsuite']['consumer_key'],
            'consumer_secret': st.secrets['netsuite']['consumer_secret'],
            'token_id': st.secrets['netsuite']['token_id'],
            'token_secret': st.secrets['netsuite']['token_secret'],
        }
    else:
        # No credentials found
        st.error("⚠️ NetSuite credentials not configured.")
        st.stop()
        return None

def call_netsuite_saved_search(search_id):
    """
    Call NetSuite RESTlet to fetch saved search results
    
    Args:
        search_id: NetSuite saved search internal ID (e.g., 3977)
    
    Returns:
        list: Search results from NetSuite
    """
    creds = get_netsuite_credentials()
    
    # OAuth 1.0 signature for NetSuite
    auth = OAuth1(
        creds['consumer_key'],
        creds['consumer_secret'],
        creds['token_id'],
        creds['token_secret'],
        signature_method='HMAC-SHA256',
        realm=creds['account_id']
    )
    
    # Build URL with search ID parameter
    url = f"{creds['restlet_url']}&searchId={search_id}"
    
    try:
        response = requests.get(
            url,
            auth=auth,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        st.error("NetSuite request timed out. Please try again.")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"NetSuite API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            st.error(f"Response: {e.response.text}")
        return []


def get_brake_tester_equipment():
    """
    Fetch all brake tester equipment from NetSuite saved search 3977
    Maps NetSuite column names to match CSV structure
    
    Returns:
        pandas.DataFrame: Equipment data with standardized column names
    """
    with st.spinner("Fetching equipment from NetSuite..."):
        data = call_netsuite_saved_search(3977)
    
    if data:
        df = pd.DataFrame(data)
        
        # Map columns FIRST (before dropping anything)
        column_mapping = {
            'Name': 'Name.1',                          # Customer name
            'Internal ID': 'Customer_Internal_ID',      # Equipment internal ID
            'ID': 'ID',                                 # ✅ ACTUAL customer ID from NetSuite!
            'Date Created': 'Date Created',
            'item1': 'Item',                           # Item name/code
            'Description': 'Description',
            'Serial Number': 'Serial Number',
            'Mfg Serial Number': 'Mfg Serial Number',
            'Customer Equipment Quantity': 'Customer Equipment Quantity',
            'Shipping Address 1': 'Shipping Address 1',
            'Shipping City': 'Shipping City',
            'Shipping State/Province': 'Shipping State/Province',
            'Shipping Zip': 'Shipping Zip',
        }
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # NOW drop unnecessary columns (AFTER mapping ID!)
        columns_to_drop = ['Equipment Address', 'Primary Contact', 'First Name', 'Last Name', 
                          'Shipping Address', 'Shipping Address 3', 'Last Modified']
        
        for col in columns_to_drop:
            if col in df.columns:
                df = df.drop(columns=[col])
        
        # If Description is empty or NaN, use Item
        mask = (df['Description'].isna()) | (df['Description'] == '')
        df.loc[mask, 'Description'] = df.loc[mask, 'Item']
        
        # ✅ DO NOT CREATE FAKE ID - we already have the real one from NetSuite!
        # REMOVE THIS LINE: df['ID'] = df['Name.1'] + ' | ' + df['Shipping Zip'].fillna('')
        
        # Add missing required columns (if any)
        required_columns = ['ID', 'Name.1', 'Date Created', 'Item', 'Customer Equipment Quantity', 
                          'Shipping Address 1', 'Shipping City', 'Shipping Zip', 
                          'Serial Number', 'Mfg Serial Number', 'Description', 'Customer_Internal_ID']
        
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Clean up data
        df['Customer Equipment Quantity'] = df['Customer Equipment Quantity'].replace('', '1')
        df['Customer Equipment Quantity'] = df['Customer Equipment Quantity'].fillna(1)
        df['Customer Equipment Quantity'] = pd.to_numeric(df['Customer Equipment Quantity'], errors='coerce').fillna(1)
        
        for col in ['Serial Number', 'Mfg Serial Number', 'Description', 'Item']:
            if col in df.columns:
                df[col] = df[col].fillna('')
                df[col] = df[col].replace('nan', '')
        
        return df
    else:
        return pd.DataFrame()

def get_lift_equipment():
    """
    Fetch all lift equipment from NetSuite
    You'll need to create a separate saved search for lifts
    
    Returns:
        pandas.DataFrame: Lift equipment data
    """
    # TODO: Create saved search for lifts and update search ID
    lift_search_id = 3977  # Replace with actual lift search ID when created
    
    with st.spinner("Fetching lifts from NetSuite..."):
        data = call_netsuite_saved_search(lift_search_id)
    
    if data:
        return pd.DataFrame(data)
    else:
        return pd.DataFrame()