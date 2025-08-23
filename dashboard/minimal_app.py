import streamlit as st
import pandas as pd
import os
from pathlib import Path
from dashboard.data import load_epm_dataset, load_csv

st.set_page_config(page_title="EPM Minimal Dashboard", layout="wide")

@st.cache_data(show_spinner=True)
def cached_load_epm(repo_root_str: str):
    return load_epm_dataset(Path(repo_root_str))

@st.cache_data
def cached_load_csv(path: str):
    return load_csv(path)

def main():
    st.title("Educational Process Mining - Minimal")
    source = st.radio("Data source", ["Bundled EPM Dataset", "CSV file"], index=0, horizontal=True)

    df = None
    if source == "Bundled EPM Dataset":
        repo_root = Path(__file__).resolve().parents[1]
        dataset_dir = repo_root / "EPM Dataset 2"
        st.caption(f"Using dataset: {dataset_dir}")
        try:
            raw, event_log, stats = cached_load_epm(str(repo_root))
            df = event_log
            st.success(f"Loaded {stats.get('total_events', 0):,} events from {stats.get('total_cases', 0)} cases")
            st.dataframe(df.head(20))
        except Exception as e:
            st.error(f"Failed to load EPM dataset: {e}")
    else:
        data_path = st.text_input("CSV path", value=os.getenv("EPM_DATA", ""))
        if data_path:
            try:
                df = cached_load_csv(data_path)
                st.success(f"Loaded {len(df)} rows from {data_path}")
                st.dataframe(df.head(20))
            except Exception as e:
                st.error(f"Failed to load CSV: {e}")

if __name__ == "__main__":
    main()
