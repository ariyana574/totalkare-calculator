"""
Brake Tester Contract Calculator - WITH EXTENDED WARRANTY SUPPORT
"""

from config.pricing import get_pricing
from calculators.addons_calculator import AddonsCalculator


class BrakeTesterCalculator:
    """Calculate pricing for brake tester contracts"""
    
    def __init__(self, tier: str, quantity: float, price_list: str = "new", years: int = 1):
        """
        Initialize calculator
            
        Args:
            tier: "one_lift", "multi_sets", or "national_accounts"
            quantity: From NetSuite
            price_list: "new", "old", or "new_extended_warranty"
            years: Contract duration
        """
        self.tier = tier
        self.quantity = quantity
        self.price_list = price_list
        self.years = years
        
        # Get correct pricing from Google Sheets
        pricing = get_pricing('new')  # ✅ Always get 'new' pricing first
        
        # ✅ Try multiple locations for brake tester rates
        brake_rates = pricing.get("brake_tester_rates", {})
        
        # Check if extended warranty
        if price_list == 'new_extended_warranty':
            # Try to get extended warranty rates
            if 'new_extended_warranty' in brake_rates:
                # Found it in brake_tester_rates dict
                tier_rates = brake_rates.get('new_extended_warranty', {})
                self.base_rate = tier_rates.get(tier, 0)
            else:
                # Manual fallback - extended warranty pricing
                extended_rates = {
                    'one_lift': 1500,
                    'multi_sets': 1440,
                    'national_accounts': 1392
                }
                self.base_rate = extended_rates.get(tier, 0)
        else:
            # Standard pricing (new or old)
            base_rates = pricing.get("brake_tester_base_rates", {})
            self.base_rate = base_rates.get(tier, 0)
            
            # If not found, try the other structure
            if self.base_rate == 0 and price_list in brake_rates:
                tier_rates = brake_rates.get(price_list, {})
                self.base_rate = tier_rates.get(tier, 0)
        
        # Validate we got a rate
        if self.base_rate == 0:
            raise ValueError(f"No pricing found for tier '{tier}' with price_list '{price_list}'. Check Google Sheets!")
        
        self.parts_discount = pricing.get("parts_discounts", {}).get("brake_tester", 30)
        
    def calculate_total(self, addons: AddonsCalculator = None) -> dict:
        """
        Calculate total brake tester contract cost
        
        Args:
            addons: AddonsCalculator with ancillary equipment
            
        Returns:
            Complete pricing breakdown
        """
        # Base rate per unit
        per_unit_base = self.base_rate
        
        # Add ancillary equipment (if any)
        addon_total = 0
        addon_breakdown = []
        
        if addons:
            addon_info = addons.get_breakdown()
            addon_total = addon_info["total_per_unit"]
            addon_breakdown = addon_info["addons"]
        
        # Total per unit
        per_unit_total = per_unit_base + addon_total
        
        # Multiply by quantity
        annual_total = per_unit_total * self.quantity

        total_contract_cost = annual_total * self.years

        monthly_dd = annual_total / 12
        
        return {
            "contract_type": "brake_tester",
            "tier": self.tier,
            "quantity": self.quantity,
            "years": self.years,
            "base_rate_per_unit": self.base_rate,
            "ancillary_per_unit": addon_total,
            "ancillary_breakdown": addon_breakdown,
            "total_per_unit": per_unit_total,
            "annual_total": round(annual_total, 2),
            "total_contract_cost": round(total_contract_cost, 2),
            "monthly_dd": round(monthly_dd, 2),
            "pay_upfront": round(total_contract_cost, 2), 
            "parts_discount": self.parts_discount,
            "pm_visits_per_year": 2,
            "calibrations_per_year": 2,
            "labour_included": False,
            "price_list": self.price_list
        }
    
    def get_labour_rates(self) -> dict:
        """Get labour rates for brake testers"""
        pricing = get_pricing('new')
        return pricing.get("labour_rates", {}).get("brake_tester", {})