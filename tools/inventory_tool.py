"""
Inventory Tool - Checks product availability and margins
Day 2 Concept: Tools & MCP
"""

import json
import os
from typing import Dict, List, Optional


def get_product_info(product_id: str) -> Dict:
    """
    Get product details including price, margin, and stock.
    
    Args:
        product_id: The unique product identifier
        
    Returns:
        Dictionary containing product information
    """
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'product_catalog.json')
    
    try:
        with open(data_path, 'r') as f:
            products = json.load(f)
        
        for product in products:
            if product['product_id'] == product_id:
                return product
        
        return {"error": f"Product {product_id} not found"}
    
    except FileNotFoundError:
        return {"error": "Product catalog not found"}


def check_stock_availability(product_id: str, quantity: int = 1) -> bool:
    """
    Check if sufficient stock is available.
    
    Args:
        product_id: Product to check
        quantity: Desired quantity
        
    Returns:
        True if stock is available, False otherwise
    """
    product = get_product_info(product_id)
    
    if "error" in product:
        return False
    
    return product.get('stock_quantity', 0) >= quantity


def get_products_by_category(category: str) -> List[Dict]:
    """
    Get all products in a category.
    
    Args:
        category: Product category
        
    Returns:
        List of matching products
    """
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'product_catalog.json')
    
    try:
        with open(data_path, 'r') as f:
            products = json.load(f)
        
        return [p for p in products if p.get('category') == category]
    
    except FileNotFoundError:
        return []


def calculate_margin(product_id: str, discount_percent: float = 0) -> float:
    """
    Calculate profit margin after discount.
    
    Args:
        product_id: Product to analyze
        discount_percent: Discount percentage to apply
        
    Returns:
        Margin percentage after discount
    """
    product = get_product_info(product_id)
    
    if "error" in product:
        return 0.0
    
    price = product.get('price', 0)
    cost = product.get('cost', 0)
    
    discounted_price = price * (1 - discount_percent / 100)
    margin = ((discounted_price - cost) / discounted_price * 100) if discounted_price > 0 else 0
    
    return round(margin, 2)
