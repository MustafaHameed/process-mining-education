import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def show_basic_charts(df: pd.DataFrame):
    st.subheader("Basic charts")
    if df is None or df.empty:
        st.info("Load data to see charts.")
        return
    num_cols = df.select_dtypes(include="number").columns
    if len(num_cols) > 0:
        st.write("Histogram of first numeric column")
        st.plotly_chart(px.histogram(df, x=num_cols[0]), use_container_width=True)