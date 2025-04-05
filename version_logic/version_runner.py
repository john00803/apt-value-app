import streamlit as st
from modules.auth_manager import is_paid_user

def run_version(version_name, email):
    if version_name in ["v4", "v4s", "v5-B"] and not is_paid_user(email):
        st.warning("이 분석은 유료 구독자 전용입니다.")
        return
    st.subheader(f"{version_name} 분석 결과")
    st.write("기본 분석 결과를 출력합니다.")
    if is_paid_user(email):
        st.success("✅ 전문가 판단 멘트: 이 물건은 중장기 관점에서 안정적인 선택입니다.")
    else:
        st.info("🔒 전문가 판단 멘트는 유료 구독 후 확인 가능합니다.")
