import streamlit as st
import requests
import urllib.parse
import pandas as pd

st.set_page_config(page_title="영양성분 검색기", page_icon="🍎", layout="wide")

# 세션 상태 초기화 (현재 어느 화면에 있는지 저장)
if 'step' not in st.session_state: st.session_state.step = 'home'
if 'category' not in st.session_state: st.session_state.category = None
if 'subcategory' not in st.session_state: st.session_state.subcategory = None

st.title("🍎 스마트 영양성분 검색기")

# 1. 메인 홈 화면 (4개 버튼)
if st.session_state.step == 'home':
    st.subheader("카테고리를 선택하세요")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("🍎 원재료"): st.session_state.step, st.session_state.category = 'search', '원재료'
    if col2.button("☕ 카페"): st.session_state.step, st.session_state.category = 'cafe', '카페'
    if col3.button("🏪 편의점"): st.session_state.step, st.session_state.category = 'conv', '편의점'
    if col4.button("🍴 그외"): st.session_state.step, st.session_state.category = 'search', '그외'

# 2. 카페 세부 분류
elif st.session_state.step == 'cafe':
    st.subheader("브랜드를 선택하세요")
    brands = ["스타벅스", "투썸플레이스", "메가커피", "컴포즈커피", "그외"]
    cols = st.columns(len(brands))
    for i, brand in enumerate(brands):
        if cols[i].button(brand):
            st.session_state.subcategory = brand
            st.session_state.step = 'search'
    if st.button("⬅️ 뒤로가기"): st.session_state.step = 'home'

# 3. 편의점 세부 분류
elif st.session_state.step == 'conv':
    st.subheader("편의점을 선택하세요")
    brands = ["CU", "GS25", "세븐일레븐", "그외"]
    cols = st.columns(len(brands))
    for i, brand in enumerate(brands):
        if cols[i].button(brand):
            st.session_state.subcategory = brand
            st.session_state.step = 'search'
    if st.button("⬅️ 뒤로가기"): st.session_state.step = 'home'

# 4. 검색 화면
elif st.session_state.step == 'search':
    st.markdown(f"### 🔍 {st.session_state.category} > {st.session_state.subcategory if st.session_state.subcategory else ''}")
    search_word = st.text_input("메뉴나 식품명을 입력하세요", "")
    
    if st.button("검색"):
        # API 호출 및 검색 로직 (기존과 동일)
        with st.spinner('데이터 검색 중...'):
            API_KEY = st.secrets["FOOD_API_KEY"]
            url = "https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02"
            params = {'ServiceKey': urllib.parse.unquote(API_KEY.strip()), 'FOOD_NM_KR': search_word, 'numOfRows': '100', 'type': 'json'}
            
            response = requests.get(url, params=params)
            data = response.json().get('body', {}).get('items', [])
            
            # 필터링 로직 (선택한 브랜드가 포함된 결과만 추출)
            if data:
                filtered = [item for item in data if st.session_state.subcategory is None or st.session_state.subcategory in item.get('MAKER_NM', '')]
                for item in filtered:
                    with st.expander(f"🍽️ {item.get('FOOD_NM_KR')} ({item.get('MAKER_NM', '일반')})"):
                        st.write(f"열량: {item.get('AMT_NUM1', '0')} kcal / 단백질: {item.get('AMT_NUM3', '0')}g")
            else:
                st.warning("결과가 없습니다.")
                
    if st.button("🏠 홈으로"): st.session_state.step = 'home'
