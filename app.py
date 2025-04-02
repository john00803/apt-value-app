import streamlit as st
import openai
import os
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas

from usage_tracker import load_user_plan, increment_usage, is_usage_exceeded
from gpt_module import gpt_fix_ocr_text
from apt_parser import parse_text_v2  # ⚠️ parser.py가 아니라 apt_parser.py여야 합니다

# ✅ UI 시작
st.set_page_config(page_title="🏠 아파트 가치 평가", layout="centered")
st.title("🏡 아파트 가치 평가 프로그램")
st.write("텍스트를 직접 입력하면 GPT가 분석 후 자동으로 시세 정보를 추출합니다.")

# ✅ 사용자 요금제
user_email = st.sidebar.text_input("📧 이메일을 입력하세요")
user_plan = load_user_plan(user_email) if user_email else None
is_premium_user = user_plan in ["standard", "pro"]
gpt_answer = None

# ✅ 텍스트 입력 (이미지 OCR 제거)
user_input = st.text_area(
    "📄 부동산 정보 텍스트 입력",
    placeholder="예: 반포자이84㎡ 23억 10층 남향",
    height=100
)

if st.button("📊 분석하기") and user_input:
    openai.api_key = os.getenv("OPENAI_API_KEY")

    if openai.api_key:
        exceeded, used, limit = is_usage_exceeded(user_email, user_plan or "free")
        if exceeded:
            st.warning(f"'{user_plan}' 플랜은 하루 {limit}회까지만 질문할 수 있어요. (현재 {used}회 사용)")
        else:
            # ✅ GPT 보정
            fixed_text = gpt_fix_ocr_text(user_input)
            st.subheader("🔧 GPT 보정 결과")
            st.code(fixed_text)

            # ✅ 텍스트 파싱
            parsed_data = parse_text_v2(fixed_text)
            st.subheader("📌 자동 분석 결과")
            st.json(parsed_data)

            # ✅ GPT 요약 응답
            question = f"{parsed_data['apt_name']} 아파트의 투자 가치는 어떤가요?"
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "너는 부동산 투자 조언 전문가야."},
                    {"role": "user", "content": question}
                ]
            )
            gpt_answer = response.choices[0].message.content.strip()
            st.subheader("💬 GPT 분석")
            st.success(gpt_answer)
            increment_usage(user_email)
    else:
        st.error("OpenAI API 키가 누락되어 있습니다.")

# ✅ PDF 저장
if gpt_answer and st.button("📄 PDF로 저장"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.setFont("Helvetica", 12)
    c.drawString(50, 800, f"아파트 가치 평가 리포트 - {parsed_data['apt_name']}")
    c.drawString(50, 780, f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    text_obj = c.beginText(50, 750)
    for line in gpt_answer.split('\n'):
        text_obj.textLine(line)
    c.drawText(text_obj)
    c.showPage()
    c.save()

    st.download_button(
        label="PDF 다운로드",
        data=buffer.getvalue(),
        file_name=f"{parsed_data['apt_name']}_GPT분석.pdf",
        mime="application/pdf"
    )
