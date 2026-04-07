"""
TotalKare Service Contract Calculator - Admin Page
Manage pricing tables via Google Sheets
"""

import streamlit as st
import pandas as pd
from config.sheets_config import (
    get_sheet_data,
    update_sheet_data,
    add_ancillary_item
)

# Set page config
st.set_page_config(
    page_title="TotalKare Admin",
    page_icon="🔧",
    layout="wide"
)

# Simple password protection
def check_password():
    """Returns True if password is correct"""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    
    if not st.session_state.password_correct:
        st.title("🔐 Admin Login")
        password = st.text_input("Enter admin password:", type="password")
        
        if st.button("Login"):
            # Get password from secrets - NO fallback!
            if "admin" not in st.secrets or "password" not in st.secrets["admin"]:
                st.error("⚠️ Admin password not configured. Please add to secrets.")
                st.stop()
            
            correct_password = st.secrets["admin"]["password"]
            
            if password == correct_password:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("Incorrect password")
        return False
    return True


def main():
    """Main admin interface"""
    if not check_password():
        return
    
    st.title("🔧 TotalKare Admin Dashboard")


    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("Logout"):
            st.session_state.password_correct = False
            st.rerun()
    with col2:
        if st.button("🔄 Clear Cache"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✓ Cleared!")
    with col3:
        st.empty() 

    st.markdown("---")
    
    # Navigation
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "Lift Rates",
        "Brake Tester Rates",
        "ROTE Rates",
        "Add-ons",
        "Ancillary Equipment",
        "Labour Rates",
        "Intro Offers",
        "PRO-2 Warranty",
        "Add New Ancillary"
    ])
    
    # Tab 1: Lift Rates
    with tab1:
        st.subheader("Vehicle Lift Base Rates")
        df = get_sheet_data("LiftRates")
        
        if df is not None:
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="fixed",
                key="lift_rates_editor"
            )
            
            if st.button("Save Lift Rates", key="save_lift"):
                if update_sheet_data("LiftRates", edited_df):
                    st.success("✓ Lift rates updated successfully!")
                    st.cache_resource.clear()
                else:
                    st.error("Failed to update lift rates")
    
    # Tab 2: Brake Tester Rates
    with tab2:
        st.subheader("Brake Tester Base Rates")
        df = get_sheet_data("BrakeTesterRates")
        
        if df is not None:
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="fixed",
                key="brake_rates_editor"
            )
            
            if st.button("Save Brake Tester Rates", key="save_brake"):
                if update_sheet_data("BrakeTesterRates", edited_df):
                    st.success("✓ Brake tester rates updated!")
                    st.cache_resource.clear()
                else:
                    st.error("Failed to update rates")
    
    # Tab 3: ROTE Rates
    with tab3:
        st.subheader("ROTE (Reports of Thorough Examination) Rates")
        df = get_sheet_data("ROTERates")
        
        if df is not None:
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="fixed",
                key="rote_rates_editor"
            )
            
            if st.button("Save ROTE Rates", key="save_rote"):
                if update_sheet_data("ROTERates", edited_df):
                    st.success("✓ ROTE rates updated!")
                    st.cache_resource.clear()
                else:
                    st.error("Failed to update rates")
    
    # Tab 4: Add-ons
    with tab4:
        st.subheader("Add-ons (Kluberplex, Lube Pots, Battery Plan)")
        df = get_sheet_data("AddonsRates")
        
        if df is not None:
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="fixed",
                key="addons_editor"
            )
            
            if st.button("Save Add-on Rates", key="save_addons"):
                if update_sheet_data("AddonsRates", edited_df):
                    st.success("✓ Add-on rates updated!")
                    st.cache_resource.clear()
                else:
                    st.error("Failed to update rates")
    
    # Tab 5: Ancillary Equipment
    with tab5:
        st.subheader("Ancillary Equipment Rates")
        df = get_sheet_data("AncillaryRates")
        
        if df is not None:
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic",
                key="ancillary_editor"
            )
            
            if st.button("Save Ancillary Rates", key="save_ancillary"):
                if update_sheet_data("AncillaryRates", edited_df):
                    st.success("✓ Ancillary rates updated!")
                    st.cache_resource.clear()
                else:
                    st.error("Failed to update rates")
    
    # Tab 6: Labour Rates
    with tab6:
        st.subheader("Labour Rates")
        df = get_sheet_data("LabourRates")
        
        if df is not None:
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="fixed",
                key="labour_editor"
            )
            
            if st.button("Save Labour Rates", key="save_labour"):
                if update_sheet_data("LabourRates", edited_df):
                    st.success("✓ Labour rates updated!")
                    st.cache_resource.clear()
                else:
                    st.error("Failed to update rates")
    
    # Tab 7: Intro Offers
    with tab7:
        st.subheader("Introductory Offers")
        df = get_sheet_data("IntroOffers")
        
        if df is not None:
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="fixed",
                key="intro_editor"
            )
            
            if st.button("Save Intro Offers", key="save_intro"):
                if update_sheet_data("IntroOffers", edited_df):
                    st.success("✓ Intro offers updated!")
                    st.cache_resource.clear()
                else:
                    st.error("Failed to update rates")
    
    # Tab 8: PRO-2 Warranty
    with tab8:
        st.subheader("PRO-2 Warranty Rates")
        df = get_sheet_data("PRO2Warranty")
        
        if df is not None:
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="fixed",
                key="pro2_editor"
            )
            
            if st.button("Save PRO-2 Rates", key="save_pro2"):
                if update_sheet_data("PRO2Warranty", edited_df):
                    st.success("✓ PRO-2 rates updated!")
                    st.cache_resource.clear()
                else:
                    st.error("Failed to update rates")
    
    # Tab 9: Add New Ancillary
    with tab9:
        st.subheader("Add New Ancillary Equipment")
        
        st.write("Add a new ancillary equipment type with pricing:")
        
        equipment_name = st.text_input(
            "Equipment Type Name (use underscore for spaces, e.g., 'new_equipment_type'):",
            key="new_anc_name"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            price_new = st.number_input(
                "New Price List (2025):",
                min_value=0.0,
                step=1.0,
                key="new_anc_price_new"
            )
        
        with col2:
            price_old = st.number_input(
                "Old Price List (2023/24):",
                min_value=0.0,
                step=1.0,
                key="new_anc_price_old"
            )
        
        if st.button("Add Ancillary Equipment", key="add_anc_btn"):
            if equipment_name and price_new > 0 and price_old > 0:
                if add_ancillary_item(equipment_name, price_new, price_old):
                    st.success(f"✓ Added {equipment_name} successfully!")

                    # ADD THESE TWO LINES:
                    st.cache_data.clear()
                    st.cache_resource.clear()

                    st.info("Cache cleared! This equipment will now appear in the main calculator!")
                    st.rerun()  # Refresh the page to show new item in the table above
                else:
                    st.error("Failed to add equipment")
            else:
                st.warning("Please fill in all fields with valid values")

if __name__ == "__main__":
    main()