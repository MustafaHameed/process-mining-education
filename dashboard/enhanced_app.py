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

# Import visualization components using relative imports
from .components.process_map import generate_process_map
from .components.metrics_panel import display_metrics_panel
from .components.analysis_panel import display_analysis_panel

# Import interpreters using relative imports
from .interpreters.bottleneck_detector import detect_bottlenecks
from .interpreters.conformance_analyzer import analyze_conformance
from .interpreters.pattern_analyzer import analyze_patterns

# Constants
AUTHOR = "Educational Process Mining Team"

# Page config
st.set_page_config(
    page_title="Educational Process Mining Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .dashboard-title {
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
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Dashboard title
    st.markdown('<div class="dashboard-title">Educational Process Mining Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-subtitle">Explore and analyze educational process data using process mining techniques</div>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("Data Input")
    uploaded_file = st.sidebar.file_uploader("Upload event log (CSV or XES)", type=["csv", "xes", "zip"])
    
    # Initialize session state if not already done
    if "event_log_loaded" not in st.session_state:
        st.session_state.event_log_loaded = False
    
    if "raw_data" not in st.session_state:
        st.session_state.raw_data = None
    
    if "event_log" not in st.session_state:
        st.session_state.event_log = None
    
    # Load data if file is uploaded
    raw_data = None
    event_log = None
    num_cases = 0
    num_events = 0
    
    if uploaded_file:
        try:
            # Check if it's a zip file
            if uploaded_file.name.endswith('.zip'):
                # Create a temporary directory to extract files
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    # Get list of files in the zip
                    file_list = zip_ref.namelist()
                    
                    # Show available files in the zip
                    st.sidebar.subheader("Files in the archive:")
                    selected_file = st.sidebar.selectbox("Choose a file to analyze:", file_list)
                    
                    # Extract the selected file
                    with zip_ref.open(selected_file) as file:
                        file_content = file.read()
                        
                        # Process based on file extension
                        if selected_file.endswith('.csv'):
                            raw_data = pd.read_csv(io.BytesIO(file_content))
                            
                            # Try to detect case, activity, and timestamp columns
                            case_column = None
                            activity_column = None
                            timestamp_column = None
                            
                            # Look for common column names
                            for col in raw_data.columns:
                                col_lower = col.lower()
                                if 'case' in col_lower or 'student' in col_lower:
                                    case_column = col
                                elif 'activity' in col_lower or 'event' in col_lower or 'action' in col_lower:
                                    activity_column = col
                                elif 'time' in col_lower or 'date' in col_lower:
                                    timestamp_column = col
                            
                            # Let user verify or select columns
                            case_column = st.sidebar.selectbox("Select case ID column:", raw_data.columns, index=raw_data.columns.get_loc(case_column) if case_column else 0)
                            activity_column = st.sidebar.selectbox("Select activity column:", raw_data.columns, index=raw_data.columns.get_loc(activity_column) if activity_column else 0)
                            timestamp_column = st.sidebar.selectbox("Select timestamp column:", raw_data.columns, index=raw_data.columns.get_loc(timestamp_column) if timestamp_column else 0)
                            
                            # Create event log in PM4Py format
                            log_df = raw_data.rename(columns={
                                case_column: 'case:concept:name',
                                activity_column: 'concept:name',
                                timestamp_column: 'time:timestamp'
                            })
                            
                            # Convert timestamp column to datetime if not already
                            if not pd.api.types.is_datetime64_any_dtype(log_df['time:timestamp']):
                                try:
                                    log_df['time:timestamp'] = pd.to_datetime(log_df['time:timestamp'])
                                except:
                                    st.sidebar.warning("Could not convert timestamp column to datetime format. Using as is.")
                            
                            # Convert to event log
                            event_log = log_df
                            
                            # Count cases and events
                            num_cases = log_df['case:concept:name'].nunique()
                            num_events = len(log_df)
                            
                        elif selected_file.endswith('.xes'):
                            # Parse XES file
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".xes") as tmp:
                                tmp.write(file_content)
                                tmp_path = tmp.name
                            
                            # Use PM4Py to parse
                            event_log = pm4py.read_xes(tmp_path)
                            
                            # Count cases and events
                            num_cases = len(event_log)
                            num_events = sum(len(trace) for trace in event_log)
                            
                            # Try to convert to DataFrame for easier filtering
                            try:
                                log_df = pm4py.convert_to_dataframe(event_log)
                                raw_data = log_df.copy()
                            except:
                                st.sidebar.warning("Could not convert XES to DataFrame format. Some filtering options may be limited.")
                        
                        else:
                            st.sidebar.error(f"Unsupported file format: {selected_file}")
            
            else:  # Single file upload
                if uploaded_file.name.endswith('.csv'):
                    raw_data = pd.read_csv(uploaded_file)
                    
                    # Try to detect case, activity, and timestamp columns
                    case_column = None
                    activity_column = None
                    timestamp_column = None
                    
                    # Look for common column names
                    for col in raw_data.columns:
                        col_lower = col.lower()
                        if 'case' in col_lower or 'student' in col_lower:
                            case_column = col
                        elif 'activity' in col_lower or 'event' in col_lower or 'action' in col_lower:
                            activity_column = col
                        elif 'time' in col_lower or 'date' in col_lower:
                            timestamp_column = col
                    
                    # Let user verify or select columns
                    case_column = st.sidebar.selectbox("Select case ID column:", raw_data.columns, index=raw_data.columns.get_loc(case_column) if case_column else 0)
                    activity_column = st.sidebar.selectbox("Select activity column:", raw_data.columns, index=raw_data.columns.get_loc(activity_column) if activity_column else 0)
                    timestamp_column = st.sidebar.selectbox("Select timestamp column:", raw_data.columns, index=raw_data.columns.get_loc(timestamp_column) if timestamp_column else 0)
                    
                    # Create event log in PM4Py format
                    log_df = raw_data.rename(columns={
                        case_column: 'case:concept:name',
                        activity_column: 'concept:name',
                        timestamp_column: 'time:timestamp'
                    })
                    
                    # Convert timestamp column to datetime if not already
                    if not pd.api.types.is_datetime64_any_dtype(log_df['time:timestamp']):
                        try:
                            log_df['time:timestamp'] = pd.to_datetime(log_df['time:timestamp'])
                        except:
                            st.sidebar.warning("Could not convert timestamp column to datetime format. Using as is.")
                    
                    # Convert to event log
                    event_log = log_df
                    
                    # Count cases and events
                    num_cases = log_df['case:concept:name'].nunique()
                    num_events = len(log_df)
                    
                elif uploaded_file.name.endswith('.xes'):
                    # Save uploaded file to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".xes") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                    
                    # Use PM4Py to parse
                    event_log = pm4py.read_xes(tmp_path)
                    
                    # Count cases and events
                    num_cases = len(event_log)
                    num_events = sum(len(trace) for trace in event_log)
                    
                    # Try to convert to DataFrame for easier filtering
                    try:
                        log_df = pm4py.convert_to_dataframe(event_log)
                        raw_data = log_df.copy()
                    except:
                        st.sidebar.warning("Could not convert XES to DataFrame format. Some filtering options may be limited.")
                
                else:
                    st.sidebar.error(f"Unsupported file format: {uploaded_file.name}")
            
            # Add filters in the sidebar if we have data
            if raw_data is not None:
                st.sidebar.header("Filters")
                
                # Session filter if 'session' column exists
                if 'session' in raw_data.columns:
                    available_sessions = sorted(raw_data['session'].unique())
                    selected_sessions = st.sidebar.multiselect(
                        "Filter by session",
                        options=available_sessions,
                        default=available_sessions
                    )
                    
                    if selected_sessions:
                        filtered_data = raw_data[raw_data['session'].isin(selected_sessions)]
                        
                        # Update event log with filtered data
                        if 'case:concept:name' in filtered_data.columns and 'concept:name' in filtered_data.columns:
                            event_log = filtered_data
                            # Count cases and events in filtered data
                            num_cases = filtered_data['case:concept:name'].nunique()
                            num_events = len(filtered_data)
                
                # Save to session state for reuse
                st.session_state.raw_data = raw_data
                st.session_state.event_log = event_log
                st.session_state.event_log_loaded = True
                
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.info("Please check your file format and try again.")
    
    # Use data from session state if available
    if not (raw_data and event_log) and st.session_state.event_log_loaded:
        raw_data = st.session_state.raw_data
        event_log = st.session_state.event_log
        
        # Count cases and events
        if isinstance(event_log, pd.DataFrame):
            num_cases = event_log['case:concept:name'].nunique() if 'case:concept:name' in event_log.columns else 0
            num_events = len(event_log)
        else:
            # PM4Py event log
            num_cases = len(event_log) if event_log else 0
            num_events = sum(len(trace) for trace in event_log) if event_log else 0
    
    # If no data, show message
    if not (raw_data is not None and event_log is not None):
        st.info("Upload a CSV or XES file to start your process mining analysis.")
        st.markdown("""
        ### Getting Started with Educational Process Mining
        
        This dashboard helps you analyze educational process data using process mining techniques.
        
        Upload your event log to explore:
        - Process maps showing the flow of educational activities
        - Performance metrics for different learning pathways
        - Patterns and insights in student behavior
        - Conformance checking against reference models
        
        The tool supports CSV files with case ID, activity, and timestamp columns, or XES files.
        """)
        return
    
    # If we have raw data with session info, display session information
    if raw_data is not None and 'session' in raw_data.columns and 'student_id' in raw_data.columns:
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
    
    # Create tabs in the main content area for different visualizations
    st.markdown("## Analysis Tabs")
    tab0, tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Overview",
        "📊 Process Map", 
        "⏱️ Performance Metrics", 
        "🔍 Patterns & Insights", 
        "✅ Conformance"
    ])
    
    with tab0:
        st.header("Process Overview")
        
        # If we have raw data, display session information
        if raw_data is not None and 'session' in raw_data.columns and 'student_id' in raw_data.columns:
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
        
        # Activity Frequency Analysis
        st.subheader("Activity Frequency Analysis")
        
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
                        try:
                            if 'concept:name' in event:
                                activity = event["concept:name"]
                                activity_counts[activity] = activity_counts.get(activity, 0) + 1
                        except (TypeError, KeyError):
                            continue
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
        st.subheader("Hourly Activity Distribution")
        
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
                        try:
                            if "time:timestamp" in event:
                                timestamp = event["time:timestamp"]
                                if hasattr(timestamp, 'hour'):  # Check if it's a datetime object
                                    hour = timestamp.hour
                                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
                        except (TypeError, KeyError):
                            continue
            
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
    
    with tab1:
        st.header("Process Map")
        try:
            process_map_fig = generate_process_map(event_log)
            st.plotly_chart(process_map_fig, use_container_width=True)
            
            st.subheader("Interpretation")
            st.markdown("""
            The process map visualizes:
            - **Activity Flow**: The sequence of educational activities
            - **Frequency**: How often each activity and path occurs
            - **Bottlenecks**: Where students may get stuck in the learning process
            - **Deviations**: Unexpected paths through the learning materials
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
                import tempfile
                import os
                from pm4py.objects.petri_net.obj import PetriNet, Marking
                from pm4py.objects.petri_net.utils import petri_utils
                from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
                
                # Create a simple Petri net for educational processes
                net = PetriNet("Sample Educational Process")
                
                # Places
                start = PetriNet.Place("start")
                study_materials = PetriNet.Place("study_materials")
                attempt_exercise = PetriNet.Place("attempt_exercise")
                review_feedback = PetriNet.Place("review_feedback")
                end = PetriNet.Place("end")
                
                # Add places to net
                net.places.add(start)
                net.places.add(study_materials)
                net.places.add(attempt_exercise)
                net.places.add(review_feedback)
                net.places.add(end)
                
                # Transitions
                t_start = PetriNet.Transition("t_start", "Login")
                t_study = PetriNet.Transition("t_study", "Read Materials")
                t_attempt = PetriNet.Transition("t_attempt", "Submit Exercise")
                t_review = PetriNet.Transition("t_review", "View Feedback")
                t_end = PetriNet.Transition("t_end", "Logout")
                
                # Add transitions to net
                net.transitions.add(t_start)
                net.transitions.add(t_study)
                net.transitions.add(t_attempt)
                net.transitions.add(t_review)
                net.transitions.add(t_end)
                
                # Arcs
                petri_utils.add_arc_from_to(start, t_start, net)
                petri_utils.add_arc_from_to(t_start, study_materials, net)
                petri_utils.add_arc_from_to(study_materials, t_study, net)
                petri_utils.add_arc_from_to(t_study, attempt_exercise, net)
                petri_utils.add_arc_from_to(attempt_exercise, t_attempt, net)
                petri_utils.add_arc_from_to(t_attempt, review_feedback, net)
                petri_utils.add_arc_from_to(review_feedback, t_review, net)
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
                        self.file_path = file_path
                        self.name = os.path.basename(file_path)
                        with open(file_path, 'rb') as f:
                            self._content = f.read()
                    
                    def getvalue(self):
                        return self._content
                
                # Use the SampleModelFile as reference model
                ref_model = SampleModelFile(temp_file)
                
                st.success("Sample educational process model loaded successfully")
                
                # Display the model structure
                st.subheader("Sample Model Structure")
                st.markdown("""
                The sample educational process model includes these main activities:
                1. Login → Start the learning session
                2. Read Materials → Study the course content
                3. Submit Exercise → Attempt to solve problems
                4. View Feedback → Review assessment results
                5. Logout → End the learning session
                """)
                
            except Exception as e:
                st.error(f"Error creating sample model: {str(e)}")
                st.info("Please upload a custom model instead.")
        
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

if __name__ == "__main__":
    main()
