import pandas as pd
import pm4py
from collections import defaultdict
from datetime import datetime

def analyze_patterns(event_log):
    """
    Analyze process patterns in the event log.
    
    Args:
        event_log: PM4Py event log or pandas DataFrame
        
    Returns:
        Dictionary with pattern analysis results
    """
    results = {}
    
    # Add metadata
    results["analysis_metadata"] = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analyst": "MustafaHameed"
    }
    
    # Handle different event log formats
    if isinstance(event_log, pd.DataFrame):
        # DataFrame handling
        if 'case:concept:name' in event_log.columns and 'concept:name' in event_log.columns:
            # Analyze variants from DataFrame
            variants = {}
            
            # Sort by timestamp if available
            if 'time:timestamp' in event_log.columns:
                event_log_sorted = event_log.sort_values(['case:concept:name', 'time:timestamp'])
            else:
                event_log_sorted = event_log
            
            # Group by case and create variants
            for case_id, case_df in event_log_sorted.groupby('case:concept:name'):
                variant = ','.join(case_df['concept:name'].tolist())
                if variant not in variants:
                    variants[variant] = []
                variants[variant].append(case_id)
        else:
            # Not properly formatted
            variants = {}
    else:
        # Try PM4Py EventLog format
        try:
            variants = pm4py.get_variants(event_log)
        except:
            # Fallback: create variants manually
            variants = {}
            
            for trace in event_log:
                try:
                    # Extract case ID
                    if hasattr(trace, 'attributes') and "concept:name" in trace.attributes:
                        case_id = trace.attributes["concept:name"]
                    else:
                        case_id = str(id(trace))  # Use object ID if case ID not available
                    
                    # Create variant from activities
                    activities = []
                    for event in trace:
                        try:
                            if isinstance(event, dict):
                                activity = event.get("concept:name")
                            else:
                                activity = event["concept:name"]
                            
                            if activity is not None:
                                activities.append(str(activity))
                        except (TypeError, KeyError, AttributeError):
                            continue
                    
                    variant = ','.join(activities)
                    if variant not in variants:
                        variants[variant] = []
                    variants[variant].append(case_id)
                except:
                    # Skip any trace that causes errors
                    continue
    
    # Create variant distribution
    variant_distribution = []
    other_count = 0
    other_cases = 0
    
    # Sort variants by frequency
    sorted_variants = sorted(variants.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Take top 5 variants for visualization
    for i, (variant, traces) in enumerate(sorted_variants):
        if i < 5:
            variant_name = f"Variant {i+1}"
            # Convert tuple variant to string if needed
            variant_str = ",".join(variant) if isinstance(variant, tuple) else variant
            variant_distribution.append({
                "variant": variant_name,
                "count": len(traces),
                "activities": variant_str
            })
        else:
            other_count += len(traces)
            other_cases += 1
    
    # Add "Other" category if there are more variants
    if other_count > 0:
        variant_distribution.append({
            "variant": f"Other ({other_cases} variants)",
            "count": other_count,
            "activities": "Various"
        })
    
    results["variant_distribution"] = pd.DataFrame(variant_distribution) if variant_distribution else pd.DataFrame({
        "variant": ["No variants found"],
        "count": [0],
        "activities": ["None"]
    })
    
    # Analyze common sequences (bigrams)
    sequence_counts = defaultdict(int)
    
    # Handle different event log formats
    if isinstance(event_log, pd.DataFrame):
        if 'case:concept:name' in event_log.columns and 'concept:name' in event_log.columns:
            # Sort by timestamp if available
            if 'time:timestamp' in event_log.columns:
                event_log_sorted = event_log.sort_values(['case:concept:name', 'time:timestamp'])
            else:
                event_log_sorted = event_log
            
            # Process each case
            for case_id, case_df in event_log_sorted.groupby('case:concept:name'):
                activities = case_df['concept:name'].tolist()
                
                # Count sequences (bigrams)
                for i in range(len(activities) - 1):
                    sequence = f"{activities[i]} → {activities[i+1]}"
                    sequence_counts[sequence] += 1
    else:
        # Process PM4Py EventLog
        for trace in event_log:
            # Extract activity names safely
            activities = []
            
            for event in trace:
                try:
                    if isinstance(event, dict):
                        activity = event.get("concept:name")
                    else:
                        activity = event["concept:name"]
                    
                    if activity is not None:
                        activities.append(str(activity))
                except (TypeError, KeyError, AttributeError):
                    continue
            
            # Count sequences (bigrams)
            for i in range(len(activities) - 1):
                sequence = f"{activities[i]} → {activities[i+1]}"
                sequence_counts[sequence] += 1
    
    # Convert to DataFrame
    common_sequences = []
    for sequence, count in sorted(sequence_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        common_sequences.append({
            "sequence": sequence,
            "frequency": count
        })
    
    # Ensure we have at least one row
    if not common_sequences:
        common_sequences.append({
            "sequence": "No sequences found",
            "frequency": 0
        })
    
    results["common_sequences"] = pd.DataFrame(common_sequences)
    
    # Analyze rework (repeated activities within a case)
    rework_counts = defaultdict(int)
    
    # Handle different event log formats
    if isinstance(event_log, pd.DataFrame):
        if 'case:concept:name' in event_log.columns and 'concept:name' in event_log.columns:
            # Process each case
            for case_id, case_df in event_log.groupby('case:concept:name'):
                activities = case_df['concept:name'].tolist()
                
                # Count rework instances
                seen_activities = set()
                for activity in activities:
                    if activity in seen_activities:
                        rework_counts[activity] += 1
                    seen_activities.add(activity)
    else:
        # Process PM4Py EventLog
        for trace in event_log:
            # Extract activity names safely
            activities = []
            
            for event in trace:
                try:
                    if isinstance(event, dict):
                        activity = event.get("concept:name")
                    else:
                        activity = event["concept:name"]
                    
                    if activity is not None:
                        activities.append(str(activity))
                except (TypeError, KeyError, AttributeError):
                    continue
            
            # Count rework instances
            seen_activities = set()
            for activity in activities:
                if activity in seen_activities:
                    rework_counts[activity] += 1
                seen_activities.add(activity)
    
    # Convert to DataFrame
    rework_patterns = []
    for activity, rework_count in sorted(rework_counts.items(), key=lambda x: x[1], reverse=True):
        if rework_count > 0:
            rework_patterns.append({
                "activity": activity,
                "rework_count": rework_count
            })
    
    # If rework_patterns is empty, add a placeholder row to avoid plotting errors
    if not rework_patterns:
        rework_patterns.append({
            "activity": "No Rework",
            "rework_count": 0
        })
    
    results["rework_patterns"] = pd.DataFrame(rework_patterns)
    
    # Detect potential anomalies (very rare variants)
    anomalies = []
    
    # Calculate median trace length
    trace_lengths = []
    
    # Handle different event log formats
    if isinstance(event_log, pd.DataFrame):
        if 'case:concept:name' in event_log.columns:
            # Get case lengths
            case_lengths = event_log.groupby('case:concept:name').size()
            trace_lengths = case_lengths.tolist()
    else:
        # Process PM4Py EventLog
        for trace in event_log:
            try:
                # Count events in trace
                event_count = 0
                for event in trace:
                    event_count += 1
                trace_lengths.append(event_count)
            except:
                # Skip any trace that causes errors
                continue
    
    # Calculate median length if we have traces
    if trace_lengths:
        median_length = median(trace_lengths)
        
        # Find anomalies
        if isinstance(event_log, pd.DataFrame):
            if 'case:concept:name' in event_log.columns:
                # Find rare variants
                for variant, cases in variants.items():
                    if len(cases) == 1:
                        variant_length = len(variant.split(","))
                        if abs(variant_length - median_length) > 3:
                            anomalies.append({
                                "case_id": cases[0],
                                "variant": variant,
                                "length": variant_length,
                                "reason": "Unusual length"
                            })
        else:
            # Process PM4Py EventLog variants
            for variant, traces in variants.items():
                if len(traces) == 1:
                    # Get variant length
                    if isinstance(variant, tuple):
                        variant_length = len(variant)
                    else:
                        variant_length = len(variant.split(","))
                    
                    if abs(variant_length - median_length) > 3:
                        try:
                            # Get case ID
                            if hasattr(traces[0], 'attributes') and "concept:name" in traces[0].attributes:
                                case_id = traces[0].attributes["concept:name"]
                            else:
                                case_id = str(id(traces[0]))
                            
                            variant_str = ",".join(variant) if isinstance(variant, tuple) else variant
                            anomalies.append({
                                "case_id": case_id,
                                "variant": variant_str,
                                "length": variant_length,
                                "reason": "Unusual length"
                            })
                        except:
                            # Skip any trace that causes errors
                            continue
    
    # If no anomalies found, add placeholder
    if not anomalies:
        anomalies.append({
            "case_id": "None",
            "variant": "None",
            "length": 0,
            "reason": "No anomalies found"
        })
    
    results["anomalies"] = pd.DataFrame(anomalies)
    
    return results

def median(values):
    """Calculate the median of a list of values"""
    if not values:
        return 0
        
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 0:
        return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
    else:
        return sorted_values[n//2]

# Deprecated: use dashboard.interpreters.pattern_analyzer instead.
raise RuntimeError("Deprecated module. Use 'dashboard.interpreters.pattern_analyzer'.")
