import pandas as pd
from datetime import datetime

def check_usage(email, limit=2):
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        df = pd.read_csv("data/gpt_usage.csv")
    except FileNotFoundError:
        return True
    user_today = df[(df["email"] == email) & (df["date"] == today)]
    count = int(user_today["count"].values[0]) if not user_today.empty else 0
    return count < limit

def record_usage(email):
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        df = pd.read_csv("data/gpt_usage.csv")
    except FileNotFoundError:
        df = pd.DataFrame(columns=["email", "date", "count"])
    idx = df[(df["email"] == email) & (df["date"] == today)].index
    if len(idx) > 0:
        df.loc[idx[0], "count"] += 1
    else:
        df = df.append({"email": email, "date": today, "count": 1}, ignore_index=True)
    df.to_csv("data/gpt_usage.csv", index=False)
