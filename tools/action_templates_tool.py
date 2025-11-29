"""
Action Templates Tool - Provides marketing action templates
Used by Agent 3 (Action Generator)
"""

import json
import os
from typing import Dict, List, Optional


def get_action_templates(category: str = "all") -> Dict:
    """
    Retrieve marketing action templates.
    
    Args:
        category: Category of templates ('email_campaigns', 'sms_campaigns', 
                 'push_notifications', 'retargeting_ads', 'all')
        
    Returns:
        Action templates dictionary
    """
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'action_templates.json')
    
    try:
        with open(data_path, 'r') as f:
            templates = json.load(f)
        
        action_types = templates.get('action_types', {})
        
        if category == "all":
            return action_types
        elif category in action_types:
            return {category: action_types[category]}
        else:
            return {
                "error": f"Category '{category}' not found",
                "available_categories": list(action_types.keys())
            }
    
    except FileNotFoundError:
        return {"error": "Action templates file not found"}


def get_template_by_id(template_id: str) -> Optional[Dict]:
    """
    Get a specific template by its ID.
    
    Args:
        template_id: Template identifier
        
    Returns:
        Template dictionary or None
    """
    all_templates = get_action_templates(category="all")
    
    if "error" in all_templates:
        return None
    
    # Search through all categories
    for category, templates in all_templates.items():
        for template in templates:
            if template.get('template_id') == template_id:
                return template
    
    return None


def get_templates_by_scenario(scenario: str) -> List[Dict]:
    """
    Get recommended templates for a specific scenario.
    
    Args:
        scenario: Scenario type ('cart_abandonment', 'win_back', 'vip_nurture', 
                 'first_time_visitor', 'repeat_customer')
        
    Returns:
        List of recommended templates
    """
    scenario_mapping = {
        "cart_abandonment": ["cart_abandonment_basic", "cart_reminder_sms", "dynamic_product_ads"],
        "win_back": ["win_back_campaign", "whats_new_showcase"],
        "vip_nurture": ["vip_early_access", "personalized_recommendation"],
        "first_time_visitor": ["welcome_new_customer", "social_proof_showcase"],
        "repeat_customer": ["loyalty_reward_email", "replenishment_reminder"],
        "seasonal": ["seasonal_preview_email"]
    }
    
    template_ids = scenario_mapping.get(scenario, [])
    
    templates = []
    for tid in template_ids:
        template = get_template_by_id(tid)
        if template:
            templates.append(template)
    
    return templates


def get_channels_by_preference(preferred_channel: str = None) -> List[str]:
    """
    Get list of channels ranked by preference or defaults.
    
    Args:
        preferred_channel: Preferred channel if known
        
    Returns:
        Ordered list of channels
    """
    if preferred_channel:
        # Put preferred first, then others
        all_channels = ["email", "sms", "push", "retargeting_ads"]
        other_channels = [c for c in all_channels if c != preferred_channel]
        return [preferred_channel] + other_channels
    else:
        # Default ranking (by ROI)
        return ["email", "push", "sms", "retargeting_ads"]


def estimate_action_performance(template: Dict) -> Dict:
    """
    Estimate performance metrics for a template.
    
    Args:
        template: Action template
        
    Returns:
        Performance estimates
    """
    return {
        "template_id": template.get('template_id'),
        "template_name": template.get('name'),
        "channel": template.get('channel'),
        "expected_conversion_rate": template.get('typical_conversion_rate', 0.3),
        "cost_per_send": template.get('cost_per_send', template.get('cost_per_impression', 0.05)),
        "urgency_level": template.get('urgency_level', 'medium')
    }


def get_action_combinations() -> Dict:
    """Get predefined action sequences for complex scenarios."""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'action_templates.json')
    
    try:
        with open(data_path, 'r') as f:
            templates = json.load(f)
        
        return templates.get('action_combinations', {})
    
    except FileNotFoundError:
        return {}
