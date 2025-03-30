import streamlit as st
import pandas as pd
import openai
import os
import hashlib
import re
from io import BytesIO
from reportlab.pdfgen import canvas
from PIL import Image
import pytesseract
import cv2
import numpy as np

# ✅ Tesseract 경로 설정 (로컬 실행 시)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ✅ 사용자 이메일 기반 인증 (users.csv)
@st.cache_data
def load_user_plan(email):
    try:
        df = pd.read_csv("users.csv")
        user = df[df['email'] == email].iloc[0]
        return user['plan']
    except:
        return None

# ✅ GPT 사용 기록

def increment_usage(email):
    try:
        df = pd.read_csv("gpt_usage.csv")
    except:
        df = pd.DataFrame(columns=["email", "count"])
    if email in df.email.values:
        df.loc[df.email == email, "count"] += 1
    else:
        df = pd.concat([df, pd.DataFrame([[email, 1]], columns=["email", "count"])], ignore_index=True)
    df.to_csv("gpt_usage.csv", index=False)

def get_usage_count(email):
    try:
        df = pd.read_csv("gpt_usage.csv")
        return int(df[df.email == email]["count"].values[0])
    except:
        return 0

# ✅ OCR 전처리

def preprocess_for_ocr(image_file):
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
    blurred = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 31, 15)
    return thresh

# ✅ OCR 추출

def extract_text_from_image(image_file) -> str:
    processed_img = preprocess_for_ocr(image_file)
    pil_img = Image.fromarray(processed_img)
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(pil_img, lang='kor+eng', config=config)
    return text

# ✅ OCR 보정 with GPT
@st.cache_data(show_spinner="GPT 보정 중...")
def gpt_fix_ocr_text(raw_ocr):
    if not openai.api_key:
        return raw_ocr
    prompt = f"""다음은 OCR로 인식된 부정확한 텍스트입니다. 사람이 이해할 수 있도록 실제 부동산 문장으로 고쳐줘.\n텍스트: {raw_ocr}"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "너는 부동산 OCR 보정 전문가야."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# ✅ OCR 파싱

def parse_ocr_text(ocr_text):
    name_pattern = r"^(.*?)(?=\s*매[매메])"
    nm = re.search(name_pattern, ocr_text)
    apt_name = nm.group(1).strip() if nm else None

    price_pattern = r"(\d+)\s*억\s*(\d{1,3}(?:[.,]?\d{3})?)"
    match_price = re.search(price_pattern, ocr_text)
    price_val = 0
    if match_price:
        main_val = float(match_price.group(1))
        sub_val = match_price.group(2).replace(",", "").replace(".", "")
        sub_val = float(sub_val) if sub_val else 0
        price_val = int(main_val * 10000 + sub_val)

    return apt_name, price_val

# ✅ 이메일 인증 및 UI
user_email = st.sidebar.text_input("이메일을 입력하세요")
user_plan = load_user_plan(user_email) if user_email else None
is_premium_user = user_plan in ["standard", "pro"]

st.title("\U0001F3E0 아파트 가치 평가 프로그램")
st.write("안녕하세요! 이 앱은 아파트 시세와 분석 정보를 제공합니다.")

uploaded_image = st.file_uploader("아파트 정보 이미지 업로드 (매매, 평수 포함)", type=["png", "jpg", "jpeg"])
if uploaded_image:
    image_bytes = uploaded_image.read()
    extracted_text = extract_text_from_image(BytesIO(image_bytes))
    st.write("**OCR 추출 결과:**")
    st.code(extracted_text)

    openai.api_key = os.getenv("OPENAI_API_KEY")
    fixed_text = gpt_fix_ocr_text(extracted_text)
    st.write("**GPT 보정 결과:**")
    st.code(fixed_text)

    apt_name_parsed, price_parsed = parse_ocr_text(fixed_text)
    if apt_name_parsed and price_parsed:
        st.success(f"자동 인식 - 아파트명: {apt_name_parsed}, 시세: {price_parsed}만원")
        if st.button("분석하기 (OCR 결과 반영)"):
            st.session_state["apt_name"] = apt_name_parsed
            st.session_state["price"] = price_parsed
    else:
        st.warning("OCR + GPT 결과에서도 아파트명이나 시세를 인식하지 못했습니다.")

apt_name = st.text_input("\U0001F3E2 아파트 이름 입력", key="apt_name")
price = st.number_input("\U0001F4B0 현재 시세 (만원)", min_value=0, key="price")

if apt_name and price > 0:
    st.subheader("\U0001F4CA 요약 평가 (v1~v2 기반)")
    st.write(f"`{apt_name}` 의 시세는 {price:,}만원입니다.")
    st.bar_chart({"항목": [price, price * 1.05, price * 0.95]})

    # ✅ 질의응답 모듈
    st.markdown("---")
    st.subheader("\U0001F4AC GPT 질의응답")
    sample_questions = [
        f"{apt_name} 아파트는 투자 가치가 있나요?",
        f"{apt_name}의 시세는 앞으로 어떻게 될까요?",
        f"{apt_name}의 실거주 만족도는 어떤가요?"
    ]
    question = st.selectbox("자동 질문 예시 또는 직접 입력:", sample_questions + ["직접 입력"])
    user_question = st.text_input("질문을 입력하세요") if question == "직접 입력" else question

    if st.button("질문하기") and user_question:
        if openai.api_key:
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
            st.error("OpenAI API 키가 누락되어 있습니다.")


