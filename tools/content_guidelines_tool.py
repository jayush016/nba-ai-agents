"""
Content Guidelines Tool - Provides content creation best practices
Used by Agent 7 (Content Creator)
"""

import json
import os
from typing import Dict, List, Optional


def query_content_guidelines(guideline_type: str = "all") -> Dict:
    """
    Query content creation guidelines.
    
    Args:
        guideline_type: Type of guidelines ('brand_voice', 'personalization', 
                       'subject_lines', 'email_structure', 'sms', 'push', 
                       'compliance', 'templates', 'all')
        
    Returns:
        Content guidelines dictionary
    """
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'content_guidelines.json')
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            guidelines = json.load(f)
        
        if guideline_type == "all":
            return guidelines
        elif guideline_type == "brand_voice":
            return {"brand_voice": guidelines.get('brand_voice', {})}
        elif guideline_type == "personalization":
            return {"personalization_tokens": guidelines.get('personalization_tokens', {})}
        elif guideline_type == "subject_lines":
            return {"subject_line_formulas": guidelines.get('subject_line_formulas', {})}
        elif guideline_type == "email_structure":
            return {"email_structure_best_practices": guidelines.get('email_structure_best_practices', {})}
        elif guideline_type == "sms":
            return {"sms_guidelines": guidelines.get('sms_guidelines', {})}
        elif guideline_type == "push":
            return {"push_notification_guidelines": guidelines.get('push_notification_guidelines', {})}
        elif guideline_type == "compliance":
            return {"compliance_requirements": guidelines.get('compliance_requirements', {})}
        elif guideline_type == "templates":
            return {"content_templates_by_scenario": guidelines.get('content_templates_by_scenario', {})}
        else:
            return {"error": f"Unknown guideline type: {guideline_type}"}
    
    except FileNotFoundError:
        return {"error": "Content guidelines file not found"}


def get_subject_line_formula(scenario: str) -> Dict:
    """
    Get subject line formula for a scenario.
    
    Args:
        scenario: Scenario type ('cart_abandonment', 'discount_offers', etc.)
        
    Returns:
        Subject line formulas
    """
    guidelines = query_content_guidelines(guideline_type="subject_lines")
    formulas = guidelines.get('subject_line_formulas', {})
    
    if scenario in formulas:
        return formulas[scenario]
    else:
        return {
            "error": f"No formula for scenario: {scenario}",
            "available_scenarios": list(formulas.keys())
        }


def get_content_template(scenario: str) -> Optional[Dict]:
    """
    Get full content template for a scenario.
    
    Args:
        scenario: Scenario type
        
    Returns:
        Content template dictionary
    """
    guidelines = query_content_guidelines(guideline_type="templates")
    templates = guidelines.get('content_templates_by_scenario', {})
    
    return templates.get(scenario)


def personalize_content(template_text: str, customer_data: Dict, product_data: Dict = None) -> str:
    """
    Replace personalization tokens in content.
    
    Args:
        template_text: Text with tokens like {{customer_name}}
        customer_data: Customer data dictionary
        product_data: Optional product data
        
    Returns:
        Personalized content string
    """
    content = template_text
    
    # Customer tokens
    tokens = {
        "{{customer_name}}": customer_data.get('name', 'Valued Customer'),
        "{{first_name}}": customer_data.get('name', '').split()[0] if customer_data.get('name') else 'there',
        "{{days_since_purchase}}": str(customer_data.get('days_since_last_purchase', 0)),
        "{{loyalty_tier}}": customer_data.get('segment', 'valued'),
    }
    
    # Product tokens if provided
    if product_data:
        tokens.update({
            "{{product_name}}": product_data.get('name', 'your item'),
            "{{category}}": product_data.get('category', 'product'),
            "{{original_price}}": str(product_data.get('price', 0)),
        })
    
    # Replace all tokens
    for token, value in tokens.items():
        content = content.replace(token, str(value))
    
    return content


def get_brand_tone(scenario: str, customer_segment: str = "general") -> str:
    """
    Get recommended brand tone for scenario.
    
    Args:
        scenario: Scenario type
        customer_segment: Customer segment
        
    Returns:
        Recommended tone ('professional', 'friendly', 'urgent', 'helpful')
    """
    # Mapping scenarios to tones
    tone_mapping = {
        "cart_abandonment": "urgent",
        "win_back": "friendly",
        "vip_nurture": "professional",
        "welcome": "helpful",
        "flash_sale": "urgent",
        "replenishment": "helpful"
    }
    
    return tone_mapping.get(scenario, "friendly")


def validate_content(content: str, channel: str) -> Dict:
    """
    Validate content against guidelines.
    
    Args:
        content: Content string
        channel: Channel type
        
    Returns:
        Validation results
    """
    issues = []
    warnings = []
    
    if channel == "email":
        guidelines = query_content_guidelines(guideline_type="email_structure")
        email_best = guidelines.get('email_structure_best_practices', {})
        
        # Check subject line length (if it's a subject)
        subject_guidelines = email_best.get('subject_line', {})
        max_length = subject_guidelines.get('max_length_chars', 50)
        
        if len(content) > max_length:
            warnings.append(f"Content length ({len(content)}) exceeds recommended {max_length} chars")
    
    elif channel == "sms":
        guidelines = query_content_guidelines(guideline_type="sms")
        sms_guidelines = guidelines.get('sms_guidelines', {})
        max_length = sms_guidelines.get('max_length_chars', 160)
        
        if len(content) > max_length:
            issues.append(f"SMS content ({len(content)} chars) exceeds limit of {max_length}")
    
    elif channel == "push":
        guidelines = query_content_guidelines(guideline_type="push")
        push_guidelines = guidelines.get('push_notification_guidelines', {})
        max_body = push_guidelines.get('body_max_chars', 120)
        
        if len(content) > max_body:
            warnings.append(f"Push notification content may be truncated")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "character_count": len(content)
    }


def get_call_to_action(scenario: str) -> List[str]:
    """
    Get recommended call-to-action phrases for scenario.
    
    Args:
        scenario: Scenario type
        
    Returns:
        List of CTA options
    """
    cta_mapping = {
        "cart_abandonment": ["Complete My Purchase", "Finish Checkout", "Get My Discount"],
        "win_back": ["Come Back & Save", "Start Shopping", "See What's New"],
        "vip_nurture": ["Shop The Collection", "View Your Picks", "Get Early Access"],
        "discount_offer": ["Shop Now", "Claim My Discount", "Unlock My Deal"],
        "replenishment": ["Reorder Now", "Stock Up", "Add to Cart"]
    }
    
    return cta_mapping.get(scenario, ["Shop Now", "Learn More", "Get Started"])
