import streamlit as st
import pandas as pd
import openai
import os
import hashlib
from io import BytesIO
from reportlab.pdfgen import canvas

# ------------------
# ✅ 사용자 이메일 기반 인증 (users.csv)
# ------------------
@st.cache_data
def load_user_plan(email):
    try:
        df = pd.read_csv("users.csv")
        user = df[df['email'] == email].iloc[0]
        return user['plan']  # lite, standard, pro 등
    except:
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

user_email = st.sidebar.text_input("이메일을 입력하세요")
user_plan = load_user_plan(user_email) if user_email else None
is_premium_user = user_plan in ["standard", "pro"]

# ------------------
# ✅ 공통 기능: 모든 사용자에게 제공
# ------------------
st.title("\U0001f3e0 아파트 가치 평가 프로그램")
st.write("안녕하세요! 이 앱은 아파트 시세와 분석 정보를 제공합니다.")

apt_name = st.text_input("\U0001f3e2 아파트 이름 입력")
price = st.number_input("\U0001f4b0 현재 시세 (만원)", min_value=0)

if apt_name and price > 0:
    st.subheader("\ud83d\udcca 요약 평가 (v1~v2 기반)")
    st.write(f"`{apt_name}` 의 시세는 {price:,}만원입니다.")

    st.bar_chart({
        "항목": [price, price * 1.05, price * 0.95]
    })

# ------------------
# \ud83d\udd10 유료 사용자 전용 기능
# ------------------
    if is_premium_user:
        st.markdown("---")
        st.subheader("\ud83d\udd10 정밀 분석 (v3~v5 기반)")

        pir = round(price / 6800, 2)  # 예시 평균소득: 6800만원
        irr = round((price * 0.04) / (price * 0.6) * 100, 2)

        st.write("### 투자 지표")
        st.write(f"- PIR: {pir}\n- IRR: {irr}%\n- 보안등급: 중간")

        st.write("### \ud83d\udec1 레이더 차트")
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

        st.write("### \ud83c\udfe8 유사 아파트 비교")
        comparison_df = pd.DataFrame({
            "이름": ["명문아파트", "세계명문"],
            "PIR": [pir + 0.5, pir - 0.3],
            "IRR": [irr - 0.7, irr + 1.2]
        })
        st.dataframe(comparison_df)

        # ------------------
        # \ud83d\udcc4 PDF 생성 및 다운로드 기능
        # ------------------
        def generate_pdf():
            buffer = BytesIO()
            p = canvas.Canvas(buffer)
            p.setFont("Helvetica", 14)
            p.drawString(50, 800, f"아파트 이름: {apt_name}")
            p.drawString(50, 780, f"현재 시세: {price:,}만원")
            p.drawString(50, 760, "요약 브리핑:")
            text = p.beginText(50, 740)
            text.setFont("Helvetica", 12)
            for line in gpt_summary.split('\n'):
                text.textLine(line)
            p.drawText(text)
            p.showPage()
            p.save()
            buffer.seek(0)
            return buffer

        pdf = generate_pdf()
        st.download_button("PDF 보고서 다운로드", data=pdf, file_name="apt_report.pdf")

        st.write("### \ud83d\udc69\u200d\ud83c\udfeb 전문가 총평")
        st.info("\n- '빠숑': 입지 전문가\n- '신성철': 거시경제 전문가\n- '훨훨': 실거주 분석 전문가\n- '당부쌤': 정주여건·수요 흐름 분석가")

    elif user_email:
        st.warning("\ud83d\udd10 이 항목은 유료 구독자에게만 제공됩니다.")
    else:
        st.info("왼쪽 사이드바에 이메일을 입력하면 전체 기능이 활성화됩니다.")
