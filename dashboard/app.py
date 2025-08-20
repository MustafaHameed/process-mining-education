import streamlit as st
import pandas as pd
import pm4py
import plotly.graph_objects as go
import networkx as nx
from pathlib import Path
import sys
from datetime import datetime

# Add the parent directory to the path to import from the main module
sys.path.append(str(Path(__file__).parent.parent))

# Import dashboard components
from components.process_map import generate_process_map
from components.metrics_panel import display_metrics_panel
from components.analysis_panel import display_analysis_panel

# Import interpreters
from interpreters.pattern_analyzer import analyze_patterns
from interpreters.bottleneck_detector import detect_bottlenecks
from interpreters.conformance_analyzer import analyze_conformance

# Dashboard metadata
LAST_UPDATED = "2025-08-20 09:36:40"
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
                    display_dashboard(event_log)
            else:
                # XES file
                if st.button("Process Event Log"):
                    event_log = pm4py.read_xes(uploaded_file)
                    display_dashboard(event_log)
        
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

def display_dashboard(event_log):
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

if __name__ == "__main__":
    main()