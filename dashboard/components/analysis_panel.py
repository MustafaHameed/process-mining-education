import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def display_analysis_panel(patterns):
    """
    Display a panel with process pattern analysis and insights.
    
    Args:
        patterns: Dictionary with pattern analysis results
    """
    # Display analysis metadata
    st.caption(f"Analysis timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Analyst: MustafaHameed")
    
    # Display variant analysis
    st.subheader("Process Variants")
    
    # Create a pie chart for variant distribution
    if "variant_distribution" in patterns:
        fig = px.pie(
            patterns["variant_distribution"], 
            values="count", 
            names="variant",
            title="Distribution of Process Variants",
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Display common sequences
    if "common_sequences" in patterns:
        st.subheader("Common Activity Sequences")
        st.dataframe(patterns["common_sequences"])
    
    # Display rework patterns
    if "rework_patterns" in patterns:
        st.subheader("Rework Patterns")
        fig = px.bar(
            patterns["rework_patterns"],
            x="activity",
            y="rework_count",
            labels={"activity": "Activity", "rework_count": "Rework Count"},
            title="Activities with Rework"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Display anomalies if they exist
    if "anomalies" in patterns and not patterns["anomalies"].empty:
        st.subheader("Potential Anomalies")
        st.dataframe(patterns["anomalies"])
        
        st.info("""
        Anomalies represent unusual process executions that deviate from common patterns.
        These may indicate exceptions, errors, or special cases that should be investigated.
        """)
    
    # Display educational insights
    st.subheader("Educational Insights")
    
    with st.expander("What are process variants?"):
        st.markdown("""
        **Process variants** are different ways a process can be executed from start to finish.
        
        Each variant represents a unique sequence of activities. In real-world processes:
        - A high number of variants may indicate an unstructured process
        - A few dominant variants with many rare variants may indicate a process with exceptions
        - Many equally distributed variants may indicate a flexible process
        
        Understanding variants helps identify the "happy path" and deviations.
        """)
    
    with st.expander("How to interpret rework patterns?"):
        st.markdown("""
        **Rework** occurs when activities need to be repeated within the same case, indicating:
        
        - Potential quality issues requiring corrections
        - Iterative work processes (like document revisions)
        - Loops in the process flow
        
        High rework rates may indicate inefficiencies that could be addressed through process improvement.
        """)
    
    with st.expander("What makes a good process?"):
        st.markdown("""
        Characteristics of an efficient process include:
        
        - **Streamlined flow**: Minimal unnecessary activities or handoffs
        - **Consistency**: Limited variations in how the process is executed
        - **Clear structure**: Well-defined sequence of activities
        - **Minimal bottlenecks**: No significant delays at particular activities
        - **Limited rework**: Activities rarely need to be repeated
        - **Appropriate automation**: Routine tasks are automated
        """)