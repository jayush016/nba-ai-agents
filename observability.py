"""
Observability Module for Next Best Action System
Uses MLflow to track agent execution, traces, and metrics.
"""

import os
import mlflow
from datetime import datetime

def setup_observability():
    """Initialize MLflow experiment and tracing."""
    
    # Set the experiment name
    experiment_name = "Next_Best_Action_ADK"
    mlflow.set_experiment(experiment_name)
    
    print(f"[Observability] MLflow experiment set to: {experiment_name}")
    
    # Enable autologging for GenAI libraries if available
    # mlflow.langchain.autolog() # If we were using LangChain
    # mlflow.openai.autolog()    # If we were using OpenAI
    
    # Since we are using Google ADK, we will manually log traces
    # or use a generic python function tracer if we want
    
    return mlflow

def log_agent_execution(agent_name, input_data, output_data, duration_s):
    """Log a single agent execution as a run or trace."""
    
    # In a real scenario, we would use mlflow.trace
    # For now, we'll log metrics to the active run
    
    try:
        mlflow.log_metric(f"{agent_name}_duration_seconds", duration_s)
        
        # We can also log inputs/outputs as artifacts or params
        # Truncate if too long
        input_str = str(input_data)[:500]
        output_str = str(output_data)[:500]
        
        mlflow.log_param(f"{agent_name}_input_sample", input_str)
        # mlflow.log_text(str(output_data), f"{agent_name}_output.json")
        
    except Exception as e:
        print(f"[Observability] Warning: Failed to log to MLflow: {e}")

if __name__ == "__main__":
    setup_observability()
    print("Observability setup complete.")
