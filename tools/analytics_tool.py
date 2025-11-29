"""
Analytics Tool - Analyzes historical action performance
Day 3 & 4 Concepts: Memory & Evaluation
"""

import json
import os
from typing import Dict, List


def get_historical_actions(customer_id: str = None) -> List[Dict]:
    """
    Get historical marketing actions.
    
    Args:
        customer_id: Optional filter by customer
        
    Returns:
        List of historical actions
    """
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'historical_actions.json')
    
    try:
        with open(data_path, 'r') as f:
            actions = json.load(f)
        
        if customer_id:
            return [a for a in actions if a.get('customer_id') == customer_id]
        
        return actions
    
    except FileNotFoundError:
        return []


def get_action_performance_by_type(action_type: str) -> Dict:
    """
    Calculate performance metrics for a specific action type.
    
    Args:
        action_type: Type of action (e.g., 'email_discount', 'abandoned_cart_reminder')
        
    Returns:
        Performance metrics dictionary
    """
    actions = get_historical_actions()
    filtered = [a for a in actions if a.get('action_type') == action_type]
    
    if not filtered:
        return {
            "action_type": action_type,
            "total_actions": 0,
            "avg_roi": 0,
            "conversion_rate": 0,
            "open_rate": 0,
            "click_rate": 0
        }
    
    total = len(filtered)
    conversions = sum(1 for a in filtered if a.get('converted', False))
    opens = sum(1 for a in filtered if a.get('opened', False))
    clicks = sum(1 for a in filtered if a.get('clicked', False))
    avg_roi = sum(a.get('roi', 0) for a in filtered) / total
    
    return {
        "action_type": action_type,
        "total_actions": total,
        "avg_roi": round(avg_roi, 2),
        "conversion_rate": round(conversions / total * 100, 2),
        "open_rate": round(opens / total * 100, 2),
        "click_rate": round(clicks / total * 100, 2)
    }


def find_similar_successful_actions(customer_segment: str, product_category: str) -> List[Dict]:
    """
    Find successful actions for similar customers/products.
    This demonstrates MEMORY - learning from past successes.
    
    Args:
        customer_segment: Target customer segment
        product_category: Product category
        
    Returns:
        List of successful similar actions
    """
    from tools.customer_data_tool import get_all_customers
    from tools.inventory_tool import get_product_info
    
    actions = get_historical_actions()
    similar_actions = []
    
    for action in actions:
        if not action.get('converted', False):
            continue
        
        # Check if customer segment matches
        customer_id = action.get('customer_id')
        customers = get_all_customers()
        customer = next((c for c in customers if c['customer_id'] == customer_id), None)
        
        if customer and customer.get('segment') == customer_segment:
            # Check if product category matches
            product_id = action.get('product_recommended')
            product = get_product_info(product_id)
            
            if not isinstance(product, dict) or 'error' in product:
                continue
            
            if product.get('category') == product_category:
                similar_actions.append(action)
    
    return similar_actions


def calculate_best_discount_range(customer_segment: str) -> Dict:
    """
    Analyze historical data to find optimal discount range.
    
    Args:
        customer_segment: Customer segment to analyze
        
    Returns:
        Recommended discount range
    """
    from tools.customer_data_tool import get_all_customers
    
    actions = get_historical_actions()
    customers = get_all_customers()
    
    segment_actions = []
    for action in actions:
        customer = next((c for c in customers if c['customer_id'] == action['customer_id']), None)
        if customer and customer.get('segment') == customer_segment and action.get('converted'):
            segment_actions.append(action)
    
    if not segment_actions:
        return {"min_discount": 10, "max_discount": 20, "avg_discount": 15}
    
    discounts = [a.get('discount_percentage', 0) for a in segment_actions]
    
    return {
        "min_discount": min(discounts),
        "max_discount": max(discounts),
        "avg_discount": round(sum(discounts) / len(discounts), 1)
    }


def score_action(action: Dict) -> Dict:
    """
    Calculate ROI score for a specific action.
    
    Args:
        action: Action dictionary
        
    Returns:
        Score dictionary
    """
    action_type = action.get('action_type', 'unknown')
    channel = action.get('channel', 'email')
    estimated_cost = action.get('estimated_cost', 0)
    
    # Get historical performance
    perf = get_action_performance_by_type(action_type)
    conversion_rate = perf.get('conversion_rate', 0)
    avg_roi = perf.get('avg_roi', 0)
    
    # Calculate score (simplified logic)
    # Base score from historical ROI
    score = min(10, max(1, avg_roi / 2))  # Normalize ROI to 1-10
    
    # Adjust for cost (lower cost = higher score)
    if estimated_cost < 50:
        score += 1
    elif estimated_cost > 500:
        score -= 1
        
    # Adjust for channel
    if channel == 'email':
        score += 0.5  # Email is cheap and effective
        
    return {
        "action_id": action.get('action_id'),
        "roi_score": round(min(10, max(1, score)), 1),
        "predicted_roi": avg_roi,
        "conversion_probability": conversion_rate,
        "confidence": "medium"
    }
