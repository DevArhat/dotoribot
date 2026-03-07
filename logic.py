import datetime
import math
import os

import aiohttp

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
    return f"""# {result_tuple[1]}
```python
# 설명도토리
거래소: {result_tuple[0]:,} 골드
인원수: {dotoris} 명
입찰가: {result_tuple[1]:,} 골드
분배금: {result_tuple[2]:,} 골드
판매금: {result_tuple[3]:,} 골드```"""

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