import streamlit as st
import os
import openai
import pandas as pd
from io import BytesIO

from usage_tracker import load_user_plan, increment_usage, is_usage_exceeded
from ocr_utils import extract_text_from_image
from gpt_module import gpt_fix_ocr_text
from parser import parse_text_v2

# ✅ 사이드바에서 사용자 이메일 입력
user_email = st.sidebar.text_input("이메일을 입력하세요")
user_plan = load_user_plan(user_email) if user_email else None

st.info("앱이 로드되는 동안 잠시 기다려 주세요.")
st.title("🏠 아파트 가치 평가 프로그램")
st.write("이미지를 업로드하면 자동으로 시세 정보를 추출합니다.")

# 이미지 업로드
uploaded_image = st.file_uploader("이미지 업로드 (png, jpg, jpeg)", type=["png", "jpg", "jpeg"])

if uploaded_image:
    image_bytes = uploaded_image.read()
    extracted_text = extract_text_from_image(BytesIO(image_bytes))
    st.write("**OCR 추출 결과:**")
    st.code(extracted_text)
    
    # OpenAI API 키 설정 (환경 변수에 등록되어 있어야 함)
    openai.api_key = os.getenv("OPENAI_API_KEY")
    fixed_text = gpt_fix_ocr_text(extracted_text)
    st.write("**GPT 보정 결과:**")
    st.code(fixed_text)
    
    parsed_data = parse_text_v2(fixed_text)
    st.success(f"자동 인식 결과: {parsed_data}")
    
    # 사용자가 직접 수정할 수 있도록 기본값 채워진 입력폼 제공
    apt_name = st.text_input("아파트 이름", value=parsed_data.get('apt_name', ''))
    size = st.text_input("전용면적 (㎡)", value=parsed_data.get('size', ''))
    floor = st.text_input("층수", value=parsed_data.get('floor', ''))
    direction = st.text_input("방향", value=parsed_data.get('direction', ''))
    price = st.number_input("현재 시세 (억)", min_value=0.0, value=float(parsed_data.get('price', 0)), step=0.1)
    
    if apt_name and price > 0:
        st.subheader("요약 평가")
        st.write(f"`{apt_name}`의 시세는 **{price:.1f}억**입니다.")
        st.bar_chart({"항목": [price, price * 1.05, price * 0.95]})
        
        st.markdown("---")
        st.subheader("GPT 질의응답")
        sample_questions = [
            f"{apt_name} 아파트는 투자 가치가 있나요?",
            f"{apt_name}의 시세는 앞으로 어떻게 될까요?",
            f"{apt_name}의 실거주 만족도는 어떤가요?"
        ]
        question = st.selectbox("질문 선택", sample_questions + ["직접 입력"])
        user_question = st.text_input("질문 입력") if question == "직접 입력" else question
        
        if st.button("질문하기") and user_question:
            if openai.api_key:
                plan = user_plan or "free"
                exceeded, used, limit = is_usage_exceeded(user_email, plan)
                if exceeded:
                    st.warning(f"'{plan}' 플랜은 하루 {limit}회까지만 질문 가능합니다. (현재 {used}회 사용)")
                else:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "너는 부동산 분석 및 투자 조언 전문가야."},
                            {"role": "user", "content": user_question}
                        ]
                    )
                    st.success(response.choices[0].message.content.strip())
                    increment_usage(user_email)
            else:
                st.error("OpenAI API 키가 누락되었습니다.")
