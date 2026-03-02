"""
Brake Tester Contract Calculator
"""

from config.pricing import get_pricing
from calculators.addons_calculator import AddonsCalculator


class BrakeTesterCalculator:
    """Calculate pricing for brake tester contracts"""
    
    def __init__(self, tier: str, quantity: float, price_list: str = "new",  years: int = 1):
        """
        Initialize calculator
            
        Args:
            tier: "one_lift", "multi_sets", or "national_accounts"
            quantity: From NetSuite
        """
        self.tier = tier
        self.quantity = quantity
        self.price_list = price_list
        self.years = years

        
        # Get correct pricing
        from config.pricing import get_pricing
        pricing = get_pricing(price_list)
        
        self.base_rate = pricing["brake_tester_base_rates"][tier]
        self.parts_discount = pricing["parts_discounts"]["brake_tester"]
        
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
            "labour_included": False
        }
    
    def get_labour_rates(self) -> dict:
        """Get labour rates for brake testers"""
        from config.pricing import get_pricing
        pricing = get_pricing(self.price_list)
        return pricing["labour_rates"]["brake_tester"]