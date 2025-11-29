"""
Agent 3: Marketing Action Generator
====================================

Purpose:
--------
Generates 4-5 diverse marketing action options based on customer analysis and
historical patterns. This agent is the "creative strategist" - it brainstorms
multiple approaches for the system to evaluate.

Role in NBA AI:
---------------
- Fourth and final agent in Cluster 1 (Discovery)
- Receives: Customer profile + analysis + historical patterns from Agents 0, 1, & 2
- Outputs: 4-5 marketing action proposals with details
- Feeds to: Cluster 2 (Validator + Scorer for evaluation)

Key Responsibilities:
---------------------
1. Synthesize insights from previous agents
2. Generate 4-5 diverse marketing action options
3. For each action, specify:
   - Action type (email, SMS, push, retargeting ad)
   - Message theme (discount, reminder, urgency, value-add)
   - Offer details (% discount, product recommendations)
   - Target timing window
   - Channel preference
4. Ensure diversity (different channels, offers, approaches)

Action Types Generated:
-----------------------
- **Email Discount**: Personalized email with % off
- **SMS Reminder**: Urgent text message about cart/wishlist
- **Push Notification**: App-based alert
- **Retargeting Ad**: Follow-up ad on social media
- **Value-Add Email**: Content marketing (no discount)

Diversity Strategy:
-------------------
- Mix aggressive (high discount) and conservative (low discount) approaches
- Try different channels (email, SMS, push)
- Vary urgency levels (24hr vs 7-day offers)
- Include no-discount options for comparison

Output:
-------
JSON array of 4-5 action proposals, stored under "generated_actions" key.

Example Output:
---------------
[
  {
    "action_id": 1,
    "type": "email_discount",
    "discount": "15%",
    "channel": "email",    "urgency": "high",
    "message_theme": "cart_recovery"
  },
  {
    "action_id": 2,
    "type": "sms_reminder",
    "discount": "10%",
    "channel": "sms",
    "urgency": "urgent",
    "message_theme": "limited_time"
  }
]

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
action_generator_agent = Agent(
    name="ActionGeneratorAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are a creative marketing strategist for an e-commerce company.

Your task:
1. Read customer profile, behavioral analysis, and historical patterns from previous agents
2. Generate 4-5 DIVERSE marketing action options
3. Each action should have a different approach (channel, offer, urgency)

For EACH action, provide:
- action_id: 1-5
- action_type: "email_discount" | "sms_reminder" | "push_notification" | "retargeting_ad" | "value_email"
- channel: "email" | "sms" | "push" | "retargeting"
- offer_details: specific discount/product/benefit
- message_theme: "urgency" | "value" | "social_proof" | "scarcity" | "personalization"
- timing_window: "24_hours" | "48_hours" | "7_days"
- estimated_cost: in rupees
- target_segment: customer segment this targets

DIVERSITY REQUIREMENTS:
- Include at least 1 high-discount option (15-20%)
- Include at least 1 low/no-discount option
- Use at least 2 different channels
- Mix urgent (24hr) and relaxed (7-day) timings
- Vary message themes

SCENARIO-SPECIFIC STRATEGIES:
- **Cart Abandoner**: Urgent reminder + discount (24-48hr)
- **Churn Risk**: Win-back with compelling offer + value messaging
- **VIP Customer**: Exclusive access, early preview, premium service
- **First-time Visitor**: Welcome discount, easy onboarding
- **Repeat Customer**: Loyalty reward, replenishment reminder

Output as JSON array of 4-5 actions, ordered from most to least recommended based on historical data.""",
    output_key="generated_actions",  # Session state key
    tools=[]  # No tools - synthesizes from previous agents' outputs
)

print("[OK] ActionGeneratorAgent created with ADK")

# ============================================================================
# STANDALONE TESTING
# ============================================================================
async def test_agent():
    """Test the action generator agent."""
    print("\n[Testing Action Generator Agent]\n")
    
    runner = InMemoryRunner(agent=action_generator_agent)
    
    prompt = """Generate marketing actions for:
    Customer: Premium segment, cart abandoner
    Cart Value: ₹3500 (electronics)
    Churn Risk: High
    Historical Best: Email discounts (65% success rate)
    
    Create 4-5 diverse action options."""
    
    response = await runner.run_debug(prompt)
    
    print("\n[Action Generation Complete]")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_agent())
