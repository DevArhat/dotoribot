import aiohttp
import asyncio
from dotenv import load_dotenv

import os, json

from logic import SpaceController

load_dotenv()

sc = SpaceController()
KAKAO_MAP_API_KEY = f"KakaoAK {os.getenv('KAKAO_MAP_API_KEY')}"


async def kakao_map(동네: str = '서울'):
    REQ_URL = "https://dapi.kakao.com/v2/local/search/keyword.json?"
    keyword = sc.remove_space(동네)
    headers = {
        "Authorization": KAKAO_MAP_API_KEY
    }

    print(headers)

    params = {
        "query": f"{keyword}",
        "category_group_code": "FD6",
        "sort": "accuracy",
        "size": 10
    }
    reponse_status = None
    async with aiohttp.ClientSession() as session:
        async with session.get(REQ_URL, headers=headers, params=params) as response:
            if response.status == 200:
                reponse_status = 200
                data = await response.json()
            else:
                reponse_status = response.status
                data = None
    if not data:
        print(response_status)
        print("X")
    
    parsed_data = data.get('documents', None)

    for rstrnt in parsed_data:
        print(f"{rstrnt.get('place_name')} // {rstrnt.get('address_name')}")
        print(f"{(rstrnt.get('x'))}   {(rstrnt.get('y'))}")

async def call_km_api():
    REQ_URL= "https://apis-navi.kakaomobility.com/v1/waypoints/directions"
    headers = {
        "Authorization": KAKAO_MAP_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "origin": {
            "x": 127.11024293202674,
            "y": 37.394348634049784,
        },
        "destination": {
            "x": 127.10860518470294,
            "y": 37.401999820065534
        },
        "waypoints": [
            {
                "name": "경유1",
                "x": 127.11341936045922,
                "y": 37.39639094915999
            },
            {
                "name": "경유2",
                "x": 126.889810723306,
                "y": 37.4802731041657
            }
        ],
        "priority": "RECOMMEND",
        "car_fuel": "GASOLINE",
        "car_hipass": True,
        "alternatives": False,
        "road_details": False,
        "summary": False
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(REQ_URL, headers=headers, data=json.dumps(data)) as response:
            if response.status == 200:
                reponse_status = 200
                data = await response.json()
            else:
                reponse_status = response.status
                data = None
    if not data:
        print(response_status)
        print("X")
    else:
        print("✅")
        with open('api_response_type1_2.txt', 'w', encoding='utf-8') as f:
            f.write(f"{parse_result(data)}")




    data = {
        "origin": {
            "x": 127.11024293202674,
            "y": 37.394348634049784,
        },
        "destination": {
            "x": 127.10860518470294,
            "y": 37.401999820065534
        },
        "waypoints": [
            {
                "name": "경유1",
                "x": 127.11341936045922,
                "y": 37.39639094915999
            },
            {
                "name": "경유2",
                "x": 126.889810723306,
                "y": 37.4802731041657
            }
        ],
        "priority": "RECOMMEND",
        "car_fuel": "GASOLINE",
        "car_hipass": True,
        "alternatives": False,
        "road_details": False,
        "summary": True
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(REQ_URL, headers=headers, data=json.dumps(data)) as response:
            if response.status == 200:
                reponse_status = 200
                data = await response.json()
            else:
                reponse_status = response.status
                data = None
    if not data:
        print(response_status)
        print("X")
    else:
        print("✅")
        with open('api_response_type2_2.txt', 'w', encoding='utf-8') as f:
            f.write(f"{parse_result(data)}")


def parse_result(response_data):

    # JSON 문자열인 경우 딕셔너리로 변환
    if isinstance(response_data, str):
        response_data = json.loads(response_data.replace("'", '"'))

    route = response_data['routes'][0]
    
    # 1. 요약 정보 추출 (거리 및 시간)
    # summary=True/False에 따라 위치가 달라질 수 있으나 보통 routes[0]['summary']에 존재
    summary = route.get('summary', {})
    total_distance = summary.get('distance', 0)  # 단위: 미터(m)
    total_duration = summary.get('duration', 0)  # 단위: 초(s)

    # 2. 동선(방문 순서) 추출
    # 경유지 최적화 결과는 sections 리스트의 'name'을 순서대로 읽으면 됩니다.
    sections = route.get('sections', [])
    visit_order = []
    
    if sections:
        # 시작점 추가
        visit_order.append("출발지")
        
        for section in sections:
            # 각 구간의 도착지 이름을 추가
            destination_name = section.get('name', '이름 없음')
            # 카카오 API는 목적지를 '목적지'라는 텍스트 대신 빈 값으로 보낼 때가 있음
            if not destination_name:
                destination_name = "목적지"
            visit_order.append(destination_name)

    # 3. 데이터 가공 (보기 좋게 변환)
    distance_km = round(total_distance / 1000, 2)
    duration_min = round(total_duration / 60)
    order_str = " -> ".join(visit_order)

    return {
        "distance": f"{distance_km}km",
        "duration": f"{duration_min}분",
        "order": order_str
    }

# 테스트 (올려주신 파일 데이터 기준 결과)
# 결과 예시: {'distance': '13.45km', 'duration': '22분', 'order': '출발지 -> 경유1 -> 경유2 -> 목적지'}



if __name__ == "__main__":
    asyncio.run(call_km_api())
    # asyncio.run(kakao_map('구로'))