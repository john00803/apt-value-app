import streamlit as st

def show_initial_screen():
    st.markdown("## 분석 목적을 선택해주세요")
    option = st.radio("분석 목적", [
        "입지만 빠르게 보고 싶어요",
        "지금 사도 되는 타이밍인가요?",
        "두 물건을 비교하고 싶어요",
        "수익률 계산이 궁금해요",
        "경매 물건 리스크가 걱정돼요",
        "손님에게 설명할 보고서가 필요해요"
    ])
    if st.button("선택 완료"):
        return option
 def show_initial_screen():
    st.markdown("## 🏠 아파트 가치 평가 프로그램 – 버전 선택 가이드")
    st.info("아래 목적에 따라 가장 적합한 분석 버전을 선택하세요.")

    version_descriptions = {
        "입지만 빠르게 보고 싶어요": "📍 v1 – 연식 보정 입지 점수만 빠르게 확인",
        "지금 사도 되는 타이밍인가요?": "⏳ v2 – 실거래·정책 포함 시점 판단",
        "두 물건을 비교하고 싶어요": "📊 v3 – 항목별 비교 + 전문가 결론",
        "수익률 계산이 궁금해요": "💰 v4 – 수익률 중심 투자 시뮬",
        "경매 물건 리스크가 걱정돼요": "⚠️ v4s – 유찰·전세가율 중심 위험 평가",
        "손님에게 설명할 보고서가 필요해요": "🧾 v5-B – 전문가 브리핑용 리포트 생성"
    }

    for label, desc in version_descriptions.items():
        st.radio("", [f"{desc}"], key=label)
    
    choice = st.radio("🧭 분석 목적을 선택하세요", list(version_descriptions.keys()), index=0)
    if st.button("🔍 분석 시작"):
        return choice
    return None

 return None
