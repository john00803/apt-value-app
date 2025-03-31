import re

def parse_text_v2(text: str) -> dict:
    """
    OCR + GPT 보정 텍스트에서 아파트 이름, 시세(억), 평수, 층수, 방향 등을 추출
    """
    result = {
        "apt_name": None,
        "price": None,
        "size": None,
        "floor": None,
        "direction": None
    }

    # ✅ 아파트 이름: "푸르지오", "힐스테이트" 등
    apt_pattern = r"([가-힣A-Za-z0-9\s]+)(?:아파트|APT|주상복합|단지)"
    apt_match = re.search(apt_pattern, text)
    if apt_match:
        result["apt_name"] = apt_match.group(1).strip()

    # ✅ 시세: "8억 5,000", "10억" 등
    price_pattern = r"(\d{1,2})\s*억\s*([0-9,]*)"
    price_match = re.search(price_pattern, text)
    if price_match:
        uk = int(price_match.group(1))
        man = price_match.group(2).replace(",", "")
        man = int(man) if man else 0
        result["price"] = uk + man / 10000

    # ✅ 전용면적: "84㎡", "전용 59" 등
    size_pattern = r"(?:전용)?\s*(\d{2,3})\s*㎡?"
    size_match = re.search(size_pattern, text)
    if size_match:
        result["size"] = size_match.group(1)

    # ✅ 층수: "15층", "고층", "중층", "저층"
    floor_pattern = r"(\d{1,3})\s*층|고층|중층|저층"
    floor_match = re.search(floor_pattern, text)
    if floor_match:
        result["floor"] = floor_match.group(0).strip()

    # ✅ 방향: 남향, 남서향, 동향 등
    direction_pattern = r"(남향|남서향|남동향|동향|서향|북향)"
    dir_match = re.search(direction_pattern, text)
    if dir_match:
        result["direction"] = dir_match.group(1)

    return result



