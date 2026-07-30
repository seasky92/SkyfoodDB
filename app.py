import streamlit as st
import pandas as pd
import random
from collections import Counter
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="로또 패턴 분석기", layout="wide")

# 주소를 직접 넣었습니다!
SHEET_URL = "https://docs.google.com/spreadsheets/d/1tW8KwjFh9PZEoLxNyoiboi_UFc9CRFX0tIj0pdIqGf4/edit?usp=drivesdk"

creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(creds)

@st.cache_data(ttl=5)
def load_data():
    sheet = client.open_by_url(SHEET_URL).sheet1
    data = sheet.get_all_values()
    parsed = []
    for row in data[1:]:
        if row and row[0]: 
            try:
                parsed.append([int(str(x).replace(',', '').strip()) for x in row[:8]])
            except: continue
    return sorted(parsed, key=lambda x: x[0])

data = load_data()

# 패턴 계산 로직 (기존 유지)
pattern_data = []
for i in range(4, len(data)):
    curr = data[i]
    prev4 = data[i-4:i]
    appeared = [n for d in prev4 for n in d[1:7]]
    freq = Counter(appeared)
    c0 = sum(1 for n in curr[1:7] if freq[n] == 0)
    c1 = sum(1 for n in curr[1:7] if freq[n] == 1)
    c2 = sum(1 for n in curr[1:7] if freq[n] >= 2)
    pattern_data.append({"회차": curr[0], "패턴": f"{c0}:{c1}:{c2}"})

df_patterns = pd.DataFrame(pattern_data)

st.title("🎯 로또 패턴 분석 및 추천")

# 1. 랜덤 추천
st.subheader("🎲 인기 패턴 기반 랜덤 추천")
pattern_counts = df_patterns['패턴'].value_counts()
selected_p = st.selectbox("패턴 선택", ["전체 패턴 중 랜덤"] + list(pattern_counts.index))

if st.button("행운 번호 추천받기"):
    p_str = random.choices(list(pattern_counts.index), weights=pattern_counts.values)[0] if "랜덤" in selected_p else selected_p
    c0, c1, c2 = map(int, p_str.split(":"))
    last_4 = [n for d in data[-4:] for n in d[1:7]]
    freq = Counter(last_4)
    pool0 = [n for n in range(1, 46) if freq[n] == 0]
    pool1 = [n for n in range(1, 46) if freq[n] == 1]
    pool2 = [n for n in range(1, 46) if freq[n] >= 2]
    if len(pool0) >= c0 and len(pool1) >= c1 and len(pool2) >= c2:
        res = random.sample(pool0, c0) + random.sample(pool1, c1) + random.sample(pool2, c2)
        st.success(f"[{p_str} 패턴] 추천번호: {sorted(res)}")

# 2. 누적 데이터
st.subheader("📊 누적 당첨번호 데이터")
df_display = pd.DataFrame(data, columns=['회차', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', '보너스'])
df_display = pd.merge(df_display, df_patterns, on='회차', how='left')
st.dataframe(df_display.sort_values(by='회차', ascending=False), use_container_width=True)

# 3. 데이터 관리 (상시 노출)
st.divider()
st.subheader("⚙️ 데이터베이스 관리")
menu = st.radio("작업 선택", ["📝 신규 입력", "✏️ 수정", "🗑️ 삭제"], horizontal=True)

sheet = client.open_by_url(SHEET_URL).sheet1

if menu == "📝 신규 입력":
    with st.form("new_row", clear_on_submit=True):
        cols = st.columns(4)
        new_draw = cols[0].number_input("회차", value=data[-1][0]+1 if data else 1)
        n1, n2, n3 = cols[1].number_input("n1", value=1), cols[2].number_input("n2", value=1), cols[3].number_input("n3", value=1)
        cols2 = st.columns(4)
        n4, n5, n6 = cols2[0].number_input("n4", value=1), cols2[1].number_input("n5", value=1), cols2[2].number_input("n6", value=1)
        bonus = cols2[3].number_input("보너스", value=7)
        if st.form_submit_button("입력 완료"):
            sheet.append_row([new_draw, n1, n2, n3, n4, n5, n6, bonus])
            st.rerun()

elif menu == "✏️ 수정":
    target_draw = st.selectbox("수정할 회차", [row[0] for row in reversed(data)])
    target_row = next((row for row in data if row[0] == target_draw), None)
    if target_row:
        with st.form("edit_row"):
            c_nums = st.columns(7)
            n1 = c_nums[0].number_input("n1", value=target_row[1])
            n2 = c_nums[1].number_input("n2", value=target_row[2])
            n3 = c_nums[2].number_input("n3", value=target_row[3])
            n4 = c_nums[3].number_input("n4", value=target_row[4])
            n5 = c_nums[4].number_input("n5", value=target_row[5])
            n6 = c_nums[5].number_input("n6", value=target_row[6])
            bonus = c_nums[6].number_input("보너스", value=target_row[7])
            if st.form_submit_button("수정 적용"):
                row_idx = data.index(target_row) + 2
                values = [target_draw, n1, n2, n3, n4, n5, n6, bonus]
                for i, val in enumerate(values):
                    sheet.update_cell(row_idx, i + 1, val)
                st.rerun()

elif menu == "🗑️ 삭제":
    if st.button("마지막 회차 삭제 확인"):
        sheet.delete_rows(len(data)+1)
        st.rerun()

# 4. 하단 시각화 (기존 유지)
st.divider()
st.subheader("📍 최근 5회차 용지 패턴")
recent_5 = list(reversed(data[-5:]))
for row in recent_5:
    st.write(f"**{row[0]}회차:** {sorted(row[1:7])} (보너스: {row[7]})")

st.subheader("📊 패턴 출현 빈도 그래프")
st.bar_chart(df_patterns['패턴'].value_counts())
