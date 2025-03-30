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

    pyeong_pattern = r"(\d+(?:\.\d+)?)\s*py"
    match_pyeong = re.search(pyeong_pattern, ocr_text)
    pyeong_val = float(match_pyeong.group(1)) if match_pyeong else None

    floor_pattern = r"(\d+/\d+)\s*층"
    match_floor = re.search(floor_pattern, ocr_text)
    floor_val = match_floor.group(1) if match_floor else None

    direction_pattern = r"([동서남북]{1,2}향)"
    match_direction = re.search(direction_pattern, ocr_text)
    direction_val = match_direction.group(1) if match_direction else None

    return apt_name, price_val, pyeong_val, floor_val, direction_val

# ✅ 이메일 인증 및 UI
user_email = st.sidebar.text_input("이메일을 입력하세요")
user_plan = load_user_plan(user_email) if user_email else None
is_premium_user = user_plan in ["standard", "pro"]

st.title("\U0001F3E0 아파트 가치 평가 프로그램")
st.write("안녕하세요! 이 앱은 아파트 시세와 분석 정보를 제공합니다.")

# ✅ 이미지 업로드 & 분석
uploaded_image = st.file_uploader("아파트 정보 이미지 업로드 (매매, 평수, 층수, 방향 포함)", type=["png", "jpg", "jpeg"])
if uploaded_image:
    image_bytes = uploaded_image.read()
    extracted_text = extract_text_from_image(BytesIO(image_bytes))
    st.write("**OCR 추출 결과:**")
    st.write(extracted_text)
    apt_name_parsed, price_parsed, pyeong_parsed, floor_parsed, direction_parsed = parse_ocr_text(extracted_text)
    if apt_name_parsed and price_parsed:
        st.success(f"자동 인식 - 아파트명: {apt_name_parsed}, 시세: {price_parsed}만원")
        if pyeong_parsed:
            st.success(f"평수: {pyeong_parsed}py")
        if floor_parsed:
            st.success(f"층수: {floor_parsed}")
        if direction_parsed:
            st.success(f"방향: {direction_parsed}")
    else:
        st.warning("OCR 결과에서 아파트명이나 시세를 인식하지 못했습니다.")
    if st.button("분석하기 (OCR 결과 반영)"):
        if apt_name_parsed:
            st.session_state["apt_name"] = apt_name_parsed
        if price_parsed:
            st.session_state["price"] = price_parsed

apt_name = st.text_input("\U0001F3E2 아파트 이름 입력", key="apt_name")
price = st.number_input("\U0001F4B0 현재 시세 (만원)", min_value=0, key="price")

if apt_name and price > 0:
    st.subheader("\U0001F4CA 요약 평가 (v1~v2 기반)")
    st.write(f"`{apt_name}` 의 시세는 {price:,}만원입니다.")
    st.bar_chart({"항목": [price, price * 1.05, price * 0.95]})

    if is_premium_user:
        st.markdown("---")
        st.subheader("\U0001F512 정밀 분석 (v3~v5 기반)")
        pir = round(price / 6800, 2)
        irr = round((price * 0.04) / (price * 0.6) * 100, 2)
        st.write("### 투자 지표")
        st.write(f"- PIR: {pir}\n- IRR: {irr}%\n- 보안등급: 중간")

        st.write("### \U0001F4E1 레이더 차트")
        st.radar_chart({"분석요소": [80, 70, 90]})

        openai.api_key = os.getenv("OPENAI_API_KEY")

        def generate_cache_key(prompt):
            key_base = f"{apt_name}_{price}_{user_email}"
            return hashlib.md5(key_base.encode()).hexdigest()

        @st.cache_data(show_spinner="GPT 브리핑 캐싱 중...")
        def get_cached_gpt_summary(prompt, key):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "너는 부동산 투자 분석 전문가야."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()

        if openai.api_key:
            if user_plan == "standard" and get_usage_count(user_email) >= 5:
                st.warning("GPT 사용 한도를 초과했습니다. (일 5회)")
            else:
                prompt = f"{apt_name} 아파트의 시세는 {price}만원일 때, 요약 분석을 해줘."
                cache_key = generate_cache_key(prompt)
                gpt_summary = get_cached_gpt_summary(prompt, cache_key)
                st.success(gpt_summary)
                increment_usage(user_email)
        else:
            st.error("OpenAI API 키가 설정되지 않았습니다.")

        st.write("### \U0001F3E3 유사 아파트 비교")
        comparison_df = pd.DataFrame({
            "이름": ["명문아파트", "세계명문"],
            "PIR": [pir + 0.5, pir - 0.3],
            "IRR": [irr - 0.7, irr + 1.2]
        })
        st.dataframe(comparison_df)

        def generate_pdf():
            buffer = BytesIO()
            p = canvas.Canvas(buffer)
            p.setFont("Helvetica", 14)
            p.drawString(50, 800, f"아파트 이름: {apt_name}")
            p.drawString(50, 780, f"현재 시세: {price:,}만원")
            p.drawString(50, 760, "요약 브리핑:")
            text = p.beginText(50, 740)
            p.setFont("Helvetica", 12)
            for line in gpt_summary.split('\n'):
                text.textLine(line)
            p.drawText(text)
            p.showPage()
            p.save()
            buffer.seek(0)
            return buffer

        pdf = generate_pdf()
        st.download_button("PDF 보고서 다운로드", data=pdf, file_name="apt_report.pdf")

        st.write("### \U0001F469‍\U0001F3EB 전문가 총평")
        st.info("- '빠숑': 입지 전문가\n- '신성철': 거시경제 전문가\n- '훨훨': 실거주 분석 전문가\n- '당부쌤': 정주여건·수요 흐름 분석가")

        # ✅ 추가 GPT 질의응답 영역
        with st.expander("💬 GPT에게 추가 질문하기"):
            user_question = st.text_area("질문을 입력하세요 (예: 이 아파트 투자 괜찮을까요?)")
            if st.button("GPT에게 질문"):
                if user_question and openai.api_key:
                    full_prompt = f"[{apt_name}] 아파트 시세는 {price}만원입니다. 사용자 질문: {user_question}"
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "너는 부동산 투자 분석 전문가야."},
                            {"role": "user", "content": full_prompt}
                        ]
                    )
                    st.success(response.choices[0].message.content.strip())

    elif user_email:
        st.warning("\U0001F512 이 항목은 유료 구독자에게만 제공됩니다.")
    else:
        st.info("왼쪽 사이드바에 이메일을 입력하면 전체 기능이 활성화됩니다.")


