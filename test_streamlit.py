import streamlit as st

st.title("Simple Streamlit Test")
st.write("This is a simple test to verify Streamlit is working correctly.")

if st.button("Click Me"):
    st.success("Button clicked!")
