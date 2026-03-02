"""
Special Pricing Rules & Adjustments
"""

# ============================================
# SERVICE VISIT MULTIPLIERS
# ============================================

SERVICE_MULTIPLIERS = {
    "half_service": 0.5,        # Only 1 service instead of 2
    "g8_outdoor": 2.0,          # G8/Fixed/Outdoor (4 services)
    "g9": 1.5                   # G9 lifts (3 services)
}

# ============================================
# EXCEPTIONAL AREAS (5-day lead time)
# ============================================

EXCEPTIONAL_POSTCODES = [
    "AB", "DD", "HS", "IM", "IV", "JE", "GG", "GY",
    "KW", "KY", "PA", "PH", "ZE"
]

# ============================================
# ISLANDS (Special restrictions)
# ============================================

ISLAND_AREAS = {
    "shetlands": {
        "allowed_contracts": ["extra_service"],
        "visits_per_year": 1,  # Only 1 visit
        "rote_available": False,
        "note": "Shetlands only 1 visit per year"
    },
    "isle_of_man": {
        "allowed_contracts": ["extra_service"],
        "visits_per_year": 2,
        "rote_available": False,
        "note": "Extra contracts only, no ROTE"
    },
    "isle_of_wight": {
        "allowed_contracts": ["extra_service"],
        "visits_per_year": 2,
        "rote_available": False,
        "note": "Extra contracts only, no ROTE"
    },
    "jersey": {
        "allowed_contracts": ["extra_service"],
        "visits_per_year": 2,
        "rote_available": False,
        "note": "Extra contracts only, no ROTE"
    },
    "guernsey": {
        "allowed_contracts": ["extra_service"],
        "visits_per_year": 2,
        "rote_available": False,
        "note": "Extra contracts only, no ROTE"
    }
}

# ============================================
# EQUIPMENT TYPE RULES
# ============================================

EQUIPMENT_RULES = {
    "g8_galv_outdoor": {
        "requires_4_services": True,
        "multiplier": 2.0,
        "warning": "G8/GALV/Outdoor lifts MUST have 4 visits or warranty is void"
    },
    "g9": {
        "requires_3_services": True,
        "multiplier": 1.5,
        "warning": "G9 lifts require 3 services per year"
    }
}

# ============================================
# INTRODUCTORY OFFERS (First year only)
# ============================================

INTRODUCTORY_OFFERS = {
    "extra_service": 432,       # Normal: £540
    "extra_1_rote": 624,
    "extra_2_rote": 780,
    "brake_tester": 850         # Normal: £1,092
}

# ============================================
# VALIDATION RULES
# ============================================

def is_exceptional_area(postcode: str) -> bool:
    """Check if postcode is in exceptional area"""
    if not postcode:
        return False
    # Check first 2-3 characters
    prefix = postcode[:2].upper()
    return prefix in EXCEPTIONAL_POSTCODES

def requires_special_servicing(equipment_type: str) -> dict:
    """Check if equipment needs special servicing"""
    equipment_type_lower = equipment_type.lower()
    
    # Check G9 FIRST (before G8/washbay check)
    if "g9" in equipment_type_lower:
        return EQUIPMENT_RULES["g9"]
    elif any(term in equipment_type_lower for term in ["g8", "galv", "washbay", "outdoor"]):
        return EQUIPMENT_RULES["g8_galv_outdoor"]
    else:
        return {"requires_4_services": False, "requires_3_services": False}
def get_island_restrictions(postcode: str) -> dict:
    """Get restrictions for island locations"""
    postcode_upper = postcode.upper() if postcode else ""
    
    # Simple checks (you might need more sophisticated logic)
    if "ZE" in postcode_upper:  # Shetlands
        return ISLAND_AREAS["shetlands"]
    elif "IM" in postcode_upper:  # Isle of Man
        return ISLAND_AREAS["isle_of_man"]
    elif "PO" in postcode_upper:  # Isle of Wight
        return ISLAND_AREAS["isle_of_wight"]
    elif "JE" in postcode_upper:  # Jersey
        return ISLAND_AREAS["jersey"]
    elif "GY" in postcode_upper or "GG" in postcode_upper:  # Guernsey
        return ISLAND_AREAS["guernsey"]

    return None