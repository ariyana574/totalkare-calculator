"""
Vehicle Lift Contract Calculator
"""

from config.pricing import get_pricing
from config.rules import SERVICE_MULTIPLIERS, requires_special_servicing


class LiftCalculator:
    """Calculate pricing for vehicle lift contracts"""
    
    def __init__(self, contract_type: str, tier: str, quantity: float, price_list: str = "new", years: int = 1, pm_visits: int = 2):
        """
        Initialize calculator
        
        Args:
            contract_type: "standard_service", "extra_service", or "fixed_labour"
            tier: "one_lift", "multi_sets", or "national_accounts"
            quantity: From NetSuite (e.g., 0.25, 1.0, 1.5, 6.0)
        """
        self.contract_type = contract_type
        self.tier = tier
        self.quantity = quantity
        self.price_list = price_list
        self.years = years
        self.pm_visits = pm_visits

        # Get correct pricing
        from config.pricing import get_pricing
        pricing = get_pricing(price_list)

        self.base_rate = pricing["lift_base_rates"][contract_type][tier]
        self.parts_discount = pricing["parts_discounts"][contract_type]
        
    def calculate_base_cost(self, equipment_type: str = None) -> dict:
        """
        Calculate base contract cost
        
        Args:
            equipment_type: Equipment description (checks for G8, G9, etc.)
            
        Returns:
            dict with base_rate, multiplier, adjusted_base
        """
        multiplier = 1.0
        adjustment_reason = None
        
        # Check for special servicing requirements
        if equipment_type:
            rules = requires_special_servicing(equipment_type)
            
            if rules.get("requires_4_services"):
                multiplier = SERVICE_MULTIPLIERS["g8_outdoor"]
                adjustment_reason = "G8/Outdoor (4 services required)"
            elif rules.get("requires_3_services"):
                multiplier = SERVICE_MULTIPLIERS["g9"]
                adjustment_reason = "G9 (3 services required)"
        
        adjusted_base = self.base_rate * multiplier
        
        return {
            "base_rate": self.base_rate,
            "multiplier": multiplier,
            "adjustment_reason": adjustment_reason,
            "adjusted_base_per_unit": adjusted_base
        }
    
    def calculate_total(self, equipment_type: str = None,
                   addons = None) -> dict:
        """Calculate total contract cost"""
        # Get base cost with adjustments
        base_calc = self.calculate_base_cost(equipment_type)
        adjusted_base = base_calc["adjusted_base_per_unit"]

        # Only apply PM visits multiplier if NOT G8/G9 (they're already adjusted)
        if base_calc["multiplier"] == 1.0:  # Normal lift - no G8/G9 detected
            if self.pm_visits == 1:
                adjusted_base = adjusted_base * 0.5  # Half price for 1 visit
            elif self.pm_visits == 3:
                adjusted_base = adjusted_base * 1.5  # 1.5x for 3 visits
            elif self.pm_visits == 4:
                adjusted_base = adjusted_base * 2.0  # Double for 4 visits
            # else: pm_visits == 2 (default, no change)
        # If G8/G9 detected, base_calc already has the correct multiplier applied

        actual_pm_visits = self.pm_visits

        # Add optional add-ons (if provided)
        addon_total = 0
        if addons is not None:
            if hasattr(addons, 'get_breakdown'):
                addon_breakdown = addons.get_breakdown()
                addon_total = addon_breakdown.get("total_per_unit", 0)
            else:
                addon_total = addons.get("total_per_unit", 0)

        # Calculate per-unit total
        per_unit_total = adjusted_base + addon_total

        # Multiply by quantity
        annual_total = per_unit_total * self.quantity

        total_contract_cost = annual_total * self.years

        monthly_dd = annual_total / 12

        return {
            "contract_type": self.contract_type,
            "tier": self.tier,
            "quantity": self.quantity,
            "years": self.years,
            "base_rate_per_unit": self.base_rate,
            "adjustment": base_calc,
            "addons_per_unit": addon_total,
            "total_per_unit": per_unit_total,
            "annual_total": round(annual_total, 2),
            "total_contract_cost": round(total_contract_cost, 2),
            "monthly_dd": round(monthly_dd, 2),
            "pay_upfront": round(total_contract_cost, 2),
            "parts_discount": self.parts_discount,
            "pm_visits_per_year": actual_pm_visits,
            "labour_included": self.contract_type == "fixed_labour"
        }
    def _get_visit_count(self, multiplier: float) -> int:
        """Determine number of PM visits based on multiplier"""
        if multiplier == 2.0:
            return 4  # G8/Outdoor
        elif multiplier == 1.5:
            return 3  # G9
        elif multiplier == 0.5:
            return 1  # Half-price (1 visit)
        else:
            return 2  # Standard
    
    def get_labour_rates(self) -> dict:
        """Get labour rates for this contract type"""
        from config.pricing import get_pricing
        pricing = get_pricing(self.price_list)
        return pricing["labour_rates"][self.contract_type]

# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def quick_calculate_lift(contract_type: str, tier: str, quantity: float,
                        equipment_type: str = None) -> dict:
    """Quick calculation without add-ons"""
    calc = LiftCalculator(contract_type, tier, quantity)
    return calc.calculate_total(equipment_type)


def format_currency(amount: float) -> str:
    """Format as GBP currency"""
    return f"£{amount:,.2f}" 
