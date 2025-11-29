"""
Agent 6: Timing Optimizer
==========================

Purpose:
--------
Calculates the optimal send time for marketing messages to maximize open rates
and conversions. This agent is the "chronobiologist" - it knows when customers
are most likely to engage.

Role in NBA AI:
---------------
- First agent in Cluster 3 (Execution)
- Receives: Top-ranked action from Agents 4 & 5
- Outputs: Optimal send date/time
- Feeds to: Agent 7 (Content Creator)

Key Responsibilities:
---------------------
1. Analyze customer's past engagement patterns (best open times)
2. Consider day-of-week preferences
3. Factor in time zone
4. Account for action urgency (24hr vs 7-day campaigns)
5. Avoid bad times (late night, early morning, weekends for B2B)
6. Calculate specific send datetime

Tools Used:
-----------
- calculate_send_time(): Determines optimal timing based on customer behavior and action type

Timing Strategies:
------------------
- **Cart Abandonment**: ASAP (within 2-4 hours of abandonment)
- **Churn Win-back**: Tuesday-Thursday, 10 AM-2 PM (business hours)
- **VIP Offers**: Evening (6-8 PM) when they have time to browse
- **General Promotions**: Based on customer's historical best open time

Time Zone Handling:
-------------------
- Converts to customer's local time zone
- Ensures delivery during waking hours (6 AM - 10 PM)
- Avoids Sundays/holidays for non-urgent messages

Output:
-------
Optimized send timing, stored under "optimal_timing" key.

Example Output:
---------------
{
  "send_date": "2025-01-22",
  "send_time": "19:30",
  "timezone": "Asia/Kolkata",
  "day_of_week": "Wednesday",
  "reasoning": "Customer typically opens emails at 7-8 PM on weekdays",
  "urgency_level": "high",
  "hours_from_now": 4
}

Why This Matters:
-----------------
- **Open rates** vary 2-3x based on send time
- **Conversion rates** can double with optimal timing
- Wrong timing = message goes to spam/ignored
- Respect customer preferences = better engagement

Research-Backed Best Times:
---------------------------
- **E-commerce**: Tuesday-Thursday, 10 AM or 7-9 PM
- **Cart Recovery**: Within 4 hours of abandonment
- **Mobile Apps**: Evening (6-9 PM) when users relax
- **Avoid**: Monday mornings, Friday afternoons, weekends

Author: NBA AI Team
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from typing import Optional

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

# Import timing tool
from tools.timing_intelligence_tool import calculate_send_time

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
timing_agent = Agent(
    name="TimingAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are a timing optimization specialist for marketing campaigns.

Your task:
1. Read the selected marketing action from previous agents
2. Identify action type, urgency, and customer segment
3. Call calculate_send_time to determine optimal send datetime
4. Provide clear scheduling recommendation

Timing guidelines:
- **High Urgency** (cart abandonment): 2-4 hours from now
- **Medium Urgency** (churn win-back): Next business day, 10 AM-2 PM
- **Low Urgency** (general promo): Customer's typical engagement time
- **VIP Customers**: Evening (7-9 PM) for leisurely browsing
- **First-time Customers**: Midday (11 AM-1 PM) during break times

Day-of-week strategy:
- **Best**: Tuesday, Wednesday, Thursday (highest engagement)
- **Good**: Monday (new week energy), Friday AM (pre-weekend)
- **Avoid**: Friday PM, Saturday, Sunday (unless retail/consumer)

Output format:
{
  "recommended_send_datetime": "2025-01-22 19:30",
  "timezone": "Asia/Kolkata",
  "day_of_week": "Wednesday",
  "hours_from_now": 4,
  "reasoning": "Cart abandonment requires urgent follow-up within 4 hours. Customer historically opens evening emails.",
  "alternative_time": "2025-01-23 10:00" (if recommended time is not feasible)
}

IMPORTANT:
- Never schedule for past times
- Respect "do not disturb" hours (11 PM - 6 AM)
- Consider customer's timezone (not system timezone)
- Urgent actions override best-time optimization""",
    output_key="optimal_timing",  # Session state key
    tools=[FunctionTool(calculate_send_time)]  # Timing calculation tool
)

print("[OK] TimingAgent created with ADK")

# ============================================================================
# STANDALONE TESTING
# ============================================================================
async def test_agent():
    """Test the timing agent."""
    print("\n[Testing Timing Agent]\n")
    
    runner = InMemoryRunner(agent=timing_agent)
    
    prompt = """Calculate optimal send time for:
    Action: Cart abandonment email
    Customer: Premium segment, timezone Asia/Kolkata
    Urgency: High
    Current time: 2025-01-22 15:30
    
    Determine best send datetime."""
    
    response = await runner.run_debug(prompt)
    
    print("\n[Timing Optimization Complete]")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_agent())
