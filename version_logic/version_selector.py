def recommend_version(purpose: str) -> str:
    mapping = {
        "입지만 빠르게 보고 싶어요": "v1",
        "지금 사도 되는 타이밍인가요?": "v2",
        "두 물건을 비교하고 싶어요": "v3",
        "수익률 계산이 궁금해요": "v4",
        "경매 물건 리스크가 걱정돼요": "v4s",
        "손님에게 설명할 보고서가 필요해요": "v5-B"
    }
    return mapping.get(purpose, "v1")
