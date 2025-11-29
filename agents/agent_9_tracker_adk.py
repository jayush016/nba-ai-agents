"""
Agent 9: Results Tracker & Learning Engine
===========================================

Purpose:
--------
Records marketing action outcomes and updates historical data to enable continuous
learning. This agent is the "data scientist" - it ensures the system gets smarter
with every interaction.

Role in NBA AI:
---------------
- Final agent in Cluster 3 (Execution) - AFTER human approval
- Receives: Approval decision (APPROVED/REJECTED) from Agent 8
- Outputs: Recorded result + updated historical patterns
- Enables: Future predictions to improve via Agent 2 (Pattern Matcher)

**THIS IS THE LEARNING LOOP CLOSER** 🔄

Key Responsibilities:
---------------------
1. Read approval decision from Agent 8 (HITL)
2. Extract complete action details (customer, action type, cost, ROI)
3. Record outcome status:
   - "scheduled" if APPROVED
   - "cancelled" if REJECTED
4. Update historical_actions.json with new data point
5. Update historical_patterns summary for Agent 2
6. Provide confirmation of successful recording

Tools Used:
-----------
- record_result(): Saves action outcome to both files:
  - historical_actions.json (detailed log)
  - historical_patterns.json (aggregated insights)

What Gets Recorded:
-------------------
{
  "timestamp": "2025-01-22T19:30:00",
  "customer_id": "CUST_12345",
  "customer_segment": "premium",
  "scenario_type": "cart_abandoner",
  "action_type": "email_discount",
  "channel": "email",
  "discount_percent": 15,
  "estimated_cost": 575,
  "predicted_roi": 8.5,
  "action_status": "scheduled" | "cancelled",
  "approved_by": "human",
  "send_datetime": "2025-01-22 19:30"
}

The Learning Loop:
------------------
```
┌──────────────────────────────────────────────────────────┐
│                    LEARNING CYCLE                        │
└──────────────────────────────────────────────────────────┘

1. Agent 9 records: "Email discount to premium cart abandoner"
                    ↓
2. Historical data updated: "premium + cart_abandoner + email = 1 more data point"
                    ↓
3. Next similar customer arrives...
                    ↓
4. Agent 2 reads historical data: "Email worked for 65% of similar customers"
                    ↓
5. Agent 3 generates: "Email discount (based on historical success)"
                    ↓
6. Better prediction = Better results = More data = Even better predictions
```

**Every action makes the system smarter!**

Why This Matters:
-----------------
- **Without Agent 9**: System never learns, predictions stay static
- **With Agent 9**: System improves 5-10% monthly as data grows
- **ROI Impact**: Better predictions = Higher conversion = More revenue
- **Compound Effect**: More data → Better patterns → More conversions → More data...

Data Flow:
----------
Agent 8 (Approval) → Agent 9 (Tracker) → historical_actions.json
                                      → historical_patterns.json
                                      → Agent 2 (Pattern Matcher) reads this data

Output:
-------
Recording confirmation, stored under "tracking_result" key.

Example Output:
---------------
{
  "status": "success",
  "message": "Action recorded as SCHEDULED",
  "recorded_data": {
    "customer_id": "CUST_12345",
    "action_type": "email_discount",
    "action_status": "scheduled",
    "timestamp": "2025-01-22T19:30:00"
  },
  "historical_update": "Added to premium_cart_abandoner pattern (now 121 samples)",
  "learning_impact": "This data will improve future predictions for similar customers"
}

Production Enhancements:
------------------------
In production, Agent 9 would also:
- Log to database (not just JSON files)
- Trigger webhook for marketing automation platform
- Update customer profile with engagement timestamp
- Send to analytics system (Google Analytics, Mixpanel)
- Queue message in email service provider (SendGrid, Mailchimp)

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

# Import results tracking tool
from tools.results_tracker_tool import record_result

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
tracker_agent = Agent(
    name="ResultsTrackerAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are a marketing performance analyst and data recorder.

Your task is to track results and update historical data for future learning.

CRITICAL: The previous agent (Agent 8) has either APPROVED or REJECTED the marketing action.
- If APPROVED: Record the action as "scheduled" to historical data
- If REJECTED: Record as "cancelled"

When recording:
1. Read the complete action details from previous agents:
   - Customer ID and segment
   - Action type (email, SMS, push)
   - Channel and offer details
   - Estimated cost and predicted ROI
   - Approval decision (APPROVED/REJECTED)
2. Call record_result to save the outcome
3. This updates BOTH the results file AND historical_patterns data
4. The historical data will help future predictions get better over time

Output format:
{
  "recording_status": "success",
  "action_recorded": {
    "customer_id": "CUST_XXXXX",
    "action_type": "email_discount",
    "action_status": "scheduled" | "cancelled",
    "timestamp": "ISO datetime",
    "segment": "customer_segment",
    "predicted_roi": X.X
  },
  "historical_data_updated": true,
  "pattern_updated": "segment_scenario combination",
  "learning_impact": "Description of how this helps future predictions",
  "next_steps": "Action will be executed at scheduled time" OR "Action cancelled, no execution"
}

IMPORTANT:
- ALWAYS call record_result (even for rejected actions - we learn from those too!)
- Include ALL relevant details from previous agents
- Provide clear confirmation message
- Explain how this recording helps the system learn

Remember: Your work enables the entire system to get smarter. Every data point you record
makes future predictions more accurate, leading to higher conversion rates and better ROI.""",
    output_key="tracking_result",  # Session state key
    tools=[FunctionTool(record_result)]  # Results recording tool
)

print("[OK] ResultsTrackerAgent created with ADK (Agent 9)")

# ============================================================================
# STANDALONE TESTING
# ============================================================================
async def test_agent():
    """Test the results tracker agent."""
    print("\n[Testing Results Tracker Agent]\n")
    
    runner = InMemoryRunner(agent=tracker_agent)
    
    prompt = """Record this marketing action:
    Customer: CUST_12345 (premium segment)
    Action: Email with 15% discount
    Status: APPROVED by human reviewer
    Cost: ₹575
    Predicted ROI: 8.5
    Schedule: 2025-01-22 19:30
    
    Update historical data."""
    
    response = await runner.run_debug(prompt)
    
    print("\n[Tracking Complete]")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_agent())
