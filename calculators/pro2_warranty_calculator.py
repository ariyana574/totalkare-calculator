"""
PRO-2 Warranty Package Calculator
(Separate from standard service contracts)
"""

from config.pricing import get_pricing


class Pro2WarrantyCalculator:
    """Calculate PRO-2 warranty package pricing"""
    
    def __init__(self, warranty_type: str, units: int, years: int, price_list: str = "new"):
        """
        Args:
            warranty_type: "standard_2_year", "full_3_year", or "full_5_year"
            units: Total number of PRO-2 lifts
            years: Contract duration (2, 3, or 5)
        """
        self.warranty_type = warranty_type
        self.units = units
        self.years = years
        self.price_list = price_list
        
        # Get correct pricing
        from config.pricing import get_pricing
        pricing = get_pricing(price_list)
        
        self.rate_per_unit = pricing["pro2_warranty_rates"][warranty_type]
        
    def calculate_total(self) -> dict:
        """Calculate total warranty cost"""
        annual_cost = self.rate_per_unit * self.units
        total_contract = annual_cost * self.years
        monthly_dd = annual_cost / 12
        
        return {
            "warranty_type": self.warranty_type,
            "units": self.units,
            "years": self.years,
            "rate_per_unit_per_year": self.rate_per_unit,
            "annual_cost": round(annual_cost, 2),
            "total_contract_cost": round(total_contract, 2),
            "monthly_dd": round(monthly_dd, 2),
            "parts_included": True,
            "labour_included": True
        }


# Quick function
def calculate_pro2_warranty(warranty_type: str, units: int, years: int) -> dict:
    """Quick PRO-2 warranty calculation"""
    calc = Pro2WarrantyCalculator(warranty_type, units, years)
    return calc.calculate_total()