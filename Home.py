"""
TotalKare Service Contract Calculator
Main Streamlit Application
"""

import streamlit as st
import pandas as pd
import pathlib
from datetime import datetime

BASE_DIR = pathlib.Path(__file__).parent

st.set_page_config(
    page_title="TotalKare Contract Calculator",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Clear cache button (AFTER set_page_config)
if st.sidebar.button("🔄 Refresh Prices from Google Sheets"):
    st.cache_resource.clear()
    st.rerun()

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'equipment_type' not in st.session_state:
    st.session_state.equipment_type = None
if 'customer_data' not in st.session_state:
    st.session_state.customer_data = None
if 'selected_equipment' not in st.session_state:
    st.session_state.selected_equipment = []
if 'contract_config' not in st.session_state:
    st.session_state.contract_config = {}

# Title
st.title("🔧 TotalKare Service Contract Calculator")
st.markdown("---")

# Main app logic
def main():
    if st.session_state.step == 1:
        show_equipment_type_selection()
    elif st.session_state.step == 2:
        show_csv_upload()
    elif st.session_state.step == 3:
        show_equipment_selection()
    elif st.session_state.step == 4:
        show_contract_type_selection()
    elif st.session_state.step == 5:
        show_pricing_tier_selection()
    elif st.session_state.step == 6:
        show_service_options()
    elif st.session_state.step == 7:
        show_review_and_calculate()

def show_equipment_type_selection():
    """Step 1: Choose Lift or Brake Tester"""
    st.header("Step 1: Choose Equipment Type")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏗️ Vehicle Lifts", use_container_width=True, type="primary"):
            st.session_state.equipment_type = "lift"
            st.session_state.step = 2
            st.rerun()
    
    with col2:
        if st.button("🚗 Brake Tester", use_container_width=True, type="primary"):
            st.session_state.equipment_type = "brake_tester"
            st.session_state.step = 2
            st.rerun()

def show_csv_upload():
    """Step 2: Upload NetSuite Data or Fetch from API"""
    st.header("Step 2: Load Equipment Data")
    
    # Data source toggle - API FIRST
    data_source = st.radio(
        "📊 Select Data Source",
        ["Fetch from NetSuite API", "Upload CSV File"],
        horizontal=True
    )
    
    if data_source == "Upload CSV File":
        # Original CSV upload logic
        uploaded_file = st.file_uploader(
            "Upload NetSuite Customer Equipment CSV",
            type=['csv'],
            help="Export from NetSuite: Customer Equipment list"
        )
        
        if uploaded_file is not None:
            try:
                # Read CSV
                df = pd.read_csv(uploaded_file)
                
                # Validate required columns
                required_cols = ['ID', 'Name.1', 'Date Created', 'Item', 'Customer Equipment Quantity', 
                   'Shipping Address 1', 'Shipping City', 'Shipping Zip', 'Serial Number', 'Mfg Serial Number']
                
                missing = [col for col in required_cols if col not in df.columns]
                if missing:
                    st.error(f"Missing columns: {', '.join(missing)}")
                    return
                
                # Store in session state
                st.session_state.customer_data = df
                
                # Show stats
                st.success("✓ File uploaded successfully!")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Records", len(df))
                with col2:
                    st.metric("Unique Customers", df['ID'].nunique())
                with col3:
                    equipment_count = df['Item'].nunique()
                    st.metric("Equipment Types", equipment_count)
                
                # Continue button
                if st.button("Continue to Equipment Selection →", type="primary"):
                    st.session_state.step = 3
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    else:
        # NetSuite API
        from utils.netsuite_api import get_brake_tester_equipment
        
        # Only show fetch button if no data is loaded
        if st.session_state.customer_data is None:
            st.info("Click the button below to fetch equipment data from NetSuite")
            
            if st.button("🔄 Fetch Equipment from NetSuite", type="primary"):
                df = get_brake_tester_equipment()
                
                if not df.empty:
                    # Store in session state
                    st.session_state.customer_data = df
                    st.rerun()  # Rerun to hide the button
                else:
                    st.error("❌ No equipment found in NetSuite or connection failed")
        
        # Show data and continue button when data exists
        if st.session_state.customer_data is not None:
            df = st.session_state.customer_data
            
            st.success(f"✅ Data ready: {len(df)} records loaded")
            
            # Show stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Records", len(df))
            with col2:
                try:
                    unique_count = len(df['ID'].unique()) if 'ID' in df.columns else 0
                    st.metric("Unique Customers", unique_count)
                except:
                    st.metric("Unique Customers", "-")
            with col3:
                try:
                    item_count = len(df['Item'].unique()) if 'Item' in df.columns else 0
                    st.metric("Equipment Types", item_count)
                except:
                    st.metric("Equipment Types", "-")

            # Debug info
            with st.expander("🔍 Debug: Data Structure"):
                st.write("**Columns:**")
                st.write(df.columns.tolist())
                st.write("\n**Data Preview:**")
                st.dataframe(df.head(3))
            
            # Continue button
            if st.button("Continue to Equipment Selection →", type="primary", key="continue"):
                st.session_state.step = 3
                st.rerun()
    
    # Back button
    if st.button("← Back"):
        st.session_state.step = 1
        st.rerun()
def show_equipment_selection():
    """Step 3: Select customer and equipment"""
    st.header("Step 3: Select Customer & Equipment")
    
    # Check if data exists
    if st.session_state.customer_data is None:
        st.error("No customer data loaded. Please go back and upload CSV.")
        if st.button("← Back to Upload"):
            st.session_state.step = 2
            st.rerun()
        return
    
    df = st.session_state.customer_data
    
    # Customer selection dropdown
    customer_ids = df['ID'].unique()
    customer_options = []
    customer_display_to_id = {}
    
    for cid in customer_ids:
        # Convert both to string for comparison - THIS IS THE FIX
        customer_records = df[df['ID'].astype(str) == str(cid)]
        
        if len(customer_records) > 0:
            customer_name = customer_records['Name.1'].iloc[0]
            address_1 = customer_records['Shipping Address 1'].iloc[0] if 'Shipping Address 1' in customer_records.columns else ''
            zip_code = customer_records['Shipping Zip'].iloc[0] if 'Shipping Zip' in customer_records.columns else ''
            
            # Show equipment count
            equipment_count = len(customer_records)
            display = f"{customer_name} - ID: {cid} - {address_1} {zip_code} ({equipment_count} items)"
            customer_options.append(display)
            customer_display_to_id[display] = str(cid)
    
    selected_customer = st.selectbox(
        "Select Customer:",
        options=[None] + customer_options,
        format_func=lambda x: "-- Select a customer --" if x is None else x,
        help="Search by typing customer name or address"
    )
    
    if selected_customer is not None:
        # Extract customer ID from selection map
        customer_id = customer_display_to_id.get(selected_customer, None)
        
        if customer_id is None:
            st.error("Unable to determine customer ID from selection")
            return
        
        # Get customer data (ensure types align)
        customer_df = df[df['ID'].astype(str) == str(customer_id)]
        
        if len(customer_df) == 0:
            st.error("No equipment found for this customer")
            return
        
        # Display customer info
        address_1 = str(customer_df['Shipping Address 1'].iloc[0]) if 'Shipping Address 1' in customer_df.columns else ''
        city = str(customer_df['Shipping City'].iloc[0]) if 'Shipping City' in customer_df.columns else ''
        zip_code = str(customer_df['Shipping Zip'].iloc[0]) if 'Shipping Zip' in customer_df.columns else ''

        st.info(f"""
        **Customer:** {customer_df['Name.1'].iloc[0]}
        **Address:** {address_1}, {city} {zip_code}
        **Company Code:** {customer_id}
        **Equipment Count:** {len(customer_df)} items
        """)
        
        # Check for island restrictions
        postcode = customer_df['Shipping Zip'].iloc[0] if 'Shipping Zip' in customer_df.columns else ''
        from config.rules import get_island_restrictions
        island_rules = get_island_restrictions(postcode)
        
        if island_rules:
            if "shetlands" in str(island_rules.get("note", "")).lower():
                st.warning("""
                ⚠️ **SHETLANDS LOCATION DETECTED**
                Special restrictions apply:
                • Only EXTRA contracts available
                • Only 1 PM visit per year allowed
                • ROTE not available
                • Ferry/hotel charges will be added separately
                """)
            else:
                st.warning("""
                ⚠️ **ISLAND LOCATION DETECTED**
                Special restrictions apply:
                • Only EXTRA contracts available
                • ROTE not available
                • Ferry/hotel charges will be added separately
                """)
        
        # Equipment selection
        st.subheader("Select Equipment for Contract")
        
        selected_items = []
        for idx, row in customer_df.iterrows():
            # Get serial number (fallback logic)
            serial = row['Serial Number'] if pd.notna(row['Serial Number']) and str(row['Serial Number']).strip() != '' else row.get('Mfg Serial Number', '')
            
            # Get description or use item as fallback
            description = row['Description'] if pd.notna(row['Description']) and str(row['Description']).strip() != '' else row['Item']
            
            # Get date created safely
            date_created = str(row.get('Date Created', ''))[:10] if pd.notna(row.get('Date Created')) else 'N/A'
            
            item_label = f"**{description}** - {row['Item']} (Serial: {serial}) - Qty: {row['Customer Equipment Quantity']} - Date: {date_created}"
            
            if st.checkbox(item_label, key=f"eq_{idx}"):
                selected_items.append({
                    'item': row['Item'],
                    'description': description,
                    'serial': serial,
                    'quantity': float(row['Customer Equipment Quantity']) if pd.notna(row['Customer Equipment Quantity']) and str(row['Customer Equipment Quantity']).strip() != '' else 1.0,
                    'customer_name': row['Name.1'],
                    'customer_id': customer_id,
                    'address_1': str(row.get('Shipping Address 1', '')),
                    'city': str(row.get('Shipping City', '')),
                    'state': str(row.get('Shipping State/Province', '')),
                    'postcode': str(row.get('Shipping Zip', ''))
                })
        
        # Store selections
        st.session_state.selected_equipment = selected_items
        st.session_state.island_restrictions = island_rules
        
        # Continue button
        if selected_items:
            if st.button(f"Continue with {len(selected_items)} item(s) selected →", type="primary"):
                st.session_state.step = 4
                st.rerun()
        else:
            st.warning("Please select at least one equipment item")
    
    # Back button
    if st.button("← Back"):
        st.session_state.step = 2
        st.rerun()
def show_contract_type_selection():
    """Step 4: Contract type, duration, price list"""
    st.header("Step 4: Contract Type & Duration")
    
    island_rules = st.session_state.get('island_restrictions')
    
    # Price list selection
    st.subheader("Price List Selection")
    price_list = st.radio(
        "Choose price list:",
        options=["new", "old"],
        format_func=lambda x: "New Prices (2025)" if x == "new" else "Old Prices (2023/24)",
        horizontal=True
    )
    st.session_state.contract_config['price_list'] = price_list
    
    st.markdown("---")
    
    # Contract type selection
    st.subheader("Choose Service Contract Type")
    
    if st.session_state.equipment_type == "lift":
        # Check if island restricts contract types
        if island_rules and island_rules.get('allowed_contracts') == ['extra_service']:
            st.warning("⚠️ Island location: Only EXTRA contracts available")
            contract_type = "extra_service"
            st.info("**Extra Service** (Only option for islands)\n- 2 visits/year, 30% parts discount")
        else:
            contract_options = {
                "standard_service": "Standard Service (10% parts discount)",
                "extra_service": "Extra Service (30% parts discount)",
                "fixed_labour": "Fixed Labour (35% discount, FREE labour)",
                "pro2_warranty": "PRO-2 Warranty Package"
            }
            
            contract_type = st.radio(
                "Select contract type:",
                options=list(contract_options.keys()),
                format_func=lambda x: contract_options[x]
            )
    else:
        # Brake tester - only one option
        contract_type = "brake_tester"
        st.info("**Extra Service Brake Tester** (Only option)\n- 2 visits/year, 30% parts discount")
    
    st.session_state.contract_config['contract_type'] = contract_type
    
    # Contract duration (not for PRO-2)
    if contract_type != "pro2_warranty":
        st.markdown("---")
        st.subheader("Contract Duration")
        years = st.selectbox(
            "Select duration:",
            options=[1, 2, 3, 5],
            format_func=lambda x: f"{x} Year{'s' if x > 1 else ''}"
        )
        st.session_state.contract_config['years'] = years
        
        # Introductory offer - ONLY for EXTRA service lifts
        if st.session_state.equipment_type == "lift" and contract_type == "extra_service":
            st.markdown("---")
            intro_offer = st.checkbox(
                "Apply introductory offer (first year only)",
                help="Discounted pricing for new Extra Service contracts"
            )
            
            if intro_offer:
                # Show dropdown to select which intro offer
                intro_option = st.selectbox(
                    "Select intro offer type:",
                    options=["extra_service", "extra_1_rote", "extra_2_rote"],
                    format_func=lambda x: {
                        "extra_service": "Extra Service Only (£432)",
                        "extra_1_rote": "Extra + 1 ROTE (£624)",
                        "extra_2_rote": "Extra + 2 ROTE (£780)"
                    }[x]
                )
                st.session_state.contract_config['intro_offer'] = True
                st.session_state.contract_config['intro_option'] = intro_option
                
                st.info(f"""
                **Selected Intro Offer:** {intro_option.replace('_', ' ').title()}
                
                You can still add other add-ons (Kluberplex, Lube Pots, Battery Plan) in the next step.
                """)
            else:
                st.session_state.contract_config['intro_offer'] = False
                st.session_state.contract_config['intro_option'] = None
        else:
            # No intro offer for Standard/Fixed/Brake Tester
            st.session_state.contract_config['intro_offer'] = False
            st.session_state.contract_config['intro_option'] = None
    
    # PRO-2 specific options
    if contract_type == "pro2_warranty":
        st.markdown("---")
        st.subheader("PRO-2 Warranty Options")
        warranty_type = st.radio(
            "Select warranty package:",
            options=["standard_2_year", "full_3_year", "full_5_year"],
            format_func=lambda x: {
                "standard_2_year": "2-Year Standard (£492/unit/year)",
                "full_3_year": "3-Year Full Coverage (£612/unit/year)",
                "full_5_year": "5-Year Full Coverage (£1,020/unit/year)"
            }[x]
        )
        st.session_state.contract_config['warranty_type'] = warranty_type
        # Extract years from warranty type
        st.session_state.contract_config['years'] = int(warranty_type.split('_')[1][0])
        
        # No intro offers for PRO-2
        st.session_state.contract_config['intro_offer'] = False
        st.session_state.contract_config['intro_option'] = None
    
    # Continue button
    if st.button("Continue →", type="primary"):
        if contract_type == "pro2_warranty":
            st.session_state.step = 6  
        else:
            st.session_state.step = 5
        st.rerun()
    
    # Back button
    if st.button("← Back"):
        st.session_state.step = 3
        st.rerun()

def show_pricing_tier_selection():
    """Step 5: Select pricing tier"""
    st.header("Step 5: Select Pricing Tier")
    
    st.subheader("Choose customer pricing tier:")
    
    tier = st.radio(
        "Pricing tier:",
        options=["one_lift", "multi_sets", "national_accounts"],
        format_func=lambda x: {
            "one_lift": "One Lift (Standard pricing)",
            "multi_sets": "Multi Sets (Volume discount)",
            "national_accounts": "National Accounts (Best pricing)"
        }[x]
    )
    
    st.session_state.contract_config['tier'] = tier
    
    # Show postcode info
    equipment = st.session_state.selected_equipment[0]
    st.info(f"**Postcode:** {equipment['postcode']}")
    
    # Continue button
    if st.button("Continue →", type="primary"):
        st.session_state.step = 6
        st.rerun()
    
    # Back button
    if st.button("← Back"):
        st.session_state.step = 4
        st.rerun()

def show_service_options():
    """Step 6: Configure service options"""
    st.header("Step 6: Configure Service Options")
    
    if st.session_state.equipment_type == "lift":
        show_lift_service_options()
    else:
        show_brake_tester_service_options()

def show_lift_service_options():
    """Service options for lifts"""
    # Set default tier for PRO-2 (doesn't matter which, won't be used)
    if st.session_state.contract_config['contract_type'] == 'pro2_warranty':
        if 'tier' not in st.session_state.contract_config:
            st.session_state.contract_config['tier'] = 'national_accounts'
    
    equipment_list = st.session_state.selected_equipment
    island_rules = st.session_state.get('island_restrictions')
    contract_type = st.session_state.contract_config['contract_type']
     
    # Show ALL selected equipment
    st.subheader(f"Selected Equipment ({len(equipment_list)} item{'s' if len(equipment_list) > 1 else ''})")
    for idx, equipment in enumerate(equipment_list, 1):
        st.info(f"**{idx}. {equipment['description']}** - {equipment['item']} (Serial: {equipment['serial']}) - Qty: {equipment['quantity']}")
    
    st.markdown("---")
    
    # PM Visits selection (NOT for PRO-2 warranty)
    if contract_type != 'pro2_warranty':
        st.subheader("PM Visits Per Year")
        
        # Check for G8/G9 on FIRST equipment
        from config.rules import requires_special_servicing
        first_equipment = equipment_list[0]
        special_rules = requires_special_servicing(first_equipment['description'])
        
        if island_rules and "shetlands" in str(island_rules.get("note", "")).lower():
            pm_visits = 1
            st.warning("⚠️ Shetlands: Only 1 PM visit allowed")
            st.session_state.contract_config['pm_visits'] = pm_visits
        else:
            # Show G8/G9 warning
            if special_rules.get("requires_4_services"):
                st.warning("⚠️ G8/Outdoor lift detected - 4 PM visits recommended")
                default_visits = 4
            elif special_rules.get("requires_3_services"):
                st.warning("⚠️ G9 lift detected - 3 PM visits recommended")
                default_visits = 3
            else:
                default_visits = 2
            
            pm_visits = st.selectbox(
                "Select PM visits:",
                options=[1, 2, 3, 4],
                index=[1, 2, 3, 4].index(default_visits),
                format_func=lambda x: f"{x} visit{'s' if x > 1 else ''}" + 
                                     (" (50% discount)" if x == 1 else "")
            )
            st.session_state.contract_config['pm_visits'] = pm_visits
    else:
        # PRO-2 always 2 PM visits
        st.info("**PM Visits:** 2 per year (fixed for PRO-2 warranty)")
        st.session_state.contract_config['pm_visits'] = 2
    
    # ROTE selection
    st.markdown("---")
    st.subheader("ROTE (Reports of Thorough Examination)")
    
    # Check if intro offer already includes ROTE
    intro_option = st.session_state.contract_config.get('intro_option')
    
    if intro_option in ['extra_1_rote', 'extra_2_rote']:
        # Intro offer already includes ROTE - auto-select it
        if intro_option == 'extra_1_rote':
            rote_visits = 1
            st.info("✓ 1 ROTE visit/year included in intro offer (locked)")
        else:
            rote_visits = 2
            st.info("✓ 2 ROTE visits/year included in intro offer (locked)")
    else:
        # Normal ROTE selection
        if island_rules and not island_rules.get("rote_available", True):
            rote_visits = 0
            st.warning("⚠️ ROTE not available for island locations")
        else:
            rote_visits = st.radio(
                "Select ROTE visits:",
                options=[0, 1, 2],
                format_func=lambda x: "No ROTE" if x == 0 else f"{x} ROTE visit{'s' if x > 1 else ''}/year"
            )
    
    st.session_state.contract_config['rote_visits'] = rote_visits
    
    # Add-ons with QUANTITY
    st.markdown("---")
    st.subheader("Optional Add-ons")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        kluberplex_check = st.checkbox("Kluberplex Lube Pots (Recommended for G8/GALV/outdoor)")
    with col2:
        if kluberplex_check:
            kluberplex_qty = st.number_input("Qty", min_value=1, value=1, step=1, key="kluberplex_qty")
        else:
            kluberplex_qty = 0
    
    col1, col2 = st.columns([3, 1])
    with col1:
        lube_pots_check = st.checkbox("Standard Lube Pots (Recommended for MVL/SVL/SIV/RG)")
    with col2:
        if lube_pots_check:
            lube_pots_qty = st.number_input("Qty", min_value=1, value=1, step=1, key="lube_pots_qty")
        else:
            lube_pots_qty = 0
    
    col1, col2 = st.columns([3, 1])
    with col1:
        battery_plan_check = st.checkbox("Battery Plan (For cable-free lifts T8DC/S6CF)")
    with col2:
        if battery_plan_check:
            battery_plan_qty = st.number_input("Qty", min_value=1, value=1, step=1, key="battery_plan_qty")
        else:
            battery_plan_qty = 0
    
    st.session_state.contract_config['kluberplex_qty'] = kluberplex_qty
    st.session_state.contract_config['lube_pots_qty'] = lube_pots_qty
    st.session_state.contract_config['battery_plan_qty'] = battery_plan_qty
    
    # Ancillary equipment with QUANTITY (DYNAMIC - loads from Google Sheets)
    st.markdown("---")
    st.subheader("Ancillary Equipment")
    
    # Get available ancillary from pricing
    from config.pricing import get_pricing
    pricing = get_pricing(st.session_state.contract_config.get('price_list', 'new'))
    available_ancillary = pricing.get('ancillary_rates', {})
    
    if available_ancillary:
        st.write("Select ancillary equipment and specify quantity:")
        
        ancillary_items = {}
        
        for equipment_type in sorted(available_ancillary.keys()):
            price = available_ancillary[equipment_type]
            display_name = equipment_type.replace('_', ' ').title()
            
            col1, col2 = st.columns([3, 1])
            with col1:
                checked = st.checkbox(f"{display_name} (£{price})", key=f"lift_anc_{equipment_type}")
            
            if checked:
                with col2:
                    qty = st.number_input(
                        "Qty", 
                        min_value=1, 
                        value=1, 
                        step=1, 
                        key=f"lift_qty_{equipment_type}"
                    )
                    ancillary_items[equipment_type] = qty
        
        st.session_state.contract_config['ancillary_items'] = ancillary_items
    else:
        st.warning("No ancillary equipment available in pricing")
        st.session_state.contract_config['ancillary_items'] = {}
    
    # Continue button
    if st.button("Continue to Review →", type="primary"):
        st.session_state.step = 7
        st.rerun()
    
    # Back button
    if st.button("← Back"):
        st.session_state.step = 5
        st.rerun()

def show_brake_tester_service_options():
    """Service options for brake testers"""
    equipment_list = st.session_state.selected_equipment
    island_rules = st.session_state.get('island_restrictions')
    
    # Show ALL selected equipment
    st.subheader(f"Selected Equipment ({len(equipment_list)} item{'s' if len(equipment_list) > 1 else ''})")
    for idx, equipment in enumerate(equipment_list, 1):
        st.info(f"**{idx}. {equipment['description']}** - {equipment['item']} (Serial: {equipment['serial']}) - Qty: {equipment['quantity']}")
    
    st.markdown("---")
    
    st.info("Brake testers include:\n- 2 PM visits/year (fixed)\n- 2 Calibrations/year\n- 30% parts discount")
    
    # ROTE selection
    st.subheader("ROTE (Reports of Thorough Examination)")
    
    if island_rules and not island_rules.get("rote_available", True):
        rote_visits = 0
        st.warning("⚠️ ROTE not available for island locations")
    else:
        rote_visits = st.radio(
            "Select ROTE visits:",
            options=[0, 1, 2],
            format_func=lambda x: "No ROTE" if x == 0 else f"{x} ROTE visit{'s' if x > 1 else ''}/year"
        )
    
    st.session_state.contract_config['rote_visits'] = rote_visits
    
    # Ancillary equipment with QUANTITY (DYNAMIC - loads from Google Sheets)
    st.markdown("---")
    st.subheader("Ancillary Equipment")
    
    # Get available ancillary from pricing
    from config.pricing import get_pricing
    pricing = get_pricing(st.session_state.contract_config.get('price_list', 'new'))
    available_ancillary = pricing.get('ancillary_rates', {})
    
    if available_ancillary:
        st.write("Select ancillary equipment and specify quantity:")
        
        ancillary_items = {}
        
        for equipment_type in sorted(available_ancillary.keys()):
            price = available_ancillary[equipment_type]
            display_name = equipment_type.replace('_', ' ').title()
            
            col1, col2 = st.columns([3, 1])
            with col1:
                checked = st.checkbox(f"{display_name} (£{price})", key=f"bt_anc_{equipment_type}")
            
            if checked:
                with col2:
                    qty = st.number_input(
                        "Qty", 
                        min_value=1, 
                        value=1, 
                        step=1, 
                        key=f"bt_qty_{equipment_type}"
                    )
                    ancillary_items[equipment_type] = qty
        
        st.session_state.contract_config['ancillary_items'] = ancillary_items
    else:
        st.warning("No ancillary equipment available in pricing")
        st.session_state.contract_config['ancillary_items'] = {}
    
    # Continue button
    if st.button("Continue to Review →", type="primary"):
        st.session_state.step = 7
        st.rerun()
    
    # Back button
    if st.button("← Back"):
        st.session_state.step = 5
        st.rerun()
def show_review_and_calculate():
    """Step 7: Review and calculate pricing"""
    st.header("Step 7: Review & Calculate")
    
    equipment_list = st.session_state.selected_equipment
    config = st.session_state.contract_config
    
    if not equipment_list:
        st.error("No equipment selected!")
        return
    
    # Customer info (same for all equipment)
    first_equipment = equipment_list[0]
    
    # Display customer summary
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Customer Information")
        st.write(f"**Customer:** {first_equipment['customer_name']}")
        st.write(f"**Address:** {first_equipment.get('address_1', '')}")
        st.write(f"**City:** {first_equipment.get('city', '')}")
        st.write(f"**Postcode:** {first_equipment['postcode']}")
        st.write(f"**Company Code:** {first_equipment['customer_id']}")
    
    with col2:
        st.subheader("Contract Details")
        st.write(f"**Contract Type:** {config['contract_type'].replace('_', ' ').title()}")
        
        # Only show tier for non-PRO2 contracts
        if config['contract_type'] != 'pro2_warranty':
            st.write(f"**Tier:** {config['tier'].replace('_', ' ').title()}")
        
        st.write(f"**Duration:** {config['years']} year{'s' if config['years'] > 1 else ''}")
        st.write(f"**Price List:** {'New (2025)' if config['price_list'] == 'new' else 'Old (2023/24)'}")
    
    st.markdown("---")
    
    # Show all equipment
    st.subheader(f"Equipment Included ({len(equipment_list)} item{'s' if len(equipment_list) > 1 else ''})")
    
    # Display equipment in a nice table
    for idx, equipment in enumerate(equipment_list, 1):
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{idx}. {equipment['description']}**")
        with col2:
            st.write(f"Item: {equipment['item']}")
            st.write(f"Serial: {equipment['serial']}")
        with col3:
            st.write(f"Qty: **{equipment['quantity']}**")
    
    st.markdown("---")
    
    # Calculate combined pricing
    total_annual = 0
    total_contract = 0
    monthly_dd = 0
    result_data = None  # Store for PDF generation
    
    # Check if PRO-2 warranty
    if config['contract_type'] == 'pro2_warranty':
        # PRO-2 warranty calculation
        st.subheader("💰 PRO-2 Warranty Pricing")
        
        # Calculate total units
        total_units = sum([eq['quantity'] for eq in equipment_list])
        
        # Calculate using Pro2WarrantyCalculator
        from calculators.pro2_warranty_calculator import Pro2WarrantyCalculator
        from calculators.addons_calculator import AddonsCalculator
        
        calc = Pro2WarrantyCalculator(
            warranty_type=config['warranty_type'],
            units=int(total_units),
            years=config['years'],
            price_list=config['price_list']
        )
        
        result = calc.calculate_total()
        
        # Add ALL add-ons if selected (ROTE, Kluberplex, Lube Pots, Battery Plan, Ancillary)
        addons_total_annual = 0
        if (config.get('rote_visits', 0) > 0 or config.get('kluberplex') or 
            config.get('lube_pots') or config.get('battery_plan') or config.get('ancillary')):
            
            addons_calc = AddonsCalculator(
                tier='national_accounts',  # PRO-2 doesn't have tiers
                quantity=total_units,
                price_list=config['price_list'],
                pm_visits=2
            )
            
            # Add ROTE
            if config.get('rote_visits', 0) > 0:
                addons_calc.add_rote(visits=config['rote_visits'])
            
            # Add Kluberplex
            if config.get('kluberplex'):
                addons_calc.add_kluberplex()
            
            # Add Lube Pots
            if config.get('lube_pots'):
                addons_calc.add_lube_pots()
            
            # Add Battery Plan
            if config.get('battery_plan'):
                addons_calc.add_battery_plan()
            
            # Add Ancillary
            for anc in config.get('ancillary', []):
                addons_calc.add_ancillary(anc)
            
            addons_breakdown = addons_calc.get_breakdown()
            addons_total_annual = addons_breakdown['total_per_unit'] * total_units
            
            # Add to result
            result['annual_cost'] += addons_total_annual
            result['total_contract_cost'] += (addons_total_annual * config['years'])
            result['monthly_dd'] = result['annual_cost'] / 12
        
        # Display totals
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rate per Unit/Year", f"£{result['rate_per_unit_per_year']:,.2f}")
        with col2:
            st.metric("Annual Total", f"£{result['annual_cost']:,.2f}")
        with col3:
            st.metric(f"Total ({config['years']} years)", f"£{result['total_contract_cost']:,.2f}")
        
        # Show what's included
        included_items = [
            "✓ All parts included",
            "✓ All labour included (callouts, travel, on-site)",
            "✓ 2 service visits per year",
            f"✓ {config['years']}-year coverage"
        ]
        
        # Show add-ons
        if config.get('rote_visits', 0) > 0:
            included_items.append(f"✓ {config['rote_visits']} ROTE visit{'s' if config['rote_visits'] > 1 else ''}/year")
        if config.get('kluberplex'):
            included_items.append("✓ Kluberplex Lube Pots")
        if config.get('lube_pots'):
            included_items.append("✓ Standard Lube Pots")
        if config.get('battery_plan'):
            included_items.append("✓ Battery Plan")
        if config.get('ancillary'):
            for anc in config['ancillary']:
                included_items.append(f"✓ {anc.replace('_', ' ').title()}")
        
        st.info("\n".join(included_items))
        
        if addons_total_annual > 0:
            st.success(f"**Add-ons Total:** +£{addons_total_annual:,.2f}/year")
        
        total_annual = result['annual_cost']
        total_contract = result['total_contract_cost']
        monthly_dd = result['monthly_dd']
        result_data = result
    
    else:
        # Regular lift or brake tester contracts
        with st.expander("📊 View Individual Equipment Pricing", expanded=False):
            for idx, equipment in enumerate(equipment_list, 1):
                st.write(f"**Equipment {idx}: {equipment['description']}**")

                # Only include add-ons for the FIRST equipment
                if idx == 1:
                    # First equipment - include all add-ons
                    result = calculate_lift_contract(equipment, config) if st.session_state.equipment_type == "lift" else calculate_brake_tester_contract(equipment, config)
                    result_data = result  # Store for PDF
                else:
                    # Subsequent equipment - NO add-ons
                    config_no_addons = config.copy()
                    config_no_addons['rote_visits'] = 0
                    config_no_addons['kluberplex_qty'] = 0
                    config_no_addons['lube_pots_qty'] = 0
                    config_no_addons['battery_plan_qty'] = 0
                    config_no_addons['ancillary_items'] = {}

                    result = calculate_lift_contract(equipment, config_no_addons) if st.session_state.equipment_type == "lift" else calculate_brake_tester_contract(equipment, config_no_addons)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Annual", f"£{result['annual_total']:,.2f}")
                with col2:
                    st.metric("Monthly DD", f"£{result['monthly_dd']:,.2f}")
                with col3:
                    st.metric(f"{config['years']}yr Total", f"£{result['total_contract_cost']:,.2f}")

                total_annual += result['annual_total']
                total_contract += result['total_contract_cost']

                st.markdown("---")

        # Calculate monthly DD from total annual
        monthly_dd = total_annual / 12
        
        # Display combined totals
        st.subheader("💰 Combined Contract Pricing")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Annual Total",
                f"£{total_annual:,.2f}",
                help="Combined annual cost for all equipment"
            )
        
        with col2:
            st.metric(
                "Monthly Direct Debit",
                f"£{monthly_dd:,.2f}",
                help="Monthly payment amount"
            )
        
        with col3:
            st.metric(
                f"Total Contract ({config['years']} year{'s' if config['years'] > 1 else ''})",
                f"£{total_contract:,.2f}",
                help="Total cost over contract duration"
            )
        
    # Show service details
    st.markdown("---")
    st.subheader("📋 Service Details")

    if st.session_state.equipment_type == "lift":
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**PM Visits:** {config.get('pm_visits', 2)} per year")
            if config.get('rote_visits', 0) > 0:
                st.write(f"**ROTE Visits:** {config['rote_visits']} per year")
        with col2:
            # Show add-ons with quantities
            if config.get('kluberplex_qty', 0) > 0:
                st.write(f"✓ Kluberplex Lube Pots (×{config['kluberplex_qty']})")
            if config.get('lube_pots_qty', 0) > 0:
                st.write(f"✓ Standard Lube Pots (×{config['lube_pots_qty']})")
            if config.get('battery_plan_qty', 0) > 0:
                st.write(f"✓ Battery Plan (×{config['battery_plan_qty']})")
    else:
        st.write("**PM Visits:** 2 per year (fixed)")
        st.write("**Calibrations:** 2 per year")
        if config.get('rote_visits', 0) > 0:
            st.write(f"**ROTE Visits:** {config['rote_visits']} per year")

    # Ancillary equipment with quantities
    if config.get('ancillary_items'):
        st.write("**Ancillary Equipment:**")
        for anc_type, qty in config['ancillary_items'].items():
            st.write(f"  • {anc_type.replace('_', ' ').title()} (×{qty})")

    # PDF Generation Section (ONLY for brake testers)
    if st.session_state.equipment_type == "brake_tester":
        st.markdown("---")
        st.subheader("📄 Generate PDF Contract")
        
        uploaded_pdf = st.file_uploader(
            "Upload brake tester contract template (PDF):",
            type=['pdf'],
            help="Upload either Standard or AFT Brake Tester template",
            key="pdf_template"
        )
        
        if uploaded_pdf:
            # Detect template type
            if "AFT" in uploaded_pdf.name.upper():
                template_type = "AFT"
                st.info("🔍 Detected: **AFT Brake Tester Template** (with pit jacks option)")
            else:
                template_type = "Standard"
                st.info("🔍 Detected: **Standard Brake Tester Template**")
            
            # Generate PDF button
            if st.button("📄 Generate Filled Contract", type="primary", key="gen_pdf"):
                try:
                    from utils.pdf_filler import fill_brake_tester_pdf
                    from config.pricing import get_pricing

                    # Get labour rates from Google Sheets
                    pricing_data = get_pricing(config.get('price_list', 'new'))
                    labour_rates = pricing_data.get('labour_rates', {}).get('brake_tester', {})

                    total_months = config.get('years', 1) * 12
                    correct_monthly_dd = total_contract / total_months

                    # Prepare result data with labour rates
                    pdf_result = {
                        'annual_cost': total_annual,
                        'monthly_dd': correct_monthly_dd,
                        'total_contract_cost': total_contract,
                        'labour_rates': labour_rates
                    }

                    # Fill the PDF
                    filled_pdf = fill_brake_tester_pdf(
                        template_file=uploaded_pdf,
                        template_type=template_type,
                        equipment_list=equipment_list,
                        config=config,
                        pricing_result=pdf_result
                    )

                    # Generate filename
                    customer_name = first_equipment.get('customer_name', 'Customer').replace(' ', '_')
                    filename = f"Brake_Tester_Contract_{customer_name}_{datetime.now().strftime('%Y%m%d')}.pdf"

                    # Download button
                    st.download_button(
                        label="⬇️ Download Filled Contract",
                        data=filled_pdf,
                        file_name=filename,
                        mime="application/pdf",
                        key="download_pdf"
                    )

                    st.success("✓ PDF generated successfully!")

                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
                    st.exception(e)  # Show full traceback for debugging

    st.markdown("---")

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("← Back to Options"):
            st.session_state.step = 6 if config['contract_type'] != 'pro2_warranty' else 4
            st.rerun()

    with col2:
        if st.button("🔄 Start New Quote"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.step = 1
            st.rerun()
def calculate_lift_contract(equipment, config):
    """Calculate lift contract pricing"""
    from calculators.lift_calculator import LiftCalculator
    from calculators.addons_calculator import AddonsCalculator
    from config.pricing import get_pricing
    
    # Get config values
    contract_type = config['contract_type']
    tier = config['tier']
    price_list = config['price_list']
    
    # Initialize calculator
    calc = LiftCalculator(
        contract_type=contract_type,
        tier=tier,
        quantity=equipment['quantity'],
        price_list=price_list,
        years=config['years'],
        pm_visits=config.get('pm_visits', 2)
    )
    
    # Add-ons with quantities
    addons_calc = None
    if (config.get('rote_visits', 0) > 0 or config.get('kluberplex_qty', 0) > 0 or
        config.get('lube_pots_qty', 0) > 0 or config.get('battery_plan_qty', 0) > 0 or
        config.get('ancillary_items')):

        addons_calc = AddonsCalculator(
            tier=tier,
            quantity=1.0,  # Changed from equipment['quantity'] - user specifies quantity directly!
            price_list=price_list,
            pm_visits=config.get('pm_visits', 2)
        )

        if config.get('rote_visits', 0) > 0:
            addons_calc.add_rote(visits=config['rote_visits'])

        # Add with quantities
        for _ in range(config.get('kluberplex_qty', 0)):
            addons_calc.add_kluberplex()

        for _ in range(config.get('lube_pots_qty', 0)):
            addons_calc.add_lube_pots()

        for _ in range(config.get('battery_plan_qty', 0)):
            addons_calc.add_battery_plan()

        # Ancillary with quantities
        for anc_type, qty in config.get('ancillary_items', {}).items():
            for _ in range(qty):
                addons_calc.add_ancillary(anc_type)

    # Calculate
    result = calc.calculate_total(
        equipment_type=equipment['description'],
        addons=addons_calc
    )
    
    # Apply intro offer if selected (FIRST YEAR ONLY)
    if config.get('intro_offer', False) and config.get('intro_option'):
        pricing = get_pricing(price_list)
        intro_offers = pricing.get('introductory_offers', {})
        intro_option = config['intro_option']
        
        if intro_option in intro_offers:
            intro_rate = intro_offers[intro_option]
            
            # Get normal rate for extra service
            normal_rate = pricing['lift_base_rates']['extra_service'][tier]
            
            # Add ROTE to normal rate if intro option includes it
            if intro_option == 'extra_1_rote':
                normal_rate += pricing['rote_rates']['1_visit'][tier]
            elif intro_option == 'extra_2_rote':
                normal_rate += pricing['rote_rates']['2_visits'][tier]
            
            # Apply PM visits multiplier
            pm_visits = config.get('pm_visits', 2)
            if pm_visits == 1:
                intro_rate = intro_rate * 0.5
                normal_rate = normal_rate * 0.5
            elif pm_visits == 3:
                intro_rate = intro_rate * 1.5
                normal_rate = normal_rate * 1.5
            elif pm_visits == 4:
                intro_rate = intro_rate * 2.0
                normal_rate = normal_rate * 2.0
            
            # Calculate first year savings
            first_year_intro = intro_rate * equipment['quantity']
            first_year_normal = normal_rate * equipment['quantity']
            first_year_savings = first_year_normal - first_year_intro
            
            # Adjust totals (only first year gets discount)
            result['annual_total'] = result['annual_total'] - first_year_savings
            result['total_contract_cost'] = result['total_contract_cost'] - first_year_savings
            result['monthly_dd'] = result['annual_total'] / 12
            result['pay_upfront'] = result['total_contract_cost']
            result['intro_offer_applied'] = True
            result['first_year_savings'] = round(first_year_savings, 2)
    
    return result
def calculate_brake_tester_contract(equipment, config):
    """Calculate brake tester contract pricing"""
    from calculators.brake_tester_calculator import BrakeTesterCalculator
    from calculators.addons_calculator import AddonsCalculator
    
    # Initialize calculator
    calc = BrakeTesterCalculator(
        tier=config['tier'],
        quantity=equipment['quantity'],
        price_list=config['price_list'],
        years=config['years']
    )
    
    # Add-ons
    addons_calc = None
    if config.get('rote_visits', 0) > 0 or config.get('ancillary_items'):
        addons_calc = AddonsCalculator(
            tier=config['tier'],
            quantity=1.0,  # Add-ons are per contract
            price_list=config['price_list'],
            pm_visits=2
        )
        
        if config.get('rote_visits', 0) > 0:
            addons_calc.add_rote(visits=config['rote_visits'])
        
        # Ancillary with quantities
        for anc_type, qty in config.get('ancillary_items', {}).items():
            for _ in range(qty):
                addons_calc.add_ancillary(anc_type)
    
    # Calculate - pass the calculator object
    result = calc.calculate_total(addons=addons_calc)
    
    return result
if __name__ == "__main__":
    main()
