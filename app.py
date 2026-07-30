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

st.title("🎯 로또 패턴 분석 및 추천")

# 1. 랜덤 추천 / 2. 누적 데이터 생략(기능유지)

# 3. 데이터 관리
st.subheader("⚙️ 데이터베이스 관리")
menu = st.radio("작업 선택", ["📝 신규 입력", "✏️ 수정", "🗑️ 삭제"], horizontal=True)

sheet = client.open_by_url(SHEET_URL).sheet1

if menu == "📝 신규 입력":
    with st.form("new_row", clear_on_submit=True):
        cols = st.columns(8)
        new_draw = cols[0].number_input("회차", value=data[-1][0]+1 if data else 1)
        nums = [cols[i+1].number_input(f"n{i+1}", min_value=1, max_value=45, value=i+1) for i in range(6)]
        bonus = cols[7].number_input("보너스", min_value=1, max_value=45, value=7)
        if st.form_submit_button("입력 완료"):
            sheet.append_row([new_draw] + nums + [bonus])
            st.success(f"{new_draw}회차 입력 성공!")
            st.rerun()

elif menu == "✏️ 수정":
    target_draw = st.selectbox("수정할 회차", [row[0] for row in reversed(data)])
    target_row = next((row for row in data if row[0] == target_draw), None)
    if target_row:
        with st.form("edit_row"):
            c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
            n1 = c1.number_input("n1", value=target_row[1])
            n2 = c2.number_input("n2", value=target_row[2])
            n3 = c3.number_input("n3", value=target_row[3])
            n4 = c4.number_input("n4", value=target_row[4])
            n5 = c5.number_input("n5", value=target_row[5])
            n6 = c6.number_input("n6", value=target_row[6])
            bonus = c7.number_input("보너스", value=target_row[7])
            
            if st.form_submit_button("수정 적용"):
                row_idx = data.index(target_row) + 2
                # 명확하게 한 셀씩 수정하여 오류 방지
                values = [target_draw, n1, n2, n3, n4, n5, n6, bonus]
                for i, val in enumerate(values):
                    sheet.update_cell(row_idx, i + 1, val)
                st.success("수정 완료!")
                st.rerun()

elif menu == "🗑️ 삭제":
    if st.button("마지막 회차 삭제"):
        sheet.delete_rows(len(data)+1)
        st.success("삭제 완료!")
        st.rerun()
