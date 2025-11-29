"""
Agent 4: Business Rules Validator
==================================

Purpose:
--------
Validates marketing actions against business rules, compliance requirements,
budget constraints, and inventory availability. This agent is the "compliance officer" -
it ensures actions are legal, affordable, and feasible.

Role in NBA AI:
---------------
- First agent in Cluster 2 (Validation) - runs in PARALLEL with Agent 5
- Receives: Generated actions from Agent 3
- Outputs: Validation results (pass/fail) for each  action
- Feeds to: Cluster 3 (Execution Planning)

Key Responsibilities:
---------------------
1. Check business rule compliance (budget, frequency caps, blacklists)
2. Verify inventory availability for promoted products
3. Ensure legal/regulatory compliance (CAN-SPAM, GDPR, DND lists)
4. Validate offer feasibility (discount limits, product eligibility)
5. Filter out invalid actions
6. Flag actions that need additional approval

Tools Used:
-----------
- None - Uses built-in reasoning based on standard business rules

Validation Rules:
-----------------
- **Budget**: Actions over $10 per customer flagged as expensive
- **Channels**: Email/SMS generally allowed, Push notifications typically not opted-in
- **Compliance**: Follow anti-spam regulations
- **Cost**: Flag actions with estimated_cost > $10

Output:
-------
Validation results for each action, stored under "validation_results" key.

Example Output:
---------------
{
  "validated_actions": [
    {"action_id": 1, "valid": true, "reason": "All checks passed"},
    {"action_id": 2, "valid": false, "reason": "Push channel not opted in"},
  ],
  "passed_action_ids": [1, 3],
  "failed_action_ids": [2, 4],
  "compliance_summary": "2 out of 4 actions passed validation"
}

Why This Matters:
-----------------
- Prevents spam complaints
- Avoids legal penalties (GDPR fines)
- Protects brand reputation
- Ensures financial responsibility
- Maintains customer trust

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
validator_agent = Agent(
    name="ValidatorAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are a compliance and business rules specialist.

Your task:
1. Read the generated marketing actions from the previous agent's output
2. For EACH action in the list, check if it passes business rules
3. Summarize which actions are valid and which are not

Business rules checks:
- Email/SMS channels: Customer must have opted in (check compliance)
- Push notifications: Generally not permitted unless explicitly opted in  
- Budget: Actions with estimated_cost > $10 per customer are too expensive
- All actions must follow anti-spam regulations

Output a JSON object with:
{
  "validated_actions": [
    {"action_id": 1, "valid": true, "reason": "Passed all checks"},
    {"action_id": 2, "valid": false, "reason": "Push channel not opted in"},
    ...
  ],
  "passed_action_ids": [1, 3, 4],
  "failed_action_ids": [2],
  "compliance_summary": "3 out of 4 actions passed validation"
}

IMPORTANT:
- Email and SMS are generally valid channels
- Push notifications typically fail (customer not opted in)
- Actions over $10 estimated_cost should be flagged
- Always explain why an action failed""",
    output_key="validation_results",
    tools=[]  # No tools needed - agent will use built-in reasoning
)

print("[OK] ValidatorAgent created with ADK")

# ============================================================================
# STANDALONE TESTING
# ============================================================================
async def test_agent():
    """Test the validator agent."""
    print("\n[Testing Validator Agent]\n")
    
    runner = InMemoryRunner(agent=validator_agent)
    
    prompt = """Validate these marketing actions:
    Action 1: Email with 15% discount to premium customer (cost: $5)
    Action 2: SMS to customer (cost: $3)
    Action 3: Push notification for in-stock product (cost: $2)
    
    Check all business rules."""
    
    response = await runner.run_debug(prompt)
    
    print("\n[Validation Complete]")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_agent())
