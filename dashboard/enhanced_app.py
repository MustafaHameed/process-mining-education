import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from pathlib import Path

# Support running this file directly via Streamlit by ensuring the repo root is importable
try:
    from dashboard.components.metrics_panel import show_summary_metrics
    from dashboard.components.analysis_panel import show_basic_charts
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from dashboard.components.metrics_panel import show_summary_metrics
    from dashboard.components.analysis_panel import show_basic_charts

# Try to import the EPM processor from the repo root; fall back by appending the root to sys.path
try:
    from data_preprocessing import EPMDataProcessor
except ModuleNotFoundError:
    import sys as _sys
    _sys.path.append(str(Path(__file__).resolve().parents[1]))
    from data_preprocessing import EPMDataProcessor

st.set_page_config(page_title="EPM Enhanced Dashboard", layout="wide")

@st.cache_data
def load_csv(path: str):
    return pd.read_csv(path)

@st.cache_data(show_spinner=True)
def load_epm_dataset(dataset_path: str):
    processor = EPMDataProcessor(dataset_path)
    raw = processor.load_all_data()
    import streamlit as st
    import pandas as pd
    import os
    from pathlib import Path

    from dashboard.data import load_epm_dataset, load_csv
    from dashboard.components.metrics_panel import show_summary_metrics
    from dashboard.components.analysis_panel import show_basic_charts

    st.set_page_config(page_title="EPM Enhanced Dashboard", layout="wide")

    @st.cache_data(show_spinner=True)
    def cached_load_epm(repo_root_str: str):
        return load_epm_dataset(Path(repo_root_str))

    @st.cache_data
    def cached_load_csv(path: str):
        return load_csv(path)


    def main():
        st.title("Educational Process Mining - Enhanced")
        source = st.radio("Data source", ["Bundled EPM Dataset", "CSV file"], index=0, horizontal=True)

        df = None
        if source == "Bundled EPM Dataset":
            repo_root = Path(__file__).resolve().parents[1]
            st.caption(f"Using dataset under: {repo_root / 'EPM Dataset 2'}")
            try:
                raw, event_log, stats = cached_load_epm(str(repo_root))
                df = event_log
                st.success(f"Loaded {stats.get('total_events', 0):,} events")
            except Exception as e:
                st.error(f"Failed to load bundled dataset: {e}")
        else:
            data_path = st.text_input("CSV path", value=os.getenv("EPM_DATA", ""))
            if data_path and os.path.exists(data_path):
                try:
                    df = cached_load_csv(data_path)
                    st.success(f"Loaded {len(df):,} rows from {data_path}")
                except Exception as e:
                    st.error(f"CSV load error: {e}")
            else:
                st.info("Enter a valid CSV path or set EPM_DATA.")

        tab1, tab2 = st.tabs(["Metrics", "Charts"])
        with tab1:
            show_summary_metrics(df if df is not None else pd.DataFrame())
        with tab2:
            show_basic_charts(df if df is not None else pd.DataFrame())


    if __name__ == "__main__":
        main()
