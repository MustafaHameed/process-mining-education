import pandas as pd
import pm4py
from datetime import timedelta, datetime

def detect_bottlenecks(event_log):
    """
    Detect bottlenecks in the process.
    
    Args:
        event_log: PM4Py event log or pandas DataFrame
        
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
    
    # Handle different event log formats
    if isinstance(event_log, pd.DataFrame):
        if 'case:concept:name' in event_log.columns and 'concept:name' in event_log.columns and 'time:timestamp' in event_log.columns:
            # Make sure timestamp is datetime
            if not pd.api.types.is_datetime64_any_dtype(event_log['time:timestamp']):
                try:
                    event_log['time:timestamp'] = pd.to_datetime(event_log['time:timestamp'])
                except:
                    # Return empty results if we can't process timestamps
                    return pd.DataFrame({
                        "element": ["No bottlenecks found"],
                        "type": ["None"],
                        "metric": ["None"],
                        "value_seconds": [0],
                        "value_formatted": ["0 seconds"],
                        "occurrences": [0],
                        "analysis_date": [analysis_metadata["timestamp"]],
                        "analyst": [analysis_metadata["analyst"]]
                    })
            
            # Process each case
            for case_id, case_df in event_log.groupby('case:concept:name'):
                # Sort by timestamp
                case_df = case_df.sort_values('time:timestamp')
                
                # Track activities in the case
                case_activities = {}
                
                # Process events
                for i, (_, event) in enumerate(case_df.iterrows()):
                    activity = event['concept:name']
                    timestamp = event['time:timestamp']
                    
                    # Check if this is a completion event (last occurrence of activity in case)
                    if i == len(case_df) - 1 or case_df.iloc[i+1]['concept:name'] != activity:
                        if activity in case_activities:
                            # Calculate duration
                            duration = timestamp - case_activities[activity]
                            
                            if activity not in activity_durations:
                                activity_durations[activity] = []
                            
                            activity_durations[activity].append(duration.total_seconds())
                        
                        # Calculate waiting time to next activity
                        if i < len(case_df) - 1:
                            next_activity = case_df.iloc[i+1]['concept:name']
                            waiting_time = case_df.iloc[i+1]['time:timestamp'] - timestamp
                            
                            transition = f"{activity} → {next_activity}"
                            if transition not in waiting_times:
                                waiting_times[transition] = []
                            
                            waiting_times[transition].append(waiting_time.total_seconds())
                    
                    # Record first occurrence of each activity in the case
                    if activity not in case_activities:
                        case_activities[activity] = timestamp
        else:
            # Not properly formatted DataFrame
            return pd.DataFrame({
                "element": ["Missing required columns"],
                "type": ["Error"],
                "metric": ["None"],
                "value_seconds": [0],
                "value_formatted": ["0 seconds"],
                "occurrences": [0],
                "analysis_date": [analysis_metadata["timestamp"]],
                "analyst": [analysis_metadata["analyst"]]
            })
    else:
        # Try PM4Py EventLog format
        try:
            for trace in event_log:
                # Extract events with timestamps
                ordered_events = []
                
                for event in trace:
                    try:
                        # Safe access to event attributes
                        if isinstance(event, dict):
                            activity = event.get("concept:name")
                            timestamp = event.get("time:timestamp")
                        else:
                            activity = event["concept:name"]
                            timestamp = event["time:timestamp"]
                        
                        if activity is not None and timestamp is not None:
                            ordered_events.append((activity, timestamp))
                    except (TypeError, KeyError, AttributeError):
                        continue
                
                # Sort events by timestamp
                ordered_events.sort(key=lambda x: x[1])
                
                # Track activities in the case
                case_activities = {}
                
                # Process events
                for i, (activity, timestamp) in enumerate(ordered_events):
                    # Check if this is a completion event
                    if i == len(ordered_events) - 1 or ordered_events[i+1][0] != activity:
                        if activity in case_activities:
                            # Calculate duration
                            try:
                                duration = timestamp - case_activities[activity]
                                duration_seconds = duration.total_seconds()
                                
                                if activity not in activity_durations:
                                    activity_durations[activity] = []
                                
                                activity_durations[activity].append(duration_seconds)
                            except (TypeError, AttributeError):
                                # Skip if we can't calculate duration
                                pass
                        
                        # Calculate waiting time to next activity
                        if i < len(ordered_events) - 1:
                            next_activity, next_timestamp = ordered_events[i+1]
                            try:
                                waiting_time = next_timestamp - timestamp
                                waiting_seconds = waiting_time.total_seconds()
                                
                                transition = f"{activity} → {next_activity}"
                                if transition not in waiting_times:
                                    waiting_times[transition] = []
                                
                                waiting_times[transition].append(waiting_seconds)
                            except (TypeError, AttributeError):
                                # Skip if we can't calculate waiting time
                                pass
                    
                    # Record first occurrence of each activity in the case
                    if activity not in case_activities:
                        case_activities[activity] = timestamp
        except Exception as e:
            # Return empty results if we can't process the event log
            return pd.DataFrame({
                "element": [f"Error: {str(e)}"],
                "type": ["Error"],
                "metric": ["None"],
                "value_seconds": [0],
                "value_formatted": ["0 seconds"],
                "occurrences": [0],
                "analysis_date": [analysis_metadata["timestamp"]],
                "analyst": [analysis_metadata["analyst"]]
            })
    
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
    
    # If no bottlenecks found, add a placeholder
    if not bottlenecks:
        bottlenecks.append({
            "element": "No bottlenecks found",
            "type": "None",
            "metric": "None",
            "value_seconds": 0,
            "value_formatted": "0 seconds",
            "occurrences": 0
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
