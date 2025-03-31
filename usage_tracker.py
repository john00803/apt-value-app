import pandas as pd
import os
from datetime import datetime

USERS_CSV = "users.csv"
USAGE_CSV = "gpt_usage.csv"

def load_user_plan(email):
    """사용자 요금제 로드 (없으면 'free' 반환)"""
    if not os.path.exists(USERS_CSV):
        return "free"
    df = pd.read_csv(USERS_CSV)
    row = df[df['email'] == email]
    return row.iloc[0]['plan'] if not row.empty else "free"

def increment_usage(email):
    """사용량 +1"""
    today = datetime.today().strftime("%Y-%m-%d")
    if os.path.exists(USAGE_CSV):
        df = pd.read_csv(USAGE_CSV)
    else:
        df = pd.DataFrame(columns=["email", "date", "count"])

    row = df[(df["email"] == email) & (df["date"] == today)]
    if not row.empty:
        idx = row.index[0]
        df.at[idx, "count"] += 1
    else:
        df = pd.concat([df, pd.DataFrame([{"email": email, "date": today, "count": 1}])], ignore_index=True)

    df.to_csv(USAGE_CSV, index=False)

def is_usage_exceeded(email, plan):
    """요금제별 사용량 제한 검사"""
    plan_limits = {
        "free": 5,
        "standard": 20,
        "pro": 50
    }
    limit = plan_limits.get(plan, 5)
    today = datetime.today().strftime("%Y-%m-%d")

    if os.path.exists(USAGE_CSV):
        df = pd.read_csv(USAGE_CSV)
        row = df[(df["email"] == email) & (df["date"] == today)]
        used = int(row.iloc[0]['count']) if not row.empty else 0
    else:
        used = 0

    return used >= limit, used, limit
