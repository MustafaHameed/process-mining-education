import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

from dashboard.components.metrics_panel import show_summary_metrics
from dashboard.components.analysis_panel import show_basic_charts

st.set_page_config(page_title="EPM Enhanced Dashboard", layout="wide")

@st.cache_data
def load_csv(path: str):
    return pd.read_csv(path)

def main():
    st.title("Educational Process Mining - Enhanced")
    data_path = st.text_input("CSV path", value=os.getenv("EPM_DATA", "data/epm_sample.csv"))
    df = None
    if data_path and os.path.exists(data_path):
        try:
            df = load_csv(data_path)
            st.success(f"Loaded {len(df)} rows from {data_path}")
        except Exception as e:
            st.error(f"Failed to load CSV: {e}")
    else:
        st.info("Enter a valid CSV path or set EPM_DATA environment variable.")

    tab1, tab2 = st.tabs(["Metrics", "Charts"])
    with tab1:
        show_summary_metrics(df if df is not None else pd.DataFrame())
    with tab2:
        show_basic_charts(df if df is not None else pd.DataFrame())

if __name__ == "__main__":
    main()
