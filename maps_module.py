import aiohttp
import os, json
import datetime as dt

from dotenv import load_dotenv
from logic import SpaceController

sc = SpaceController()
load_dotenv()

# ── Kakao Map API ──────────────────────────────────────────
KAKAO_MAP_API_KEY = f"KakaoAK {os.getenv('KAKAO_MAP_API_KEY')}"
REQ_URL = "https://dapi.kakao.com/v2/local/search/keyword.json?"


async def get_kakao_places(keyword: str, max_results: int = 5):
    """카카오 API로 검색어에 대한 상위 장소를 가져옵니다."""
    headers = {"Authorization": KAKAO_MAP_API_KEY}
    params = {"query": keyword, "size": max_results, "sort": "accuracy"}

    async with aiohttp.ClientSession() as session:
        async with session.get(REQ_URL, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('documents', [])
    return []


# ── TMap API ───────────────────────────────────────────────
TMAP_API_KEY = f"{os.getenv('TMAP_API_KEY')}"
TMAP_OPT_URL = 'https://apis.openapi.sk.com/tmap/routes/routeOptimization10?version=1'


async def tmap_optimization(출발, 도착, 경유리스트):
    if len(경유리스트) == 1:
        return f"{출발.get('place_name')} -> {경유리스트[0].get('place_name')} -> {도착.get('place_name')}"
    tzone = dt.timezone(dt.timedelta(hours=9))
    now = dt.datetime.now(tzone).strftime("%Y%m%d%H%M")

    result_text = ''

    headers = {
        "appKey": TMAP_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    경유_리스트 = []
    for i, 경유 in enumerate(경유리스트):
        경유_리스트.append({
            "viaPointId": f"via{i+1}",
            "viaPointName": 경유.get('place_name', "몰루"),
            "viaX": str(경유.get('x', 0)),
            "viaY": str(경유.get('y', 0))
        })

    data = {
        "startName": 출발.get('place_name', "몰루"),
        "startX": str(출발.get('x', 0)),
        "startY": str(출발.get('y', 0)),
        "endName": 도착.get('place_name', "몰루"),
        "endX": str(도착.get('x', 0)),
        "endY": str(도착.get('y', 0)),
        "viaPoints": 경유_리스트,
        "startTime": now
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(TMAP_OPT_URL, headers=headers, data=json.dumps(data)) as response:
            if response.status == 200:
                reponse_status = 200
                responsejson = await response.json()
            else:
                reponse_status = response.status
                responsejson = None

    try:
        if not responsejson:
            return f"🐿️ 앗! 동선을 짜다가 길을 잃었어... ({reponse_status})"
        else:
            rp = responsejson.get("properties", {})
            total_time_temp, total_dist_temp, total_fare_temp = int(rp.get("totalTime", "0")), int(rp.get("totalDistance", "0")), int(rp.get("totalFare", "0"))
            total_time = f"{total_time_temp // 60}분 {total_time_temp % 60}초"
            total_dist = f"{(total_dist_temp // 1000):,.1f}km"
            total_fare = f"{total_fare_temp:,}원"
            response_features = responsejson.get("features", [])
            if not response_features:
                return f"🐿️ 앗! 동선을 짜다가 길을 잃었어... ({reponse_status})"
            result_text = f"{출발.get('place_name', '몰루')} -> "
            for rf in response_features:
                if rf["geometry"]["type"] != "Point" or "via" not in rf["properties"]["viaPointId"]:
                    continue
                pointname = rf.get("properties", {}).get("viaPointName", "").replace("[0] ", "")
                result_text += f"{pointname} -> "
            result_text += f"{도착.get('place_name', '몰루')}\n"
            result_text += f"\n총 거리 : {total_dist}\n총 소요 시간 : {total_time}"
            if total_fare_temp > 0:
                result_text += f"\n총 요금 : {total_fare}"
            return result_text
    except Exception as e:
        return f"🐿️ 앗! 동선을 짜다가 길을 잃었어... ({e})"
