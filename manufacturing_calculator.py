import numpy as np

def calculate_multi_quantity_prices(
    machine_cost_per_hour,
    material_cost_per_unit,
    production_time_minutes,
    setup_time_minutes,
    quantities,
    setup_cost_per_hour=None,  # Optional separate setup cost rate
    material_discount_tiers=None,  # Optional material discount for larger quantities
    overhead_percentage=20.0,
    profit_margin_percentage=25.0,
    additional_material_cost=0.0,
    include_labor_cost=False,
    labor_cost_per_hour=0.0
):
    """
    Calculate prices for multiple quantity tiers, considering setup costs.
    
    Parameters:
    -----------
    machine_cost_per_hour : float
        Cost of running the machine per hour
    material_cost_per_unit : float
        Cost of material per unit/piece
    production_time_minutes : float
        Time in minutes to produce one piece
    setup_time_minutes : float
        Time in minutes to set up the machine (divided across the batch)
    quantities : list
        List of quantities to calculate prices for
    setup_cost_per_hour : float, optional
        Cost per hour for setup time (if different from machine_cost_per_hour)
    material_discount_tiers : dict, optional
        Dictionary of quantity thresholds and corresponding discount percentages
        e.g., {10: 5, 50: 10, 100: 15} means 5% discount for 10+ units, 10% for 50+, etc.
    overhead_percentage : float, optional
        Overhead percentage (0-100)
    profit_margin_percentage : float, optional
        Profit margin percentage (0-100)
    additional_material_cost : float, optional
        Additional material costs per piece
    include_labor_cost : bool, optional
        Whether to include labor cost as a separate component
    labor_cost_per_hour : float, optional
        Cost of labor per hour (used only if include_labor_cost=True)
    
    Returns:
    --------
    dict
        Dictionary containing price calculations for each quantity
    """
    # If setup cost not specified, use machine cost
    if setup_cost_per_hour is None:
        setup_cost_per_hour = machine_cost_per_hour
    
    # If no material discounts specified, create empty dict
    if material_discount_tiers is None:
        material_discount_tiers = {}
    
    results = {}
    
    for quantity in quantities:
        # Calculate setup cost per piece (setup time divided by quantity)
        setup_time_hours = setup_time_minutes / 60.0
        setup_cost = setup_cost_per_hour * setup_time_hours
        setup_cost_per_piece = setup_cost / quantity
        
        # Apply material discount if applicable
        discounted_material_cost = material_cost_per_unit
        applied_discount = 0
        
        # Find the highest discount tier that applies to this quantity
        for tier_quantity, discount_percentage in sorted(material_discount_tiers.items()):
            if quantity >= tier_quantity:
                applied_discount = discount_percentage
        
        # Apply the discount if any
        if applied_discount > 0:
            discounted_material_cost = material_cost_per_unit * (1 - applied_discount/100)
        
        # Calculate regular price
        regular_result = calculate_price(
            machine_cost_per_hour,
            discounted_material_cost,
            production_time_minutes,
            labor_cost_per_hour,
            overhead_percentage,
            profit_margin_percentage,
            additional_material_cost,
            quantity,
            include_labor_cost
        )
        
        # Add setup cost to the calculation
        price_with_setup = regular_result['price_per_piece'] + setup_cost_per_piece
        total_cost = price_with_setup * quantity
        
        # Create result for this quantity
        results[quantity] = {
            'price_per_piece': price_with_setup,
            'total_cost': total_cost,
            'setup_cost_per_piece': setup_cost_per_piece,
            'material_discount_percentage': applied_discount,
            'discounted_material_cost': discounted_material_cost,
            'base_result': regular_result
        }
    
    return results

def calculate_machine_cost_per_hour(
    electricity_cost_per_hour=0.0,
    maintenance_cost_per_hour=0.0,
    depreciation_cost_per_hour=0.0,
    facility_cost_per_hour=0.0,
    other_costs_per_hour=0.0,
    labor_cost_per_hour=0.0
):
    """
    Calculate the total machine cost per hour.
    
    Parameters:
    -----------
    electricity_cost_per_hour : float
        Cost of electricity per hour
    maintenance_cost_per_hour : float
        Maintenance cost per hour
    depreciation_cost_per_hour : float
        Depreciation cost per hour
    facility_cost_per_hour : float
        Facility/space cost per hour
    other_costs_per_hour : float
        Other miscellaneous costs per hour
    labor_cost_per_hour : float
        Labor costs per hour
        
    Returns:
    --------
    float
        Total machine cost per hour
    """
    # Sum all the hourly costs
    total_cost_per_hour = (
        electricity_cost_per_hour +
        maintenance_cost_per_hour +
        depreciation_cost_per_hour +
        facility_cost_per_hour +
        other_costs_per_hour +
        labor_cost_per_hour
    )
    
    return total_cost_per_hour

def calculate_price(
    machine_cost_per_hour,
    material_cost_per_unit,
    production_time_minutes,
    labor_cost_per_hour=0.0,  # Now optional, defaults to 0
    overhead_percentage=20.0,
    profit_margin_percentage=25.0,
    additional_material_cost=0.0,
    batch_size=1,
    include_labor_cost=False  # New parameter to determine whether to include labor cost separately
):
    """
    Calculate the manufacturing cost and price per piece.
    
    Parameters:
    -----------
    machine_cost_per_hour : float
        Cost of running the machine per hour (includes labor if include_labor_cost=False)
    material_cost_per_unit : float
        Cost of material per unit/piece
    production_time_minutes : float
        Time in minutes to produce one piece
    labor_cost_per_hour : float, optional
        Cost of labor per hour (used only if include_labor_cost=True)
    overhead_percentage : float, optional
        Overhead percentage (0-100)
    profit_margin_percentage : float, optional
        Profit margin percentage (0-100)
    additional_material_cost : float, optional
        Additional material costs per piece
    batch_size : int, optional
        Number of pieces in the batch
    include_labor_cost : bool, optional
        Whether to include labor cost as a separate component
        
    Returns:
    --------
    dict
        Dictionary containing all calculated values
    """
    # Convert minutes to hours
    production_time_hours = production_time_minutes / 60.0
    
    # Calculate costs per piece
    machine_cost_per_piece = machine_cost_per_hour * production_time_hours
    labor_cost_per_piece = labor_cost_per_hour * production_time_hours if include_labor_cost else 0.0
    material_cost_per_piece = material_cost_per_unit
    
    # Calculate base cost before overhead
    direct_cost_per_piece = machine_cost_per_piece + labor_cost_per_piece + material_cost_per_piece + additional_material_cost
    
    # Calculate overhead cost
    overhead_cost_per_piece = direct_cost_per_piece * (overhead_percentage / 100.0)
    
    # Base cost including overhead
    base_cost_per_piece = direct_cost_per_piece + overhead_cost_per_piece
    
    # Calculate profit and final price
    profit_per_piece = base_cost_per_piece * (profit_margin_percentage / 100.0)
    price_per_piece = base_cost_per_piece + profit_per_piece
    
    # Calculate batch totals
    total_batch_cost = price_per_piece * batch_size
    
    # Calculate percentages for breakdown
    total_cost = price_per_piece
    machine_cost_percentage = (machine_cost_per_piece / total_cost) * 100
    material_cost_percentage = (material_cost_per_piece / total_cost) * 100
    additional_material_cost_percentage = (additional_material_cost / total_cost) * 100
    labor_cost_percentage = (labor_cost_per_piece / total_cost) * 100
    overhead_cost_percentage = (overhead_cost_per_piece / total_cost) * 100
    base_cost_percentage = (base_cost_per_piece / total_cost) * 100
    profit_percentage = (profit_per_piece / total_cost) * 100
    
    # Return all calculated values
    return {
        'machine_cost_per_piece': machine_cost_per_piece,
        'labor_cost_per_piece': labor_cost_per_piece,
        'material_cost_per_piece': material_cost_per_piece,
        'additional_material_cost': additional_material_cost,
        'direct_cost_per_piece': direct_cost_per_piece,
        'overhead_cost_per_piece': overhead_cost_per_piece,
        'base_cost_per_piece': base_cost_per_piece,
        'profit_per_piece': profit_per_piece,
        'price_per_piece': price_per_piece,
        'total_batch_cost': total_batch_cost,
        
        # Percentages for breakdown
        'machine_cost_percentage': machine_cost_percentage,
        'material_cost_percentage': material_cost_percentage,
        'additional_material_cost_percentage': additional_material_cost_percentage,
        'labor_cost_percentage': labor_cost_percentage,
        'overhead_cost_percentage': overhead_cost_percentage,
        'base_cost_percentage': base_cost_percentage,
        'profit_percentage': profit_percentage
    }
