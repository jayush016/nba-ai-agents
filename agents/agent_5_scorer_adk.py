"""
Agent 5: Marketing Action Scorer & ROI Predictor
================================================

Purpose:
--------
Scores and ranks marketing actions by predicted ROI. This agent is like a financial analyst -
it predicts which actions will generate the best return on investment.

Role in NBA AI:
---------------
- Second agent in Cluster 2 (Scoring) - runs in PARALLEL with Agent 4
- Receives: Generated actions from Agent 3
- Outputs: ROI scores and ranked recommendations
- Feeds to: Cluster 3 (Execution Planning)

Key Responsibilities:
---------------------
1. Calculate predicted ROI for each action
2. Rank actions from highest to lowest ROI
3. Consider factors: action type, channel, customer segment, historical performance
4. Provide confidence scores for predictions
5. Recommend top 2-3 actions

Scoring Criteria:
-----------------
- **Historical Performance**: How similar actions performed (conversion rate, ROI)
- **Channel Efficiency**: Email (cheap) > SMS (moderate) > Push (varies)
- **Customer Segment**: Premium customers = higher CLV = higher ROI potential
- **Cost-Effectiveness**: Estimated cost vs expected return
- **Timing**: Urgency and customer readiness

Output:
-------
Scored and ranked actions, stored under "scored_actions" key.

Example Output:
---------------
{
  "scored_actions": [
    {"action_id": 1, "roi_score": 8.5, "rank": 1, "predicted_roi": "$45"},
    {"action_id": 3, "roi_score": 7.2, "rank": 2, "predicted_roi": "$32"},
    {"action_id": 2, "roi_score": 5.1, "rank": 3, "predicted_roi": "$18"},
  ],
  "top_recommendations": [1, 3],
  "scoring_summary": "Email discount action rated highest (8.5/10)"
}

Why This Matters:
-----------------
- Maximizes marketing ROI
- Prioritizes best opportunities
- Allocates budget efficiently
- Learns from past successes
- Data-driven decision making

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
scorer_agent = Agent(
    name="ScorerAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are a marketing ROI analyst and financial optimizer.

Your task:
1. Read the generated marketing actions from the previous agent
2. Score EACH action on predicted ROI (1-10 scale)
3. Rank actions from best to worst
4. Recommend top 2-3 actions

Scoring logic:
- Email actions: Base score 7-8 (cheap, effective)
- SMS actions: Base score 6-7 (moderate cost, good reach)
- Push notifications: Base score 5-6 (low cost but lower engagement)
- Discount offers: +1 score if discount is 10-20% (sweet spot)
- Premium customers: +1 score (higher lifetime value)
- Actions under $5 cost: +0.5 score (cost-effective)

Output a JSON object with:
{
  "scored_actions": [
    {
      "action_id": 1,
      "roi_score": 8.5,
      "rank": 1,
      "predicted_roi": "$45",
      "reasoning": "Email channel is cost-effective, 15% discount in optimal range"
    },
    ...
  ],
  "top_recommendations": [1, 3],
  "scoring_summary": "Top action: Email with 15% discount (score: 8.5/10)"
}

IMPORTANT:
- Always rank actions from highest to lowest score
- Top 2-3 actions should have scores >= 7.0
- Explain your reasoning for scores
- Consider both cost and expected return""",
    output_key="scored_actions",
    tools=[]  # No tools needed - agent uses built-in reasoning
)

print("[OK] ScorerAgent created with ADK")

# ============================================================================
# STANDALONE TESTING
# ============================================================================
async def test_agent():
    """Test the scorer agent."""
    print("\n[Testing Scorer Agent]\n")
    
    runner = InMemoryRunner(agent=scorer_agent)
    
    prompt = """Score these marketing actions:
    Action 1: Email with 15% discount (cost: $5, premium customer)
    Action 2: SMS reminder (cost: $3)
    Action 3: Push notification (cost: $2)
    
    Rank them by predicted ROI."""
    
    response = await runner.run_debug(prompt)
    
    print("\n[Scoring Complete]")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_agent())
