"""
Agent 8: Human-in-the-Loop (HITL) Approval Gateway
===================================================

Purpose:
--------
**THE MOST CRITICAL AGENT** - Pauses execution and requests human approval before any
marketing action is executed. This prevents AI from making costly mistakes or sending
inappropriate messages.

How HITL Works:
---------------
1. Agent receives proposed action from Agent 7 (Content Creator)
2. Extracts action summary, cost, and expected ROI
3. Calls request_human_approval() which:
   - PAUSES orchestrator execution ⏸️
   - Displays approval screen to human
   - Waits for YES/NO decision
4. Human reviews and approves/rejects
5. Execution RESUMES with decision ▶️
6. Result passed to Agent 9 (Tracker)

Why This Matters:
-----------------
- Gives humans final control over AI decisions
- Prevents spam or inappropriate messages
- Protects brand reputation  
- Ensures compliance (GDPR, CAN-SPAM)
- Builds trust in the AI system

Two-Call Pattern:
-----------------
Call 1: request_confirmation() → Execution pauses
Wait... (human reviews)
Call 2: Check tool_confirmation → Resume with decision

Author: NBA AI Team
"""

import os
import sys
from dotenv import load_dotenv

# ============================================================================
# ADK IMPORTS
# ============================================================================
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================
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
# HITL APPROVAL FUNCTION
# ============================================================================
def request_human_approval(
    action_summary: str,
    estimated_cost: str,
    expected_roi: str,
    tool_context: ToolContext
) -> dict:
    """
    Request human approval for a marketing action.
    
    This implements the Human-in-the-Loop (HITL) pattern using ADK's
    tool_context.request_confirmation() mechanism.
    
    Args:
        action_summary: Summary of the proposed action
        estimated_cost: Estimated cost of the action
        expected_roi: Expected return on investment
        tool_context: ADK tool context for HITL
        
    Returns:
        Approval decision (approved: True/False)
    """
    # First call: Request confirmation (PAUSES execution here)
    if not tool_context.tool_confirmation:
        print(f"\n{'='*60}")
        print("HUMAN APPROVAL REQUIRED")
        print(f"{'='*60}")
        print(f"Action: {action_summary}")
        print(f"Cost: {estimated_cost}")
        print(f"Expected ROI: {expected_roi}")
        print(f"{'='*60}\n")
        
        # This PAUSES execution until human responds
        tool_context.request_confirmation(
            hint=f"Approve marketing action?",
            payload={
                "action": action_summary,
                "cost": estimated_cost,
                "roi": expected_roi
            }
        )
        return {"status": "pending", "message": "Waiting for human approval"}
    
    # Second call: Check decision (RESUMES execution with answer)
    if tool_context.tool_confirmation.confirmed:
        return {
            "status": "approved",
            "message": "Action approved by human reviewer",
            "approved": True
        }
    else:
        return {
            "status": "rejected",
            "message": "Action rejected by human reviewer",
            "approved": False
        }

# ============================================================================
# AGENT DEFINITION
# ============================================================================
approval_agent = Agent(
    name="HumanApprovalAgent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are the Human Approval Gateway for marketing actions.

Your task:
1. Read the final marketing content and action details from the previous agents
2. Extract: action summary, estimated cost, and expected ROI
3. Call request_human_approval with these details
4. If approved, output "APPROVED - Action can proceed"
5. If rejected, output "REJECTED - Action cancelled"

Always call the approval tool with clear, concise information.""",
    output_key="approval_status",  # Session state key
    tools=[FunctionTool(request_human_approval)]  # HITL tool
)

print("[OK] HumanApprovalAgent created with ADK (Agent 8)")
