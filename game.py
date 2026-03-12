import os
import random
import sqlite3
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GAME_DB_PATH = os.path.join(BASE_DIR, 'game_data.db')


def _get_connection():
    """DB 커넥션을 반환한다."""
    conn = sqlite3.connect(GAME_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """money, game_result 테이블을 생성한다 (없으면)."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS money (
            user_id TEXT PRIMARY KEY,
            current_amount INTEGER NOT NULL DEFAULT 0,
            money_grant_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_result (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL REFERENCES money(user_id),
            money_fluctuation INTEGER NOT NULL
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


def give_money(user_id: str) -> tuple:
    """
    유저에게 100000원을 지급한다.
    5분 쿨타임이 있으며, 쿨타임 내 재요청 시 지급하지 않는다.

    Returns:
        (True, 현재잔액) — 지급 성공
        (False, 남은초) — 쿨타임 중
    """
    amount = 100000
    cooldown_seconds = 300  # 5분

    conn = _get_connection()
    cursor = conn.cursor()

    # 사용자 조회
    cursor.execute("SELECT current_amount, money_grant_at FROM money WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row is not None:
        # 쿨타임 확인
        grant_time = datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.utcnow()
        elapsed = (now - grant_time).total_seconds()

        if elapsed < cooldown_seconds:
            remaining = int(cooldown_seconds - elapsed)
            conn.close()
            return (False, remaining)

    # 지급: UPSERT + money_grant_at 갱신
    cursor.execute("""
        INSERT INTO money (user_id, current_amount, money_grant_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            current_amount = current_amount + ?,
            money_grant_at = CURRENT_TIMESTAMP
    """, (user_id, amount, amount))

    cursor.execute("SELECT current_amount FROM money WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return (True, balance)


def play_game(user_id: str, bet: int) -> tuple:
    """
    가위바위보 게임을 수행한다.
    
    Args:
        user_id: 유저 ID (문자열)
        bet: 베팅 금액 (양수)
    
    Returns:
        (result, fluctuation, balance)
        result: "win" / "lose" / "draw"
        fluctuation: 금액 변동 (+bet, -bet, 0)
        balance: 게임 후 현재 잔액
    
    Raises:
        ValueError: 베팅 금액이 0 이하이거나 잔액보다 클 때
    """
    if bet <= 0:
        raise ValueError("베팅 금액은 0보다 커야 합니다.")

    current_balance = get_balance(user_id)
    if current_balance < bet:
        raise ValueError(f"잔액이 부족합니다. (현재 잔액: {current_balance:,}원)")

    # 40% 승리, 40% 패배, 20% 무승부
    roll = random.random()
    if roll < 0.4:
        result = "win"
        fluctuation = bet
    elif roll < 0.8:
        result = "lose"
        fluctuation = -bet
    else:
        result = "draw"
        fluctuation = 0

    conn = _get_connection()
    cursor = conn.cursor()

    # money 테이블 UPSERT
    cursor.execute("""
        INSERT INTO money (user_id, current_amount) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET current_amount = current_amount + ?
    """, (user_id, fluctuation, fluctuation))

    # game_result 테이블 INSERT
    cursor.execute("""
        INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)
    """, (user_id, fluctuation))

    # 갱신된 잔액 조회
    cursor.execute("SELECT current_amount FROM money WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return (result, fluctuation, balance)
