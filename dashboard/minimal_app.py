import streamlit as st
import pandas as pd
import os
from pathlib import Path
import sys

# Add the parent directory to the path to import from the main module
sys.path.append(str(Path(__file__).parent.parent))

# Import data preprocessing
from data_preprocessing import EPMDataProcessor

st.set_page_config(
    page_title="Process Mining Educational Dashboard - Minimal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for styling
st.markdown("""
<style>
    .minimal-header {
        color: #4CAF50;
        border-bottom: 2px solid #4CAF50;
        padding-bottom: 10px;
    }
    .port-info {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown("<h1 class='minimal-header'>Process Mining Educational Dashboard - Minimal Version</h1>", unsafe_allow_html=True)
    st.caption("This is a minimal version with basic data loading and summary capabilities")
    st.markdown("<div class='port-info'>Running on port 8501</div>", unsafe_allow_html=True)
    
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
                
                # Process the dataset when button is clicked
                if st.button("Process EPM Dataset"):
                    with st.spinner("Loading and processing EPM dataset..."):
                        # Create data processor
                        processor = EPMDataProcessor(dataset_path)
                        
                        # Load raw data
                        raw_data = processor.load_all_data()
                        
                        if raw_data.empty:
                            st.error("Failed to load dataset. Please check the dataset path.")
                        else:
                            # Display basic information
                            st.header("Dataset Summary")
                            
                            # Display sessions information
                            sessions_info = raw_data.groupby('session')['student_id'].nunique()
                            
                            # Prepare data for simple display
                            sessions = sessions_info.index.tolist()
                            student_counts = sessions_info.values.tolist()
                            
                            # Create simple table
                            session_data = pd.DataFrame({
                                'Session': sessions,
                                'Number of Students': student_counts
                            })
                            
                            st.dataframe(session_data)
                            
                            # Display total events
                            st.metric("Total Events", f"{len(raw_data):,}")
                            
                            # Success message
                            st.success(f"Dataset successfully loaded with {raw_data['student_id'].nunique()} students across {len(sessions)} sessions.")
            else:
                st.error(f"EPM Dataset not found at {dataset_path}. Please check the path.")

if __name__ == "__main__":
    main()
