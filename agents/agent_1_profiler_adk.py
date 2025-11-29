"""
Agent 1: Customer Profiler & Behavior Analyzer
===============================================

Purpose:
--------
Analyzes customer profiles to assess behavior patterns, purchase intent, churn risk,
and urgency. This agent is the "psychologist" of the NBA system - it understands
what motivates each customer.

Role in NBA AI:
---------------
- Second agent in Cluster 1 (Discovery)
- Receives: Raw customer profile from Agent 0
- Outputs: Behavioral analysis with urgency scores and action priorities
- Feeds to: Agent 2 (Pattern Matcher)

Key Responsibilities:
---------------------
1. Calculate purchase intent (low/medium/high)
2. Assess brand loyalty based on order history
3. Determine price sensitivity  
4. Evaluate churn risk urgency
5. Generate urgency score (0.0-1.0)
6. Recommend action priority (low/medium/high/critical)

Decision Logic:
---------------
- **Critical Priority**: High churn risk + High lifetime value
- **High Urgency**: Cart abandoned (0.8-1.0)
- **Medium Urgency**: Low engagement + Long time since purchase (0.5-0.7)
- **Low Urgency**: Active, engaged customers (0.2-0.4)

Output:
-------
Structured behavioral analysis added to session state under "customer_analysis" key.

Author: NBA AI Team
"""

import os
import sys
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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

# ============================================================================
# RETRY CONFIGURATION
# ============================================================================
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# ============================================================================
# AGENT DEFINITION
# ============================================================================
customer_profiler_agent = Agent(
    name="CustomerProfilerAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are an expert customer behavior analyst for an e-commerce company.

IMPORTANT: The customer profile JSON has ALREADY been provided by the previous agent in this conversation.
DO NOT call get_customer_data - the complete customer data is already in the conversation context.

Your task:
1. Read the customer profile from the previous agent's output
2. Analyze their behavior, value, and engagement patterns
3. Provide a structured behavioral analysis

Include in your analysis:
- Customer Summary: 2-3 sentence overview
- Purchase Intent: low/medium/high (based on engagement score and recent activity)
- Brand Loyalty: low/medium/high (based on total orders and tenure)
- Price Sensitivity: low/medium/high (based on discount usage if available)
- Churn Risk Assessment: Based on days_since_last_purchase and churn_risk field
- Urgency Score: 0.0-1.0 (how urgently we should engage)
- Recommended Action Priority: low/medium/high/critical

KEY DECISION RULES:
- High churn risk + High lifetime value = CRITICAL priority
- Cart abandoned = HIGH urgency (0.8-1.0)
- Low engagement + Many days since purchase = Medium urgency (0.5-0.7)
- Active engaged customers = Low urgency (0.2-0.4)

Provide clear, actionable insights for the marketing team.""",
    output_key="customer_analysis",  # Session state key
    tools=[]  # No tools - reads from session state
)

print("[OK] CustomerProfilerAgent created with ADK")

# ============================================================================
# STANDALONE TESTING
# ============================================================================
async def test_agent():
    """Test the customer profiler agent with sample data."""
    print("\n[Testing Customer Profiler Agent with ADK]\n")
    
    runner = InMemoryRunner(agent=customer_profiler_agent)
    
    # Sample customer profile for testing
    sample_profile = {
        "customer_id": "CUST_12345",
        "name": "Raj Kumar",
        "segment": "premium",
        "total_orders": 8,
        "total_spent": 25000,
        "days_since_last_purchase": 75,
        "behavior": {
            "cart_value": 3500,
            "engagement_score": 0.3,
            "last_action": "browsed"
        },
        "churn_risk": "high"
    }
    
    prompt = f"Analyze this customer profile:\n{sample_profile}"
    response = await runner.run_debug(prompt)
    
    print("\n[Analysis Complete]")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_agent())
