import streamlit as st

st.title("아파트 가치 평가 프로그램")
st.write("안녕하세요, 이 앱은 아파트 분석 프로그램입니다!")

apt_name = st.text_input("아파트 이름을 입력하세요")
apt_price = st.number_input("현재 시세 (만원 단위)", step=10)

if apt_name and apt_price:
    st.success(f"{apt_name}의 예상 가치는 {apt_price * 1.05:.0f}만 원입니다.")
