"""
PDF Form Filler for Brake Tester and Lift Contracts
Fills PDF form fields with calculated contract data
"""

from pypdf import PdfReader, PdfWriter
from io import BytesIO
from datetime import datetime


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
    template_file.seek(0)
    reader = PdfReader(template_file)
    writer = PdfWriter()
    
    # Clone all pages
    writer.append(reader)
    
    # Get first equipment for customer info
    first_equipment = equipment_list[0]
    
    # Prepare field data
    field_data = {}
    
    # CUSTOMER INFO
    field_data['Company_name'] = first_equipment.get('customer_name', '')
    field_data['company_name'] = first_equipment.get('customer_name', '')
    
    # Format address
    address_1 = first_equipment.get('address_1', '')
    city = first_equipment.get('city', '')
    state = first_equipment.get('state', '').replace('.', '').replace('- -', '').strip()
    postcode = first_equipment.get('postcode', '')
    
    field_data['Company_address'] = address_1
    field_data['Company_address_2'] = city
    field_data['Company_address_3'] = state
    field_data['Company_address_4'] = postcode
    field_data['company_address'] = address_1
    field_data['company_address_2'] = city
    field_data['company_address_3'] = state
    field_data['company_address_4'] = postcode
    
    field_data['Contact_Name'] = first_equipment.get('customer_name', '')
    field_data['Contact_name'] = first_equipment.get('customer_name', '')
    field_data['contact_name'] = first_equipment.get('customer_name', '')
    field_data['Company_Code'] = first_equipment.get('customer_id', '')
    
    # EQUIPMENT INFO (Products 1-4 and Serial Numbers 1-4)
    # Get ancillary items from config
    ancillary_items = config.get('ancillary_items', {})
    
    # Format products and serials (includes ancillary)
    products, serials = format_lift_products_and_serials(equipment_list, ancillary_items)
    
    for i in range(4):
        prod_field = 'Product' if i == 0 else f'Product_{i+1}'
        serial_field = 'Serial_Number' if i == 0 else f'Serial_Number_{i+1}'
        
        field_data[prod_field] = products[i] if i < len(products) else ''
        field_data[serial_field] = serials[i] if i < len(serials) else ''
    
    # Total quantity
    total_qty = sum([eq.get('quantity', 1) for eq in equipment_list])
    field_data['Quantity'] = str(int(total_qty))
    
    # CONTRACT DETAILS
    field_data['Service_Contract_Type'] = format_contract_type(contract_type)
    field_data['Contract_Length'] = f"{config.get('years', 1)} Year{'s' if config.get('years', 1) > 1 else ''}"
    field_data['No_PM_Visits'] = str(config.get('pm_visits', 2))
    
    # ROTE visits (handle typo in some templates)
    rote_visits = config.get('rote_visits', 0)
    field_data['No_ROTE_Visits'] = str(rote_visits) if rote_visits > 0 else '0'
    field_data['No_ROTE_Vists'] = str(rote_visits) if rote_visits > 0 else '0'  # Typo version
    
    # Parts discount
    parts_discount = get_parts_discount(contract_type)
    field_data['Parts_Discount'] = f"{parts_discount}%"
    
    # PRICING
    monthly_dd = pricing_result.get('monthly_dd', 0)
    total_cost = pricing_result.get('total_contract_cost', 0)
    
    field_data['Monthly_DD'] = f"£{monthly_dd:,.2f}"
    field_data['Pay_Up_front'] = f"£{total_cost:,.2f}"
    
    # LABOUR RATES
    labour_rates = pricing_result.get('labour_rates', {})
    field_data['Call_Out_Cost'] = f"£{labour_rates.get('callout_first_hour', 0):.2f}"
    field_data['Travel_Labour'] = f"£{labour_rates.get('travel', 0):.2f}"
    field_data['TRAVEL LABOUR PER HOUR'] = f"£{labour_rates.get('additional_hours', 0):.2f}"
    field_data['LABOUR HOURLY RATE FOR MISUSE & DAMAGE'] = f"£{labour_rates.get('misuse_damage', 0):.2f}"
    
    # Fill all pages
    for page_num in range(len(writer.pages)):
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


def format_contract_type(contract_type):
    """Map contract type to display name"""
    mapping = {
        'standard_service': 'Standard Service',
        'extra_service': 'Extra Service',
        'fixed_labour': 'Fixed Labour',
        'pro2_warranty': 'PRO-2 Warranty'
    }
    return mapping.get(contract_type, contract_type)


def get_parts_discount(contract_type):
    """Get parts discount percentage for contract type"""
    discounts = {
        'standard_service': 10,
        'extra_service': 30,
        'fixed_labour': 35,
        'pro2_warranty': 0  # PRO-2 includes all parts
    }
    return discounts.get(contract_type, 0)


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
    
    template_file.seek(0)
    reader = PdfReader(template_file)
    writer = PdfWriter()
    
    # Clone everything
    writer.append(reader)
    
    # Get data
    first_equipment = equipment_list[0]
    address_line_1 = first_equipment.get('address_1', '')
    city = first_equipment.get('city', '')
    state = first_equipment.get('state', '')
    postcode = first_equipment.get('postcode', '')
    
    if state in ['.', '- -', 'nan', None]:
        state = ''
    
    total_quantity = sum([int(eq.get('quantity', 1)) for eq in equipment_list])
    labour_rates = pricing_result.get('labour_rates', {})
    contract_years = config.get('years', 1)
    total_contract_cost = pricing_result.get('total_contract_cost', 0)
    monthly_dd = pricing_result.get('monthly_dd', 0)
    
    # Get ancillary items from config
    ancillary_items = config.get('ancillary_items', {})

    # Format products and serials (includes ancillary)
    product_boxes, serial_boxes = format_products_and_serials(equipment_list, ancillary_items)
    
    # Form data
    form_data = {
        'company_name': first_equipment.get('customer_name', ''),
        'company_address': address_line_1,
        'company_address_2': city,
        'company_address_3': state,
        'company_address_4': postcode,
        'contact_name': config.get('contact_name', ''),
        'company_code': first_equipment.get('customer_id', ''),
        'Company_Code': first_equipment.get('customer_id', ''),
        'Product': product_boxes[0],
        'Product_2': product_boxes[1],
        'Product_3': product_boxes[2],
        'Product_4': product_boxes[3],
        'Quantity': str(total_quantity),
        'Serial_Number': serial_boxes[0],
        'Serial_Number_1': serial_boxes[0],
        'Serial_Number_2': serial_boxes[1],
        'Serial_Number_3': serial_boxes[2],
        'Serial_Number_4': serial_boxes[3],
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
        'Call_Out_Cost': f"£{labour_rates.get('callout_first_hour', 0):.2f}",
        'Call_Out_Cost 2': f"£{labour_rates.get('callout_first_hour', 0):.2f}",
        'Travel_Labour': f"£{labour_rates.get('travel', 0):.2f}",
        'Travel_Labour 2': f"£{labour_rates.get('travel', 0):.2f}",
        'Labour_Hourly_Rate': f"£{labour_rates.get('additional_hours', 0):.2f}",
        'Labour_Hourly_Rate 2': f"£{labour_rates.get('additional_hours', 0):.2f}",
        'TRAVEL LABOUR PER HOUR': f"£{labour_rates.get('travel', 0):.2f}",
        'LABOUR HOURLY RATE FOR MISUSE & DAMAGE': f"£{labour_rates.get('misuse_damage', 0):.2f}",
        'Monthly_DD': f"£{monthly_dd:.2f}",
        'Monthly_DD 2': f"£{monthly_dd:.2f}",
        'Pay_Up_front': f"£{total_contract_cost:.2f}",
        'Pay_Up_front 2': f"£{total_contract_cost:.2f}",
    }

    
    # Fill pages
    writer.update_page_form_field_values(writer.pages[0], form_data)
    if len(writer.pages) > 1:
        writer.update_page_form_field_values(writer.pages[1], form_data)
    
    # Write
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output
