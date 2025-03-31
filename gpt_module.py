import openai
import streamlit as st

def gpt_fix_ocr_text(raw_ocr):
    if not openai.api_key:
        return raw_ocr

    st.write("\U0001F50D GPT 입력 텍스트:")
    st.code(raw_ocr)

    cleaned_ocr = raw_ocr.encode("utf-8", errors="ignore").decode("utf-8")

    prompt = f"""다음은 OCR로 인식된 부정확한 텍스트입니다. 사람이 이해할 수 있도록 실제 부동산 문장으로 고쳐줘.\n텍스트: {cleaned_ocr}"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "너는 부동산 OCR 보정 전문가야."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()
