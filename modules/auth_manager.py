import streamlit as st
import pandas as pd

def get_current_user():
    return st.text_input("이메일을 입력하세요", key="user_email")

def is_paid_user(email):
    df = pd.read_csv("data/users.csv")
    user = df[df["email"] == email]
    return not user.empty and user.iloc[0]["is_paid"] == "yes"
