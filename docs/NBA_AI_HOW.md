# NBA AI - HOW Documentation
## Technical Architecture & Implementation

---

## System Overview

**NBA AI** is built using **Google's Agent Development Kit (ADK)** with a **3-cluster orchestration pattern:**

```
NbaOrchestrator (SequentialAgent)
├── Cluster 1: Discovery (SequentialAgent) - 4 agents
├── Cluster 2: Validation (ParallelAgent) - 2 agents  
└── Cluster 3: Execution (SequentialAgent) - 4 agents
```

**Technology Stack:**
- **Framework:** Google ADK (Agent Development Kit)
- **LLM:** Gemini 2.5 Flash Lite
- **Patterns:** Sequential, Parallel, Loop
- **Tools:** FunctionTool for Python business logic
- **Session:** InMemorySessionService (upgradable to Database)
- **Language:** Python 3.14+

---

## Architecture Deep Dive

### The Orchestrator
**File:** `coordinator_full.py`

**Core Implementation:**
```python
nba_orchestrator = SequentialAgent(
    name="NbaOrchestrator",
    sub_agents=[
        cluster_1_discovery,   # Sequential: 4 agents
        cluster_2_validation,  # Parallel: 2 agents
        cluster_3_execution    # Sequential: 4 agents
    ],
    description="Complete Next Best Action Orchestrator (10 agents with HITL)"
)
```

**How it works:**
1. User calls: `await runner.run_debug("start")`
2. Orchestrator executes clusters **sequentially**
3. Within Cluster 2, agents run **in parallel**
4. Each agent's `output_key` is stored in **session state**
5. Subsequent agents read from session state (no database lookups)

**Key Code:**
```python
# coordinator_full.py lines 21-76
from agents.agent_0_proxy_adk import proxy_agent
from agents.agent_1_profiler_adk import customer_profiler_agent
# ... imports all 10 agents

# Create clusters
cluster_1_discovery = SequentialAgent(
    name="DiscoveryCluster",
    sub_agents=[
        proxy_agent,              # 0
        customer_profiler_agent,  # 1
        pattern_matcher_agent,    # 2
        action_generator_agent    # 3
    ]
)

cluster_2_validation = ParallelAgent(  # PARALLEL!
    name="ValidationCluster",
    sub_agents=[
        validator_agent,  # 4
        scorer_agent      # 5
    ]
)

cluster_3_execution = SequentialAgent(
    name="ExecutionCluster",
    sub_agents=[
        timing_agent,     # 6
        content_agent,    # 7
        approval_agent,   # 9 - HITL
        tracker_agent     # 8
    ]
)
```

---

## Agent Implementation Details

### Agent 0: Proxy Customer Generator
**File:** `agents/agent_0_proxy_adk.py`

**How it works:**
```python
proxy_agent = Agent(
    name="ProxyCustomerAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are a customer data generator for an e-commerce system.
    
    Generate a JSON object with this EXACT structure:
    {
        "customer_id": "CUST_XXX",
        "name": "Full Name", 
        "age": 25,
        "segment": "value_conscious|premium|vip",
        "behavior": {...},
        "preferences": {...}
    }
    Return ONLY the JSON object. No markdown formatting.""",
    output_key="generated_customer_profile"  # Stored in session state
)
```

**Technical Flow:**
1. LLM receives instruction + user message ("start")
2. LLM generates realistic customer JSON
3. ADK stores output in `session.state["generated_customer_profile"]`
4. Next agent reads from session state automatically

**No Tools:** This agent uses pure LLM generation, no function calling.

---

### Agent 1: Customer Profiler
**File:** `agents/agent_1_profiler_adk.py`

**How it works:**
```python
customer_profiler_agent = Agent(
    name="CustomerProfilerAgent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="""You are an expert customer behavior analyst.

    IMPORTANT: The customer profile JSON has ALREADY been provided 
    by the previous agent in this conversation.
    DO NOT call get_customer_data - read from conversation context.
    
    Analyze and provide:
    - Purchase Intent: low/medium/high
    - Urgency Score: 0.0-1.0
    - Recommended Action Priority: low/medium/high/critical
    """,
    output_key="customer_analysis",
    tools=[]  # NO TOOLS - reads from session state
)
```

**Key Design Decision:**
- **Original design** had `tools=[FunctionTool(get_customer_data)]`
- **Problem:** Tried to fetch from database, but customer was just generated!
- **Solution:** Removed tool, agent now reads from previous agent's output
- **Result:** Smooth pipeline, no database errors

**Technical Flow:**
1. ADK automatically provides conversation history to agent
2. Agent sees Proxy's JSON output in context
3. LLM analyzes the JSON
4. Outputs structured analysis
5. Stored in `session.state["customer_analysis"]`

---

### Agent 2: Pattern Matcher
**File:** `agents/agent_2_pattern_adk.py`

**How it works:**
```python
pattern_matcher_agent = Agent(
    name="PatternMatcherAgent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="""You are a data analyst specializing in customer patterns.
    
    When you receive a customer profile (JSON), you MUST:
    1. Call `find_similar_customer_segment` to find matching segments
    2. Call `get_best_performing_action` for that segment
    3. Generate insights
    """,
    output_key="pattern_analysis",
    tools=[
        FunctionTool(find_similar_customer_segment),
        FunctionTool(get_best_performing_action)
    ]
)
```

**Tool Implementation:**
**File:** `tools/historical_patterns_tool.py`

**Critical Fix Made:**
```python
# BEFORE (BROKEN):
def find_similar_customer_segment(customer_profile: Dict) -> Dict:
    # Gemini can't serialize Dict parameters!
    
# AFTER (WORKING):
def find_similar_customer_segment(customer_profile_json: str) -> Dict:
    """
    Args:
        customer_profile_json: Customer profile as JSON string
    """
    # Parse JSON string to dict
    customer_profile = json.loads(customer_profile_json)
    
    # Match logic based on attributes
    churn_risk = customer_profile.get('churn_risk', 'low')
    cart_status = customer_profile.get('cart_status', 'empty')
    
    if cart_status == 'abandoned':
        matched_segment = 'price_sensitive_cart_abandoners'
    elif churn_risk == 'high':
        matched_segment = 'high_churn_risk'
    # ... more logic
    
    # Query historical data
    result = query_historical_patterns(segment=matched_segment)
    
    return {
        "matched_segment": matched_segment,
        "segment_data": result.get('data', {}),
        "confidence": 0.85
    }
```

**Why the param type change?**
- Gemini API's function calling **cannot serialize complex types**
- `Dict` parameter → `400 INVALID_ARGUMENT` error
- `str` parameter → Works perfectly, agent passes JSON string
- This is a **universal ADK pattern**: use primitive types (`str`, `int`, `float`)

---

### Agent 3: Action Generator
**File:** `agents/agent_3_generator_adk.py`

**How it works:**
```python
action_generator_agent = Agent(
    name="ActionGeneratorAgent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="""You are a creative marketing strategist.
    
    Generate 4-5 diverse marketing actions as a JSON array.
    Each action must include:
    - action_id, action_type, channel, strategy
    - discount_percentage, estimated_cost
    - expected_conversion_rate
    """,
    output_key="proposed_actions",
    tools=[FunctionTool(get_action_templates)]
)
```

**Tool:** `get_action_templates()`
- Returns pre-defined marketing templates
- LLM customizes templates based on customer profile
- Enables consistent action structure

**Output Example:**
```json
[
    {
        "action_id": "EMAIL_PROMO_001",
        "action_type": "nurture",
        "channel": "email",
        "strategy": "10% discount + urgency messaging",
        "estimated_cost": 0.10,
        "expected_conversion_rate": 0.65
    },
    // ... 3-4 more actions
]
```

---

### Agent 4 & 5: Validator + Scorer (Parallel Execution)
**Files:** 
- `agents/agent_4_validator_adk.py`
- `agents/agent_5_scorer_adk.py`

**How Parallel Execution Works:**
```python
cluster_2_validation = ParallelAgent(
    name="ValidationCluster",
    sub_agents=[
        validator_agent,  # Runs simultaneously
        scorer_agent      # Runs simultaneously
    ]
)
```

**Technical Implementation:**
1. ADK's `ParallelAgent` uses `asyncio.gather()`
2. Both agents receive the same input (session state)
3. Execute concurrently (not blocking each other)
4. Both outputs are combined in session state
5. **Result:** Faster execution (2 agents in time of 1)

**Validator Implementation:**
```python
validator_agent = Agent(
    name="ValidatorAgent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    tools=[
        FunctionTool(check_permission_rules),
        FunctionTool(check_budget_rules),
        FunctionTool(check_inventory_rules)
    ]
)
```

Tools check business rules:
```python
# tools/business_rules_tool.py
def check_budget_rules(action: dict) -> dict:
    """Validate action against budget constraints."""
    estimated_cost = action.get('estimated_cost', 0)
    
    # Rule: Single action can't cost more than $5
    if estimated_cost > 5.0:
        return {
            "is_valid": False,
            "reason": "Cost exceeds single action limit ($5)"
        }
    
    return {"is_valid": True, "reason": "Budget OK"}
```

**Scorer Implementation:**
```python
scorer_agent = Agent(
    name="ScorerAgent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="""Score each action on a 1-10 scale.
    
    Evaluate:
    - Channel fit (matches customer preference?)
    - Offer strength (compelling?)
    - Timing appropriateness
    - Cost efficiency
    
    Calculate predicted ROI.
    Sort actions by score DESC.""",
    tools=[]  # Pure LLM reasoning
)
```

Output format:
```json
[
    {
        "action_id": "EMAIL_PROMO_001",
        "score": 9,
        "score_breakdown": {
            "channel_fit": 10,
            "offer_strength": 8,
            "timing_appropriateness": 9,
            "cost_efficiency": 8
        },
        "predicted_roi": 2.2,
        "confidence": 0.85
    }
]
```

---

### Agent 6: Timing Optimizer
**File:** `agents/agent_6_timing_adk.py`

**How it works:**
```python
timing_agent = Agent(
    name="TimingOptimizerAgent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    tools=[
        FunctionTool(get_optimal_send_time),
        FunctionTool(calculate_send_time),
        FunctionTool(get_day_of_week_insights)
    ]
)
```

**Key Tool:** `calculate_send_time()`
**File:** `tools/timing_intelligence_tool.py`

**Critical Fix Made:**
```python
# BEFORE (BROKEN):
def calculate_send_time(
    channel: str,
    urgency: str = "medium",
    from_time: datetime = None  # ❌ Gemini can't handle datetime
) -> datetime:
    return from_time + timedelta(hours=2)  # ❌ Type error!

# AFTER (WORKING):
def calculate_send_time(
    channel: str,
    urgency: str = "medium",
    from_time: str = None  # ✅ JSON-serializable string
) -> str:
    # Parse ISO string to datetime
    if from_time is None:
        from_time_dt = datetime.now()
    else:
        from_time_dt = datetime.fromisoformat(from_time)
    
    # Calculate timing
    timing_rec = get_optimal_send_time(channel, urgency)
    
    if timing_rec.get('recommended_timing') == 'immediate':
        return from_time_dt.isoformat()
    
    # Default: 2 hours from now
    result = from_time_dt + timedelta(hours=2)
    return result.isoformat()  # ✅ Return as string
```

**Why this pattern?**
- Gemini function calling only supports: `str`, `int`, `float`, `bool`
- Complex types (`datetime`, `Dict`, `List[Dict]`) cause errors
- **Solution:** Use ISO strings, parse inside function

---

### Agent 7: Content Creator
**File:** `agents/agent_7_content_adk.py`

**How it works:**
```python
content_agent = Agent(
    name="ContentCreatorAgent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="""You are an expert marketing copywriter.
    
    Create personalized email/SMS content:
    - Subject line (catchy, under 50 chars)
    - Preview text
    - Greeting (use customer name!)
    - Body (compelling, action-oriented)
    - Call-to-action
    - Urgency element
    
    Output as JSON with all fields.""",
    tools=[FunctionTool(validate_content)]
)
```

**Tool:** `validate_content()`
- Checks against brand guidelines
- Ensures no prohibited words
- Validates tone matches customer segment

**Example Output:**
```json
{
    "channel": "email",
    "subject_line": "Priya, your cart misses you! 🛒",
    "preview_text": "Complete your purchase and save 15%",
    "greeting": "Hi Priya,",
    "body": "We noticed you left some amazing items...",
    "call_to_action": "Complete My Purchase",
    "urgency_element": "Offer expires in 24 hours!",
    "validation_status": "valid"
}
```

---

### Agent 8: Human Approval (HITL)
**File:** `agents/agent_9_approval_adk.py`

**How it works:**
```python
def request_human_approval(
    action_summary: str,
    estimated_cost: str,
    expected_roi: str,
    tool_context: ToolContext  # ADK's HITL mechanism
) -> dict:
    # First call: Request confirmation
    if not tool_context.tool_confirmation:
        print(f"\n{'='*60}")
        print("HUMAN APPROVAL REQUIRED")
        print(f"Action: {action_summary}")
        print(f"Cost: {estimated_cost}")
        print(f"Expected ROI: {expected_roi}")
        print(f"{'='*60}\n")
        
        tool_context.request_confirmation(
            hint=f"Approve marketing action?",
            payload={"action": action_summary}
        )
        return {"status": "pending"}  # ⏸️ PAUSES HERE
    
    # Second call: Check decision
    if tool_context.tool_confirmation.confirmed:
        return {"status": "approved", "approved": True}  # ▶️ RESUMES
    else:
        return {"status": "rejected", "approved": False}

approval_agent = Agent(
    name="HumanApprovalAgent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    tools=[FunctionTool(request_human_approval)]
)
```

**How ADK HITL Works:**

1. **Tool calls `request_confirmation()`**
   - ADK generates `adk_request_confirmation` event
   - Execution **PAUSES** ⏸️
   - Event contains `invocation_id` for resuming

2. **Human reviews and decides**
   - In production: API call, UI button, Slack approval, etc.
   - In demo: Terminal input or auto-approve

3. **System resumes with decision**
   - Construct `FunctionResponse` with `confirmed: True/False`
   - Call `runner.run_async()` again with same `invocation_id`
   - Execution **RESUMES** ▶️ from exact point

**Production Implementation:**
```python
# coordinator_full.py would be updated to:
async def run_journey_with_hitl(self, scenario):
    events = []
    async for event in runner.run_async(...):
        # Detect pause
        if event has adk_request_confirmation:
            approval_id = event.function_call.id
            invocation_id = event.invocation_id
            
            # Send to approval API/UI
            decision = await approval_api.request_approval(...)
            
            # Resume execution
            response = types.FunctionResponse(
                id=approval_id,
                confirmed=decision.approved
            )
            resume_msg = types.Content(parts=[types.Part(function_response=response)])
            
            # Continue from where we paused
            async for event in runner.run_async(
                invocation_id=invocation_id,
                new_message=resume_msg
            ):
                # System resumes here!
```

---

### Agent 9: Results Tracker
**File:** `agents/agent_8_tracker_adk.py`

**How it works:**
```python
# Wrapper functions for class methods
tracker = OriginalTracker()  # From agent_8_tracker.py

def record_result(customer_id: str, action: dict, result: dict) -> dict:
    """Record a result - updates historical data."""
    return tracker.record_action_result(customer_id, action, result)

tracker_agent = Agent(
    name="ResultsTrackerAgent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="""Read approval status from previous agent.
    
    If APPROVED:
        - Record as "scheduled" 
        - Update historical_customer_data.json
        - Future predictions will use this data
    
    If REJECTED:
        - Record as "cancelled"
    
    Call record_result with full action details.""",
    tools=[
        FunctionTool(record_result),
        FunctionTool(get_summary)
    ]
)
```

**Implementation:** `agents/agent_8_tracker.py` (lines 72-78)
```python
def _save_result(self, result_record: Dict):
    """Save result to results file."""
    # Load existing results
    if os.path.exists(self.results_file):
        with open(self.results_file, 'r') as f:
            results = json.load(f)
    else:
        results = []
    
    # Append new result
    results.append(result_record)
    
    # Save back
    with open(self.results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Also update historical patterns
    self._update_historical_patterns(result_record)
```

**Historical Learning Loop:**
```python
def _update_historical_patterns(self, result_record: Dict):
    """Update historical data with new learnings."""
    # Read historical_customer_data.json
    with open('data/historical_customer_data.json', 'r') as f:
        historical_data = json.load(f)
    
    # Extract segment
    segment = result_record['customer_segment']
    
    # Update segment success rates
    if segment in historical_data['customer_segments']:
        segment_data = historical_data['customer_segments'][segment]
        
        # Update action success rate
        action_type = result_record['action']['channel']
        for action in segment_data['successful_actions']:
            if action['action'] == action_type:
                # Recalculate success rate with new data
                action['success_rate'] = calculate_new_rate(...)
    
    # Save updated historical data
    with open('data/historical_customer_data.json', 'w') as f:
        json.dump(historical_data, f, indent=2)
```

**Result:** Next time Agent 2 analyzes a similar customer, it sees updated success rates!

---

## Data Flow

```
1. User Input: "start"
   ↓
2. Proxy generates customer JSON
   → Stored in session.state["generated_customer_profile"]
   ↓
3. Profiler reads from session.state
   → Analyzes, outputs to session.state["customer_analysis"]
   ↓
4. Pattern Matcher reads from session.state
   → Calls tools: find_similar_customer_segment(JSON string)
   → Outputs to session.state["pattern_analysis"]
   ↓
5. Generator reads from session.state
   → Calls tool: get_action_templates()
   → Outputs to session.state["proposed_actions"]
   ↓
6. PARALLEL: Validator + Scorer
   → Both read from session.state
   → Both output simultaneously
   → Combined in session.state["validation_results"] + ["scored_actions"]
   ↓
7. Timing reads from session.state
   → Calls tool: calculate_send_time(channel, urgency, from_time_str)
   → Outputs to session.state["timing_recommendation"]
   ↓
8. Content reads from session.state
   → Generates personalized email/SMS
   → Outputs to session.state["final_content"]
   ↓
9. Approval reads from session.state
   → Calls tool: request_human_approval(...)
   → tool_context.request_confirmation() 
   → ⏸️ EXECUTION PAUSES
   → Human decides
   → ▶️ EXECUTION RESUMES
   → Outputs to session.state["approval_status"]
   ↓
10. Tracker reads from session.state
    → Calls tool: record_result(customer_id, action, result)
    → Updates historical_customer_data.json
    → Outputs to session.state["tracker_output"]
    ↓
11. Complete! System returns final state
```

---

## ADK Patterns Used

### 1. SequentialAgent
```python
SequentialAgent(
    sub_agents=[agent_1, agent_2, agent_3]
)
```
- Executes agents in order
- Each agent's output available to next
- **Use case:** When order matters (profiling before generating)

### 2. ParallelAgent
```python
ParallelAgent(
    sub_agents=[validator, scorer]
)
```
- Executes agents simultaneously using `asyncio.gather()`
- **Use case:** Independent validation tasks

### 3. FunctionTool
```python
FunctionTool(my_python_function)
```
- Wraps Python function as agent tool
- **Critical:** Use primitive types only (`str`, `int`, not `Dict`)

### 4. ToolContext (HITL)
```python
def my_tool(param: str, tool_context: ToolContext) -> dict:
    if not tool_context.tool_confirmation:
        tool_context.request_confirmation(...)
        return {"status": "pending"}  # Pauses
    
    # Resumed with decision
    if tool_context.tool_confirmation.confirmed:
        return {"approved": True}
```

### 5. Session State Management
```python
agent = Agent(
    output_key="customer_profile"  # Stores in session.state
)
```
- Every agent's output stored automatically
- Next agents access via conversation history

---

## Running the System

**File:** `coordinator_full.py` (lines 83-107)
```python
async def main():
    # Create runner with orchestrator
    runner = InMemoryRunner(agent=nba_orchestrator)
    
    # Execute with simple string trigger
    response = await runner.run_debug("start")
    
    print("ORCHESTRATOR COMPLETE")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

**What `run_debug` does:**
1. Creates new session with `InMemorySessionService`
2. Sends "start" message to first agent (Proxy)
3. Orchestrator executes all 10 agents sequentially/parallel
4. Returns complete session history

---

## Key Technical Decisions

### 1. Why ADK over LangChain/CrewAI?
- **Google-native:** Direct integration with Gemini
- **Production-ready:** Deploys to Vertex AI Agent Engine
- **HITL built-in:** `ToolContext` for human approval
- **Observability:** LoggingPlugin, trace IDs, metrics

### 2. Why InMemorySessionService?
- **Development speed:** No database setup
- **Upgradable:** Switch to `DatabaseSessionService` for production
- **Sufficient:** For competition demo and MVP

### 3. Why remove database lookups from profiler?
- **Pipeline integrity:** Data flows through agents, not external DB
- **Simplicity:** No race conditions, no "customer not found" errors
- **Performance:** Faster execution, no DB round trips

### 4. Why parallel validation?
- **Speed:** Cut execution time by 50% for validation phase
- **Independence:** Validator and Scorer don't depend on each other
- **Scalability:** Can add more parallel validators easily

---

## File Structure

```
Capstone Project/
├── coordinator_full.py          # Main orchestrator
├── agents/
│   ├── agent_0_proxy_adk.py     # Customer generator
│   ├── agent_1_profiler_adk.py  # Profiler (NO tools)
│   ├── agent_2_pattern_adk.py   # Pattern matcher
│   ├── agent_3_generator_adk.py # Action generator
│   ├── agent_4_validator_adk.py # Validator
│   ├── agent_5_scorer_adk.py    # Scorer
│   ├── agent_6_timing_adk.py    # Timing optimizer
│   ├── agent_7_content_adk.py   # Content creator
│   ├── agent_9_approval_adk.py  # HITL approval
│   └── agent_8_tracker_adk.py   # Tracker + learner
├── tools/
│   ├── customer_data_tool.py           # (Not used in pipeline)
│   ├── historical_patterns_tool.py     # Agent 2 tools
│   ├── action_templates_tool.py        # Agent 3 tools
│   ├── business_rules_tool.py          # Agent 4 tools
│   ├── timing_intelligence_tool.py     # Agent 6 tools
│   └── content_guidelines_tool.py      # Agent 7 tools
├── data/
│   ├── historical_customer_data.json   # Segment patterns (UPDATED by Agent 8)
│   ├── historical_actions.json         # Action results (UPDATED by Agent 8)
│   ├── action_templates.json           # Marketing templates
│   ├── timing_intelligence.json        # Timing data
│   └── content_guidelines.json         # Brand guidelines
└── observability.py                    # MLflow integration (future)
```

---

## Production Deployment

### Step 1: Add Persistence
```python
from google.adk.sessions import DatabaseSessionService

session_service = DatabaseSessionService(
    db_url="postgresql://user:pass@host/db"
)
```

### Step 2: Add Observability
```python
from google.adk.plugins import LoggingPlugin

runner = Runner(
    agent=nba_orchestrator,
    plugins=[LoggingPlugin()]
)
```

### Step 3: Deploy to Vertex AI
```bash
adk deploy --project=my-project --location=global
```

### Step 4: Integrate HITL with API
Replace print statements in approval tool with API calls:
```python
def request_human_approval(...):
    if not tool_context.tool_confirmation:
        # Send to approval API
        approval_id = await approval_api.create_request({
            "action": action_summary,
            "cost": estimated_cost
        })
        tool_context.request_confirmation(...)
```

---

## Summary

**NBA AI** uses cutting-edge ADK patterns to create a production-ready, intelligent marketing system:

✅ **SequentialAgent** for ordered workflows  
✅ **ParallelAgent** for concurrent validation  
✅ **FunctionTool** for business logic integration  
✅ **ToolContext** for human-in-the-loop control  
✅ **Session state** for seamless data flow  
✅ **ISO strings** for datetime handling  
✅ **Historical learning** for continuous improvement  

**Technical Excellence:** Clean architecture, scalable patterns, production-ready code.
