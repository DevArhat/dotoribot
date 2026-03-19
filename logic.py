import FinanceDataReader as fdr
import requests
import yt_dlp

import datetime
import json
import math
import os
import re
import sqlite3
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, 'bot.log')
KOSPI_TICKER_PATH = os.path.join(BASE_DIR, 'kospi_ticker.json')
TEST_LOG_PATH = os.path.join(BASE_DIR, 'test.log')
TIME_TABLE_PATH = os.path.join(BASE_DIR, 'time_table.json')

class SpaceController:
    _SPACE_REPLACER = re.compile(r'\s{2,}')
    _SPACE_REMOVER = re.compile(r'\s')
    _NEWLINE_REMOVER = re.compile(r'\r?\n')
    
    def __init__(self):
        pass
    
    def replace_space(self, text):
        result_text = self._NEWLINE_REMOVER.sub('', text)
        result_text = self._SPACE_REPLACER.sub(' ', result_text)
        return result_text
    
    def remove_space(self, text):
        return self._SPACE_REMOVER.sub('', text)
        

class LostArkGuardian:
    def __init__(self):
        self.kst = datetime.timezone(datetime.timedelta(hours=9))
        self.guardians = [
            "루멘칼리고", "가르가디스", "스콜라키아", "크라티오스", 
            "아게오로스", "드렉탈라스", "소나벨", "베스칼"
        ]
        self.cards = [
            "암구", "토구", "토구", "뇌구", "세구", "화구", "암구", "화구"
        ]
        self.anchor_date = datetime.datetime(2026, 3, 4, 6, 0, 0, tzinfo=self.kst)
        
    def get_lostark_weekly_info_predict(self, year, month, day):
        target_date = datetime.datetime(year, month, day, 10, 0, 0, tzinfo=self.kst)
        return self.get_lostark_weekly_info(target_date)
        
    def get_lostark_weekly_info(self, target_date=None):
        kst = datetime.timezone(datetime.timedelta(hours=9))
        
        if target_date is None:
            target_date = datetime.datetime.now(kst)
        elif target_date.tzinfo is None:
            target_date = target_date.replace(tzinfo=kst)

        
        anchor_date = datetime.datetime(2026, 3, 4, 6, 0, 0, tzinfo=kst)
        
        temp_start = target_date.replace(hour=6, minute=0, second=0, microsecond=0)
        
        days_to_subtract = (temp_start.weekday() - 2) % 7
        week_start = temp_start - datetime.timedelta(days=days_to_subtract)
        
        if target_date < week_start:
            week_start -= datetime.timedelta(days=7)
            
        week_end = week_start + datetime.timedelta(days=7)
        
        delta = week_start - anchor_date
        elapsed_weeks = delta.days // 7
        
        current_guardian = self.guardians[elapsed_weeks % len(self.guardians)]
        current_card = self.cards[elapsed_weeks % len(self.cards)]
        next_guardian = self.guardians[(elapsed_weeks + 1) % len(self.guardians)]
        next_card = self.cards[(elapsed_weeks + 1) % len(self.cards)]
        
        next_week_start = week_end
        next_week_end = next_week_start + datetime.timedelta(days=7)
        
        start_str = week_start.strftime("%Y-%m-%d")
        end_str = week_end.strftime("%Y-%m-%d")
        next_start_str = next_week_start.strftime("%Y-%m-%d")
        next_end_str = next_week_end.strftime("%Y-%m-%d")
        
        return (f"{start_str} ~ {end_str}",
                f"{current_guardian}", f"{current_card}",
                f"{next_start_str} ~ {next_end_str}",
                f"{next_guardian}", f"{next_card}")
        
        
class RhythmDotori:
    # e2-micro 환경을 위해 리소스 사용 최소화
    ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

# 네트워크 스트림 불안정 시 재연결 옵션
    ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
    def __init__(self):
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_format_options) # type: ignore


    
class Lotto:
    def get_latest_lotto_drw(self):
        """
        로또 1회차(2002-12-07 20:00) 이후로 매주 토요일 20시를 기준으로 
        현재 시각까지 경과된 주(week) 수를 계산하여 최신 회차를 반환합니다.
        """
        # 로또 1회차 추첨 시간 (토요일 20시)
        first_draw_date = datetime.datetime(2002, 12, 7, 20, 0)
        current_date = datetime.datetime.now()
        
        # 두 날짜 사이의 차이 계산
        elapsed_time = current_date - first_draw_date
        
        # 7일(604800초) 단위로 나누어 현재 회차 계산
        # 1회차부터 시작하므로 결과값에 +1을 합니다.
        latest_drw = (elapsed_time.days // 7) + 1
        
        return latest_drw

    def get_lotto_numbers(self, drwNo=None):
        """
        지정된 회차 혹은 최신 회차의 당첨 번호를 가져옵니다.
        """
        # 회차 정보가 인자로 들어오지 않으면 최신 회차를 계산
        if drwNo is None:
            drwNo = self.get_latest_lotto_drw()
            
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={drwNo}"
        
        try:
            response = requests.get(url)
            response.raise_for_status() # HTTP 에러 발생 시 예외 발생
            data = response.json()
            
            if data.get("returnValue") == "success":
                numbers = [data[f"drwtNo{i}"] for i in range(1, 7)]
                bonus = data["bnusNo"]
                return f"[{drwNo}회 당첨번호] {numbers} + 보너스: {bonus} (추첨일: {data['drwNoDate']})"
            else:
                # 아직 추첨 전인 회차이거나 잘못된 회차인 경우
                return f"{drwNo}회차 데이터를 찾을 수 없습니다. (아직 추첨 전일 수 있습니다.)"
                
        except Exception as e:
            return f"오류가 발생했습니다: {e}"


STOCK_DB_PATH = os.path.join(BASE_DIR, 'stock_data.db')

_STOCK_DF_CACHE = {}

def get_cached_stock_df(ticker: str):
    now = time.time()
    if ticker in _STOCK_DF_CACHE:
        cache_time, cached_df = _STOCK_DF_CACHE[ticker]
        if now - cache_time < 30:
            return cached_df
    
    df = fdr.DataReader(ticker, start="", end="")
    if df is not None and not df.empty:
        _STOCK_DF_CACHE[ticker] = (now, df)
    return df

class StockInfoWithSqlite:
    def __init__(self):
        conn = sqlite3.connect(STOCK_DB_PATH)
        cursor = conn.cursor()

        # stocks 테이블에서 code → official_name 매핑 (stock_data)
        cursor.execute("SELECT code, official_name FROM stocks")
        self.stock_data = {code: [name] for code, name in cursor.fetchall()}

        # keywords 테이블에서 keyword → code 매핑 (ALIAS_MAP)
        cursor.execute("SELECT keyword, code FROM keywords")
        self.ALIAS_MAP = {keyword: code for keyword, code in cursor.fetchall()}

        conn.close()

    def get_stock_info(self, input: str):
        input = SpaceController().remove_space(input).strip().upper()
        if bool(re.fullmatch(r'[A-Z0-9]{6}', input)):
            ticker=input
        else:
            ticker=str(self.ALIAS_MAP[input]) if input in self.ALIAS_MAP else input

        try:
            df = get_cached_stock_df(ticker)
            if df is None or df.empty:
                raise ValueError("Empty DataFrame")
        except Exception as e:
            return f"{os.getenv('ANGRY_KOKO')} 주가 정보가 업셔.. 일시적인 오류 or 입력 잘못됨 or 봇에 등록 안함 $ {e}"


        data = {
            "prev": df.iloc[-2],
            "today": df.iloc[-1]
        }

        return self.arrange_data(data, ticker)

    def arrange_data(self, data:dict, ticker:str):
        prev_open = int(data['prev']['Open'])
        prev_close = int(data['prev']['Close'])
        prev_high = int(data['prev']['High'])
        prev_low = int(data['prev']['Low'])
        prev_volume = int(data['prev']['Volume'])

        today_open = int(data['today']['Open'])
        today_close = int(data['today']['Close'])
        today_high = int(data['today']['High'])
        today_low = int(data['today']['Low'])
        today_volume = int(data['today']['Volume'])

        prev_change = (data['prev']['Change'])*100
        today_change = (data['today']['Change'])*100

        prev_date = data['prev'].name.strftime("%Y-%m-%d")
        today_date = data['today'].name.strftime("%Y-%m-%d")

        price_gap = today_close - prev_close
        up_or_down = ''

        if price_gap < 0:
            price_gap_str = f"-{-price_gap:,.0f}"
            up_or_down = '📉'
        elif price_gap > 0:
            price_gap_str = f"+{price_gap:,.0f}"
            up_or_down = '📈'
        else:
            price_gap_str = f"{price_gap:,.0f}"

        if prev_change < 0:
            prev_change_str = f"-{-prev_change:.2f}%"
        elif prev_change > 0:
            prev_change_str = f"+{prev_change:.2f}%"
        else:
            prev_change_str = f"{prev_change:.2f}%"

        if today_change < 0:
            today_change_str = f"-{-today_change:.2f}%"
        elif today_change > 0:
            today_change_str = f"+{today_change:.2f}%"
        else:
            today_change_str = f"{today_change:.2f}%"

        display_name = self.stock_data[ticker][0] if ticker in self.stock_data else ticker
        msg = f"""# {display_name} : {up_or_down} {today_close:,.0f} ( {price_gap_str} | {today_change_str} )
```markdown
{display_name} ({ticker}) 가격정보
날짜: {today_date:^10} || {prev_date}
시가: {today_open:^10,.0f} || {prev_open:^10,.0f}
종가: {today_close:^10,.0f} || {prev_close:^10,.0f}
고가: {today_high:^10,.0f} || {prev_high:^10,.0f}
저가: {today_low:^10,.0f} || {prev_low:^10,.0f}
등락: {today_change_str:^10} || {prev_change_str:^10}
거래량: {today_volume:^10,.0f} || {prev_volume:^10,.0f}
```
"""
        return msg


def calc_logic(price, dotoris):        
    if dotoris not in [4,8,16]:
        if dotoris == 44:
            dotoris = 4
        elif dotoris == 88:
            dotoris = 8
        elif dotoris == 116 or dotoris == 166:
            dotoris = 16
        else:
            return f"{os.getenv('ANGRY_KOKO')} ({dotoris}인 컨텐츠가 어딨어!!)"
    if price < 50:
        return f"{os.getenv('ANGRY_KOKO')} ({price} 골드짜리를 왜입찰해!!)"

    real_value = price * 0.95
    threshold_value = 100000 * dotoris / (dotoris - 1)
    
    if real_value <= threshold_value:
        # 입찰가가 10만 골드 이하
        optimal_bid = real_value * (dotoris - 1) / dotoris
    else:
        # 입찰가가 10만 골드 초과일 때 초과분 5% 수수료 고려 계산식
        optimal_bid = (real_value * (dotoris - 1) - 5000) / (dotoris - 0.05)
        
    optimal_bid = math.floor(optimal_bid)
    
    if optimal_bid <= 100000:
        total_distribution = optimal_bid
    else:
        total_distribution = 100000 + (optimal_bid - 100000) * 0.95

    distribution_per_person = math.floor(total_distribution / (dotoris - 1))
    
    winner_profit = math.floor(real_value - optimal_bid)
    
    result_tuple = (
        price,
        optimal_bid,
        distribution_per_person,
        winner_profit
    )
    return (f"""# {result_tuple[1]}
```python
# 설명도토리
거래소: {result_tuple[0]:,} 골드
인원수: {dotoris} 명
입찰가: {result_tuple[1]:,} 골드
분배금: {result_tuple[2]:,} 골드
판매금: {result_tuple[3]:,} 골드```""", result_tuple)

def calc_logic_v2(price, dotoris):
    if dotoris not in [4,8,16]:
        if dotoris == 44:
            dotoris = 4
        elif dotoris == 88:
            dotoris = 8
        elif dotoris == 116 or dotoris == 166:
            dotoris = 16
        else:
            return f"{os.getenv('ANGRY_KOKO')} ({dotoris}인 컨텐츠가 어딨어!!)"
    if price < 50:
        return f"{os.getenv('ANGRY_KOKO')} ({price} 골드짜리를 왜입찰해!!)"

    real_value = price * 0.95
    threshold_value = 100000 * dotoris / (dotoris - 1)
    
    if real_value <= threshold_value:
        # 입찰가가 10만 골드 이하
        optimal_bid = real_value * (dotoris - 1) / dotoris
    else:
        # 입찰가가 10만 골드 초과일 때 초과분 5% 수수료 고려 계산식
        optimal_bid = (real_value * (dotoris - 1) - 5000) / (dotoris - 0.05)
        
    optimal_bid = math.ceil(optimal_bid / 1.1)
    
    if optimal_bid <= 100000:
        total_distribution = optimal_bid
    else:
        total_distribution = 100000 + (optimal_bid - 100000) * 0.95

    distribution_per_person = math.floor(total_distribution / (dotoris - 1))
    
    winner_profit = math.floor(real_value - optimal_bid)
    
    result_tuple = (
        price,
        optimal_bid,
        distribution_per_person,
        winner_profit
    )
    return (f"""# {result_tuple[1]}
```python
# 설명도토리
거래소: {result_tuple[0]:,} 골드
인원수: {dotoris} 명
입찰가: {result_tuple[1]:,} 골드
분배금: {result_tuple[2]:,} 골드
판매금: {result_tuple[3]:,} 골드```""", result_tuple)    


def show_sheet_link_for_individuals(ctx):
    username, user_id, _ = get_user_info_from_ctx(ctx)
    sheet_link_base = os.getenv('DOTORI_TIME_TABLE')
    SHEET_DB_PATH = os.path.join(BASE_DIR, 'time_table_range.db')
    conn = sqlite3.connect(SHEET_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT table_range FROM table_ranges WHERE user_id = ?", (user_id,))
    query_result = cursor.fetchone()
    conn.close()
    if query_result:
        result = f"{sheet_link_base}&range={query_result[0]}"
    else:
        result = sheet_link_base

    return result
        



def run_vercel(game, dolpa):

    api_url = f"https://gacha-simulator-api.vercel.app/simulate/{game}/{dolpa}"
    
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        history_log = "\n".join(data['logs']['log'])
        if game == "end":
            result = f"""## {data.get('game', '')} {data.get('target_rank', '0')}돌 시뮬레이션 결과
```markdown
뽑기 횟수: {data.get('total_pulls', 0)}회 ({data['raw']['cost']:,} 원)
필요 트럭: {data['trucks']['raw']}트럭 ({data['trucks']['raw_cost']:,} 원)
무뽑 재료: {data['crumbs']['total']:,}개 ({data['crumbs']['tickets_changed']}회 가능)
획득 현황: 픽업 {data['pull_result']['pickup_6']}, 픽뚫 {data['pull_result']['other_6']}, 5성 {data['pull_result']['star_5']}, 4성 {data['pull_result']['star_4']}

히스토리: 
{history_log}
```"""
        else:
            result = f"""### {data.get('game', '')} {data.get('target_rank', '0')}돌 시뮬레이션 결과
```markdown
# 뽑기 환급 재료 미사용 기준
뽑기 횟수: {data.get('total_pulls', 0)}회 ({data['raw']['cost']:,} 원)
필요 트럭: {data['trucks']['raw']}트럭 ({data['trucks']['raw_cost']:,} 원)

# 뽑기 환급 재료 사용 기준
뽑기 횟수: {data['after_exchange']['pulls']}회 ({data['after_exchange']['cost']:,} 원)
필요 트럭: {data['trucks']['after_exchange']}트럭 ({data['trucks']['after_exchange_cost']:,} 원)

뽑기 재료: {data['crumbs']['total']:,}개 ({data['crumbs']['tickets_changed']}회 가능)
획득 현황: 픽업 {data['pull_result']['pickup_5']}, 픽뚫 {data['pull_result']['other_5']}, 4성 {data['pull_result']['star_4']}, 무기 {data['pull_result']['weapon_3']}

히스토리:
{history_log}
```"""
        return result
    else:
        return f"API 요청 실패: {response.status_code}"
def get_user_info_from_ctx(ctx):
    try:
        if ctx is None:
            user = None
            username = "SYSTEM"
            user_id = "0"
        else:
            user = getattr(ctx, 'author', getattr(ctx, 'user', ctx))
            user_id = getattr(user, 'id', '0')
            name_temp = getattr(user, 'display_name', None) or str(user)
            username = name_temp if name_temp else 'UNKNOWN'
    except:
        user = None
        username = "UNKNOWN"
        user_id = "0"
    
    return username, user_id, user


def write_log(target, command, details, path):
    timezone_kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(timezone_kst).strftime('%Y-%m-%dT%H:%M:%S+09:00')
    
    username, user_id, _ = get_user_info_from_ctx(target)
    
    msg = f"[{now}] {username}({user_id}) | {command} | {details}\n"

    with open(path, 'a', encoding='utf-8') as log_file:
        log_file.write(msg)

def add_log(target, command, details='No Details'):
    path = LOG_PATH
    write_log(target, command, details, path)
    
def add_test_log(target, command, details='No Details'):
    path = TEST_LOG_PATH
    write_log(target, command, details, path)
        
def get_game_key(game):
    game_map = {
        'gen': ["원신"],
        'hsr': ["붕스", "스타레일", "붕괴"],
        'zzz': ["젠존제", "찢", "젠레스"],
        'wuwa': ["명조", "띵조"],
        'end': ["엔필", "엔드필드"]
    }
    
    game = game.replace(" ", "")

    for key, keywords in game_map.items():
        if any(kw in game for kw in keywords):
            return key

    return 'hsr'



