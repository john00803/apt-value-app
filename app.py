import streamlit as st
from main_router import run_router
st.set_page_config(page_title="아파트 가치 평가", layout="wide")
run_router()
