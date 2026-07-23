import streamlit as st
import requests
import urllib.parse

st.set_page_config(page_title="영양성분 검색기", page_icon="🍎", layout="wide")

st.title("🍎 실시간 영양성분 검색기 (최신 DB)")
st.markdown("식약처 최신 공공데이터(FoodNtrCpntDbInfo02)를 활용하여 영양성분을 검색합니다.")

try:
    API_KEY = st.secrets["FOOD_API_KEY"]
except:
    st.error("🚨 API 키가 설정되지 않았습니다. Streamlit Secrets 설정을 확인해주세요.")
    st.stop()

search_word = st.text_input("🔍 검색할 식품명을 입력하세요 (예: 사과, 아메리카노)", "")

if st.button("검색하기", type="primary"):
    if search_word:
        with st.spinner('식약처 최신 데이터베이스를 뒤지는 중... 🕵️‍♂️'):
            try:
                # 💡 사용자님이 발급받은 End Point 주소로 정확히 변경!
                url = "https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02"
                
                safe_key = urllib.parse.unquote(API_KEY.strip())
                
                params = {
                    'ServiceKey': safe_key,
                    'FOOD_NM_KR': search_word, # 신버전 검색 파라미터
                    'DESC_KOR': search_word,   # 구버전 호환용 
                    'pageNo': '1',
                    'numOfRows': '20',
                    'type': 'json'
                }
                
                response = requests.get(url, params=params)
                raw_text = response.text
                
                try:
                    data = response.json()
                except Exception:
                    st.error("🚨 서버 응답 에러")
                    st.warning("아래 문구에 'REGISTERED_ERROR'가 보인다면 정상적인 키 등록 대기 상태(1~2시간 소요)입니다!")
                    st.code(raw_text)
                    st.stop()
                
                items = data.get('body', {}).get('items', [])
                
                if not items:
                    st.warning(f"'{search_word}'에 대한 검색 결과가 없습니다.")
                else:
                    st.success(f"총 {len(items)}개의 검색 결과를 찾았습니다!")
                    
                    for item in items:
                        # 신버전(V2)과 구버전(V1) 데이터 이름을 모두 잡아내도록 스마트하게 설정
                        food_name = item.get('FOOD_NM_KR') or item.get('DESC_KOR', '이름 없음')
                        serving = item.get('SERVING_SIZE') or item.get('SERVING_WT', '0')
                        maker = item.get('MAKER_NM') or item.get('ANIMAL_PLANT', '제조사/분류 없음')
                        
                        kcal = item.get('AMT_NUM1') or item.get('NUTR_CONT1', '0')
                        carbs = item.get('AMT_NUM7') or item.get('NUTR_CONT2', '0')
                        protein = item.get('AMT_NUM3') or item.get('NUTR_CONT3', '0')
                        fat = item.get('AMT_NUM4') or item.get('NUTR_CONT4', '0')
                        sugar = item.get('AMT_NUM8') or item.get('NUTR_CONT5', '0')
                        sodium = item.get('AMT_NUM14') or item.get('NUTR_CONT6', '0')
                        
                        with st.expander(f"🍽️ {food_name} ({maker}) - {kcal} kcal"):
                            st.markdown(f"**1회 제공량:** {serving}g (또는 mL)")
                            col1, col2, col3, col4, col5 = st.columns(5)
                            col1.metric("🔥 열량", f"{kcal} kcal")
                            col2.metric("🍚 탄수화물", f"{carbs} g")
                            col3.metric("🥩 단백질", f"{protein} g")
                            col4.metric("🧈 지방", f"{fat} g")
                            col5.metric("🍭 당류", f"{sugar} g")
                            st.caption(f"나트륨: {sodium} mg")
                            
            except Exception as e:
                st.error("🚨 통신 중 에러가 발생했습니다.")
                st.write(f"상세 에러: {e}")
    else:
        st.warning("검색어를 먼저 입력해주세요!")
