import streamlit as st
import pm4py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, datetime

def show_summary_metrics(df: pd.DataFrame):
    st.subheader("Summary metrics")
    if df is None or df.empty:
        st.info("Load data to see metrics.")
        return
    st.metric("Rows", len(df))
    for c in df.select_dtypes(include="number").columns[:3]:
        st.write(f"{c}: mean={df[c].mean():.3f}, std={df[c].std():.3f}")