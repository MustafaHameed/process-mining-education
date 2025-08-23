import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import pm4py
from pm4py.objects.conversion.log import converter as log_converter
from datetime import datetime
import tempfile
import io
import zipfile
import re

# Import visualization components
from components.process_map import generate_process_map
from components.metrics_panel import display_metrics_panel
from components.analysis_panel import display_analysis_panel

# Import interpreters
from interpreters.bottleneck_detector import detect_bottlenecks
from interpreters.conformance_analyzer import analyze_conformance
from interpreters.pattern_analyzer import analyze_patterns

# Constants
AUTHOR = "MustafaHameed"
LAST_UPDATED = "2025-01-28"

# Page config
st.set_page_config(
    page_title="Educational Process Mining Dashboard - Enhanced",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .enhanced-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .dashboard-subtitle {
        font-size: 1.2rem;
        font-weight: 400;
        color: #424242;
        margin-bottom: 2rem;
    }
    .dashboard-section {
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .dashboard-footer {
        font-size: 0.8rem;
        color: #9E9E9E;
        text-align: center;
        margin-top: 2rem;
    }
    .port-info {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #1E88E5;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)


def load_epm_dataset(dataset_path="EPM Dataset 2", selected_sessions=None):
    """Load and process EPM dataset"""
    try:
        # Add the parent directory to the path to import from the main module
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))
        from data_preprocessing import EPMDataProcessor
        
        processor = EPMDataProcessor(dataset_path)
        raw_data = processor.load_all_data()
        
        if raw_data.empty:
            return None, None, 0, 0
            
        # Filter by sessions if specified
        if selected_sessions:
            raw_data = raw_data[raw_data['session'].isin(selected_sessions)]
        
        # Create event log
        event_log = processor.create_event_log(raw_data)
        
        # Get basic statistics
        num_cases = len(raw_data['student_id'].unique()) if 'student_id' in raw_data.columns else 0
        num_events = len(raw_data)
        
        return raw_data, event_log, num_cases, num_events
        
    except Exception as e:
        st.error(f"Error loading EPM dataset: {str(e)}")
        return None, None, 0, 0


def process_uploaded_file(uploaded_file):
    """Process uploaded file and convert to event log"""
    try:
        if uploaded_file.name.endswith('.zip'):
            # Handle zip files
            with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                csv_files = [f for f in file_list if f.endswith('.csv')]
                
                if not csv_files:
                    st.error("No CSV files found in the zip archive")
                    return None, None, 0, 0
                
                # Use the first CSV file
                csv_file = csv_files[0]
                with zip_ref.open(csv_file) as f:
                    raw_data = pd.read_csv(f)
                    
        elif uploaded_file.name.endswith('.csv'):
            raw_data = pd.read_csv(uploaded_file)
            
        elif uploaded_file.name.endswith('.xes'):
            # Handle XES files
            event_log = pm4py.read_xes(uploaded_file)
            raw_data = log_converter.apply(event_log, variant=log_converter.Variants.TO_DATA_FRAME)
            
        else:
            st.error("Unsupported file format")
            return None, None, 0, 0
            
        # Convert to event log format
        if 'case:concept:name' not in raw_data.columns:
            # Try to map common column names
            column_mapping = {
                'student_id': 'case:concept:name',
                'case_id': 'case:concept:name',
                'Case ID': 'case:concept:name',
                'activity': 'concept:name',
                'Activity': 'concept:name',
                'timestamp': 'time:timestamp',
                'Timestamp': 'time:timestamp',
                'time': 'time:timestamp'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in raw_data.columns:
                    raw_data = raw_data.rename(columns={old_col: new_col})
        
        # Ensure timestamp column is datetime
        if 'time:timestamp' in raw_data.columns:
            raw_data['time:timestamp'] = pd.to_datetime(raw_data['time:timestamp'])
            
        # Convert to PM4Py event log
        event_log = log_converter.apply(raw_data)
        
        num_cases = len(raw_data['case:concept:name'].unique()) if 'case:concept:name' in raw_data.columns else 0
        num_events = len(raw_data)
        
        return raw_data, event_log, num_cases, num_events
        
    except Exception as e:
        st.error(f"Error processing uploaded file: {str(e)}")
        return None, None, 0, 0


def display_dashboard(event_log, raw_data=None):
    """Display the main dashboard with tabs"""
    if event_log is None:
        st.warning("Please load a dataset to begin analysis")
        return
        
    # Get basic stats
    num_cases = len(event_log)
    num_events = sum(len(trace) for trace in event_log)
    
    # Display basic information
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cases", f"{num_cases:,}")
    with col2:
        st.metric("Total Events", f"{num_events:,}")
    with col3:
        if raw_data is not None and 'session' in raw_data.columns:
            st.metric("Sessions", f"{raw_data['session'].nunique()}")
        else:
            st.metric("Activities", f"{len(set(event['concept:name'] for trace in event_log for event in trace))}")
    
    # Session distribution chart if available
    if raw_data is not None and 'session' in raw_data.columns:
        st.subheader("Session Distribution")
        session_counts = raw_data.groupby('session')['student_id'].nunique().reset_index()
        session_counts.columns = ['Session', 'Number of Students']
        
        fig = px.bar(
            session_counts,
            x='Session',
            y='Number of Students',
            title="Number of Students per Session",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Success message
    st.success(f"Dataset successfully loaded with {num_cases} cases containing {num_events:,} events.")
    
    # Create tabs for different views
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
            - **Node color** indicates activity type (start/end/regular)
            
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
        st.markdown("""
        Conformance checking allows you to compare the actual process execution against a reference model.
        """)
        
        # Add option for sample dataset
        st.subheader("Reference Model Selection")
        reference_model_option = st.radio(
            "Choose reference model source:",
            ["Upload Custom Model", "Use Sample Model"]
        )
        
        ref_model = None
        
        if reference_model_option == "Upload Custom Model":
            ref_model = st.file_uploader("Upload reference model (BPMN or Petri Net)", type=["pnml", "bpmn"])
        else:
            st.info("Using sample reference model for educational process mining")
            # Create a simple sample Petri net for educational processes
            try:
                from pm4py.objects.petri_net.obj import PetriNet, Marking
                from pm4py.objects.petri_net import utils as petri_utils
                from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
                import tempfile
                import os
                
                # Create a simple educational process model
                net = PetriNet("educational_process")
                
                # Places
                start = PetriNet.Place("start")
                p_login = PetriNet.Place("p_login")
                p_study = PetriNet.Place("p_study")
                p_exercise = PetriNet.Place("p_exercise")
                p_review = PetriNet.Place("p_review")
                end = PetriNet.Place("end")
                
                net.places.add(start)
                net.places.add(p_login)
                net.places.add(p_study)
                net.places.add(p_exercise)
                net.places.add(p_review)
                net.places.add(end)
                
                # Transitions
                t_start = PetriNet.Transition("start", "Start")
                t_login = PetriNet.Transition("login", "Login")
                t_study = PetriNet.Transition("study", "Study Material")
                t_exercise = PetriNet.Transition("exercise", "Do Exercise")
                t_review = PetriNet.Transition("review", "Review")
                t_end = PetriNet.Transition("end", "End")
                
                net.transitions.add(t_start)
                net.transitions.add(t_login)
                net.transitions.add(t_study)
                net.transitions.add(t_exercise)
                net.transitions.add(t_review)
                net.transitions.add(t_end)
                
                # Arcs
                petri_utils.add_arc_from_to(start, t_start, net)
                petri_utils.add_arc_from_to(t_start, p_login, net)
                petri_utils.add_arc_from_to(p_login, t_login, net)
                petri_utils.add_arc_from_to(t_login, p_study, net)
                petri_utils.add_arc_from_to(p_study, t_study, net)
                petri_utils.add_arc_from_to(t_study, p_exercise, net)
                petri_utils.add_arc_from_to(p_exercise, t_exercise, net)
                petri_utils.add_arc_from_to(t_exercise, p_review, net)
                petri_utils.add_arc_from_to(p_review, t_review, net)
                petri_utils.add_arc_from_to(t_review, end, net)
                petri_utils.add_arc_from_to(end, t_end, net)
                
                # Create initial and final marking
                initial_marking = Marking()
                initial_marking[start] = 1
                final_marking = Marking()
                final_marking[end] = 1
                
                # Export to temporary file
                temp_dir = tempfile.gettempdir()
                temp_file = os.path.join(temp_dir, "sample_educational_model.pnml")
                pnml_exporter.apply(net, initial_marking, temp_file, final_marking=final_marking)
                
                # Create a file-like object from the temporary file
                class SampleModelFile:
                    def __init__(self, file_path):
                        self.name = "sample_educational_model.pnml"
                        with open(file_path, 'rb') as f:
                            self.content = f.read()
                    
                    def read(self):
                        return self.content
                
                # Use the SampleModelFile as reference model
                ref_model = SampleModelFile(temp_file)
                
                st.success("Sample educational process model loaded successfully")
                
                # Display the model structure
                st.markdown("""
                **Sample Model Structure:**
                1. Start → Login
                2. Login → Study Material  
                3. Study Material → Do Exercise
                4. Do Exercise → Review
                5. Review → End
                """)
                
            except Exception as e:
                st.error(f"Error creating sample model: {str(e)}")
        
        # Perform conformance checking if model is available
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
    
    # Add footer with metadata
    st.markdown("---")
    st.markdown(f"<div class='dashboard-footer'>Analysis performed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Dashboard by {AUTHOR}</div>", unsafe_allow_html=True)


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
                    
                    # Load available sessions
                    try:
                        raw_data, _, _, _ = load_epm_dataset(dataset_path)
                        if raw_data is not None and 'session' in raw_data.columns:
                            available_sessions = sorted(raw_data['session'].unique())
                            
                            # Session selection
                            selected_sessions = st.multiselect(
                                "Select sessions to analyze:",
                                available_sessions,
                                default=available_sessions[:3] if len(available_sessions) > 3 else available_sessions
                            )
                            
                            # Load button
                            if st.button("Load EPM Dataset"):
                                if selected_sessions:
                                    with st.spinner("Loading and processing EPM dataset..."):
                                        raw_data, event_log, num_cases, num_events = load_epm_dataset(dataset_path, selected_sessions)
                                        
                                        if event_log is not None:
                                            st.session_state.event_log = event_log
                                            st.session_state.raw_data = raw_data
                                            st.session_state.event_log_loaded = True
                                            st.success(f"Loaded {num_cases} cases with {num_events:,} events")
                                        else:
                                            st.error("Failed to load EPM dataset")
                                else:
                                    st.warning("Please select at least one session")
                        else:
                            st.error("Could not load session information from EPM dataset")
                    except Exception as e:
                        st.error(f"Error accessing EPM dataset: {str(e)}")
                else:
                    st.error(f"EPM Dataset not found at {dataset_path}")
                    st.info("Please ensure the EPM Dataset is available in the project directory")
        
        with dataset_tab2:
            # Custom file upload
            st.subheader("Upload Custom Dataset")
            uploaded_file = st.file_uploader(
                "Upload event log",
                type=["csv", "xes", "zip"],
                help="Supported formats: CSV, XES, or ZIP containing CSV files"
            )
            
            if uploaded_file:
                if st.button("Process Uploaded File"):
                    with st.spinner("Processing uploaded file..."):
                        raw_data, event_log, num_cases, num_events = process_uploaded_file(uploaded_file)
                        
                        if event_log is not None:
                            st.session_state.event_log = event_log
                            st.session_state.raw_data = raw_data
                            st.session_state.event_log_loaded = True
                            st.success(f"Loaded {num_cases} cases with {num_events:,} events")
                        else:
                            st.error("Failed to process uploaded file")
        
        # Add information section
        with st.expander("ℹ️ About Process Mining"):
            st.markdown("""
            **Process Mining** is a field of data science that focuses on the analysis of business processes based on event logs.
            
            Key techniques include:
            - **Process Discovery**: Extracting process models from event logs
            - **Conformance Checking**: Comparing actual vs. expected processes
            - **Process Enhancement**: Improving processes based on data
            - **Social Network Analysis**: Analyzing organizational perspectives
            """)
            
        st.divider()
        st.info(f"Current session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Main content area
    if st.session_state.event_log_loaded and st.session_state.event_log is not None:
        display_dashboard(st.session_state.event_log, st.session_state.raw_data)
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome to the Educational Process Mining Dashboard
        
        This enhanced dashboard provides comprehensive process mining capabilities for educational data analysis.
        
        ### Getting Started
        1. **Load Data**: Use the sidebar to load the EPM dataset or upload your own data
        2. **Explore**: Navigate through the tabs to analyze different aspects of your process
        3. **Interpret**: Use the provided interpretations to understand your findings
        
        ### Features
        - **Process Maps**: Visualize the flow of activities
        - **Performance Metrics**: Analyze timing and efficiency
        - **Pattern Analysis**: Discover common sequences and variants
        - **Conformance Checking**: Compare against reference models
        
        ### Supported Data Formats
        - CSV files with case, activity, and timestamp columns
        - XES (eXtensible Event Stream) files
        - ZIP archives containing CSV files
        - Built-in EPM (Educational Process Mining) dataset
        """)


if __name__ == "__main__":
    main()