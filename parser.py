import re

def parse_text_v2(text):
    result = {
        'apt_name': None,
        'size': None,
        'floor': None,
        'direction': None,
        'price': None,
    }

    # 특수문자 및 공백 정리 (OCR 결과 전처리)
    text = re.sub(r'[^가-힣0-9㎡평층억향\s\.]', '', text)
    text = re.sub(r'\s+', ' ', text)

    # ✅ 아파트명 사전 기반 매칭
    known_apts = [
        '초지역메이저타운푸르지오메트로단지',
        '힐스테이트중앙아파트',
        '안산레이크타운푸르지오아파트',
        '안산그랑시티자이2차'
    ]
    for apt in known_apts:
        if apt in text:
            result['apt_name'] = apt
            text = text.replace(apt, '')

    # ✅ 전용면적 (㎡ 또는 평)
    size_match = re.search(r'(\d{2,3}\.?\d*)\s*(㎡|평)', text)
    if size_match:
        result['size'] = size_match.group(1)

    # ✅ 층수 (예: 12층)
    floor_match = re.search(r'(\d{1,3})층', text)
    if floor_match:
        result['floor'] = floor_match.group(1)

    # ✅ 방향 (남향/동향 등)
    dir_match = re.search(r'(남향|동향|서향|북향)', text)
    if dir_match:
        result['direction'] = dir_match.group(1)

    # ✅ 가격 (8.3억, 9억 등)
    price_match = re.search(r'(\d+\.?\d*)\s*억', text)
    if price_match:
        result['price'] = price_match.group(1)

    return result

