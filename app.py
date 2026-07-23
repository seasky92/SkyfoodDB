import streamlit as st
import pandas as pd
import requests
import urllib.parse

# 1. 앱 기본 설정
st.set_page_config(page_title="영양성분 검색기", page_icon="🍎", layout="wide")

st.title("🍎 실시간 영양성분 검색기")
st.markdown("식약처 공공데이터를 활용하여 음식이나 브랜드 메뉴의 영양성분을 검색합니다.")

# 2. API 키 불러오기 (Secrets에서)
try:
    API_KEY = st.secrets["FOOD_API_KEY"]
except:
    st.error("🚨 API 키가 설정되지 않았습니다. Streamlit Secrets 설정을 확인해주세요.")
    st.stop()

# 3. 검색창 만들기
search_word = st.text_input("🔍 검색할 식품명을 입력하세요 (예: 아메리카노, 사과, 신라면)", "")

# 4. 검색 버튼을 눌렀을 때 동작
if st.button("검색하기", type="primary"):
    if search_word:
        with st.spinner('식약처 데이터베이스를 뒤지는 중... 🕵️‍♂️'):
            try:
                # 공공데이터포털 API 호출 주소 및 검색어 설정
                encoded_word = urllib.parse.quote(search_word)
                
                # 식품의약품안전처_식품영양성분DB API 주소
                url = f"http://apis.data.go.kr/1471000/FoodNtrIrdntInfoService1/getFoodNtrItdntList1?ServiceKey={API_KEY}&desc_kor={encoded_word}&pageNo=1&numOfRows=20&type=json"
                
                # 데이터 요청
                response = requests.get(url)
                data = response.json()
                
                # 결과 데이터 빼오기
                items = data.get('body', {}).get('items', [])
                
                if not items:
                    st.warning(f"'{search_word}'에 대한 검색 결과가 없습니다. 이름을 조금 다르게 검색해 보세요.")
                else:
                    st.success(f"총 {len(items)}개의 검색 결과를 찾았습니다!")
                    
                    # 검색 결과를 예쁜 카드 형태로 출력
                    for item in items:
                        food_name = item.get('DESC_KOR', '이름 없음')
                        serving = item.get('SERVING_WT', '0')
                        maker = item.get('ANIMAL_PLANT', '제조사/분류 없음')
                        
                        kcal = item.get('NUTR_CONT1', '0') # 열량
                        carbs = item.get('NUTR_CONT2', '0') # 탄수화물
                        protein = item.get('NUTR_CONT3', '0') # 단백질
                        fat = item.get('NUTR_CONT4', '0') # 지방
                        sugar = item.get('NUTR_CONT5', '0') # 당류
                        sodium = item.get('NUTR_CONT6', '0') # 나트륨
                        
                        # 아코디언(접었다 펴기) 형태로 메뉴 하나씩 보여주기
                        with st.expander(f"🍽️ {food_name} ({maker}) - {kcal} kcal"):
                            st.markdown(f"**1회 제공량:** {serving}g")
                            
                            # 숫자들을 5칸으로 나눠서 깔끔하게 배치
                            col1, col2, col3, col4, col5 = st.columns(5)
                            col1.metric("🔥 열량", f"{kcal} kcal")
                            col2.metric("🍚 탄수화물", f"{carbs} g")
                            col3.metric("🥩 단백질", f"{protein} g")
                            col4.metric("🧈 지방", f"{fat} g")
                            col5.metric("🍭 당류", f"{sugar} g")
                            
                            st.caption(f"나트륨: {sodium} mg")
                            
            except Exception as e:
                st.error("🚨 데이터를 불러오는 중 에러가 발생했습니다.")
                st.write(f"상세 에러 내용: {e}")
    else:
        st.warning("검색어를 먼저 입력해주세요!")

