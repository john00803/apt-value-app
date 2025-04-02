import streamlit as st
from comparison_utils import compare_v1, compare_v3_gpt, compare_v4s, compare_v5

st.set_page_config(page_title="두 물건 비교 평가", layout="wide")
st.title("📊 두 부동산 물건 비교 평가")

mode = st.selectbox("비교 버전 선택", ["v1/v2", "v3 (GPT 요약문)", "v4s (경매)", "v5 (전문가 점수)"])

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🏠 물건 1")
    if mode == "v1/v2":
        apt1 = st.text_input("아파트명 1")
        price1 = st.number_input("시세 (억)", key="p1")
        size1 = st.number_input("전용면적 (㎡)", key="s1")
        data1 = {"apt_name": apt1, "price": price1, "size": size1}


    elif mode == "v3 (GPT 요약문)":
        summary1 = st.text_area("GPT 요약문 1")

    elif mode == "v4s (경매)":
        app1 = st.number_input("감정가 (만원)", key="a1")
        bid1 = st.number_input("예상 낙찰가 (만원)", key="b1")
        jeonse1 = st.number_input("전세가 (만원)", key="j1")
        fail1 = st.selectbox("유찰횟수", [0,1,2,3,4], key="f1")
        from v4s_auction import analyze_auction
        result1 = analyze_auction(app1, bid1, jeonse1, fail1)

    elif mode == "v5 (전문가 점수)":
        score1 = {
            "교통": st.slider("교통 점수", 0, 5, 3, key="t1"),
            "학군": st.slider("학군 점수", 0, 5, 3, key="a1"),
            "실거주": st.slider("실거주 만족도", 0, 5, 3, key="l1"),
            "투자 안정성": st.slider("투자 안정성", 0, 5, 3, key="i1"),
            "브랜드": st.slider("브랜드/프리미엄", 0, 5, 3, key="b1"),
        }

with col2:
    st.markdown("### 🏠 물건 2")
    if mode == "v1/v2":
        apt2 = st.text_input("아파트명 2")
        price2 = st.number_input("시세 (억)", key="p2")
        size2 = st.number_input("전용면적 (㎡)", key="s2")
        data2 = {"apt_name": apt2, "price": price2, "size": size2}

    elif mode == "v3 (GPT 요약문)":
        summary2 = st.text_area("GPT 요약문 2")

    elif mode == "v4s (경매)":
        app2 = st.number_input("감정가 (만원)", key="a2")
        bid2 = st.number_input("예상 낙찰가 (만원)", key="b2")
        jeonse2 = st.number_input("전세가 (만원)", key="j2")
        fail2 = st.selectbox("유찰횟수", [0,1,2,3,4], key="f2")
        from v4s_auction import analyze_auction
        result2 = analyze_auction(app2, bid2, jeonse2, fail2)

    elif mode == "v5 (전문가 점수)":
        score2 = {
            "교통": st.slider("교통 점수", 0, 5, 3, key="t2"),
            "학군": st.slider("학군 점수", 0, 5, 3, key="a2"),
            "실거주": st.slider("실거주 만족도", 0, 5, 3, key="l2"),
            "투자 안정성": st.slider("투자 안정성", 0, 5, 3, key="i2"),
            "브랜드": st.slider("브랜드/프리미엄", 0, 5, 3, key="b2"),
        }

if st.button("📊 비교 평가 실행"):
    st.markdown("---")
    if mode == "v1/v2":
        st.write(compare_v1(data1, data2))
    elif mode == "v3 (GPT 요약문)":
        st.write(compare_v3_gpt(summary1, summary2))
    elif mode == "v4s (경매)":
        st.json(result1)
        st.json(result2)
        st.success(compare_v4s(result1, result2))
    elif mode == "v5 (전문가 점수)":
        st.write(compare_v5(score1, score2))
