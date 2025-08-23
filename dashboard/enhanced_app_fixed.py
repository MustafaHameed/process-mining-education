import streamlit as st
import pandas as pd
import pm4py
import plotly.graph_objects as go
import networkx as nx
from pathlib import Path
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import from the main module
sys.path.append(str(Path(__file__).parent.parent))

# Import data preprocessing
from data_preprocessing import EPMDataProcessor

# Import dashboard components (relative imports)
from components.process_map import generate_process_map
from components.metrics_panel import display_metrics_panel
from components.analysis_panel import display_analysis_panel

# Import interpreters (relative imports)
from interpreters.pattern_analyzer import analyze_patterns
from interpreters.bottleneck_detector import detect_bottlenecks
from interpreters.conformance_analyzer import analyze_conformance

# Dashboard metadata
LAST_UPDATED = "2025-08-22 16:30:00"
AUTHOR = "MustafaHameed"

st.set_page_config(
    page_title="Process Mining Educational Dashboard - Enhanced",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for styling
st.markdown("""
<style>
    .enhanced-header {
        color: #2196F3;
        border-bottom: 2px solid #2196F3;
        padding-bottom: 10px;
    }
    .port-info {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #2196F3;
    }
    .dashboard-footer {
        margin-top: 20px;
        padding-top: 10px;
        border-top: 1px solid #e6e6e6;
        color: #666;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown("<h1 class='enhanced-header'>Process Mining Educational Dashboard - Enhanced Version</h1>", unsafe_allow_html=True)
    st.caption(f"Last updated: {LAST_UPDATED} | Author: {AUTHOR}")
    st.markdown("<div class='port-info'>Running on port 8502</div>", unsafe_allow_html=True)
    
    # Create a 2-column layout: sidebar for config, main area for content
    with st.sidebar:
        st.header("Configuration")
        
        # Dataset selection tabs
        dataset_tab1, dataset_tab2 = st.tabs(["EPM Dataset", "Custom Upload"])
        
        with dataset_tab1:
            # Option to load built-in EPM dataset
            use_builtin_dataset = st.checkbox("Use built-in EPM Dataset", value=True)
            
            if use_builtin_dataset:
                # Dataset path configuration
                dataset_path = "EPM Dataset 2"
                if os.path.exists(dataset_path):
                    st.success(f"EPM Dataset found at {dataset_path}")
                    
                    # Configure session filtering
                    st.subheader("Session Configuration")
                    include_all_sessions = st.checkbox("Include all sessions", value=True)
                    if not include_all_sessions:
                        available_sessions = ["Session 1", "Session 2", "Session 3", "Session 4", "Session 5", "Session 6"]
                        selected_sessions = st.multiselect(
                            "Select sessions to analyze", 
                            available_sessions,
                            default=["Session 1"]
                        )
                    else:
                        selected_sessions = ["Session 1", "Session 2", "Session 3", "Session 4", "Session 5", "Session 6"]
                    
                    # Quality filtering options
                    st.subheader("Filtering Options")
                    min_events_per_case = st.slider(
                        "Minimum events per case", 
                        min_value=1, 
                        max_value=20, 
                        value=5,
                        help="Filter out cases with fewer events than this threshold"
                    )
                    
                    exclude_blank_other = st.checkbox("Exclude 'Blank' and 'Other' activities", value=True)
                    exclude_activities = ["Blank", "Other"] if exclude_blank_other else []
                    
                    # Process the dataset when button is clicked
                    if st.button("Process EPM Dataset", key="process_epm"):
                        with st.spinner("Loading and processing EPM dataset..."):
                            # Create data processor
                            processor = EPMDataProcessor(dataset_path)
                            
                            # Load only the selected sessions
                            processor.sessions = selected_sessions
                            
                            # Load raw data
                            raw_data = processor.load_all_data()
                            
                            if raw_data.empty:
                                st.error("Failed to load dataset. Please check the dataset path.")
                            else:
                                # Create event log
                                event_log = processor.create_event_log(raw_data)
                                
                                # Extract session information
                                session_info_dict = {}
                                
                                # Create mapping of case_id to session
                                for _, row in raw_data.iterrows():
                                    if 'case_id' in row and 'session' in row:
                                        case_id = row['case_id']
                                        session = row['session']
                                        session_info_dict[case_id] = f"Session {session}"
                                
                                # PM4Py might handle event logs differently depending on version
                                # We'll adapt to multiple formats
                                
                                # Check if event_log is a DataFrame
                                if isinstance(event_log, pd.DataFrame):
                                    if 'case:concept:name' in event_log.columns:
                                        # Add session info as a column
                                        event_log['session_info'] = event_log['case:concept:name'].map(
                                            lambda x: session_info_dict.get(x, "Unknown"))
                                else:
                                    # Try to handle as PM4Py EventLog object 
                                    try:
                                        # Add session info to trace attributes if possible
                                        for trace in event_log:
                                            try:
                                                if hasattr(trace, 'attributes'):
                                                    case_id = trace.attributes["concept:name"]
                                                    if case_id in session_info_dict:
                                                        trace.attributes["session_info"] = session_info_dict[case_id]
                                                        
                                                        # Add to events as well
                                                        for event in trace:
                                                            event["session_info"] = session_info_dict[case_id]
                                            except Exception as e:
                                                st.warning(f"Could not process trace: {e}")
                                                continue
                                    except Exception as e:
                                        st.warning(f"Event log format is not as expected: {e}")
                                
                                # Apply quality filters
                                quality_log = processor.filter_by_criteria(
                                    event_log, 
                                    min_events_per_case=min_events_per_case,
                                    exclude_activities=exclude_activities
                                )
                                
                                # Verify sessions are preserved (adapt to different event log formats)
                                preserved_sessions = set()
                                
                                # Check if quality_log is a DataFrame
                                if isinstance(quality_log, pd.DataFrame):
                                    if 'session_info' in quality_log.columns:
                                        preserved_sessions = set(quality_log['session_info'].unique())
                                    elif 'session' in quality_log.columns:
                                        preserved_sessions = set(f"Session {s}" for s in quality_log['session'].unique())
                                else:
                                    # Try to handle as PM4Py EventLog object
                                    try:
                                        for trace in quality_log:
                                            try:
                                                if hasattr(trace, 'attributes') and "session_info" in trace.attributes:
                                                    preserved_sessions.add(trace.attributes["session_info"])
                                            except:
                                                continue
                                    except:
                                        # If we can't determine preserved sessions, just continue
                                        pass
                                
                                if preserved_sessions and len(preserved_sessions) < len(selected_sessions):
                                    st.warning(f"Some sessions were lost during filtering. Keeping {len(preserved_sessions)} out of {len(selected_sessions)} sessions.")
                                
                                # Process the log for dashboard display
                                display_dashboard(quality_log, raw_data)
                else:
                    st.error(f"EPM Dataset not found at {dataset_path}. Please check the path.")
        
        with dataset_tab2:
            # Allow custom file upload
            uploaded_file = st.file_uploader("Upload Event Log (CSV or XES)", type=["csv", "xes"])
            
            if uploaded_file:
                # Load the event log
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                    col1, col2, col3 = st.columns(3)
                    case_id_col = col1.selectbox("Case ID Column", df.columns.tolist())
                    activity_col = col2.selectbox("Activity Column", df.columns.tolist())
                    timestamp_col = col3.selectbox("Timestamp Column", df.columns.tolist())
                    
                    if st.button("Process Event Log", key="process_csv"):
                        # Convert to event log
                        event_log = pm4py.format_dataframe(
                            df, 
                            case_id=case_id_col, 
                            activity_key=activity_col, 
                            timestamp_key=timestamp_col
                        )
                        display_dashboard(event_log, df)
                else:
                    # XES file
                    if st.button("Process Event Log", key="process_xes"):
                        event_log = pm4py.read_xes(uploaded_file)
                        display_dashboard(event_log, None)
        
        # Educational materials section
        st.header("Educational Resources")
        if st.checkbox("Show Process Mining Concepts"):
            st.markdown("""
            - **Process Discovery**: Extracting process models from event logs
            - **Conformance Checking**: Comparing actual vs. expected processes
            - **Process Enhancement**: Improving processes based on data
            - **Social Network Analysis**: Analyzing organizational perspectives
            """)
            
        st.divider()
        st.info(f"Current session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def display_dashboard(event_log, raw_data=None):
    # Display dataset summary first
    st.header("Dataset Summary")
    
    # Basic statistics - handle different event log formats
    try:
        if isinstance(event_log, pd.DataFrame):
            num_cases = event_log['case:concept:name'].nunique() if 'case:concept:name' in event_log.columns else 0
            num_events = len(event_log)
            num_activities = event_log['concept:name'].nunique() if 'concept:name' in event_log.columns else 0
        else:
            # Try to handle as PM4Py EventLog object
            num_cases = len(event_log)
            num_events = sum(len(trace) for trace in event_log)
            
            # Extract activities from events
            activities = set()
            for trace in event_log:
                for event in trace:
                    if 'concept:name' in event:
                        activities.add(event['concept:name'])
            num_activities = len(activities)
    except Exception as e:
        st.error(f"Error calculating statistics: {str(e)}")
        num_cases = 0
        num_events = 0
        num_activities = 0
    
    # Display metrics in columns
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cases", f"{num_cases:,}")
    col2.metric("Total Events", f"{num_events:,}")
    col3.metric("Unique Activities", num_activities)
    
    # If we have raw data, display session information
    if raw_data is not None:
        # Display sessions information
        sessions_info = raw_data.groupby('session')['student_id'].nunique()
        
        st.subheader("Session Breakdown")
        
        # Prepare data for bar chart
        sessions = sessions_info.index.tolist()
        student_counts = sessions_info.values.tolist()
        
        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=sessions, 
                y=student_counts,
                text=student_counts,
                textposition='auto',
                marker_color='royalblue'
            )
        ])
        fig.update_layout(
            title="Number of Students per Session",
            xaxis_title="Session",
            yaxis_title="Number of Students",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Success message
    st.success(f"Dataset successfully loaded with {num_cases} cases containing {num_events:,} events.")
    
    # Create tabs for different views in the main panel
    tab1, tab2, tab3, tab4 = st.tabs(["Process Map", "Performance Metrics", "Patterns & Insights", "Conformance"])
    
    with tab1:
        st.header("Process Discovery Visualization")
        try:
            process_map_fig = generate_process_map(event_log)
            st.plotly_chart(process_map_fig, use_container_width=True)
            
            st.subheader("Interpretation")
            st.markdown("""
            The process map shows the flow of activities in your process:
            - **Nodes** represent activities
            - **Edges** represent transitions between activities
            - **Edge thickness** indicates frequency of the path
            - **Node color intensity** indicates activity frequency
            
            Look for unexpected paths, loops, and parallel activities.
            """)
        except Exception as e:
            st.error(f"Error generating process map: {str(e)}")
            st.info("Please try adjusting your filtering parameters or selecting different sessions.")
    
    with tab2:
        st.header("Performance Metrics")
        try:
            display_metrics_panel(event_log)
            
            # Bottleneck analysis
            bottlenecks = detect_bottlenecks(event_log)
            st.subheader("Bottleneck Analysis")
            st.dataframe(bottlenecks)
            
            st.subheader("Interpretation")
            st.markdown("""
            Key performance indicators help identify:
            - **Process efficiency**: How quickly cases move through the process
            - **Bottlenecks**: Activities with long waiting or processing times
            - **Variations**: How consistent the process is across different cases
            """)
        except Exception as e:
            st.error(f"Error generating performance metrics: {str(e)}")
            st.info("Please try adjusting your filtering parameters or selecting different sessions.")
    
    with tab3:
        st.header("Process Patterns & Insights")
        try:
            patterns = analyze_patterns(event_log)
            display_analysis_panel(patterns)
            
            st.subheader("Interpretation")
            st.markdown("""
            Process patterns reveal:
            - **Common sequences**: Frequently occurring activity patterns
            - **Variants**: Different ways the process is executed
            - **Anomalies**: Unusual process executions that may need investigation
            - **Rework**: Activities that repeat within the same case
            """)
        except Exception as e:
            st.error(f"Error analyzing patterns: {str(e)}")
            st.info("Please try adjusting your filtering parameters or selecting different sessions.")
    
    with tab4:
        st.header("Conformance Checking")
        st.info("Upload a reference model (BPMN or Petri Net) to perform conformance checking")
        ref_model = st.file_uploader("Upload reference model", type=["pnml", "bpmn"])
        
        if ref_model:
            try:
                conformance_results = analyze_conformance(event_log, ref_model)
                st.json(conformance_results)
                
                st.subheader("Interpretation")
                st.markdown("""
                Conformance checking helps understand:
                - **Fitness**: How well the event log can be replayed on the model
                - **Precision**: Whether the model allows for behavior not seen in the log
                - **Generalization**: How well the model generalizes to unseen behavior
                - **Simplicity**: How simple and understandable the model is
                """)
            except Exception as e:
                st.error(f"Error in conformance checking: {str(e)}")
    
    # Additional analysis sections in the main panel (outside of tabs)
    st.header("Activity Frequency Analysis")
    
    # Calculate activity frequencies - handle different event log formats
    activity_counts = {}
    try:
        if isinstance(event_log, pd.DataFrame):
            if 'concept:name' in event_log.columns:
                activity_counts = event_log['concept:name'].value_counts().to_dict()
        else:
            # Try to handle as PM4Py EventLog object
            for trace in event_log:
                for event in trace:
                    if 'concept:name' in event:
                        activity = event["concept:name"]
                        activity_counts[activity] = activity_counts.get(activity, 0) + 1
    except Exception as e:
        st.error(f"Error calculating activity frequencies: {str(e)}")
    
    # Sort by frequency
    sorted_activities = sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)
    
    if sorted_activities:
        # Display as horizontal bar chart
        fig = go.Figure(data=[
            go.Bar(
                y=[a[0] for a in sorted_activities[:15]],  # Top 15 activities
                x=[a[1] for a in sorted_activities[:15]],
                orientation='h',
                marker_color='lightblue'
            )
        ])
        fig.update_layout(
            title="Top 15 Most Frequent Activities",
            yaxis_title="Activity",
            xaxis_title="Frequency",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No activity data available for frequency analysis.")
    
    # Add hourly activity distribution if timestamp data is available
    st.header("Hourly Activity Distribution")
    
    # Extract hour information from events - handle different event log formats
    hour_counts = {}
    
    try:
        if isinstance(event_log, pd.DataFrame):
            if 'time:timestamp' in event_log.columns:
                # Ensure timestamp is datetime
                if pd.api.types.is_datetime64_any_dtype(event_log['time:timestamp']):
                    hour_data = event_log['time:timestamp'].dt.hour.value_counts().to_dict()
                    hour_counts.update(hour_data)
        else:
            # Try to handle as PM4Py EventLog object
            for trace in event_log:
                for event in trace:
                    if "time:timestamp" in event:
                        timestamp = event["time:timestamp"]
                        if hasattr(timestamp, 'hour'):  # Check if it's a datetime object
                            hour = timestamp.hour
                            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        if hour_counts:
            # Create hour labels for all 24 hours
            hours = list(range(24))
            counts = [hour_counts.get(hour, 0) for hour in hours]
            
            # Display as line chart
            fig = go.Figure(data=[
                go.Scatter(
                    x=hours,
                    y=counts,
                    mode='lines+markers',
                    marker_color='darkblue',
                    line=dict(width=2)
                )
            ])
            fig.update_layout(
                title="Activity Distribution by Hour of Day",
                xaxis_title="Hour of Day",
                yaxis_title="Number of Events",
                height=400,
                xaxis=dict(tickmode='array', tickvals=list(range(24)))
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("""
            The hourly activity distribution reveals when students are most active in their learning process.
            This can help identify:
            - **Peak learning hours**: When most educational activities take place
            - **Study patterns**: Whether learning happens more in mornings, afternoons, or evenings
            - **Potential for scheduling**: Optimal times for synchronous activities or support
            """)
        else:
            st.info("No timestamp data available for hourly distribution analysis.")
    except Exception as e:
        st.info("Could not generate hourly activity distribution.")
    
    # Add footer with metadata
    st.markdown("---")
    st.markdown(f"<div class='dashboard-footer'>Analysis performed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Dashboard by {AUTHOR}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
