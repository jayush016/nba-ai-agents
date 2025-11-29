"""
Historical Patterns Tool - Analyzes past customer behavior
Used by Agent 2 (Pattern Matcher)
"""

import json
import os
from typing import Dict, List, Optional


def query_historical_patterns(segment: str = None, data_type: str = "all") -> Dict:
    """
    Query historical customer patterns and success rates.
    
    Args:
        segment: Customer segment to query (e.g., 'price_sensitive_cart_abandoners')
        data_type: Type of data to return ('segments', 'behavioral_patterns', 'product_insights', 'all')
        
    Returns:
        Dictionary with historical pattern data
    """
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'historical_customer_data.json')
    
    try:
        with open(data_path, 'r') as f:
            historical_data = json.load(f)
        
        # If specific segment requested
        if segment:
            segments = historical_data.get('customer_segments', {})
            if segment in segments:
                return {
                    "segment": segment,
                    "data": segments[segment]
                }
            else:
                return {
                    "error": f"Segment '{segment}' not found",
                    "available_segments": list(segments.keys())
                }
        
        # Return specific data type
        if data_type == "segments":
            return {"customer_segments": historical_data.get('customer_segments', {})}
        elif data_type == "behavioral_patterns":
            return {"behavioral_patterns": historical_data.get('behavioral_patterns', {})}
        elif data_type == "product_insights":
            return {"product_category_insights": historical_data.get('product_category_insights', {})}
        else:
            # Return all
            return historical_data
    
    except FileNotFoundError:
        return {"error": "Historical data file not found"}
    except json.JSONDecodeError:
        return {"error": "Error parsing historical data"}


def find_similar_customer_segment(customer_profile_json: str) -> Dict:
    """
    Find the most similar customer segment based on profile.
    
    Args:
        customer_profile_json: Customer profile as JSON string
        
    Returns:
        Best matching segment with success rates
    """
    # Parse JSON string to dict
    import json as json_lib
    try:
        customer_profile = json_lib.loads(customer_profile_json)
    except (json_lib.JSONDecodeError, TypeError):
        # If it's already a dict (shouldn't happen, but defensive)
        customer_profile = customer_profile_json if isinstance(customer_profile_json, dict) else {}
    
    # Simple matching logic based on key attributes
    churn_risk = customer_profile.get('churn_risk', 'low')
    cart_status = customer_profile.get('cart_status', 'empty')
    segment = customer_profile.get('segment', 'medium_value')
    total_orders = customer_profile.get('total_orders', 0)
    days_since_purchase = customer_profile.get('days_since_last_purchase', 0)
    
    # Determine segment
    if cart_status == 'abandoned':
        matched_segment = 'price_sensitive_cart_abandoners'
    elif segment == 'vip':
        matched_segment = 'vip_customers'
    elif churn_risk == 'high' or days_since_purchase > 60:
        matched_segment = 'high_churn_risk'
    elif total_orders == 0:
        matched_segment = 'first_time_browsers'
    elif total_orders >= 3:
        matched_segment = 'repeat_buyers'
    else:
        matched_segment = 'first_time_browsers'
    
    # Get segment data
    result = query_historical_patterns(segment=matched_segment)
    
    return {
        "matched_segment": matched_segment,
        "segment_data": result.get('data', {}),
        "confidence": 0.85  # Placeholder confidence score
    }


def get_action_success_rate(action_type: str, segment: str) -> float:
    """
    Get historical success rate for a specific action on a segment.
    
    Args:
        action_type: Type of marketing action
        segment: Customer segment
        
    Returns:
        Success rate (0.0 to 1.0)
    """
    segment_data = query_historical_patterns(segment=segment)
    
    if "error" in segment_data:
        return 0.5  # Default if no data
    
    successful_actions = segment_data.get('data', {}).get('successful_actions', [])
    
    for action in successful_actions:
        if action_type.lower() in action.get('action', '').lower():
            return action.get('success_rate', 0.5)
    
    return 0.5  # Default


def get_best_performing_action(segment: str) -> Dict:
    """
    Get the historically best-performing action for a segment.
    
    Args:
        segment: Customer segment
        
    Returns:
        Best action details
    """
    segment_data = query_historical_patterns(segment=segment)
    
    if "error" in segment_data:
        return {"error": "Segment not found"}
    
    actions = segment_data.get('data', {}).get('successful_actions', [])
    
    if not actions:
        return {"error": "No historical actions found"}
    
    # Sort by success rate
    best_action = max(actions, key=lambda x: x.get('success_rate', 0))
    
    return {
        "best_action": best_action.get('action'),
        "success_rate": best_action.get('success_rate'),
        "avg_order_value": best_action.get('avg_order_value'),
        "optimal_timing": best_action.get('optimal_timing'),
        "sample_size": best_action.get('sample_size')
    }
