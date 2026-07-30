import streamlit as st
import pandas as pd
import random
from collections import Counter
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="로또 패턴 분석기", layout="wide")

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

# 패턴 계산 로직
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

# --- UI 시작 ---
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

# 3. 데이터 관리 (신규/수정/삭제 탭 추가)
with st.expander("⚙️ 데이터베이스 관리"):
    tab1, tab2, tab3 = st.tabs(["📝 신규 입력", "✏️ 수정", "🗑️ 삭제"])
    
    # 신규 입력
    with tab1:
        with st.form("new_row"):
            cols = st.columns(8)
            new_draw = cols[0].number_input("회차", value=data[-1][0]+1 if data else 1)
            nums = [cols[i+1].number_input(f"n{i+1}", min_value=1, max_value=45, value=i+1) for i in range(6)]
            bonus = cols[7].number_input("보너스", min_value=1, max_value=45, value=7)
            if st.form_submit_button("입력 완료"):
                client.open_by_url(SHEET_URL).sheet1.append_row([new_draw] + nums + [bonus])
                st.rerun()

    # 수정 기능
    with tab2:
        sheet = client.open_by_url(SHEET_URL).sheet1
        target_draw = st.selectbox("수정할 회차 선택", [row[0] for row in reversed(data)])
        target_row_data = next((row for row in data if row[0] == target_draw), None)
        
        if target_row_data:
            with st.form("edit_row"):
                cols = st.columns(8)
                cols[0].write(f"회차: {target_row_data[0]}")
                new_nums = [cols[i+1].number_input(f"n{i+1}", min_value=1, max_value=45, value=target_row_data[i+1]) for i in range(6)]
                new_bonus = cols[7].number_input("보너스", min_value=1, max_value=45, value=target_row_data[7])
                if st.form_submit_button("수정 적용"):
                    # 해당 회차를 찾아 행 번호를 구함
                    row_idx = data.index(target_row_data) + 2 # 헤더 포함 +1
                    sheet.update(f"A{row_idx}:H{row_idx}", [[target_draw] + new_nums + [new_bonus]])
                    st.rerun()

    # 삭제 기능
    with tab3:
        if st.button("마지막 회차 삭제"):
            client.open_by_url(SHEET_URL).sheet1.delete_rows(len(data)+1)
            st.rerun()

# 4. 최근 5회차 용지 패턴
st.subheader("📍 최근 5회차 용지 패턴 (시각화)")
recent_5 = list(reversed(data[-5:]))
tabs = st.tabs([f"{row[0]}회차" for row in recent_5])
for i, tab in enumerate(tabs):
    with tab:
        win_nums, bonus = recent_5[i][1:7], recent_5[i][7]
        grid_html = "<div style='display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; max-width: 320px;'>"
        for n in range(1, 46):
            style = "background:#ff4b4b; color:white;" if n in win_nums else "background:#00cc66; color:white;" if n==bonus else "background:#f0f2f6; border:1px solid #ddd;"
            grid_html += f"<div style='{style} border-radius:4px; padding:8px 0; text-align:center;'>{n}</div>"
        st.markdown(grid_html + "</div>", unsafe_allow_html=True)

# 5. 그래프
st.divider()
st.subheader("📊 패턴 출현 빈도 그래프 (933회 ~ 1233회)")
df_graph = df_patterns[(df_patterns['회차'] >= 933) & (df_patterns['회차'] <= 1233)]
st.bar_chart(df_graph['패턴'].value_counts())

    # 신규 입력 탭 (에러 확인용)
    with tab1:
        with st.form("new_row"):
            cols = st.columns(8)
            new_draw = cols[0].number_input("회차", value=data[-1][0]+1 if data else 1)
            nums = [cols[i+1].number_input(f"n{i+1}", min_value=1, max_value=45, value=1) for i in range(6)]
            bonus = cols[7].number_input("보너스", min_value=1, max_value=45, value=7)
            
            if st.form_submit_button("입력 완료"):
                try:
                    # 데이터 입력 시도
                    sheet = client.open_by_url(SHEET_URL).sheet1
                    sheet.append_row([new_draw] + nums + [bonus])
                    st.success("데이터가 성공적으로 입력되었습니다!")
                    st.rerun()
                except Exception as e:
                    # 에러가 발생하면 화면에 보여줌
                    st.error(f"🚨 입력 실패: {e}")

