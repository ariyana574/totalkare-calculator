"""
Add-ons Calculator (ROTE, Kluberplex, Battery Plan, etc.)
"""

from config.pricing import get_pricing


class AddonsCalculator:
    """Calculate costs for optional add-ons"""
    
    def __init__(self, tier: str, quantity: float, price_list: str = "new", pm_visits: int = 2):
        """
        Initialize add-ons calculator
        
        Args:
            tier: "one_lift", "multi_sets", or "national_accounts"
            quantity: From NetSuite
        """
        self.tier = tier
        self.quantity = quantity
        self.price_list = price_list
        self.selected_addons = []
        self.total_per_unit = 0
        self.pm_visits = pm_visits

        # Get correct pricing
        from config.pricing import get_pricing
        self.pricing = get_pricing(price_list)
        
    def add_rote(self, visits: int = 2) -> float:
        """Add ROTE"""
        if visits == 2:
            cost = self.pricing["rote_rates"]["2_visits"][self.tier]
        elif visits == 1:
            cost = self.pricing["rote_rates"]["1_visit"][self.tier]
        else:
            raise ValueError("ROTE visits must be 1 or 2")
    
        self.selected_addons.append({
        "name": f"ROTE ({visits} visits/year)",
        "cost_per_unit": cost
    })
        self.total_per_unit += cost
        return cost
    
    def add_kluberplex(self) -> float:
        """Add Kluberplex grease"""
        cost = self.pricing["addon_rates"]["kluberplex"]
        self.selected_addons.append({
        "name": "Kluberplex Grease",
        "cost_per_unit": cost
    })
        self.total_per_unit += cost
        return cost

 

    def add_lube_pots(self) -> float:
        """Add regular lube pots"""
        cost = self.pricing["addon_rates"]["lube_pots"]
        self.selected_addons.append({
        "name": "Regular Lube Pots",
        "cost_per_unit": cost
    })
        self.total_per_unit += cost
        return cost
    


    def add_battery_plan(self) -> float:
        """Add battery plan"""
        cost = self.pricing["addon_rates"]["battery_plan"]
        self.selected_addons.append({
        "name": "Battery Plan (4 batteries/year)",
        "cost_per_unit": cost
    })
        self.total_per_unit += cost
        return cost

    def add_ancillary(self, equipment_type: str) -> float:
        """
        Add ancillary equipment
    
        Args:
        equipment_type: "shaker_plates", "headlamp_tester", etc.
        """
        if equipment_type not in self.pricing["ancillary_rates"]:
            raise ValueError(f"Unknown ancillary type: {equipment_type}")
    
        cost = self.pricing["ancillary_rates"][equipment_type]
    
        # Apply half-price if only 1 PM visit selected
        if self.pm_visits == 1:
            cost = cost * 0.5
    
        self.selected_addons.append({
        "name": equipment_type.replace("_", " ").title(),
        "cost_per_unit": cost
    })
        self.total_per_unit += cost
        return cost
    
    def get_breakdown(self) -> dict:
        """Get complete add-ons breakdown"""
        annual_total = self.total_per_unit * self.quantity
        
        return {
            "addons": self.selected_addons,
            "total_per_unit": self.total_per_unit,
            "annual_total": round(annual_total, 2),
            "monthly_addition": round(annual_total / 12, 2)
        }
    
    def reset(self):
        """Clear all selected add-ons"""
        self.selected_addons = []
        self.total_per_unit = 0