import streamlit as st
import pandas as pd
import requests
import urllib.parse

st.set_page_config(page_title="영양성분 검색기", page_icon="🍎", layout="wide")

st.title("🍎 실시간 영양성분 검색기")
st.markdown("식약처 공공데이터를 활용하여 음식이나 브랜드 메뉴의 영양성분을 검색합니다.")

try:
    API_KEY = st.secrets["FOOD_API_KEY"]
except:
    st.error("🚨 API 키가 설정되지 않았습니다. Streamlit Secrets 설정을 확인해주세요.")
    st.stop()

search_word = st.text_input("🔍 검색할 식품명을 입력하세요 (예: 아메리카노, 사과, 신라면)", "")

if st.button("검색하기", type="primary"):
    if search_word:
        with st.spinner('식약처 데이터베이스를 뒤지는 중... 🕵️‍♂️'):
            try:
                # 💡 핵심 변경 부분: 안전한 API 호출 방식 적용
                url = "http://apis.data.go.kr/1471000/FoodNtrIrdntInfoService1/getFoodNtrItdntList1"
                
                # 키 값의 앞뒤 공백을 없애고, 안전한 문자로 한번 풀어줍니다.
                safe_key = urllib.parse.unquote(API_KEY.strip())
                
                # 주소에 직접 붙이지 않고 params라는 안전한 바구니에 담아서 보냅니다.
                params = {
                    'ServiceKey': safe_key,
                    'desc_kor': search_word,
                    'pageNo': '1',
                    'numOfRows': '20',
                    'type': 'json'
                }
                
                response = requests.get(url, params=params)
                raw_text = response.text
                
                try:
                    data = response.json()
                except Exception:
                    st.error("🚨 식약처 서버에서 데이터를 정상적으로 보내지 않았습니다.")
                    st.warning("아래 서버 응답을 확인해주세요. (SERVICE_KEY_IS_NOT_REGISTERED_ERROR 라면 키 등록 대기 중입니다!)")
                    st.code(raw_text)
                    st.stop()
                
                items = data.get('body', {}).get('items', [])
                
                if not items:
                    st.warning(f"'{search_word}'에 대한 검색 결과가 없습니다.")
                else:
                    st.success(f"총 {len(items)}개의 검색 결과를 찾았습니다!")
                    
                    for item in items:
                        food_name = item.get('DESC_KOR', '이름 없음')
                        serving = item.get('SERVING_WT', '0')
                        maker = item.get('ANIMAL_PLANT', '제조사/분류 없음')
                        kcal = item.get('NUTR_CONT1', '0')
                        carbs = item.get('NUTR_CONT2', '0')
                        protein = item.get('NUTR_CONT3', '0')
                        fat = item.get('NUTR_CONT4', '0')
                        sugar = item.get('NUTR_CONT5', '0')
                        sodium = item.get('NUTR_CONT6', '0')
                        
                        with st.expander(f"🍽️ {food_name} ({maker}) - {kcal} kcal"):
                            st.markdown(f"**1회 제공량:** {serving}g")
                            col1, col2, col3, col4, col5 = st.columns(5)
                            col1.metric("🔥 열량", f"{kcal} kcal")
                            col2.metric("🍚 탄수화물", f"{carbs} g")
                            col3.metric("🥩 단백질", f"{protein} g")
                            col4.metric("🧈 지방", f"{fat} g")
                            col5.metric("🍭 당류", f"{sugar} g")
                            st.caption(f"나트륨: {sodium} mg")
                            
            except Exception as e:
                st.error("🚨 인터넷 연결 등의 문제가 발생했습니다.")
                st.write(f"상세 에러: {e}")
    else:
        st.warning("검색어를 먼저 입력해주세요!")
