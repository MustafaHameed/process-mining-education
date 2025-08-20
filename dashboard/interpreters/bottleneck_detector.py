import pandas as pd
import pm4py
from datetime import timedelta, datetime

def detect_bottlenecks(event_log):
    """
    Detect bottlenecks in the process.
    
    Args:
        event_log: PM4Py event log
        
    Returns:
        DataFrame with bottleneck analysis
    """
    # Add analysis metadata
    analysis_metadata = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analyst": "MustafaHameed"
    }
    
    # Extract activity durations
    activity_durations = {}
    waiting_times = {}
    
    for trace in event_log:
        case_activities = {}
        ordered_events = sorted(trace, key=lambda e: e["time:timestamp"])
        
        for i, event in enumerate(ordered_events):
            activity = event["concept:name"]
            timestamp = event["time:timestamp"]
            
            # Check if this is a completion event (last occurrence of this activity in the case)
            if i == len(ordered_events) - 1 or ordered_events[i+1]["concept:name"] != activity:
                if activity in case_activities:
                    # Calculate duration - time between first and last occurrence of the activity
                    duration = timestamp - case_activities[activity]
                    
                    if activity not in activity_durations:
                        activity_durations[activity] = []
                    
                    activity_durations[activity].append(duration.total_seconds())
                
                # Calculate waiting time to next activity
                if i < len(ordered_events) - 1:
                    next_activity = ordered_events[i+1]["concept:name"]
                    waiting_time = ordered_events[i+1]["time:timestamp"] - timestamp
                    
                    transition = f"{activity} → {next_activity}"
                    if transition not in waiting_times:
                        waiting_times[transition] = []
                    
                    waiting_times[transition].append(waiting_time.total_seconds())
            
            # Record first occurrence of each activity in the case
            if activity not in case_activities:
                case_activities[activity] = timestamp
    
    # Calculate average durations
    avg_durations = []
    for activity, durations in activity_durations.items():
        if durations:
            avg_duration = sum(durations) / len(durations)
            avg_durations.append({
                "activity": activity,
                "avg_duration_seconds": avg_duration,
                "avg_duration_formatted": format_duration(avg_duration),
                "count": len(durations)
            })
    
    # Calculate average waiting times
    avg_waiting = []
    for transition, times in waiting_times.items():
        if times:
            avg_time = sum(times) / len(times)
            avg_waiting.append({
                "transition": transition,
                "avg_waiting_seconds": avg_time,
                "avg_waiting_formatted": format_duration(avg_time),
                "count": len(times)
            })
    
    # Identify bottlenecks - activities with highest duration or transitions with highest waiting times
    bottlenecks = []
    
    # Activities with high processing time
    for item in sorted(avg_durations, key=lambda x: x["avg_duration_seconds"], reverse=True)[:5]:
        bottlenecks.append({
            "element": item["activity"],
            "type": "Activity",
            "metric": "Processing Time",
            "value_seconds": item["avg_duration_seconds"],
            "value_formatted": item["avg_duration_formatted"],
            "occurrences": item["count"]
        })
    
    # Transitions with high waiting time
    for item in sorted(avg_waiting, key=lambda x: x["avg_waiting_seconds"], reverse=True)[:5]:
        bottlenecks.append({
            "element": item["transition"],
            "type": "Transition",
            "metric": "Waiting Time",
            "value_seconds": item["avg_waiting_seconds"],
            "value_formatted": item["avg_waiting_formatted"],
            "occurrences": item["count"]
        })
    
    # Add analysis metadata to each row
    for item in bottlenecks:
        item["analysis_date"] = analysis_metadata["timestamp"]
        item["analyst"] = analysis_metadata["analyst"]
    
    return pd.DataFrame(bottlenecks)

def format_duration(seconds):
    """Format duration in seconds to a human-readable string"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    elif seconds < 86400:
        return f"{seconds/3600:.1f} hours"
    else:
        return f"{seconds/86400:.1f} days"