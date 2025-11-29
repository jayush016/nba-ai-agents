"""
Customer Data Tool - Fetches customer information
Day 2 Concept: Tools & MCP
"""

import json
import os
from typing import Dict, Optional


def get_customer_data(customer_id: str) -> Dict:
    """
    Fetch customer profile data.
    
    Args:
        customer_id: The unique customer identifier
        
    Returns:
        Dictionary containing customer information
    """
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_customers.json')
    
    try:
        with open(data_path, 'r') as f:
            customers = json.load(f)
        
        for customer in customers:
            if customer['customer_id'] == customer_id:
                return customer
        
        return {"error": f"Customer {customer_id} not found"}
    
    except FileNotFoundError:
        return {"error": "Customer database not found"}


def get_all_customers() -> list:
    """
    Fetch all customers.
    
    Returns:
        List of all customer dictionaries
    """
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_customers.json')
    
    try:
        with open(data_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def search_customers_by_segment(segment: str) -> list:
    """
    Find customers by segment.
    
    Args:
        segment: Customer segment (vip, high_value, medium_value, low_value)
        
    Returns:
        List of matching customers
    """
    customers = get_all_customers()
    return [c for c in customers if c.get('segment') == segment]
