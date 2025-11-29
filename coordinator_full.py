"""
NBA AI - Main Orchestrator
===========================

This is the main entry point for the Next Best Action (NBA) AI system.
It orchestrates 10 specialized AI agents across 3 clusters to:
1. Analyze customer behavior
2. Predict optimal marketing actions
3. Create personalized content
4. Request human approval (HITL)
5. Track results for continuous learning

Architecture:
-------------
- Cluster 1 (Sequential): Customer Discovery → Pattern Matching → Action Generation
- Cluster 2 (Parallel):   Business Rules Validation + ROI Scoring (simultaneously)
- Cluster 3 (Sequential): Timing Optimization → Content Creation → Human Approval → Results Tracking

Key Features:
-------------
- 10 specialized AI agents working together
- Parallel processing for faster validation
- Human-in-the-Loop (HITL) approval before execution
- Continuous learning from outcomes
- Session-based data flow (no redundant database calls)

Usage:
------
    python coordinator_full.py

Requirements:
-------------
- Google ADK installed
- GOOGLE_API_KEY in .env file
- All agent modules in agents/ directory

Author: NBA AI Team
License: MIT
"""

import asyncio
import sys
import io
import os
import traceback
from dotenv import load_dotenv

# Force UTF-8 encoding for stdout/stderr to handle special characters (e.g. Rupee symbol)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ============================================================================
# ADK IMPORTS - Google Agent Development Kit
# ============================================================================
from google.adk.agents import SequentialAgent, ParallelAgent
from google.adk.runners import InMemoryRunner

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================
# Add parent directory to Python path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file (contains GOOGLE_API_KEY)
load_dotenv()

# ============================================================================
# AGENT IMPORTS - All 10 specialized agents
# ============================================================================
from agents.agent_0_proxy_adk import proxy_agent              # Customer scenario generator
from agents.agent_1_profiler_adk import customer_profiler_agent   # Behavior analyzer
from agents.agent_2_pattern_adk import pattern_matcher_agent      # Historical pattern matcher
from agents.agent_3_generator_adk import action_generator_agent   # Marketing action creator
from agents.agent_4_validator_adk import validator_agent          # Business rules validator
from agents.agent_5_scorer_adk import scorer_agent                # ROI scorer & ranker
from agents.agent_6_timing_adk import timing_agent                # Timing optimizer
from agents.agent_7_content_adk import content_agent              # Content creator (copywriter)
from agents.agent_8_approval_adk import approval_agent            # Human approval (HITL)
from agents.agent_9_tracker_adk import tracker_agent              # Results tracker & learner

print("Building NBA Orchestrator with 10 agents + HITL...")

# ============================================================================
# CLUSTER 1: CUSTOMER DISCOVERY & ACTION GENERATION (Sequential)
# ============================================================================
# This cluster runs sequentially because each agent builds on the previous one's output:
# - Agent 0 generates customer profile
# - Agent 1 reads that profile and adds behavioral analysis
# - Agent 2 reads analysis and finds historical matches
# - Agent 3 reads matches and generates action options
#
# Data Flow: proxy → profiler → pattern → generator (linear pipeline)
cluster_1_discovery = SequentialAgent(
    name="DiscoveryCluster",
    sub_agents=[
        proxy_agent,              # Agent 0: Generate realistic customer scenario
        customer_profiler_agent,  # Agent 1: Analyze customer behavior & calculate urgency
        pattern_matcher_agent,    # Agent 2: Match to historical successful campaigns
        action_generator_agent    # Agent 3: Generate 4-5 marketing action options
    ],
    description="Customer discovery and action generation pipeline"
)

# ============================================================================
# CLUSTER 2: VALIDATION & SCORING (Parallel)
# ============================================================================
# This cluster runs in PARALLEL because validation and scoring are independent:
# - Agent 4 checks business rules (budget, inventory, compliance)
# - Agent 5 scores actions and predicts ROI
# Both can run simultaneously on the same input, saving time!
#
# Data Flow: validator + scorer run at the same time
cluster_2_validation = ParallelAgent(
    name="ValidationCluster",
    sub_agents=[
        validator_agent,  # Agent 4: Validate against business rules (budget, inventory)
        scorer_agent      # Agent 5: Score actions & predict ROI (1-10 scale)
    ],
    description="Parallel validation and scoring of generated actions"
)

# ============================================================================
# CLUSTER 3: EXECUTION PLANNING & TRACKING (Sequential)
# ============================================================================
# This cluster runs sequentially for the execution workflow:
# - Agent 6 determines optimal send time
# - Agent 7 creates personalized content
# - Agent 8 requests human approval (PAUSES execution here!)
# - Agent 9 records the outcome for learning
#
# Data Flow: timing → content → approval → tracker (must be sequential)
cluster_3_execution = SequentialAgent(
    name="ExecutionCluster",
    sub_agents=[
        timing_agent,    # Agent 6: Calculate optimal send time (day/time optimization)
        content_agent,   # Agent 7: Generate personalized email/SMS content
        approval_agent,  # Agent 8: Request human approval (HITL - execution PAUSES here)
        tracker_agent    # Agent 9: Record outcome to historical data (enables learning)
    ],
    description="Execution planning with human approval and tracking"
)

# ============================================================================
# FINAL ORCHESTRATOR: Combine all 3 clusters
# ============================================================================
# The top-level orchestrator runs the 3 clusters sequentially:
# 1. Discovery → 2. Validation → 3. Execution
#
# Why Sequential at this level?
# - Need customer profile before validating actions
# - Need validated/scored actions before creating content
# - Need content before requesting approval
# - Need approval before tracking outcome
nba_orchestrator = SequentialAgent(
    name="NbaOrchestrator",
    sub_agents=[
        cluster_1_discovery,   # Sequential: Discover customer & generate actions
        cluster_2_validation,  # Parallel:   Validate & score simultaneously
        cluster_3_execution    # Sequential: Plan execution, get approval, & track
    ],
    description="Complete Next Best Action Orchestrator (10 agents with HITL)"
)

# ============================================================================
# STARTUP CONFIRMATION
# ============================================================================
print("[OK] Orchestrator Ready")
print("  - Cluster 1 (Sequential): 4 agents")
print("  - Cluster 2 (Parallel):   2 agents")
print("  - Cluster 3 (Sequential): 4 agents (includes HITL)")
print("  - Total: 10 agents with Human-in-the-Loop approval")

# ============================================================================
# MAIN EXECUTION FUNCTION
# ============================================================================
async def main():
    """
    Main execution function for the NBA AI orchestrator.
    
    Flow:
    1. Initialize runner with InMemorySessionService
    2. Trigger orchestrator with "start" command
    3. All 10 agents execute in sequence/parallel as designed
    4. Human approval pauses execution at Agent 9
    5. After approval, Agent 8 records outcome
    6. Final response returned
    
    Returns:
        Final agent output after all 10 agents complete
    """
    print("\n" + "="*60)
    print("STARTING NBA ORCHESTRATOR")
    print("="*60)
    
    # Create runner with in-memory session service
    # Note: For production, use DatabaseSessionService instead
    runner = InMemoryRunner(agent=nba_orchestrator)
    
    # Trigger orchestrator with initial prompt
    print("\n>> User Input: 'start'\n")
    
    try:
        # Run in debug mode for detailed output
        # This will show each agent's output as it executes
        response = await runner.run_debug("start")
        
        print("\n" + "="*60)
        print("ORCHESTRATOR COMPLETE [SUCCESS]")
        print("="*60)
        print("\nFinal Response:")
        print(response)
        
    except Exception as e:
        # Catch and display any errors during execution
        print(f"\n[ERROR] {e}")
        traceback.print_exc()

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
