"""
Streamlit front end.

Shows: question input, generated answer, source chunks used,
confidence/groundedness indicator, and escalation flag when triggered.
"""

import streamlit as st

st.title("Explainable RAG Banking Agent")
st.caption("Ask a question in Arabic or English about CBE consumer protection circulars.")
