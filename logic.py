import datetime
import math
import os
import json
import re
import FinanceDataReader as fdr

import aiohttp

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
        

class StockInfo:
    with open(KOSPI_TICKER_PATH, 'r', encoding='utf-8') as f:
        stock_data = json.load(f)
        
    stock_data = {code: [name] for code, name in stock_data.items()}
    
    stock_alias = {
        "005930": ["삼성전자", "삼전", "스캠전자", "개미지옥"],
        "000660": ["SK하이닉스", "하이닉스", "하닉"],
        "012450": ["한화에어로스페이스", "한화에어로", "에어로", "자주포", "K9"],
        "005380": ["현대차", "현차", "현대"],
        "042660": ["한화오션", "오션"],
        "064350": ["현대로템", "로템"],
        "079550": ["LIG넥스원", "넥스원"],
        "272210": ["한화시스템"],
        "042700": ["한미반도체"],
        "252670": ["곱버스"]
    }
    
    for code, aliases in stock_alias.items():
        if code in stock_data:
            stock_data[code].extend(aliases)
        else:
            stock_data[code] = aliases
    
    
    ALIAS_MAP = {}

    def __init__(self):    
        for code, aliases in self.stock_data.items():
            for alias in aliases:
                self.ALIAS_MAP[alias] = code
    
    def get_stock_info(self, input: str):
        input = SpaceController().remove_space(input).strip().upper()
        if bool(re.fullmatch(r'[A-Z0-9]{6}', input)):
            ticker=input
        else:
            ticker=str(self.ALIAS_MAP[input]) if input in self.ALIAS_MAP else input
            
        try:
            df = fdr.DataReader(ticker, start = "", end = "")
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
        
        msg = f"""# {self.stock_data[ticker][0]} : {up_or_down} {today_close:,.0f} ( {price_gap_str} | {today_change_str} )
```markdown
{self.stock_data[ticker][0]} ({ticker}) 가격정보
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

async def run_vercel(ctx, game, dolpa):
    api_url = f"https://gacha-simulator-api.vercel.app/simulate/{game}/{dolpa}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
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
                await ctx.response.send_message(result)
            else:
                await ctx.response.send_message(f"API 요청 실패: {response.status}")
                


def add_log(target, command, details='No Details'):
    timezone_kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(timezone_kst).strftime('%Y-%m-%dT%H:%M:%S+09:00')
    
    user = target.author if hasattr(target, 'author') else target.user
    username = user.display_name or str(user)
    
    msg = f"[{now}] {username}({user.id}) | {command} | {details}"

    with open(LOG_PATH, 'a', encoding='utf-8') as log_file:
        log_file.write(msg + '\n')
        
def add_test_log(target, command, details='No Details'):
    timezone_kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(timezone_kst).strftime('%Y-%m-%dT%H:%M:%S+09:00')
    
    user = target.author if hasattr(target, 'author') else target.user
    username = user.display_name or str(user)
    
    msg = f"[{now}] {username}({user.id}) | {command} | {details}"

    with open(TEST_LOG_PATH, 'a', encoding='utf-8') as log_file:
        log_file.write(msg + '\n')
    
    
def load_time_table():
    if os.path.exists(TIME_TABLE_PATH):
        try:
            with open(TIME_TABLE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Error decoding JSON from time_table.json")
            return {}
    return {}

def refresh_time_table(data):
    try:
        with open(TIME_TABLE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error writing to time_table.json: {e}")
        
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