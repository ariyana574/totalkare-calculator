"""
PDF Form Filler for Brake Tester and Lift Contracts
Fills PDF form fields with calculated contract data
OPTIMIZED VERSION
"""

import functools


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@functools.lru_cache(maxsize=32)
def format_contract_type(contract_type):
    """Map contract type to display name"""
    mapping = {
        'standard_service': 'Standard Service',
        'extra_service': 'Extra Service',
        'fixed_labour': 'Fixed Labour',
        'pro2_warranty': 'PRO-2 Warranty'
    }
    return mapping.get(contract_type, contract_type)


@functools.lru_cache(maxsize=32)
def get_parts_discount(contract_type):
    """Get parts discount percentage for contract type"""
    discounts = {
        'standard_service': 10,
        'extra_service': 30,
        'fixed_labour': 35,
        'pro2_warranty': 0  # PRO-2 includes all parts
    }
    return discounts.get(contract_type, 0)


def format_quantity(qty):
    """Format quantity - integer if whole number, decimal otherwise"""
    return str(int(qty)) if qty == int(qty) else str(qty)


# ============================================================================
# LIFT PDF FILLING
# ============================================================================

def fill_lift_pdf(template_file, contract_type, equipment_list, config, pricing_result):
    """
    Fill lift contract PDF with equipment and pricing data
    
    Args:
        template_file: Uploaded PDF template file
        contract_type: Contract type (standard_service, extra_service, fixed_labour, pro2_warranty)
        equipment_list: List of equipment dicts with item, description, serial, quantity
        config: Contract configuration dict
        pricing_result: Pricing calculation result dict
    
    Returns:
        Filled PDF as bytes
    """
    from pypdf import PdfReader, PdfWriter
    from io import BytesIO
    
    template_file.seek(0)
    reader = PdfReader(template_file)
    writer = PdfWriter()
    writer.append(reader)
    
    # Pre-compute common values
    first_equipment = equipment_list[0]
    customer_name = first_equipment.get('customer_name', '')
    customer_id = first_equipment.get('customer_id', '')
    
    # Address components
    address_1 = first_equipment.get('address_1', '')
    city = first_equipment.get('city', '')
    state = first_equipment.get('state', '').replace('.', '').replace('- -', '').strip()
    postcode = first_equipment.get('postcode', '')
    
    # Labour rates
    labour_rates = pricing_result.get('labour_rates', {})
    callout = labour_rates.get('callout_first_hour', 0)
    travel = labour_rates.get('travel', 0)
    additional = labour_rates.get('additional_hours', 0)
    misuse = labour_rates.get('misuse_damage', 0)
    
    # Pricing
    monthly_dd = pricing_result.get('monthly_dd', 0)
    total_cost = pricing_result.get('total_contract_cost', 0)
    
    # Products and serials
    ancillary_items = config.get('ancillary_items', {})
    products, serials = format_lift_products_and_serials(equipment_list, ancillary_items)
    
    # Total quantity
    total_qty = sum([float(eq.get('quantity', 1)) for eq in equipment_list])
    quantity_str = format_quantity(total_qty)
    
    # Contract details
    years = config.get('years', 1)
    pm_visits = config.get('pm_visits', 2)
    rote_visits = config.get('rote_visits', 0)
    
    # Build field data dictionary
    field_data = {
        # Customer info
        'Company_name': customer_name,
        'company_name': customer_name,
        'Contact_Name': customer_name,
        'Contact_name': customer_name,
        'contact_name': customer_name,
        'Company_Code': customer_id,
        
        # Address
        'Company_address': address_1,
        'Company_address_2': city,
        'Company_address_3': state,
        'Company_address_4': postcode,
        'company_address': address_1,
        'company_address_2': city,
        'company_address_3': state,
        'company_address_4': postcode,
        
        # Equipment
        'Product': products[0],
        'Product_2': products[1],
        'Product_3': products[2],
        'Product_4': products[3],
        'Serial_Number': serials[0],
        'Serial_Number_2': serials[1],
        'Serial_Number_3': serials[2],
        'Serial_Number_4': serials[3],
        'Quantity': quantity_str,
        
        # Contract details
        'Service_Contract_Type': format_contract_type(contract_type),
        'Contract_Length': f"{years} Year{'s' if years > 1 else ''}",
        'No_PM_Visits': str(pm_visits),
        'No_ROTE_Visits': str(rote_visits),
        'No_ROTE_Vists': str(rote_visits),  # Typo version in some templates
        'Parts_Discount': f"{get_parts_discount(contract_type)}%",
        
        # Pricing
        'Monthly_DD': f"£{monthly_dd:,.2f}",
        'Pay_Up_front': f"£{total_cost:,.2f}",
        
        # Labour rates
        'Call_Out_Cost': f"£{callout:.2f}",
        'Travel_Labour': f"£{travel:.2f}",
        'TRAVEL LABOUR PER HOUR': f"£{additional:.2f}",
        'LABOUR HOURLY RATE FOR MISUSE & DAMAGE': f"£{misuse:.2f}",
    }
    
    # Fill only first 2 pages (most templates only have fields on first 2 pages)
    for page_num in range(min(2, len(writer.pages))):
        writer.update_page_form_field_values(writer.pages[page_num], field_data)
    
    # Write to bytes
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    
    return output


def format_lift_products_and_serials(equipment_list, ancillary_items=None):
    """
    Format lift equipment into product and serial lists for PDF boxes
    Each box can hold 2 items, comma-separated
    Includes ancillary items after lifts
    
    Args:
        equipment_list: List of lift equipment
        ancillary_items: Dict of ancillary items {type: quantity} (optional)
    
    Returns:
        (products, serials) - Lists of formatted strings for boxes 1-4
    """
    # Build combined list: lifts first, then ancillary
    all_items = []
    
    # Add lifts with serials
    for eq in equipment_list:
        item = eq.get('item', '')
        serial = eq.get('serial', '').strip()
        qty = eq.get('quantity', 1)
        
        # Add quantity notation if > 1
        if qty > 1:
            item = f"{item} x{int(qty)}"
        
        all_items.append({
            'product': item,
            'serial': serial,
            'is_ancillary': False
        })
    
    # Add ancillary items (with quantities if > 1)
    if ancillary_items:
        for anc_type, qty in ancillary_items.items():
            # Format: "Shaker Plates x2" or just "Shaker Plates" if qty=1
            display_name = anc_type.replace('_', ' ').title()
            if qty > 1:
                display_name = f"{display_name} x{qty}"
            
            all_items.append({
                'product': display_name,
                'serial': '',  # No serial for ancillary
                'is_ancillary': True
            })
    
    # Now distribute into boxes (2 per box)
    products = []
    serials = []
    
    for i in range(0, len(all_items), 2):
        box_items = all_items[i:i+2]
        
        # Format products for this box
        prod_parts = []
        serial_parts = []
        
        for item_data in box_items:
            prod_parts.append(item_data['product'])
            
            # Only add serial if not empty
            if item_data['serial']:
                serial_parts.append(item_data['serial'])
        
        products.append(', '.join(prod_parts))
        serials.append(', '.join(serial_parts))
    
    # Pad to 4 boxes
    while len(products) < 4:
        products.append('')
        serials.append('')
    
    return products, serials


# ============================================================================
# BRAKE TESTER PDF FILLING
# ============================================================================

def get_product_code(equipment):
    """Extract product code - truncate if too long"""
    item = equipment.get('item', equipment.get('description', ''))
    if len(item) > 40:
        return item[:40]
    return item


def format_products_and_serials(equipment_list, ancillary_items):
    """
    Format products and serial numbers for PDF boxes
    Box 1: First brake tester only
    Box 2-4: Up to 2 items per box (brake testers + ancillary)
    
    Args:
        equipment_list: List of brake tester equipment
        ancillary_items: Dict of ancillary items {type: quantity}
    
    Returns:
        tuple: (product_boxes, serial_boxes) - each is list of 4 strings
    """
    # Build combined list: brake testers first, then ancillary
    all_items = []
    
    # Add brake testers with serials
    for equipment in equipment_list:
        all_items.append({
            'product': get_product_code(equipment),
            'serial': equipment.get('serial', ''),
            'is_ancillary': False
        })
    
    # Add ancillary items (with quantities if > 1)
    for anc_type, qty in ancillary_items.items():
        # Format: "Shaker Plates x2" or just "Shaker Plates" if qty=1
        display_name = anc_type.replace('_', ' ').title()
        if qty > 1:
            display_name = f"{display_name} x{qty}"
        
        all_items.append({
            'product': display_name,
            'serial': '',  # No serial for ancillary
            'is_ancillary': True
        })
    
    # Now distribute into boxes
    products = []
    serials = []
    
    # Box 1: First item only (usually first brake tester)
    if len(all_items) >= 1:
        products.append(all_items[0]['product'])
        serials.append(all_items[0]['serial'])
    else:
        products.append('')
        serials.append('')
    
    # Box 2: Items 2-3
    box2_products = []
    box2_serials = []
    if len(all_items) >= 2:
        box2_products.append(all_items[1]['product'])
        box2_serials.append(all_items[1]['serial'])
    if len(all_items) >= 3:
        box2_products.append(all_items[2]['product'])
        box2_serials.append(all_items[2]['serial'])
    
    products.append(', '.join(box2_products) if box2_products else '')
    # Only include serials that aren't empty
    box2_serials_filtered = [s for s in box2_serials if s]
    serials.append(', '.join(box2_serials_filtered) if box2_serials_filtered else '')
    
    # Box 3: Items 4-5
    box3_products = []
    box3_serials = []
    if len(all_items) >= 4:
        box3_products.append(all_items[3]['product'])
        box3_serials.append(all_items[3]['serial'])
    if len(all_items) >= 5:
        box3_products.append(all_items[4]['product'])
        box3_serials.append(all_items[4]['serial'])
    
    products.append(', '.join(box3_products) if box3_products else '')
    box3_serials_filtered = [s for s in box3_serials if s]
    serials.append(', '.join(box3_serials_filtered) if box3_serials_filtered else '')
    
    # Box 4: Items 6-7
    box4_products = []
    box4_serials = []
    if len(all_items) >= 6:
        box4_products.append(all_items[5]['product'])
        box4_serials.append(all_items[5]['serial'])
    if len(all_items) >= 7:
        box4_products.append(all_items[6]['product'])
        box4_serials.append(all_items[6]['serial'])
    
    products.append(', '.join(box4_products) if box4_products else '')
    box4_serials_filtered = [s for s in box4_serials if s]
    serials.append(', '.join(box4_serials_filtered) if box4_serials_filtered else '')
    
    return products, serials


def fill_brake_tester_pdf(template_file, template_type, equipment_list, config, pricing_result):
    """Fill brake tester PDF - keeps fields editable but shows formatting"""
    from pypdf import PdfReader, PdfWriter
    from io import BytesIO
    
    template_file.seek(0)
    reader = PdfReader(template_file)
    writer = PdfWriter()
    writer.append(reader)
    
    # Pre-compute common values
    first_equipment = equipment_list[0]
    customer_name = first_equipment.get('customer_name', '')
    customer_id = first_equipment.get('customer_id', '')
    
    # Address components
    address_line_1 = first_equipment.get('address_1', '')
    city = first_equipment.get('city', '')
    state = first_equipment.get('state', '')
    postcode = first_equipment.get('postcode', '')
    
    if state in ['.', '- -', 'nan', None]:
        state = ''
    
    # Quantity
    total_quantity = sum([float(eq.get('quantity', 1)) for eq in equipment_list])
    quantity_str = format_quantity(total_quantity)
    
    # Labour rates
    labour_rates = pricing_result.get('labour_rates', {})
    callout = labour_rates.get('callout_first_hour', 0)
    travel = labour_rates.get('travel', 0)
    additional = labour_rates.get('additional_hours', 0)
    misuse = labour_rates.get('misuse_damage', 0)
    
    # Pricing
    contract_years = config.get('years', 1)
    total_contract_cost = pricing_result.get('total_contract_cost', 0)
    monthly_dd = pricing_result.get('monthly_dd', 0)
    
    # Products and serials
    ancillary_items = config.get('ancillary_items', {})
    product_boxes, serial_boxes = format_products_and_serials(equipment_list, ancillary_items)
    
    # Build form data dictionary
    form_data = {
        # Customer info
        'company_name': customer_name,
        'contact_name': config.get('contact_name', ''),
        'company_code': customer_id,
        'Company_Code': customer_id,
        
        # Address
        'company_address': address_line_1,
        'company_address_2': city,
        'company_address_3': state,
        'company_address_4': postcode,
        
        # Equipment
        'Product': product_boxes[0],
        'Product_2': product_boxes[1],
        'Product_3': product_boxes[2],
        'Product_4': product_boxes[3],
        'Quantity': quantity_str,
        'Serial_Number': serial_boxes[0],
        'Serial_Number_1': serial_boxes[0],
        'Serial_Number_2': serial_boxes[1],
        'Serial_Number_3': serial_boxes[2],
        'Serial_Number_4': serial_boxes[3],
        
        # Contract details
        'Service_Contract_Type': 'Brake Tester Service',
        'Service_Contract_Type 2': 'Brake Tester Service',
        'Contract_Length': f"{contract_years} Year{'s' if contract_years > 1 else ''}",
        'Contract_Length 2': f"{contract_years} Year{'s' if contract_years > 1 else ''}",
        'No_PM_Visits': '2',
        'No_PM_Visits 2': '2',
        'Annum_Calibration': '2',
        'Annum_Calibration 2': '2',
        'Parts_Discount': '30%',
        'Parts_Discount 2': '30%',
        
        # Labour rates
        'Call_Out_Cost': f"£{callout:.2f}",
        'Call_Out_Cost 2': f"£{callout:.2f}",
        'Travel_Labour': f"£{travel:.2f}",
        'Travel_Labour 2': f"£{travel:.2f}",
        'Labour_Hourly_Rate': f"£{additional:.2f}",
        'Labour_Hourly_Rate 2': f"£{additional:.2f}",
        'TRAVEL LABOUR PER HOUR': f"£{travel:.2f}",
        'LABOUR HOURLY RATE FOR MISUSE & DAMAGE': f"£{misuse:.2f}",
        
        # Pricing
        'Monthly_DD': f"£{monthly_dd:.2f}",
        'Monthly_DD 2': f"£{monthly_dd:.2f}",
        'Pay_Up_front': f"£{total_contract_cost:.2f}",
        'Pay_Up_front 2': f"£{total_contract_cost:.2f}",
    }
    
    # Fill only first 2 pages (brake tester templates only have fields on first 2 pages)
    for page_num in range(min(2, len(writer.pages))):
        writer.update_page_form_field_values(writer.pages[page_num], form_data)
    
    # Write to bytes
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    
    return output