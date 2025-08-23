import streamlit as st
import pm4py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, datetime

def _safe_get(event, key):
    """Safely get an attribute from a PM4Py event or dict-like object."""
    try:
        # pm4py Event behaves like dict and has get
        if hasattr(event, 'get'):
            return event.get(key, None)
        if isinstance(event, dict):
            return event.get(key, None)
        # Fallback to mapping access
        return event[key]
    except Exception:
        return None

def display_metrics_panel(event_log):
    """
    Display a panel with key process mining metrics.
    
    Args:
        event_log: PM4Py event log or pandas DataFrame
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
        event_log: PM4Py event log or pandas DataFrame
        
    Returns:
        Dictionary with metrics
    """
    metrics = {}
    
    # Handle different event log formats
    if isinstance(event_log, pd.DataFrame):
        # If it's a DataFrame
        if 'case:concept:name' in event_log.columns and 'concept:name' in event_log.columns:
            # Basic metrics
            metrics["total_cases"] = event_log['case:concept:name'].nunique()
            metrics["unique_activities"] = event_log['concept:name'].nunique()
            
            # Activity frequency
            activity_counts = event_log['concept:name'].value_counts().reset_index()
            activity_counts.columns = ['activity', 'frequency']
            metrics["activity_counts_df"] = activity_counts
            
            # Case durations
            if 'time:timestamp' in event_log.columns:
                case_durations = []
                for case_id, case_df in event_log.groupby('case:concept:name'):
                    if len(case_df) > 0:
                        start_time = case_df['time:timestamp'].min()
                        end_time = case_df['time:timestamp'].max()
                        duration_days = (end_time - start_time).total_seconds() / (24 * 3600)
                        case_durations.append(duration_days)
                
                if case_durations:
                    metrics["avg_case_duration"] = sum(case_durations) / len(case_durations)
                    metrics["case_durations_df"] = pd.DataFrame({"duration_days": case_durations})
                else:
                    metrics["avg_case_duration"] = 0
                    metrics["case_durations_df"] = pd.DataFrame({"duration_days": [0]})
            else:
                metrics["avg_case_duration"] = 0
                metrics["case_durations_df"] = pd.DataFrame({"duration_days": [0]})
            
            # Variants - approximate from DataFrame
            try:
                # Group by case_id and get sequence of activities
                case_variants = {}
                for case_id, case_df in event_log.groupby('case:concept:name'):
                    # Sort by timestamp if available
                    if 'time:timestamp' in case_df.columns:
                        case_df = case_df.sort_values('time:timestamp')
                    
                    # Create variant string
                    variant = ','.join(case_df['concept:name'].tolist())
                    if variant not in case_variants:
                        case_variants[variant] = []
                    case_variants[variant].append(case_id)
                
                metrics["variants"] = len(case_variants)
            except:
                # If variants calculation fails, set to 0
                metrics["variants"] = 0
                
            # Try to calculate throughput over time
            try:
                if 'time:timestamp' in event_log.columns:
                    # Convert to datetime if needed
                    if not pd.api.types.is_datetime64_any_dtype(event_log['time:timestamp']):
                        event_log['time:timestamp'] = pd.to_datetime(event_log['time:timestamp'])
                    
                    # Extract dates
                    all_dates = event_log['time:timestamp'].dt.date.unique()
                    
                    if len(all_dates) > 0:
                        date_range = pd.date_range(min(all_dates), max(all_dates), freq='D')
                        
                        # Get case start and end dates
                        case_timeframes = {}
                        for case_id, case_df in event_log.groupby('case:concept:name'):
                            start_date = case_df['time:timestamp'].dt.date.min()
                            end_date = case_df['time:timestamp'].dt.date.max()
                            case_timeframes[case_id] = (start_date, end_date)
                        
                        # Calculate active cases per day
                        active_cases = []
                        for date in date_range:
                            date = date.date()
                            count = sum(1 for case_id, (start, end) in case_timeframes.items() 
                                      if start <= date <= end)
                            active_cases.append({"date": date, "cases": count})
                        
                        metrics["throughput_df"] = pd.DataFrame(active_cases)
            except Exception as e:
                # If throughput calculation fails, skip it
                pass
        else:
            # Not a properly formatted PM4Py DataFrame
            metrics["total_cases"] = 0
            metrics["unique_activities"] = 0
            metrics["avg_case_duration"] = 0
            metrics["variants"] = 0
            metrics["activity_counts_df"] = pd.DataFrame({"activity": ["No data"], "frequency": [0]})
            metrics["case_durations_df"] = pd.DataFrame({"duration_days": [0]})
    else:
        # Try to handle as PM4Py EventLog object
        try:
            # Basic metrics
            metrics["total_cases"] = len(event_log)
            
            # Extract activities safely
            activities = set()
            activity_counts = {}
            
            for trace in event_log:
                for event in trace:
                    activity = _safe_get(event, "concept:name")
                    if activity is not None and isinstance(activity, (str, int)):
                        activities.add(activity)
                        activity_counts[activity] = activity_counts.get(activity, 0) + 1
            
            metrics["unique_activities"] = len(activities)
            
            # Convert activity counts to DataFrame
            metrics["activity_counts_df"] = pd.DataFrame([
                {"activity": activity, "frequency": count}
                for activity, count in activity_counts.items()
            ])
            
            # Case durations - safely extract timestamps
            case_durations = []
            for trace in event_log:
                try:
                    if len(trace) > 0:
                        timestamps = []
                        for event in trace:
                            timestamp = _safe_get(event, "time:timestamp")
                            if timestamp is not None:
                                timestamps.append(timestamp)
                        if timestamps:
                            start_time = min(timestamps)
                            end_time = max(timestamps)
                            try:
                                duration = end_time - start_time
                                duration_days = duration.total_seconds() / (24 * 3600)
                                case_durations.append(duration_days)
                            except (Exception):
                                pass
                except Exception:
                    continue
            
            if case_durations:
                metrics["avg_case_duration"] = sum(case_durations) / len(case_durations)
                metrics["case_durations_df"] = pd.DataFrame({"duration_days": case_durations})
            else:
                metrics["avg_case_duration"] = 0
                metrics["case_durations_df"] = pd.DataFrame({"duration_days": [0]})
            
            # Variants - safely get variants
            try:
                variants = pm4py.get_variants(event_log)
                metrics["variants"] = len(variants)
            except:
                # If variants calculation fails, approximate from traces
                variant_set = set()
                for trace in event_log:
                    try:
                        variant = []
                        for event in trace:
                            activity = _safe_get(event, "concept:name")
                            if activity is not None:
                                variant.append(str(activity))
                        variant_str = ",".join(variant)
                        variant_set.add(variant_str)
                    except:
                        continue
                
                metrics["variants"] = len(variant_set)
            
            # Try to calculate throughput over time
            try:
                all_timestamps = []
                case_timeframes = {}
                
                for trace in event_log:
                    try:
                        if hasattr(trace, 'attributes') and "concept:name" in trace.attributes:
                            case_id = trace.attributes["concept:name"]
                        else:
                            continue
                        timestamps = []
                        for event in trace:
                            timestamp = _safe_get(event, "time:timestamp")
                            if timestamp is not None and hasattr(timestamp, 'date'):
                                date = timestamp.date()
                                timestamps.append(date)
                                all_timestamps.append(date)
                        if timestamps:
                            case_timeframes[case_id] = (min(timestamps), max(timestamps))
                    except:
                        continue
                
                if all_timestamps and case_timeframes:
                    date_range = pd.date_range(min(all_timestamps), max(all_timestamps), freq='D')
                    
                    # Calculate active cases per day
                    active_cases = []
                    for date in date_range:
                        date = date.date()
                        count = sum(1 for case_id, (start, end) in case_timeframes.items() 
                                  if start <= date <= end)
                        active_cases.append({"date": date, "cases": count})
                    
                    metrics["throughput_df"] = pd.DataFrame(active_cases)
            except:
                # If throughput calculation fails, skip it
                pass
                
        except Exception as e:
            # If all PM4Py processing fails, return empty metrics
            metrics["total_cases"] = 0
            metrics["unique_activities"] = 0
            metrics["avg_case_duration"] = 0
            metrics["variants"] = 0
            metrics["activity_counts_df"] = pd.DataFrame({"activity": ["No data"], "frequency": [0]})
            metrics["case_durations_df"] = pd.DataFrame({"duration_days": [0]})
    
    return metrics

# Deprecated: use dashboard.components.metrics_panel instead.
raise RuntimeError("Deprecated module. Use 'dashboard.components.metrics_panel'.")
