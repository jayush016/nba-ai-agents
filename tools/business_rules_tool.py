"""
Business Rules Tool - Validates action feasibility
Used by Agent 4 (Validator)
"""

import json
import os
from typing import Dict, List


def check_business_rules(rule_type: str, **kwargs) -> Dict:
    """
    Check business rules for action validation.
    
    Args:
        rule_type: Type of rule to check ('inventory', 'budget', 'permissions', 'all')
        **kwargs: Additional parameters (product_id, customer_id, action_cost, etc.)
        
    Returns:
        Validation results
    """
    if rule_type == "inventory":
        return check_inventory_rules(**kwargs)
    elif rule_type == "budget":
        return check_budget_rules(**kwargs)
    elif rule_type == "permissions":
        return check_permission_rules(**kwargs)
    elif rule_type == "all":
        return {
            "inventory": check_inventory_rules(**kwargs),
            "budget": check_budget_rules(**kwargs),
            "permissions": check_permission_rules(**kwargs)
        }
    else:
        return {"error": f"Unknown rule type: {rule_type}"}


def check_inventory_rules(product_id: str = None, **kwargs) -> Dict:
    """Check if product is in stock and available."""
    if not product_id:
        return {"valid": True, "message": "No product check required"}
    
    # Load product catalog
    catalog_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'product_catalog.json')
    
    try:
        with open(catalog_path, 'r') as f:
            products = json.load(f)
        
        # Find product
        product = next((p for p in products if p.get('product_id') == product_id), None)
        
        if not product:
            return {
                "valid": False,
                "message": f"Product {product_id} not found"
            }
        
        stock = product.get('stock_quantity', 0)
        
        if stock > 0:
            return {
                "valid": True,
                "message": f"Product in stock ({stock} units)",
                "stock_quantity": stock
            }
        else:
            return {
                "valid": False,
                "message": "Product out of stock",
                "stock_quantity": 0
            }
    
    except FileNotFoundError:
        return {"valid": True, "message": "Product catalog not found, assuming available"}


def check_budget_rules(action_cost: float = 0, customer_id: str = None, **kwargs) -> Dict:
    """Check if action is within marketing budget."""
    # Define budget constraints
    MAX_SPEND_PER_CUSTOMER_PER_MONTH = 10.00
    TOTAL_MONTHLY_BUDGET = 50000.00
    CURRENT_MONTH_SPEND = 23450.00  # Simulated
    
    # Check customer spend limit
    if action_cost > MAX_SPEND_PER_CUSTOMER_PER_MONTH:
        return {
            "valid": False,
            "message": f"Action cost (${action_cost}) exceeds per-customer limit (${MAX_SPEND_PER_CUSTOMER_PER_MONTH})"
        }
    
    # Check total budget
    remaining_budget = TOTAL_MONTHLY_BUDGET - CURRENT_MONTH_SPEND
    
    if action_cost > remaining_budget:
        return {
            "valid": False,
            "message": f"Insufficient budget. Remaining: ${remaining_budget:.2f}",
            "remaining_budget": remaining_budget
        }
    
    return {
        "valid": True,
        "message": f"Within budget. Cost: ${action_cost}, Remaining: ${remaining_budget:.2f}",
        "remaining_budget": remaining_budget
    }


def check_permission_rules(action_type: str = None, channel: str = None, **kwargs) -> Dict:
    """Check if we have permission to contact customer via channel."""
    # Simulated permission database
    CHANNEL_PERMISSIONS = {
        "email": True,
        "sms": True,  # Assume opt-in
        "push": False,  # Not opted in
        "whatsapp": False
    }
    
    if not channel:
        return {"valid": True, "message": "No channel specified"}
    
    has_permission = CHANNEL_PERMISSIONS.get(channel.lower(), False)
    
    if has_permission:
        return {
            "valid": True,
            "message": f"Customer has opted in to {channel}"
        }
    else:
        return {
            "valid": False,
            "message": f"Customer has not opted in to {channel}. Try alternative channel."
        }


def validate_action(action: Dict) -> Dict:
    """
    Comprehensive validation of a proposed action.
    
    Args:
        action: Action dictionary with keys: action_type, channel, product_id, etc.
        
    Returns:
        Validation results with overall valid/invalid status
    """
    validations = []
    
    # Check inventory if product mentioned
    if 'product_id' in action:
        inventory_check = check_inventory_rules(product_id=action['product_id'])
        validations.append(("inventory", inventory_check))
    
    # Check budget (estimate cost based on channel)
    channel_costs = {
        "email": 0.05,
        "sms": 0.15,
        "push": 0.02,
        "whatsapp": 0.10
    }
    
    action_cost = channel_costs.get(action.get('channel', 'email'), 0.05)
    budget_check = check_budget_rules(action_cost=action_cost)
    validations.append(("budget", budget_check))
    
    # Check permissions
    permission_check = check_permission_rules(channel=action.get('channel'))
    validations.append(("permissions", permission_check))
    
    # Overall validity
    all_valid = all(v[1].get('valid', False) for v in validations)
    
    return {
        "overall_valid": all_valid,
        "checks": {name: result for name, result in validations},
        "action": action
    }


def validate_actions_batch(actions: List[Dict]) -> Dict:
    """
    Validate a list of actions in batch.
    
    Args:
        actions: List of action dictionaries
        
    Returns:
        Dictionary with validation results for all actions
    """
    results = []
    passed_ids = []
    failed_ids = []
    
    for action in actions:
        result = validate_action(action)
        action_id = action.get('action_id', 'unknown')
        
        # Add action_id to result for tracking
        result['action_id'] = action_id
        
        results.append(result)
        
        if result['overall_valid']:
            passed_ids.append(action_id)
        else:
            failed_ids.append(action_id)
            
    return {
        "validated_actions": results,
        "passed_action_ids": passed_ids,
        "failed_action_ids": failed_ids,
        "compliance_summary": f"{len(passed_ids)} out of {len(actions)} actions passed validation"
    }


def get_action_cost(action_type: str, channel: str) -> float:
    """Get estimated cost for an action."""
    channel_costs = {
        "email": 0.05,
        "sms": 0.15,
        "push": 0.02,
        "retargeting_ads": 0.75
    }
    
    return channel_costs.get(channel.lower(), 0.05)
