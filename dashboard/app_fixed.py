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

# Import dashboard components using relative imports
from components.process_map import generate_process_map
from components.metrics_panel_fixed import display_metrics_panel
from components.analysis_panel import display_analysis_panel

# Import data preprocessing
from data_preprocessing import EPMDataProcessor

# Import interpreters (relative imports)
from interpreters.pattern_analyzer import analyze_patterns
from interpreters.bottleneck_detector_fixed import detect_bottlenecks
from interpreters.conformance_analyzer import analyze_conformance

# Dashboard metadata
LAST_UPDATED = "2025-08-22 16:30:00"
AUTHOR = "MustafaHameed"

st.set_page_config(
    page_title="Process Mining Educational Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("Process Mining Educational Dashboard")
    st.caption(f"Last updated: {LAST_UPDATED} | Author: {AUTHOR}")
    
    with st.sidebar:
        st.header("Configuration")
        
        # Option to load built-in EPM dataset
        st.subheader("Dataset Options")
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
                if st.button("Process EPM Dataset"):
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
                            # Display sessions information
                            sessions_info = raw_data.groupby('session')['student_id'].nunique()
                            
                            # Create event log
                            event_log = processor.create_event_log(raw_data)
                            
                            # Add session info to event attributes
                            for trace in event_log:
                                # Extract session from case_id
                                case_id = trace.attributes["concept:name"]
                                if "Session_" in case_id:
                                    session_num = case_id.split("Session_")[1]
                                    # Add session info to trace attributes
                                    trace.attributes["session_info"] = f"Session {session_num}"
                                
                                # Add session info to each event as well
                                for event in trace:
                                    event["session_info"] = trace.attributes.get("session_info", "Unknown")
                            
                            # Apply quality filters
                            quality_log = processor.filter_by_criteria(
                                event_log, 
                                min_events_per_case=min_events_per_case,
                                exclude_activities=exclude_activities
                            )
                            
                            # Verify sessions are preserved
                            preserved_sessions = set()
                            for trace in quality_log:
                                if "session_info" in trace.attributes:
                                    preserved_sessions.add(trace.attributes["session_info"])
                            
                            if len(preserved_sessions) < len(selected_sessions):
                                st.warning(f"Some sessions were lost during filtering. Keeping {len(preserved_sessions)} out of {len(selected_sessions)} sessions.")
                            
                            # Process the log for dashboard display
                            display_dashboard(quality_log, raw_data, sessions_info)
                
            else:
                st.error(f"EPM Dataset not found at {dataset_path}. Please check the path.")
        
        # Alternatively, allow user to upload their own log
        else:
            uploaded_file = st.file_uploader("Upload Event Log (CSV or XES)", type=["csv", "xes"])
            
            if uploaded_file:
                # Load the event log
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                    col1, col2, col3 = st.columns(3)
                    case_id_col = col1.selectbox("Case ID Column", df.columns.tolist())
                    activity_col = col2.selectbox("Activity Column", df.columns.tolist())
                    timestamp_col = col3.selectbox("Timestamp Column", df.columns.tolist())
                    
                    if st.button("Process Event Log"):
                        # Convert to event log
                        event_log = pm4py.format_dataframe(
                            df, 
                            case_id=case_id_col, 
                            activity_key=activity_col, 
                            timestamp_key=timestamp_col
                        )
                        display_dashboard(event_log, df, None)
                else:
                    # XES file
                    if st.button("Process Event Log"):
                        event_log = pm4py.read_xes(uploaded_file)
                        display_dashboard(event_log, None, None)
        
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

def display_dashboard(event_log, raw_data=None, sessions_info=None):
    # Display dataset summary first
    st.header("Dataset Summary")
    
    # Basic statistics
    num_cases = len(event_log)
    num_events = sum(len(trace) for trace in event_log)
    num_activities = len({event["concept:name"] for trace in event_log for event in trace})
    
    # Display metrics in columns
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cases", f"{num_cases:,}")
    col2.metric("Total Events", f"{num_events:,}")
    col3.metric("Unique Activities", num_activities)
    
    # If we have session info, display it
    if sessions_info is not None:
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
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Process Map", "Performance Metrics", "Patterns & Insights", "Conformance"])
    
    with tab1:
        st.header("Process Discovery Visualization")
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
    
    with tab2:
        st.header("Performance Metrics")
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
    
    with tab3:
        st.header("Process Patterns & Insights")
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
    
    with tab4:
        st.header("Conformance Checking")
        st.info("Upload a reference model (BPMN or Petri Net) to perform conformance checking")
        ref_model = st.file_uploader("Upload reference model", type=["pnml", "bpmn"])
        
        if ref_model:
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
    
    # Add footer with metadata
    st.markdown("---")
    st.caption(f"Analysis performed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Dashboard by {AUTHOR}")

# Deprecated: consolidated into dashboard package with two entrypoints.
raise RuntimeError("Deprecated module. Use 'dashboard/minimal_app.py' or 'dashboard/enhanced_app.py'.")

if __name__ == "__main__":
    main()
