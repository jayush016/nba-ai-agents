"""
Results Tracker Tool - Records marketing action outcomes
Used by Agent 9 (Results Tracker)
"""

import json
import os
from datetime import datetime
from typing import Dict


def record_result(
    customer_id: str,
    action_type: str,
    action_status: str,
    segment: str,
    predicted_roi: float,
    estimated_cost: float,
    channel: str = "email",
    scenario: str = "general"
) -> Dict:
    """
    Record a marketing action result to historical data.
    
    Args:
        customer_id: Customer identifier
        action_type: Type of action (email_discount, sms_reminder, etc.)
        action_status: "scheduled" or "cancelled"
        segment: Customer segment
        predicted_roi: Predicted ROI score (1-10)
        estimated_cost: Estimated action cost
        channel: Communication channel
        scenario: Customer scenario
        
    Returns:
        Confirmation dictionary
    """
    # Prepare action record
    action_record = {
        "timestamp": datetime.now().isoformat(),
        "customer_id": customer_id,
        "customer_segment": segment,
        "scenario_type": scenario,
        "action_type": action_type,
        "channel": channel,
        "estimated_cost": estimated_cost,
        "predicted_roi": predicted_roi,
        "action_status": action_status,
        "approved_by": "human" if action_status == "scheduled" else "rejected",
    }
    
    # File paths
    actions_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'historical_actions.json')
    
    try:
        # Load existing data
        if os.path.exists(actions_file):
            with open(actions_file, 'r') as f:
                all_actions = json.load(f)
        else:
            all_actions = []
        
        # Append new action
        all_actions.append(action_record)
        
        # Save back
        with open(actions_file, 'w') as f:
            json.dump(all_actions, f, indent=2)
        
        return {
            "status": "success",
            "message": f"Action recorded as {action_status.upper()}",
            "recorded_data": action_record,
            "total_historical_actions": len(all_actions),
            "learning_impact": f"This data will improve future predictions for {segment} customers in {scenario} scenarios"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to record action: {str(e)}"
        }
