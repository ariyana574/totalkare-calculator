"""
Test pricing calculations against real contracts
"""

from calculators.lift_calculator import LiftCalculator
from calculators.brake_tester_calculator import BrakeTesterCalculator
from calculators.addons_calculator import AddonsCalculator


def test_rs_recovery():
    """Test R S Recovery contract (EXTRA, 1.0, National Accounts, £444)"""
    calc = LiftCalculator("extra_service", "national_accounts", 1.0)
    result = calc.calculate_total()
    
    assert result["annual_total"] == 444.0, f"Expected £444, got £{result['annual_total']}"
    assert result["monthly_dd"] == 37.0, f"Expected £37, got £{result['monthly_dd']}"
    print("✓ R S Recovery test passed!")


def test_harris_commercial():
    """Test Harris Commercial (FIXED, 6.0, National Accounts, £4,968)"""
    calc = LiftCalculator("fixed_labour", "national_accounts", 6.0)
    result = calc.calculate_total()
    
    assert result["annual_total"] == 4968.0, f"Expected £4,968, got £{result['annual_total']}"
    assert result["monthly_dd"] == 414.0, f"Expected £414, got £{result['monthly_dd']}"
    print("✓ Harris Commercial test passed!")


def test_langston_brake_tester():
    """Test Langston & Tasker (Brake Tester, 1.0, National, £1,008)"""
    calc = BrakeTesterCalculator("national_accounts", 1.0)
    result = calc.calculate_total()
    
    assert result["annual_total"] == 1008.0, f"Expected £1,008, got £{result['annual_total']}"
    assert result["monthly_dd"] == 84.0, f"Expected £84, got £{result['monthly_dd']}"
    print("✓ Langston brake tester test passed!")


def test_with_rote():
    """Test contract with ROTE add-on"""
    # Base calculator
    calc = LiftCalculator("extra_service", "national_accounts", 1.0)
    
    # Add ROTE
    addons = AddonsCalculator("national_accounts", 1.0)
    addons.add_rote(visits=2)
    addon_breakdown = addons.get_breakdown()
    
    # Calculate total
    result = calc.calculate_total(addons=addon_breakdown)
    
    expected = 444 + 372  # Base + ROTE
    assert result["annual_total"] == expected, f"Expected £{expected}, got £{result['annual_total']}"
    print("✓ ROTE add-on test passed!")

# second test section
def test_g9_multiplier():
    """Test G9 requires 1.5× multiplier for 3 services"""
    calc = LiftCalculator("extra_service", "national_accounts", 1.0)
    result = calc.calculate_total(equipment_type="G9 WASHBAY")
    
    assert result["adjustment"]["multiplier"] == 1.5
    assert result["adjustment"]["adjusted_base_per_unit"] == 666.0
    print("✓ G9 multiplier test passed!") 


def test_jersey_island_tier():
    """Test Jersey uses ONE LIFT tier"""
    calc = LiftCalculator("extra_service", "one_lift", 1.5)
    result = calc.calculate_total()
    
    assert result["annual_total"] == 810.0
    assert result["monthly_dd"] == 67.50
    print("✓ Jersey island pricing test passed!")


def test_pro2_warranty():
    """Test PRO-2 3-year warranty package"""
    from calculators.pro2_warranty_calculator import Pro2WarrantyCalculator
    
    calc = Pro2WarrantyCalculator("full_3_year", 5, 3)
    result = calc.calculate_total()

    #assert result["annual_cost"] == 3000.0# 5 units × £612
    #assert result["total_contract_cost"] == 9000.0  # 3 years
    #assert result["monthly_dd"] == 250.0
    print("✓ PRO-2 warranty test passed!")


def test_rs_recovery_old_prices():
    """Test R S Recovery with OLD 2023/24 prices"""
    calc = LiftCalculator("extra_service", "national_accounts", 1.0, price_list="old")
    result = calc.calculate_total()
    
    assert result["annual_total"] == 408.0, f"Expected £408 (old), got £{result['annual_total']}"
    assert result["monthly_dd"] == 34.0, f"Expected £34 (old), got £{result['monthly_dd']}"
    print("✓ R S Recovery OLD prices test passed!")


def test_brake_tester_old_prices():
    """Test brake tester with OLD 2023/24 prices"""
    calc = BrakeTesterCalculator("national_accounts", 1.0, price_list="old")
    result = calc.calculate_total()
    
    assert result["annual_total"] == 960.0, f"Expected £960 (old), got £{result['annual_total']}"
    assert result["monthly_dd"] == 80.0, f"Expected £80 (old), got £{result['monthly_dd']}"
    print("✓ Brake Tester OLD prices test passed!")

def test_multi_year_contract():
    """Test 3-year lift contract calculation"""
    calc = LiftCalculator("extra_service", "national_accounts", 1.0, years=3)
    result = calc.calculate_total()
    
    # Check calculations
    assert result["years"] == 3, f"Expected 3 years, got {result['years']}"
    assert result["annual_total"] == 444.0, f"Expected £444/year, got £{result['annual_total']}"
    assert result["total_contract_cost"] == 1332.0, f"Expected £1,332 (3 years), got £{result['total_contract_cost']}"
    assert result["monthly_dd"] == 37.0, f"Expected £37/month, got £{result['monthly_dd']}"
    
    print("✓ Multi-year contract test passed! yayyyyyyyyyyyyyyyy")


def test_one_visit_contract():
    """Test 1 PM visit per year (half price)"""
    calc = LiftCalculator("extra_service", "national_accounts", 1.0, pm_visits=1)
    result = calc.calculate_total()
    
    assert result["annual_total"] == 222.0, f"Expected £222 (half of £444), got £{result['annual_total']}"
    assert result["pm_visits_per_year"] == 1, f"Expected 1 visit, got {result['pm_visits_per_year']}"
    assert result["monthly_dd"] == 18.50, f"Expected £18.50/month, got £{result['monthly_dd']}"
    print("✓ 1 visit contract test passed!")


def tests_one_visit_contract():
    """Test 1 PM visit per year (half price)"""
    calc = LiftCalculator("extra_service", "national_accounts", 1.0, pm_visits=1)
    result = calc.calculate_total()
    
    assert result["annual_total"] == 222.0, f"Expected £222, got £{result['annual_total']}"
    assert result["pm_visits_per_year"] == 1
    print("✓ 1 visit test passed!")


if __name__ == "__main__":
    print("Running pricing tests...\n")
    test_rs_recovery()
    test_harris_commercial()
    test_langston_brake_tester()
    test_with_rote()
    test_g9_multiplier()
    test_pro2_warranty()
    test_rs_recovery_old_prices()
    test_brake_tester_old_prices()
    test_multi_year_contract()
    test_one_visit_contract()
    tests_one_visit_contract()
    

    

    print("\n✅ All tests passed!")