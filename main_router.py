import streamlit as st
from version_logic.version_runner import run_version
from modules.auth_manager import get_current_user
from gpt_chat.chat_ui import show_chat_ui
from ui.display_utils import show_initial_screen

def run_router():
    user_email = get_current_user()
    st.sidebar.write(f"사용자: {user_email}")
    mode = st.sidebar.radio("모드 선택", ["분석 시작", "OpenAI 전문가 프로그램 질의응답"])
    if mode == "OpenAI 전문가 프로그램 질의응답":
        show_chat_ui(user_email)
    else:
        choice = show_initial_screen()
        if choice:
            run_version(choice, user_email)
