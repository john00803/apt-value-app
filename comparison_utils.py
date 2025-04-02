# 비교 유틸리티 모듈 (v1, v2, v3, v4s, v5 비교 포함)

def compare_v1(data1: dict, data2: dict) -> str:
    """v1 & v2 공용: 시세, 평수, 층수, 방향 등 비교"""
    price1 = data1.get("price", 0)
    price2 = data2.get("price", 0)
    size1 = int(data1.get("size", 0))
    size2 = int(data2.get("size", 0))

    cheaper = "물건 1" if price1 < price2 else "물건 2"
    bigger = "물건 1" if size1 > size2 else "물건 2"

    return f"\n- 시세는 {cheaper}가 저렴하고,\n- 면적은 {bigger}가 더 넓습니다.\n\n종합적으로 {cheaper}를 추천합니다."

def compare_v3_gpt(summary1: str, summary2: str) -> str:
    """v3 GPT 브리핑 비교: GPT 요약 텍스트 기반 간접 평가"""
    from difflib import SequenceMatcher
    ratio = SequenceMatcher(None, summary1, summary2).ratio()
    return f"\n📘 요약문 유사도: {ratio * 100:.1f}%\n\n요약문 내용을 바탕으로 사용자가 판단하는 것이 가장 적절합니다."

def compare_v4s(result1: dict, result2: dict) -> str:
    """v4s: GAP, 전세가율, 유찰횟수 등 비교"""
    gap1 = int(result1['GAP'].replace(",", "").replace("만원", ""))
    gap2 = int(result2['GAP'].replace(",", "").replace("만원", ""))
    rate1 = float(result1['전세가율'].replace("%", ""))
    rate2 = float(result2['전세가율'].replace("%", ""))
    risk1 = result1['위험도']
    risk2 = result2['위험도']

    better = "물건 1" if (gap1 < gap2 and rate1 > rate2 and risk1 != "높음") else "물건 2"

    return f"\n- GAP: 물건1={gap1}만원, 물건2={gap2}만원\n- 전세가율: 물건1={rate1}%, 물건2={rate2}%\n- 위험도: 물건1={risk1}, 물건2={risk2}\n\n→ 종합 추천: {better}"

def compare_v5(score1: dict, score2: dict) -> str:
    """v5: 전문가 평가 점수 비교"""
    total1 = sum(score1.values())
    total2 = sum(score2.values())
    diff = abs(total1 - total2)
    better = "물건 1" if total1 > total2 else "물건 2"

    return f"\n- 총점 비교: 물건1={total1}, 물건2={total2}\n→ {better}가 약 {diff}점 높습니다. 추천: {better}"
