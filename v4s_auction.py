st.subheader("🏦 경매 분석 (v4s)")
감정가 = st.number_input("감정가", ...)
낙찰가 = st.number_input("예상 낙찰가", ...)
전세가 = st.number_input("전세가", ...)
유찰횟수 = st.selectbox("유찰 횟수", [0,1,2,3,4])

GAP = 낙찰가 - 전세가
전세가율 = 전세가 / 낙찰가 * 100

위험도 = "높음" if GAP > 2 or 전세가율 < 70 else "보통"

st.metric("GAP", f"{GAP:.2f}억")
st.metric("전세가율", f"{전세가율:.1f}%")
st.warning("⚠️ 위험: 유찰 1회 이하") if 유찰횟수 <= 1 else st.success("유찰 안정권")
