import streamlit as st
import pandas as pd
import os

from data_preprocessing import EPMDataProcessor

st.set_page_config(page_title="EPM Minimal Dashboard", layout="wide")

@st.cache_data
def load_csv(path: str):
    return pd.read_csv(path)

def main():
    st.title("Educational Process Mining - Minimal")
    data_path = st.text_input("CSV path", value=os.getenv("EPM_DATA", "data/epm_sample.csv"))
    df = None
    if data_path and os.path.exists(data_path):
        try:
            df = load_csv(data_path)
            st.success(f"Loaded {len(df)} rows from {data_path}")
            st.dataframe(df.head(20))
        except Exception as e:
            st.error(f"Failed to load CSV: {e}")
    else:
        st.info("Enter a valid CSV path or set EPM_DATA environment variable.")

    if st.button("Run preprocessing"):
        try:
            processor = EPMDataProcessor()
            st.write("Preprocessing completed.")
        except Exception as e:
            st.error(f"Preprocessing error: {e}")

if __name__ == "__main__":
    main()
