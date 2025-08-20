import streamlit as st
import pm4py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, datetime

def display_metrics_panel(event_log):
    """
    Display a panel with key process mining metrics.
    
    Args:
        event_log: PM4Py event log
    """
    # Calculate key metrics
    metrics = calculate_process_metrics(event_log)
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cases", metrics["total_cases"])
    col2.metric("Unique Activities", metrics["unique_activities"])
    col3.metric("Avg. Case Duration", f"{metrics['avg_case_duration']:.1f} days")
    col4.metric("Variants", metrics["variants"])
    
    # Analysis timestamp
    st.caption(f"Analysis performed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by MustafaHameed")
    
    # Display case duration distribution
    st.subheader("Case Duration Distribution")
    fig = px.histogram(
        metrics["case_durations_df"], 
        x="duration_days",
        nbins=20,
        labels={"duration_days": "Duration (days)"},
        title="Distribution of Case Durations"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Activity frequency
    st.subheader("Activity Frequency")
    fig2 = px.bar(
        metrics["activity_counts_df"].sort_values("frequency", ascending=False).head(10),
        x="activity",
        y="frequency",
        labels={"activity": "Activity", "frequency": "Frequency"},
        title="Top 10 Activities by Frequency"
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Throughput over time
    if "throughput_df" in metrics:
        st.subheader("Process Throughput Over Time")
        fig3 = px.line(
            metrics["throughput_df"],
            x="date",
            y="cases",
            labels={"date": "Date", "cases": "Number of Active Cases"},
            title="Case Throughput Over Time"
        )
        st.plotly_chart(fig3, use_container_width=True)

def calculate_process_metrics(event_log):
    """
    Calculate key process metrics from event log.
    
    Args:
        event_log: PM4Py event log
        
    Returns:
        Dictionary with metrics
    """
    metrics = {}
    
    # Basic metrics
    metrics["total_cases"] = len(event_log)
    
    # Unique activities
    activities = set()
    for trace in event_log:
        for event in trace:
            activities.add(event["concept:name"])
    metrics["unique_activities"] = len(activities)
    
    # Activity frequency
    activity_counts = {}
    for trace in event_log:
        for event in trace:
            activity = event["concept:name"]
            activity_counts[activity] = activity_counts.get(activity, 0) + 1
    
    metrics["activity_counts_df"] = pd.DataFrame([
        {"activity": activity, "frequency": count}
        for activity, count in activity_counts.items()
    ])
    
    # Case durations
    case_durations = []
    for trace in event_log:
        if len(trace) > 0:
            start_time = min(event["time:timestamp"] for event in trace)
            end_time = max(event["time:timestamp"] for event in trace)
            duration = end_time - start_time
            case_durations.append(duration.total_seconds() / (24 * 3600))  # Convert to days
    
    if case_durations:
        metrics["avg_case_duration"] = sum(case_durations) / len(case_durations)
        metrics["case_durations_df"] = pd.DataFrame({"duration_days": case_durations})
    else:
        metrics["avg_case_duration"] = 0
        metrics["case_durations_df"] = pd.DataFrame({"duration_days": [0]})
    
    # Variants
    variants = pm4py.get_variants(event_log)
    metrics["variants"] = len(variants)
    
    # Try to calculate throughput over time
    try:
        all_timestamps = []
        for trace in event_log:
            for event in trace:
                all_timestamps.append(event["time:timestamp"].date())
        
        if all_timestamps:
            date_range = pd.date_range(min(all_timestamps), max(all_timestamps), freq='D')
            case_starts = {}
            case_ends = {}
            
            for trace in event_log:
                case_id = trace.attributes["concept:name"]
                start_time = min(event["time:timestamp"].date() for event in trace)
                end_time = max(event["time:timestamp"].date() for event in trace)
                
                case_starts[case_id] = start_time
                case_ends[case_id] = end_time
            
            # Calculate active cases per day
            active_cases = []
            for date in date_range:
                date = date.date()
                count = sum(1 for case_id in case_starts 
                           if case_starts[case_id] <= date <= case_ends[case_id])
                active_cases.append({"date": date, "cases": count})
            
            metrics["throughput_df"] = pd.DataFrame(active_cases)
    except:
        # If throughput calculation fails, skip it
        pass
    
    return metrics