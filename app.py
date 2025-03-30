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

# ------------------
# ✅ 사용자 이메일 기반 인증 (users.csv)
# ------------------
@st.cache_data
def load_user_plan(email):
    try:
        df = pd.read_csv("users.csv")
        user = df[df['email'] == email].iloc[0]
        return user['plan']  # lite, standard, pro 등
    except Exception as e:
        return None

# ------------------
# ✅ GPT 사용 기록 저장/불러오기 (gpt_usage.csv)
# ------------------
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

# ------------------
# ✅ OCR: 이미지에서 텍스트 추출
# ------------------
def extract_text_from_image(image_file) -> str:
    img = Image.open(image_file)
    # pytesseract를 사용해 OCR 수행 (한글+영어)
    text = pytesseract.image_to_string(img, lang='kor+eng')
    return text

def parse_ocr_text(ocr_text):
    """
    OCR 텍스트에서 '아파트명'과 '시세'를 추출하는 예시 함수.
    예시: "아파트명: 센트럴팰리스, 시세: 12345만 원"
    """
    apt_pattern = r"아파트명\s*[:：]\s*([^\s,]+)"
    price_pattern = r"시세\s*[:：]\s*(\d+)"
    
    apt_match = re.search(apt_pattern, ocr_text)
    price_match = re.search(price_pattern, ocr_text)
    
    apt_name = apt_match.group(1) if apt_match else None
    price_str = price_match.group(1) if price_match else None
    price_val = int(price_str) if price_str and price_str.isdigit() else 0
    
    return apt_name, price_val

# ------------------
# 사이드바: 이메일 입력 및 사용자 구독 플랜 확인
# ------------------
user_email = st.sidebar.text_input("이메일을 입력하세요")
user_plan = load_user_plan(user_email) if user_email else None
is_premium_user = user_plan in ["standard", "pro"]

# ------------------
# 앱 메인: 기본 UI 구성
# ------------------
st.title("🏠 아파트 가치 평가 프로그램")
st.write("안녕하세요! 이 앱은 아파트 시세와 분석 정보를 제공합니다.")

# ------------------
# 이미지 업로드 + OCR 처리 및 분석하기 버튼
# ------------------
uploaded_image = st.file_uploader("아파트 정보 이미지 업로드 (시세, 이름 포함)", type=["png", "jpg", "jpeg"])
if uploaded_image:
    extracted_text = extract_text_from_image(uploaded_image)
    st.write("**OCR 추출 결과:**")
    st.write(extracted_text)
    # OCR 결과에서 아파트명과 시세 자동 파싱
    apt_name_parsed, price_parsed = parse_ocr_text(extracted_text)
    if apt_name_parsed and price_parsed:
        st.success(f"자동 인식 - 아파트명: {apt_name_parsed}, 시세: {price_parsed}만원")
    else:
        st.warning("OCR 결과에서 아파트명이나 시세를 인식하지 못했습니다.")
    # '분석하기' 버튼을 눌러 OCR 결과를 입력란에 반영
    if st.button("분석하기 (OCR 결과 반영)"):
        if apt_name_parsed:
            st.session_state["apt_name"] = apt_name_parsed
        if price_parsed:
            st.session_state["price"] = price_parsed

# ------------------
# 텍스트로 직접 입력 (세션 상태와 연동)
# ------------------
apt_name = st.text_input("🏢 아파트 이름 입력", key="apt_name")
price = st.number_input("💰 현재 시세 (만원)", min_value=0, key="price")

if apt_name and price > 0:
    st.subheader("📊 요약 평가 (v1~v2 기반)")
    st.write(f"`{apt_name}` 의 시세는 {price:,}만원입니다.")
    st.bar_chart({
        "항목": [price, price * 1.05, price * 0.95]
    })

    # ------------------
    # 🔒 유료 사용자 전용 기능
    # ------------------
    if is_premium_user:
        st.markdown("---")
        st.subheader("🔒 정밀 분석 (v3~v5 기반)")
        
        # 추가 분석: PIR 및 IRR 계산 (예시)
        pir = round(price / 6800, 2)  # 예: 평균 소득 6800만원 기준
        irr = round((price * 0.04) / (price * 0.6) * 100, 2)
        
        st.write("### 투자 지표")
        st.write(f"- PIR: {pir}\n- IRR: {irr}%\n- 보안등급: 중간")
        
        st.write("### 📡 레이더 차트")
        st.radar_chart({
            "분석요소": [80, 70, 90]
        })
        
        # ------------------
        # 🧠 GPT 요약 브리핑 (캐싱 포함)
        # ------------------
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
        
        st.write("### 🏘 유사 아파트 비교")
        comparison_df = pd.DataFrame({
            "이름": ["명문아파트", "세계명문"],
            "PIR": [pir + 0.5, pir - 0.3],
            "IRR": [irr - 0.7, irr + 1.2]
        })
        st.dataframe(comparison_df)
        
        # ------------------
        # 📄 PDF 생성 및 다운로드 기능
        # ------------------
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
        
        st.write("### 👩‍🏫 전문가 총평")
        st.info("\n- '빠숑': 입지 전문가\n- '신성철': 거시경제 전문가\n- '훨훨': 실거주 분석 전문가\n- '당부쌤': 정주여건·수요 흐름 분석가")
    
    elif user_email:
        st.warning("🔒 이 항목은 유료 구독자에게만 제공됩니다.")
    else:
        st.info("왼쪽 사이드바에 이메일을 입력하면 전체 기능이 활성화됩니다.")

# 함수: GPT 사용 기록 관련
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

