"""
Agent 0: Proxy Customer Generator (ADK Version)
=================================================

Purpose:
--------
Generates realistic customer profiles and scenarios for testing the NBA AI system.
This agent creates diverse customer personas with varying behaviors, segments, and risk levels.

Role in NBA AI:
---------------
- First agent in the pipeline
- Creates test scenarios for the system to process
- In production, this would be replaced with real customer data from a database

Output:
-------
JSON object containing:
- customer_id, name, demographics
- segment (value_conscious, premium, vip)
- purchase history (orders, spend, last purchase date)
- current behavior (cart, browsing, engagement)
- churn_risk assessment

Author: NBA AI Team
"""

import os
import sys
import json
import asyncio
from dotenv import load_dotenv

# ============================================================================
# ADK IMPORTS
# ============================================================================
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================
# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load API key from .env
load_dotenv()

# ============================================================================
# RETRY CONFIGURATION
# ============================================================================
# Configure retry logic for API calls to handle rate limits and transient errors
retry_config = types.HttpRetryOptions(
    attempts=5,              # Retry up to 5 times
    exp_base=7,              # Exponential backoff base (7 seconds)
    initial_delay=1,         # Start with 1 second delay
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

# ============================================================================
# AGENT DEFINITION
# ============================================================================
proxy_agent = Agent(
    name="ProxyCustomerAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",  # Fast, cost-effective model
        retry_options=retry_config
    ),
    instruction="""You are a customer data generator for an e-commerce system.

Your task is to generate realistic customer profiles based on a requested scenario.

SCENARIO PROMPTS:
- "cart_abandonment": High value cart, no purchase, 1-2 visits
- "churn_risk": No purchase in 60+ days, declining engagement
- "first_visit": Browsing only, no history
- "repeat_customer": 3+ orders, high engagement
- "vip": High spend (>15k), frequent buyer
- "random": Any realistic profile

REQUIRED OUTPUT FORMAT (strict JSON):
{
  "customer_id": "CUST_xxxxx",
  "name": "Full Name",
  "age": 25-65,
  "location": "City, Country",
  "segment": "value_conscious" | "premium" | "vip",
  "total_orders": 0-50,
  "total_spent": 0-100000,
  "days_since_last_purchase": 0-365,
  "behavior": {
    "last_action": "browsed" | "added_to_cart" | "purchased" | "viewed_product",
    "cart_value": 0-10000,
    "product_browsed": "Product Name",
    "category": "Electronics" | "Fashion" | "Home" | etc.,
    "engagement_score": 0.0-1.0
  },
  "preferences": {
    "preferred_channel": "email" | "sms" | "push" | "whatsapp",
    "price_sensitivity": "low" | "medium" | "high"
  },
  "scenario_type": "cart_abandoner" | "churn_risk" | "first_time_visitor" | "repeat_customer",
  "churn_risk": "low" | "medium" | "high"
}

IMPORTANT RULES:
1. Return ONLY valid JSON - no markdown, no explanations
2. Use realistic Indian/international names and locations
3. Make behavioral data consistent with scenario type
4. Engagement score should correlate with churn risk (high churn = low engagement)
5. Cart value should make sense for the product category
6. Days since last purchase should align with churn risk""",
    output_key="generated_customer_profile",  # Session state key for next agent
    tools=[]  # No tools needed - pure generation
)

print("[OK] ProxyCustomerAgent created with ADK (Gemini 2.5)")

# ============================================================================
# STANDALONE TESTING
# ============================================================================
async def test_agent():
    """
    Test function to run the proxy agent standalone.
    Useful for development and debugging.
    """
    print("\n[Testing Agent 0: Proxy Customer Generator (ADK)]\n")
    
    # Create runner with in-memory session
    runner = InMemoryRunner(agent=proxy_agent)
    
    try:
        # Test with cart abandonment scenario
        print("Generating 'cart_abandonment' scenario...\n")
        response = await runner.run_debug(
            "Generate a customer profile for scenario: cart_abandonment"
        )
        
        print("\n[Generation Complete]")
        print(response)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run standalone test
    asyncio.run(test_agent())
