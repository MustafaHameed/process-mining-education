import pandas as pd
import pm4py
from collections import defaultdict
from datetime import datetime

def analyze_patterns(event_log):
    """
    Analyze process patterns in the event log.
    
    Args:
        event_log: PM4Py event log
        
    Returns:
        Dictionary with pattern analysis results
    """
    results = {}
    
    # Add metadata
    results["analysis_metadata"] = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analyst": "MustafaHameed"
    }
    
    # Analyze variants
    variants = pm4py.get_variants(event_log)
    
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
            variant_distribution.append({
                "variant": variant_name,
                "count": len(traces),
                "activities": variant
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
    
    results["variant_distribution"] = pd.DataFrame(variant_distribution)
    
    # Analyze common sequences (bigrams)
    sequence_counts = defaultdict(int)
    
    for trace in event_log:
        activities = [event["concept:name"] for event in trace]
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
    
    results["common_sequences"] = pd.DataFrame(common_sequences)
    
    # Analyze rework (repeated activities within a case)
    rework_counts = defaultdict(int)
    
    for trace in event_log:
        activities = [event["concept:name"] for event in trace]
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
    
    results["rework_patterns"] = pd.DataFrame(rework_patterns)
    
    # Detect potential anomalies (very rare variants)
    anomalies = []
    median_length = median([len(trace) for trace in event_log])
    
    for variant, traces in variants.items():
        # Consider it anomalous if it's rare and unusually long or short
        if len(traces) == 1 and abs(len(variant.split(",")) - median_length) > 3:
            case_id = traces[0].attributes["concept:name"]
            anomalies.append({
                "case_id": case_id,
                "variant": variant,
                "length": len(variant.split(",")),
                "reason": "Unusual length"
            })
    
    results["anomalies"] = pd.DataFrame(anomalies)
    
    return results

def median(values):
    """Calculate the median of a list of values"""
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 0:
        return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
    else:
        return sorted_values[n//2]