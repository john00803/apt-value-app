import streamlit as st
from gpt_chat.chat_engine import get_response
from modules.usage_tracker import check_usage, record_usage
from modules.auth_manager import is_paid_user

def show_chat_ui(email):
    st.subheader("💬 OpenAI 전문가 프로그램 질의응답")
    if not is_paid_user(email) and not check_usage(email):
        st.error("오늘의 무료 질문 횟수를 초과했습니다. 유료 구독 시 무제한 이용 가능합니다.")
        return
    prompt = st.text_input("질문을 입력하세요")
    if st.button("질문하기") and prompt:
        with st.spinner("응답 생성 중..."):
            answer = get_response(prompt)
            st.write(f"🧠 전문가 응답: {answer}")
            if not is_paid_user(email):
                record_usage(email)
