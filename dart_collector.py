import sys
import os
import OpenDartReader
import pandas as pd
import numpy as np
import time
from datetime import datetime
import gspread
import warnings

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

# --- [1. 기본 설정] ---
API_KEY = os.environ.get("DART_API_KEY", "768240de85243c8669d05d18847fd6e456cda53b")
SPREADSHEET_URL = os.environ.get("SPREADSHEET_URL", "https://docs.google.com/spreadsheets/d/1TdpG8tYZd8g8d_AS3zCuE90G7_RVgEmaZtGXYmUHih0/edit")

TRACKER_FILE = "target_150_master.csv"

current_year = datetime.now().year
years = [str(y) for y in range(current_year - 10, current_year)]
future_years = [str(current_year), str(current_year + 1)]

# --- [2. 구글 연동] ---
print("▶ 구글 스프레드시트 인증을 시작합니다 (credentials.json 사용)...")
try:
    gc = gspread.service_account(filename="credentials.json")
except Exception as e:
    print(f"❌ 인증 실패: credentials.json 파일이 없거나 오류가 발생했습니다. ({e})")
    exit(1)

try:
    sh = gc.open_by_url(SPREADSHEET_URL)
    print(f"✅ 스프레드시트 연결 성공")
except Exception as e:
    print(f"❌ 스프레드시트 찾기 실패 ({e})")
    exit(1)

# --- [3. 데이터 수집 및 정제 함수] ---
dart = OpenDartReader(API_KEY)


def extract_account(df, account_nm_list, account_id_list=None, nth_match=0, sj_div=None):
    if df is None or df.empty or 'account_nm' not in df.columns:
        return np.nan

    working_df = df.copy()
    if sj_div is not None and 'sj_div' in working_df.columns:
        if isinstance(sj_div, str):
            sj_div = [sj_div]
        working_df = working_df[working_df['sj_div'].isin(sj_div)]
        if working_df.empty:
            return np.nan

    valid_matches = []

    if account_id_list and 'account_id' in working_df.columns:
        id_mask = working_df['account_id'].astype(str).apply(
            lambda x: any(idx.lower() in x.lower() for idx in account_id_list) if pd.notna(x) else False
        )
        for _, row in working_df[id_mask].iterrows():
            val = str(row.get('thstrm_amount', '')).replace(',', '').strip()
            try:
                num = float(val)
                if num == 0.0 and account_id_list and 'Revenue' in account_id_list:
                    continue
                valid_matches.append(num)
            except ValueError:
                continue

    clean_list = [nm.replace(' ', '') for nm in account_nm_list]
    target = working_df[working_df['account_nm'].astype(str).str.replace(' ', '').isin(clean_list)]
    for _, row in target.iterrows():
        val = str(row.get('thstrm_amount', '')).replace(',', '').strip()
        try:
            valid_matches.append(float(val))
        except ValueError:
            continue

    PARTIAL_MATCH_KEYWORDS = ('차입', '사채', '금융부채', '현금', '유형자산', '영업활동')
    for nm in clean_list:
        if any(kw in nm for kw in PARTIAL_MATCH_KEYWORDS):
            mask = working_df['account_nm'].astype(str).str.replace(' ', '').str.contains(
                nm, case=False, na=False
            )
            for _, row in working_df[mask].iterrows():
                val = str(row.get('thstrm_amount', '')).replace(',', '').strip()
                try:
                    valid_matches.append(float(val))
                except ValueError:
                    continue

    if not valid_matches:
        return np.nan

    seen = set()
    unique_matches = [x for x in valid_matches if not (x in seen or seen.add(x))]
    return unique_matches[min(nth_match, len(unique_matches) - 1)]


def get_10yr_financials(corp_code, target_years):
    all_data = []
    for year in target_years:
        df = None

        for fs_div in ['CFS', 'OFS']:
            try:
                tmp = dart.finstate_all(corp_code, year, reprt_code="11011", fs_div=fs_div)
                if isinstance(tmp, pd.DataFrame) and not tmp.empty:
                    df = tmp
                    break
            except Exception:
                pass

        if not (isinstance(df, pd.DataFrame) and not df.empty):
            try:
                df = dart.finstate(corp_code, year, reprt_code="11011")
            except Exception:
                pass

        if isinstance(df, pd.DataFrame) and not df.empty:
            df['year'] = year
            all_data.append(df)

        time.sleep(0.3)

    results = {
        year: {
            "매출액": np.nan, "영업이익": np.nan, "당기순이익": np.nan, "자산총계": np.nan,
            "부채총계": np.nan, "자기자본": np.nan, "현금성자산": np.nan,
            "단기차입금": np.nan, "장기차입금": np.nan, "영업현금흐름": np.nan, "CAPEX": np.nan
        }
        for year in target_years
    }

    if all_data:
        raw_df = pd.concat(all_data, ignore_index=True)
        for year in raw_df['year'].unique():
            yr_df = raw_df[raw_df['year'] == year]
            results[year] = {
                "매출액": extract_account(
                    yr_df, ['매출액', '영업수익', '수익(매출액)', '이자수익', '영업수익(매출액)'],
                    ['Revenue', 'GrossSales', 'OperatingRevenue'], sj_div=['IS', 'CIS']) / 1e8,
                "영업이익": extract_account(
                    yr_df, ['영업이익(손실)', '영업이익', '영업손익'],
                    ['OperatingIncomeLoss', 'ProfitLossFromOperatingActivities'], sj_div=['IS', 'CIS']) / 1e8,
                "당기순이익": extract_account(
                    yr_df, ['당기순이익(손실)', '당기순이익', '연결당기순이익', '연결분기순이익',
                            '연결반기순이익', '지배기업소유주지분당기순이익', '당기순손익'],
                    ['ProfitLoss'], sj_div=['IS', 'CIS']) / 1e8,
                "자산총계": extract_account(
                    yr_df, ['자산총계'], ['Assets'], sj_div='BS') / 1e8,
                "부채총계": extract_account(
                    yr_df, ['부채총계'], ['Liabilities'], sj_div='BS') / 1e8,
                "자기자본": extract_account(
                    yr_df, ['자본총계', '연결자본총계', '지배기업소유주지분', '자본합계'],
                    ['Equity'], sj_div='BS') / 1e8,
                "현금성자산": extract_account(
                    yr_df, ['현금및현금성자산', '현금및현금등가물', '현금및현금과예치금',
                            '현금과예치금', '현금및예치금', '현금'],
                    ['CashAndCashEquivalents', 'CashAndDeposits'], sj_div='BS') / 1e8,
                "단기차입금": extract_account(
                    yr_df, ['단기차입금', '유동차입금', '단기차입부채', '단기차입금및유동성장기차입금',
                            '유동성장기차입금', '유동성차입금', '단기금융부채', '유동금융부채', '차입부채', '예수금'],
                    ['CurrentBorrowing', 'ShortTermBorrowings', 'Borrowings'], sj_div='BS') / 1e8,
                "장기차입금": extract_account(
                    yr_df, ['장기차입금', '비유동차입금', '비유동차입부채', '사채',
                            '비유동금융부채', '장기금융부채', '장기차입부채'],
                    ['NoncurrentBorrowing', 'LongTermBorrowings', 'Debentures'],
                    nth_match=1, sj_div='BS') / 1e8,
                "영업현금흐름": extract_account(
                    yr_df, ['영업활동현금흐름', '영업활동으로인한현금흐름', '영업활동으로 인한 현금흐름',
                            '영업활동순현금흐름', '영업활동으로인한현금의증가(감소)'],
                    ['CashFlowsFromUsedInOperatingActivities', 'NetCashFlowsFromOperatingActivities'],
                    sj_div='CF') / 1e8,
                "CAPEX": extract_account(
                    yr_df, ['유형자산의취득', '유형자산의증가', '유형자산취득',
                            '유형자산의취득에따른현금유출', '유형자산취득에따른지출', '유형자산및무형자산의취득'],
                    ['PurchaseOfPropertyPlantAndEquipment'], sj_div='CF') / 1e8,
            }

    final_df = pd.DataFrame(results)
    final_df.loc['영업이익률(%)'] = (final_df.loc['영업이익'] / final_df.loc['매출액'].replace(0, np.nan)) * 100
    final_df.loc['순이익률(%)'] = (final_df.loc['당기순이익'] / final_df.loc['매출액'].replace(0, np.nan)) * 100
    final_df.loc['FCF'] = final_df.loc['영업현금흐름'] - final_df.loc['CAPEX'].abs()
    final_df.loc['ROE(%)'] = (final_df.loc['당기순이익'] / final_df.loc['자기자본'].replace(0, np.nan)) * 100
    final_df.loc['ROA(%)'] = (final_df.loc['당기순이익'] / final_df.loc['자산총계'].replace(0, np.nan)) * 100
    final_df.loc['부채비율(%)'] = (final_df.loc['부채총계'] / final_df.loc['자기자본'].replace(0, np.nan)) * 100

    sorted_cols = sorted(final_df.columns)
    final_df = final_df[sorted_cols]
    for fy in future_years:
        final_df[f"{fy}E"] = np.nan

    def calculate_cagr(row):
        hist_row = row.dropna()
        if len(hist_row) < 2:
            return np.nan
        start_val, end_val = hist_row.iloc[0], hist_row.iloc[-1]
        n = len(hist_row) - 1
        if start_val > 0 and end_val > 0 and n > 0:
            return (pow(end_val / start_val, 1 / n) - 1) * 100
        return np.nan

    final_df['CAGR(%)'] = np.nan
    hist_cols = len(sorted_cols)
    for metric in ['매출액', '영업이익', '당기순이익', '자산총계', '자기자본']:
        if metric in final_df.index:
            final_df.loc[metric, 'CAGR(%)'] = calculate_cagr(final_df.loc[metric].iloc[:hist_cols])

    return final_df.round(2)


# --- [4. 메인 실행 루프] ---
if __name__ == '__main__':
    print("\n▶ [10개 종목 자동 배치] 데이터 수집 및 섹터별 시트 적재를 시작합니다...")

    try:
        master_df = pd.read_csv(TRACKER_FILE, dtype={'종목코드': str})
    except FileNotFoundError:
        print(f"❌ '{TRACKER_FILE}' 파일이 없습니다.")
        exit(1)

    master_df['수집완료여부'] = master_df['수집완료여부'].fillna('').astype(str).str.strip()
    pending_df = master_df[master_df['수집완료여부'] != 'O']
    target_df = pending_df.head(10)

    if target_df.empty:
        print("\n🎉 모든 종목 리스트의 수집이 이미 완료되었습니다!")
        exit(0)

    print(f"\n▶ 오늘 목표 수집 타겟 {len(target_df)}개:")
    TARGET_SECTORS = {}
    for _, row in target_df.iterrows():
        sec = str(row['섹터'])
        ticker = str(row['종목코드']).strip().zfill(6)
        print(f"   - {row['기업명']} ({ticker}) : {sec}")
        TARGET_SECTORS.setdefault(sec, []).append({
            "corp_name": row['기업명'], "corp_code": ticker,
            "stock_code": ticker, "row_index": row.name
        })

    for sector, corps in TARGET_SECTORS.items():
        print(f"\n[섹터: {sector}] 진행 중...")
        try:
            ws = sh.worksheet(sector)
        except gspread.exceptions.WorksheetNotFound:
            ws = sh.add_worksheet(title=sector, rows="1000", cols="20")

        for corp in corps:
            corp_name = corp['corp_name']
            corp_code = corp['corp_code']
            ticker = corp['stock_code']
            print(f"  > [{corp_name}] 데이터 추출 중...", end="")

            df = get_10yr_financials(corp_code, years)
            if df.empty:
                print(" ❌ 데이터 없음 (API 한도 또는 미공시)")
                continue

            df_for_gs = df.reset_index().rename(columns={'index': '항목'})
            df_for_gs = df_for_gs.replace([np.inf, -np.inf, np.nan], "")
            corp_header = [[f"[{corp_name} ({ticker})]"] + [""] * (len(df_for_gs.columns) - 1)]
            upload_data = corp_header + [df_for_gs.columns.values.tolist()] + df_for_gs.values.tolist() + [[""], [""]]

            try:
                ws.append_rows(upload_data, value_input_option='USER_ENTERED')
            except gspread.exceptions.APIError as e:
                print(f" ⚠️ Sheets API 오류 ({e}), 10초 후 재시도...")
                time.sleep(10)
                ws.append_rows(upload_data, value_input_option='USER_ENTERED')

            master_df.at[corp['row_index'], '수집완료여부'] = 'O'
            master_df.to_csv(TRACKER_FILE, index=False, encoding='utf-8-sig')
            print(f" ✅ 완료")
            time.sleep(1)

    print("\n🚀 수집 완료. 내일 재실행 시 미수집 종목이 자동으로 이어집니다.")
