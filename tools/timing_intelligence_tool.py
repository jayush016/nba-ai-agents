"""
Timing Intelligence Tool - Provides optimal timing recommendations
Used by Agent 6 (Timing Optimizer)
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional


def query_timing_intelligence(data_type: str = "all") -> Dict:
    """
    Query timing intelligence data.
    
    Args:
        data_type: Type of data ('channel_timing', 'customer_behavior', 
                   'urgency', 'day_of_week', 'all')
        
    Returns:
        Timing intelligence dictionary
    """
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'timing_intelligence.json')
    
    try:
        with open(data_path, 'r') as f:
            timing_data = json.load(f)
        
        if data_type == "all":
            return timing_data
        elif data_type == "channel_timing":
            return {"channel_timing": timing_data.get('channel_timing', {})}
        elif data_type == "customer_behavior":
            return {"customer_behavior_patterns": timing_data.get('customer_behavior_patterns', {})}
        elif data_type == "urgency":
            return {"urgency_based_timing": timing_data.get('urgency_based_timing', {})}
        elif data_type == "day_of_week":
            return {"day_of_week_insights": timing_data.get('day_of_week_insights', {})}
        else:
            return {"error": f"Unknown data type: {data_type}"}
    
    except FileNotFoundError:
        return {"error": "Timing intelligence file not found"}


def get_optimal_send_time(channel: str, urgency: str = "medium", customer_scenario: str = None) -> Dict:
    """
    Get optimal send time for a channel and scenario.
    
    Args:
        channel: Communication channel ('email', 'sms', 'push', etc.)
        urgency: Urgency level ('low', 'medium', 'high', 'very_high')
        customer_scenario: Customer scenario type
        
    Returns:
        Optimal timing recommendation
    """
    timing_data = query_timing_intelligence()
    
    if "error" in timing_data:
        return {"error": "Could not load timing data"}
    
    # Handle urgency-based timing
    if urgency in ["very_high", "high"]:
        if urgency == "very_high":
            return {
                "recommended_timing": "immediate",
                "reasoning": "Very high urgency requires immediate action",
                "expected_delay_minutes": 0
            }
        elif urgency == "high":
            return {
                "recommended_timing": "within_1_hour",
                "reasoning": "High urgency requires fast action",
                "expected_delay_minutes": 30
            }
    
    # Get channel-specific timing
    channel_timing = timing_data.get('channel_timing', {}).get(channel.lower(), {})
    
    if not channel_timing:
        return {
            "recommended_timing": "default_business_hours",
            "reasoning": f"No specific timing data for channel: {channel}"
        }
    
    # Get current day of week
    now = datetime.now()
    is_weekend = now.weekday() >= 5  # Saturday = 5, Sunday = 6
    
    # Select timing based on weekday/weekend
    if is_weekend:
        best_times = channel_timing.get('best_send_times_weekend', {})
    else:
        best_times = channel_timing.get('best_send_times_weekday', {})
    
    # Find best time slot
    if best_times:
        # Select the slot with highest conversion rate
        best_slot = max(best_times.items(), key=lambda x: x[1].get('conversion_rate', 0))
        slot_name, slot_data = best_slot
        
        return {
            "recommended_timing": slot_name,
            "time_range": f"{slot_data.get('start')} - {slot_data.get('end')}",
            "expected_conversion_rate": slot_data.get('conversion_rate'),
            "reasoning": f"Best {channel} time on {'weekend' if is_weekend else 'weekday'}",
            "is_weekend": is_weekend
        }
    
    return {
        "recommended_timing": "default",
        "reasoning": "Using default timing"
    }


def get_followup_timing(customer_scenario: str, touch_number: int = 1) -> Dict:
    """
    Get timing for follow-up messages based on scenario.
    
    Args:
        customer_scenario: Scenario type ('cart_abandoners', 'browsing_no_cart', etc.)
        touch_number: Which touchpoint (1st, 2nd, 3rd)
        
    Returns:
        Follow-up timing recommendation
    """
    timing_data = query_timing_intelligence()
    behavior_patterns = timing_data.get('customer_behavior_patterns', {})
    
    scenario_data = behavior_patterns.get(customer_scenario, {})
    
    if not scenario_data:
        return {"error": f"Unknown scenario: {customer_scenario}"}
    
    # Map touch number to timing key
    timing_keys = {
        1: "optimal_followup_timing",
        2: "second_touch_timing",
        3: "final_touch_timing"
    }
    
    timing_key = timing_keys.get(touch_number, "optimal_followup_timing")
    timing = scenario_data.get(timing_key, "24_hours")
    
    return {
        "touch_number": touch_number,
        "recommended_delay": timing,
        "scenario": customer_scenario,
        "reasoning": f"Optimal timing for touch {touch_number} in {customer_scenario} scenario"
    }


def get_day_of_week_insights(channel: str = "email") -> Dict:
    """
    Get performance insights by day of week.
    
    Args:
        channel: Communication channel
        
    Returns:
        Day of week insights
    """
    timing_data = query_timing_intelligence()
    dow_insights = timing_data.get('day_of_week_insights', {})
    
    if not dow_insights:
        return {"error": "No day of week insights available"}
    
    # Rank days by performance for the channel
    performance_key = f"{channel}_performance"
    
    day_rankings = []
    for day, data in dow_insights.items():
        if performance_key in data:
            day_rankings.append({
                "day": day,
                "performance": data[performance_key],
                "message_tone": data.get('best_message_tone')
            })
    
    # Sort by performance
    day_rankings.sort(key=lambda x: x['performance'], reverse=True)
    
    return {
        "channel": channel,
        "best_days": day_rankings[:3],
        "worst_days": day_rankings[-2:],
        "all_days": day_rankings
    }


def calculate_send_time(
    channel: str,
    urgency: str = "medium",
    customer_scenario: str = None,
    from_time: str = None
) -> str:
    """
    Calculate specific datetime to send action.
    
    Args:
        channel: Communication channel
        urgency: Urgency level
        customer_scenario: Customer scenario
        from_time: Starting time as ISO string (default: now)
        
    Returns:
        Calculated send datetime as ISO string
    """
    # Parse from_time string to datetime
    if from_time is None:
        from_time_dt = datetime.now()
    else:
        try:
            from_time_dt = datetime.fromisoformat(from_time)
        except (ValueError, TypeError):
            from_time_dt = datetime.now()
    
    timing_rec = get_optimal_send_time(channel, urgency, customer_scenario)
    
    # Handle immediate
    if timing_rec.get('recommended_timing') == 'immediate':
        return from_time_dt.isoformat()
    
    # Handle within hour
    if timing_rec.get('recommended_timing') == 'within_1_hour':
        result = from_time_dt + timedelta(minutes=30)
        return result.isoformat()
    
    # Parse time range
    time_range = timing_rec.get('time_range', '')
    if '-' in time_range:
        start_time_str = time_range.split('-')[0].strip()
        try:
            # Parse start time (e.g., "19:00")
            hour, minute = map(int, start_time_str.split(':'))
            
            # Create datetime for today at that time
            send_time = from_time_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If time has passed today, schedule for tomorrow
            if send_time < from_time_dt:
                send_time += timedelta(days=1)
            
            return send_time.isoformat()
        except:
            pass
    
    # Default: schedule for next business hours
    result = from_time_dt + timedelta(hours=2)
    return result.isoformat()
