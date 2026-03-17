import os
import random
import sqlite3
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GAME_DB_PATH = os.path.join(BASE_DIR, 'game_data.db')

# 게임 승리 보상 비율 (10% 수수료 제외 후 90% 지급)
WIN_REWARD_RATE = 0.9

def apply_win_fee(profit: int) -> int:
    """승리 시 얻는 순이익에서 수수료를 제외한 금액을 반환한다."""
    if profit <= 0:
        return profit
    return int(profit * WIN_REWARD_RATE)

# 아이템 정보 정의 (사전 형태로 관리하여 추후 확장이 용이하게 함)
ITEMS = {
    "high_interest": {
        "name": "적금 통장",
        "price": 500000,
        "desc": "매일 자정(00시)마다 현재 잔액의 5%를 이자로 받습니다."
    },
    "cheat_dice": {
        "name": "사기 주사위",
        "price": 1000000,
        "desc": "올인만 할 수 있으며, 승리/패배/무승부 확률이 60/25/15 %로 변경됩니다. 판매 시 일정 확률로 도토리의 절반을 잃습니다."
    },
    "golden_acorn": {
        "name": "황금 도토리",
        "price": 1500000,
        "desc": "승리 시 0.5% 확률로 베팅 금액의 30배를 획득합니다."
    },
    "strong_acorn": {
        "name": "돈줘 강화",
        "price": 2000000,
        "desc": "/돈줘 금액이 2배 증가합니다."
    },
    "acorn_loan": {
        "name": "땡겨쓰기",
        "price": 3000000,
        "desc": "/돈많이줘 를 사용할 수 있습니다: 15,000,000개/1일"
    }
}
# ITEMS_TEMP = {
#     "high_interest": {
#         "name": "적금 통장",
#         "price": 500000,
#         "desc": "매일 자정(00시)마다 현재 잔액의 5%를 이자로 받습니다."
#     },
#     "cheat_dice": {
#         "name": "사기 주사위",
#         "price": 1000000,
#         "desc": "올인만 할 수 있으며, 승리/패배/무승부 확률이 60/25/15 %로 변경됩니다. 판매 시 일정 확률로 도토리의 절반을 잃습니다."
#     },
#     "golden_acorn": {
#         "name": "황금 도토리",
#         "price": 1500000,
#         "desc": "승/무/패 확률 35/20/45, 승리 시 0.5% 확률로 베팅 금액의 30배를 획득합니다."
#     },
#     "chicken_dice": {
#         "name": "겁쟁이 주사위",
#         "price": 1500000,
#         "desc": "승/무/패 확률 60/10/30, 승리 시 베팅 금액의 40%만 획득합니다."
#     },
#     "beast_heart": {
#         "name": "야수의 심장",
#         "price": 1500000,
#         "desc": "승/무/패 확률 20/10/70, 매 승리 시마다 베팅 금액의 3배를 획득합니다."
#     },
#     "strong_acorn": {
#         "name": "돈줘 강화",
#         "price": 2000000,
#         "desc": "/돈줘 금액이 2배 증가합니다."
#     },
#     "acorn_loan": {
#         "name": "땡겨쓰기",
#         "price": 3000000,
#         "desc": "/돈많이줘 를 사용할 수 있습니다: 15,000,000개/1일"
#     }
# }

def _get_connection():
    """DB 커넥션을 반환한다."""
    conn = sqlite3.connect(GAME_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """테이블을 생성하고 기존 DB 스키마를 업데이트한다."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    # 1. 기존 money 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS money (
            user_id TEXT PRIMARY KEY,
            current_amount INTEGER NOT NULL DEFAULT 0,
            money_grant_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # [업데이트] money 테이블에 이자 수령일(last_interest_date) 컬럼 추가 (기존 DB 호환용)
    try:
        cursor.execute("ALTER TABLE money ADD COLUMN last_interest_date TEXT")
    except sqlite3.OperationalError:
        pass  # 이미 컬럼이 존재하면 무시
        
    # [업데이트] money 테이블에 땡겨쓰기 수령일(last_loan_date) 컬럼 추가 (기존 DB 호환용)
    try:
        cursor.execute("ALTER TABLE money ADD COLUMN last_loan_date TEXT")
    except sqlite3.OperationalError:
        pass  # 이미 컬럼이 존재하면 무시
        
    # 2. 기존 game_result 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_result (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL REFERENCES money(user_id),
            money_fluctuation INTEGER NOT NULL
        )
    """)
    
    # 3. 유저의 아이템 보유를 관리하는 inventory 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            user_id TEXT NOT NULL REFERENCES money(user_id),
            item_id TEXT NOT NULL,
            purchased_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, item_id)
        )
    """)
    
    # 4. 결투 결과 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS duel_result (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_a TEXT NOT NULL REFERENCES money(user_id),
            user_b TEXT NOT NULL REFERENCES money(user_id),
            bet INTEGER NOT NULL,
            result TEXT NOT NULL,
            duel_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def get_balance(user_id: str) -> int:
    """유저의 현재 잔액을 조회한다. 없으면 0을 반환한다."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT current_amount FROM money WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def get_cooldown_info(user_id: str) -> tuple:
    """
    돈줘 쿨타임 정보를 반환한다.
    
    Returns:
        (True, None) - 돈줘 가능
        (False, available_at_kst: datetime) - 쿨타임 중, KST 기준 가능 시각
    """
    cooldown_seconds = 300
    KST = datetime.timezone(datetime.timedelta(hours=9))
    
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT money_grant_at FROM money WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return (True, None)
    
    grant_time = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    available_at_utc = grant_time + datetime.timedelta(seconds=cooldown_seconds)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    
    if now_utc >= available_at_utc:
        return (True, None)
    
    available_at_kst = available_at_utc.astimezone(KST)
    return (False, available_at_kst)

def give_money(user_id: str) -> tuple:
    """유저에게 500000원(강화 시 1000000원)을 지급한다. (5분 쿨타임)"""
    amount = 500000
    is_strong = has_item(user_id, "strong_acorn")
    if is_strong:
        amount = 1000000
        
    cooldown_seconds = 300  # 5분

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT current_amount, money_grant_at FROM money WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row is not None:
        grant_time = datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.utcnow() # 기존 코드 유지 (UTC 기준)
        elapsed = (now - grant_time).total_seconds()

        if elapsed < cooldown_seconds:
            remaining = int(cooldown_seconds - elapsed)
            conn.close()
            return (False, remaining, is_strong)

    cursor.execute("""
        INSERT INTO money (user_id, current_amount, money_grant_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            current_amount = current_amount + ?,
            money_grant_at = CURRENT_TIMESTAMP
    """, (user_id, amount, amount))

    cursor.execute("SELECT current_amount FROM money WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    
    # 지급 결과를 game_result 기록
    cursor.execute("INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)", (user_id, amount))
    
    conn.commit()
    conn.close()
    return (True, balance, is_strong)










# --- 아이템 관련 함수 ---
# 사기주사위, 황금도토리는 게임 관련 함수에서 관리

def show_item() -> str:
    """상점에서 판매 중인 아이템 목록을 마크다운 문자열로 반환한다."""
    item_info = "## 아이템 목록\n```markdown\n"
    for _, item_data in ITEMS.items():
        item_info += f"# {item_data['name']}\n"
        item_info += f"가격: {item_data['price']:,} 도토리\n"
        item_info += f"설명: {item_data['desc']}\n\n"
    item_info += "```"
    return item_info

def get_inventory_by_userid(user_id: str) -> tuple:
    """유저의 인벤토리 상태를 조회하여 문자열로 반환한다."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, purchased_at FROM inventory WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "현재 보유 중인 아이템이 없습니다.", []
    inventory_info = f"## 내 가방\n```markdown\n"
    items_list = []
    for row in rows:
        item_id = row[0]
        
        purchased_at_utc = datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        purchased_at_kst = purchased_at_utc + datetime.timedelta(hours=9)
        purchased_at = purchased_at_kst.strftime("%Y-%m-%d %H:%M:%S")
        
        # ITEMS 딕셔너리에서 아이템 이름 가져오기 (만약 삭제된 아이템이라면 알 수 없는 아이템으로 표기)
        item_name = ITEMS.get(item_id, {}).get("name", "알 수 없는 아이템")
        items_list.append(item_id)
        inventory_info += f"- {item_name} (구매일시: {purchased_at})\n"
        
    inventory_info += "```"
    return inventory_info, items_list        

def has_item(user_id: str, item_id: str) -> bool:
    """유저가 특정 아이템을 보유하고 있는지 확인한다."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
    result = cursor.fetchone()
    conn.close()
    return bool(result)

def give_money_loan(user_id: str) -> tuple:
    """
    '땡겨쓰기' 아이템 보유 시 하루 한 번 15,000,000원을 지급한다.
    
    Returns:
        (True, 잔액, 메시지) - 대출 성공
        (False, 0, 메시지) - 대출 실패 (아이템 미보유 혹은 이미 수령)
    """
    if not has_item(user_id, "acorn_loan"):
        return (False, 0, "땡겨쓰기 아이템이 필요합니다.")
        
    amount = 15000000
    # KST 기준 날짜 구하기
    KST = datetime.timezone(datetime.timedelta(hours=9))
    now_kst = datetime.datetime.now(KST)
    today_str = now_kst.strftime("%Y-%m-%d")
    
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT current_amount, last_loan_date FROM money WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    # 아직 money 테이블에 등록되지 않았다면 먼저 등록
    if not row:
        cursor.execute("INSERT INTO money (user_id, current_amount, last_loan_date) VALUES (?, ?, ?)", (user_id, amount, today_str))
        cursor.execute("INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)", (user_id, amount))
        conn.commit()
        conn.close()
        return (True, amount, "대출 성공")
        
    current_amount, last_loan_date = row
    
    # 오늘 이미 대출을 받았는지 확인
    if last_loan_date == today_str:
        conn.close()
        return (False, 0, "오늘은 이미 땡겨썼습니다! 내일 다시 오세요.")
        
    # 대출금 지급 및 지급일 갱신
    cursor.execute("""
        UPDATE money 
        SET current_amount = current_amount + ?, last_loan_date = ? 
        WHERE user_id = ?
    """, (amount, today_str, user_id))
    
    # 대출 내역을 game_result에 기록
    cursor.execute("INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)", (user_id, amount))
    
    cursor.execute("SELECT current_amount FROM money WHERE user_id = ?", (user_id,))
    new_balance = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    return (True, new_balance, "대출 성공")


def buy_item(user_id: str, item_id: str) -> tuple:
    """
    상점에서 아이템을 구매한다.
    
    Returns:
        (True, 잔액, 메시지) - 구매 성공
        (False, 잔액, 메시지) - 구매 실패 (잔액 부족, 이미 보유 등)
    """
    if item_id not in ITEMS:
        return (False, get_balance(user_id), "존재하지 않는 아이템입니다.")
        
    if has_item(user_id, item_id):
        return (False, get_balance(user_id), f"이미 '{ITEMS[item_id]['name']}'을(를) 보유하고 있습니다.")
        
    item_price = ITEMS[item_id]["price"]
    balance = get_balance(user_id)
    
    if balance < item_price:
        return (False, balance, f"잔액이 부족합니다. (가격: {item_price:,}원 / 현재 잔액: {balance:,}원)")
        
    conn = _get_connection()
    cursor = conn.cursor()
    
    # 1. 잔액 차감
    cursor.execute("UPDATE money SET current_amount = current_amount - ? WHERE user_id = ?", (item_price, user_id))
    # 2. 인벤토리에 아이템 추가
    cursor.execute("INSERT INTO inventory (user_id, item_id) VALUES (?, ?)", (user_id, item_id))
    
    cursor.execute("SELECT current_amount FROM money WHERE user_id = ?", (user_id,))
    new_balance = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    return (True, new_balance, f"'{ITEMS[item_id]['name']}'을(를) 구매했습니다!")

def sell_item(user_id: str, item_id: str) -> tuple:
    """
    유저가 보유 중인 아이템을 판매한다. 구매가의 60%를 환급한다.
    '사기 주사위'("cheat_dice") 판매 시 일정 확률로 보유 도토리의 절반을 잃음.

    Returns:
        (True, 잔액, 메시지, penalty_triggered) - 판매 성공
        (False, 잔액, 메시지, False) - 판매 실패 (아이템 미보유 등)
    """
    if item_id not in ITEMS:
        return (False, get_balance(user_id), "존재하지 않는 아이템입니다.", False)

    if not has_item(user_id, item_id):
        return (False, get_balance(user_id), f"'{ITEMS[item_id]['name']}'을(를) 보유하고 있지 않습니다.", False)

    item_price = ITEMS[item_id]["price"]
    refund = int(item_price * 0.6)
    penalty_triggered = False

    conn = _get_connection()
    cursor = conn.cursor()

    # 1. 인벤토리에서 아이템 제거
    cursor.execute("DELETE FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
    
    # 2. 잔액 환급 (기본)
    cursor.execute(
        "INSERT INTO money (user_id, current_amount) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET current_amount = current_amount + ?",
        (user_id, refund, refund)
    )

    # 3. 사기 주사위 페널티 확인
    if item_id == "cheat_dice":
        cursor.execute("SELECT current_amount FROM money WHERE user_id = ?", (user_id,))
        balance_after_refund = cursor.fetchone()[0]
        
        # 기본 확률 5%
        penalty_prob = 5
        if balance_after_refund > 1000000000:
            extra_prob = (balance_after_refund - 1000000000) // 50000000
            penalty_prob += extra_prob
        
        penalty_prob = min(penalty_prob, 60)
        
        if random.randint(1, 100) <= penalty_prob:
            penalty_triggered = True
            penalty_amount = balance_after_refund // 2
            cursor.execute("UPDATE money SET current_amount = current_amount - ? WHERE user_id = ?", (penalty_amount, user_id))
            cursor.execute("INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)", (user_id, -penalty_amount))

    cursor.execute("SELECT current_amount FROM money WHERE user_id = ?", (user_id,))
    new_balance = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    msg = f"'{ITEMS[item_id]['name']}'을(를) **{refund:,}개**에 판매했습니다! (구매가의 60%)"
    return (True, new_balance, msg, penalty_triggered)


def claim_interest(user_id: str) -> tuple:
    """
    적금통장 아이템 보유 시 일일 이자를 지급한다.
    
    Returns:
        (True, 이자금액, 갱신된잔액) - 이자 지급 성공
        (False, 0, 현재잔액) - 이자 지급 대상 아님 (아이템 미보유 또는 이미 수령)
    """
    if not has_item(user_id, "high_interest"):
        return (False, 0, get_balance(user_id))
        
    # KST 기준 날짜 구하기
    KST = datetime.timezone(datetime.timedelta(hours=9))
    now_kst = datetime.datetime.now(KST)
    today_str = now_kst.strftime("%Y-%m-%d")
    
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT current_amount, last_interest_date FROM money WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return (False, 0, 0)
        
    current_amount, last_interest_date = row
    
    # 오늘 이미 이자를 받았는지 확인
    if last_interest_date == today_str:
        conn.close()
        return (False, 0, current_amount)
        
    # 이자 계산 (현재 잔액의 5%)
    interest_amount = int(current_amount * 0.05)
    
    if interest_amount > 0:
        cursor.execute("""
            UPDATE money 
            SET current_amount = current_amount + ?, last_interest_date = ? 
            WHERE user_id = ?
        """, (interest_amount, today_str, user_id))
        
        # 이자 내역을 game_result에 기록 (옵션)
        cursor.execute("INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)", (user_id, interest_amount))
        
    conn.commit()
    
    cursor.execute("SELECT current_amount FROM money WHERE user_id = ?", (user_id,))
    new_balance = cursor.fetchone()[0]
    conn.close()
    
    return (True, interest_amount, new_balance)

def claim_interest_for_all() -> int:
    """
    '적금통장'을 보유한 모든 유저에게 일괄적으로 이자를 지급한다.
    (스케줄러나 봇의 Task Loop에서 매일 자정에 한 번 호출하기 적합)
    
    Returns:
        int: 이자를 지급받은 유저 수
    """
    # KST 기준 날짜 구하기
    KST = datetime.timezone(datetime.timedelta(hours=9))
    now_kst = datetime.datetime.now(KST)
    today_str = now_kst.strftime("%Y-%m-%d")
    
    conn = _get_connection()
    cursor = conn.cursor()
    
    # 고금리 상품을 보유하고 있으면서, 오늘 이자를 아직 받지 않은 유저 조회
    cursor.execute("""
        SELECT m.user_id, m.current_amount 
        FROM money m
        JOIN inventory i ON m.user_id = i.user_id
        WHERE i.item_id = 'high_interest' 
          AND (m.last_interest_date IS NULL OR m.last_interest_date != ?)
    """, (today_str,))
    
    targets = cursor.fetchall()
    count = 0
    
    for user_id, current_amount in targets:
        interest_amount = int(current_amount * 0.05)
        if interest_amount > 0:
            # 1. 잔액 및 수령일 업데이트
            cursor.execute("""
                UPDATE money 
                SET current_amount = current_amount + ?, last_interest_date = ? 
                WHERE user_id = ?
            """, (interest_amount, today_str, user_id))
            
            # 2. 이자 수령 내역 기록
            cursor.execute("INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)", (user_id, interest_amount))
            count += 1
            
    conn.commit()
    conn.close()
    
    return count









# --- 도토리게임 관련 기능 ---

def get_ranking(limit: int = 10) -> list:
    """보유 금액 내림차순으로 유저 목록을 조회한다."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, current_amount 
        FROM money 
        ORDER BY current_amount DESC 
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_rich_players(threshold: int = 1000000000) -> tuple:
    """보유 금액이 임계값 이상인 유저 목록과 그들 총액의 합계를 조회한다."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    # 1. 임계값 이상의 유저 조회
    cursor.execute("""
        SELECT user_id, current_amount 
        FROM money 
        WHERE current_amount >= ?
        ORDER BY current_amount DESC
    """, (threshold,))
    rows = cursor.fetchall()
    
    # 2. 해당 유저들의 총액 합계 조회
    cursor.execute("""
        SELECT SUM(current_amount) 
        FROM money 
        WHERE current_amount >= ?
    """, (threshold,))
    total_sum = cursor.fetchone()[0] or 0
    
    conn.close()
    return rows, total_sum

def duel(challenger_id: str, opponent_id: str, bet: int) -> tuple:
    """
    두 유저 간 결투를 수행한다.
    45% 도전자 승리, 45% 상대방 승리, 10% 무승부
    
    Returns:
        (result, challenger_balance, opponent_balance)
        result: "challenger_win" | "opponent_win" | "draw"
    Raises:
        ValueError: 잔액 부족 시 (부족한 유저의 user_id를 메시지에 포함)
    """
    challenger_balance = get_balance(challenger_id)
    opponent_balance = get_balance(opponent_id)
    
    if challenger_balance < bet:
        raise ValueError(f"challenger_insufficient")
    if opponent_balance < bet:
        raise ValueError(f"opponent_insufficient")
    
    roll = random.random()
    
    if roll < 0.45:
        result = "challenger_win"
        c_change = apply_win_fee(bet)
        o_change = -bet
        duel_result_code = "A"
    elif roll < 0.90:
        result = "opponent_win"
        c_change = -bet
        o_change = apply_win_fee(bet)
        duel_result_code = "B"
    else:
        result = "draw"
        c_change = 0
        o_change = 0
        duel_result_code = "D"
    
    conn = _get_connection()
    cursor = conn.cursor()
    if c_change != 0:
        cursor.execute("UPDATE money SET current_amount = current_amount + ? WHERE user_id = ?", (c_change, challenger_id))
        cursor.execute("UPDATE money SET current_amount = current_amount + ? WHERE user_id = ?", (o_change, opponent_id))
        cursor.execute("INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)", (challenger_id, c_change))
        cursor.execute("INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)", (opponent_id, o_change))
    cursor.execute("INSERT INTO duel_result (user_a, user_b, bet, result) VALUES (?, ?, ?, ?)", (challenger_id, opponent_id, bet, duel_result_code))
    conn.commit()
    conn.close()
    
    return (result, get_balance(challenger_id), get_balance(opponent_id))


def gift(sender_id: str, receiver_id: str, amount: int) -> tuple:
    """
    유저가 다른 유저에게 도토리를 선물한다.
    보내는 사람은 100% 차감, 받는 사람은 수수료 5% 제외 후 95% 지급.
    
    Returns:
        (sender_balance, receiver_balance, actual_received)
    Raises:
        ValueError: 잔액 부족 시
    """
    sender_balance = get_balance(sender_id)
    
    if sender_balance < amount:
        raise ValueError(f"sender_insufficient")
        
    actual_received = int(amount * 0.95)
    
    conn = _get_connection()
    cursor = conn.cursor()
    
    # 송금자 차감
    cursor.execute("UPDATE money SET current_amount = current_amount - ? WHERE user_id = ?", (amount, sender_id))
    
    # 수신자 지급 (없을 수도 있으므로 INSERT OR UPDATE 방식을 사용)
    cursor.execute("""
        INSERT INTO money (user_id, current_amount) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET current_amount = current_amount + ?
    """, (receiver_id, actual_received, actual_received))
    
    # 기록 (송금자)
    cursor.execute("INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)", (sender_id, -amount))
    # 기록 (수신자)
    cursor.execute("INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)", (receiver_id, actual_received))
    
    conn.commit()
    conn.close()
    
    return (get_balance(sender_id), get_balance(receiver_id), actual_received)




def play_game(user_id: str, bet: int) -> tuple:
    """
    가위바위보 게임을 수행한다.
    '사기 주사위' 아이템 보유 시 확률이 보정된다.
    """
    if bet <= 0:
        raise ValueError("베팅할 도토리는 어딨어?")

    current_balance = get_balance(user_id)
    if current_balance < bet:
        raise ValueError(f"도토리가 모자라! (현재 잔액: {current_balance:,}원)")

    # [수정] 아이템 보유 여부에 따른 확률 분기
    has_cheat_dice = has_item(user_id, "cheat_dice")
    has_golden_acorn = has_item(user_id, "golden_acorn")
    fluctuation = 0

    result = _game_roll(has_cheat_dice, has_golden_acorn)

    if "item_" in result:
        if "win" in result:
            fluctuation = current_balance
        elif "lose" in result:
            fluctuation = -current_balance
        else:
            fluctuation = 0
    else:
        if "win" in result:
            fluctuation = bet
        elif "lose" in result:
            fluctuation = -bet
        else:
            fluctuation = 0

    if "win_jackpot" in result:
        fluctuation *= 30
        
    if "win" in result and fluctuation > 0:
        fluctuation = apply_win_fee(fluctuation)

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO money (user_id, current_amount) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET current_amount = current_amount + ?
    """, (user_id, fluctuation, fluctuation))

    cursor.execute("""
        INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)
    """, (user_id, fluctuation))

    cursor.execute("SELECT current_amount FROM money WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return (result, has_cheat_dice, has_golden_acorn, fluctuation, balance)

def repeat_game(user_id: str, bet: int, repeat: int = 10) -> tuple:
    """
    게임을 여러 번 반복 수행한다.

    Returns:
        (total_fluctuation, actual_rounds, wins, losses, draws, jackpot_count,
         has_cheat_dice, has_golden_acorn, balance)
    """
    if bet <= 0:
        raise ValueError("베팅할 도토리는 어딨어?")
    if repeat <= 0:
        raise ValueError("한번은 해야지!!")
    if repeat > 100:
        raise ValueError("그렇게 많이는 못해! 중간에 까먹어!")

    current_balance = get_balance(user_id)
    if current_balance < bet:
        raise ValueError(f"도토리가 모자라! (현재 잔액: {current_balance:,}원)")

    has_cheat_dice = has_item(user_id, "cheat_dice")
    has_golden_acorn = has_item(user_id, "golden_acorn")

    total_fluctuation = 0
    wins = 0
    losses = 0
    draws = 0
    jackpot_count = 0
    actual_rounds = 0

    conn = _get_connection()
    cursor = conn.cursor()

    for _ in range(repeat):
        # 사기 주사위가 아닌 경우 잔액이 베팅금 미만이면 조기 종료
        if not has_cheat_dice and current_balance < bet:
            break
        # 사기 주사위인 경우 잔액이 0이면 조기 종료
        if has_cheat_dice and current_balance <= 0:
            break

        actual_rounds += 1
        result = _game_roll(has_cheat_dice, has_golden_acorn)

        if "item_" in result:
            if "win" in result:
                fluctuation = current_balance
            elif "lose" in result:
                fluctuation = -current_balance
            else:
                fluctuation = 0
        else:
            if "win" in result:
                fluctuation = bet
            elif "lose" in result:
                fluctuation = -bet
            else:
                fluctuation = 0

        if "win_jackpot" in result:
            fluctuation *= 30
            jackpot_count += 1
            
        if "win" in result and fluctuation > 0:
            fluctuation = apply_win_fee(fluctuation)

        if "win" in result:
            wins += 1
        elif "lose" in result:
            losses += 1
        else:
            draws += 1

        total_fluctuation += fluctuation
        current_balance += fluctuation

        cursor.execute("""
            INSERT INTO money (user_id, current_amount) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET current_amount = current_amount + ?
        """, (user_id, fluctuation, fluctuation))

        cursor.execute("""
            INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)
        """, (user_id, fluctuation))

    cursor.execute("SELECT current_amount FROM money WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return (total_fluctuation, actual_rounds, wins, losses, draws, jackpot_count,
            has_cheat_dice, has_golden_acorn, balance)

def _game_roll(has_cheat_dice: bool, has_golden_acorn: bool):
    if has_cheat_dice:
        results, weights = ['item_win', 'item_lose', 'item_draw'], [60, 25, 15]
    else:
        results, weights = ['lose', 'win', 'draw'], [40, 40, 20]
    result = random.choices(results, weights=weights, k=1)[0]

    if "win" in result and has_golden_acorn:
        jackpot_r = random.random()
        jackpot_r *= 100
        if jackpot_r < 0.5:
            result += "_jackpot"

    return result

# 스크립트 실행 시 DB 초기화 (수정된 스키마 반영)
if __name__ == "__main__":
    init_db()