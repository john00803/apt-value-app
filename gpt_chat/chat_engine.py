import openai
import streamlit as st

def get_response(prompt: str) -> str:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 부동산 분석 전문가입니다."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ 오류 발생: {str(e)}"
