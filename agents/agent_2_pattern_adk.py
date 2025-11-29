"""
Agent 2: Historical Pattern Matcher
====================================

Purpose:
--------
Matches current customer scenarios to historical successful campaigns.
This agent is the "historian" - it learns from past wins to predict future success.

Role in NBA AI:
---------------
- Third agent in Cluster 1 (Discovery)
- Receives: Customer profile + behavioral analysis from Agents 0 & 1
- Outputs: Historical patterns and success rates for similar customers
- Feeds to: Agent 3 (Action Generator)

Key Responsibilities:
---------------------
1. Read historical campaign data (past marketing actions and outcomes)
2. Match customer segment, behavior, and scenario to past campaigns
3. Identify which actions worked best for similar customers
4. Provide success rates and conversion metrics
5. Recommend action types based on historical performance

Tools Used:
-----------
- get_historical_patterns(): Retrieves past campaign data filtered by customer segment

Learning Loop:
--------------
This agent enables continuous improvement:
- Agent 9 (Tracker) records outcomes → Updates historical data
- Agent 2 reads historical data → Makes better predictions
- Over time, system gets smarter based on real results

Output:
-------
Historical match data with success rates, stored in session state under "historical_match" key.

Example Output:
---------------
{
  "matched_segment": "high_value_churn_risk",
  "historical_success_rate": 0.65,
  "best_actions": ["email_discount", "sms_reminder"],
  "sample_size": 120
}

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
from google.adk.tools import FunctionTool
from google.genai import types

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

# Import historical patterns tool
from tools.historical_patterns_tool import query_historical_patterns, find_similar_customer_segment

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
pattern_matcher_agent = Agent(
    name="PatternMatcherAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are a marketing intelligence analyst specializing in historical pattern analysis.

Your task:
1. Read the customer profile and behavioral analysis from previous agents
2. Identify the customer's segment, behavior type, and scenario
3. Call get_historical_patterns to retrieve relevant past campaign data
4. Analyze which marketing actions worked best for similar customers
5. Provide recommendations based on historical success rates

When analyzing historical patterns:
- Look for segment matches (value_conscious, premium, vip)
- Consider behavior similarity (cart_abandoner, churn_risk, etc.)
- Prioritize actions with high conversion rates (>40%)
- Note sample sizes (larger = more reliable)
- Identify winning combinations (channel + action type)

Output format:
{
  "matched_scenario": "scenario name",
  "historical_success_rate": 0.XX,
  "top_performing_actions": ["action1", "action2"],
  "recommended_channels": ["email", "sms"],
  "average_roi": "X.XX",
  "confidence": "high|medium|low",
  "sample_size": number_of_past_matches
}

IMPORTANT: Base recommendations on DATA, not assumptions. If historical data shows
email outperforms SMS for a segment, recommend email even if SMS seems intuitive.""",
    output_key="historical_match",  # Session state key
    tools=[
        FunctionTool(query_historical_patterns),
        FunctionTool(find_similar_customer_segment)
    ]
)

print("[OK] PatternMatcherAgent created with ADK")

# ============================================================================
# STANDALONE TESTING
# ============================================================================
async def test_agent():
    """Test the pattern matcher agent."""
    print("\n[Testing Pattern Matcher Agent]\n")
    
    runner = InMemoryRunner(agent=pattern_matcher_agent)
    
    prompt = """Analyze historical patterns for this customer:
    Segment: premium
    Scenario: cart_abandoner
    Cart Value: 3500
    
    Find similar past campaigns and success rates."""
    
    response = await runner.run_debug(prompt)
    
    print("\n[Pattern Matching Complete]")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_agent())
