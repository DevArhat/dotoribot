import FinanceDataReader as fdr

import os
import re
import sqlite3

import game

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOCK_TRADE_DB_PATH = os.path.join(BASE_DIR, 'dotori_stock.db')
STOCK_DATA_DB_PATH = os.path.join(BASE_DIR, 'stock_data.db')


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_connection():
    """dotori_stock.db 커넥션을 반환한다."""
    conn = sqlite3.connect(STOCK_TRADE_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_stock_db():
    """
    dotori_stock.db에 필요한 테이블을 생성하고,
    stock_data.db에서 keywords/stocks 테이블을 복제한다.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    # 1. 보유 주식 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_holdings (
            user_id TEXT NOT NULL,
            ticker  TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            avg_price BIGINT NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, ticker)
        )
    """)

    # 2. 거래 기록 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_transactions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        TEXT    NOT NULL,
            ticker         TEXT    NOT NULL,
            quantity       INTEGER NOT NULL,
            price_at_deal  BIGINT  NOT NULL,
            is_buy         BOOLEAN NOT NULL,
            transaction_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. stock_data.db 에서 keywords / stocks 테이블 복제 (성능 최적화)
    _replicate_stock_data(cursor)

    conn.commit()
    conn.close()


def _replicate_stock_data(cursor):
    """stock_data.db → dotori_stock.db 로 keywords, stocks 테이블을 복제한다."""
    # stocks 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            code          TEXT PRIMARY KEY,
            official_name TEXT NOT NULL
        )
    """)
    # keywords 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keywords (
            keyword TEXT PRIMARY KEY,
            code    TEXT NOT NULL
        )
    """)

    # 기존 데이터 삭제 후 재삽입 (동기화)
    if not os.path.exists(STOCK_DATA_DB_PATH):
        return

    src_conn = sqlite3.connect(STOCK_DATA_DB_PATH)
    src_cursor = src_conn.cursor()

    try:
        # stocks
        src_cursor.execute("SELECT code, official_name FROM stocks")
        stocks_rows = src_cursor.fetchall()
        cursor.execute("DELETE FROM stocks")
        cursor.executemany("INSERT INTO stocks (code, official_name) VALUES (?, ?)", stocks_rows)

        # keywords
        src_cursor.execute("SELECT keyword, code FROM keywords")
        keywords_rows = src_cursor.fetchall()
        cursor.execute("DELETE FROM keywords")
        cursor.executemany("INSERT INTO keywords (keyword, code) VALUES (?, ?)", keywords_rows)
    finally:
        src_conn.close()


# ---------------------------------------------------------------------------
# 종목 조회 헬퍼
# ---------------------------------------------------------------------------

_SPACE_REMOVER = re.compile(r'\s')


def resolve_ticker(name: str) -> str:
    """
    종목명 또는 별칭을 받아서 티커 코드를 반환한다.
    6자리 영숫자 티커이면 그대로 반환한다.
    
    Raises:
        ValueError: 매칭되는 티커가 없을 때
    """
    name = _SPACE_REMOVER.sub('', name).strip().upper()

    # 6자리 영숫자 티커인 경우 그대로 반환
    if bool(re.fullmatch(r'[A-Z0-9]{6}', name)):
        return name

    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM keywords WHERE keyword = ?", (name,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]

    raise ValueError(f"'{name}'에 해당하는 종목을 찾을 수 없습니다.")


def get_stock_display_name(ticker: str) -> str:
    """티커 → 공식 종목명 변환. 없으면 티커를 그대로 반환."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT official_name FROM stocks WHERE code = ?", (ticker,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else ticker


def get_current_price(ticker: str) -> int:
    """
    FinanceDataReader를 호출하여 현재(최근 종가) 가격을 반환한다.
    On Demand 호출만 수행.
    
    Raises:
        RuntimeError: 가격 조회 실패 시
    """
    try:
        df = fdr.DataReader(ticker, start="", end="")
        if df is None or df.empty:
            raise ValueError("Empty DataFrame")
        return int(df.iloc[-1]['Close'])
    except Exception as e:
        raise RuntimeError(f"'{ticker}' 주가 조회 실패: {e}")


# ---------------------------------------------------------------------------
# 매매 로직
# ---------------------------------------------------------------------------

def buy_stock(user_id: str, ticker: str, quantity: int) -> dict:
    """
    주식을 구매한다.
    
    Args:
        user_id: 유저 ID (str)
        ticker: 종목 티커
        quantity: 구매 수량
    
    Returns:
        dict: {
            'ticker', 'display_name', 'price', 'quantity',
            'total_cost', 'balance_after'
        }
    
    Raises:
        ValueError: 수량이 0 이하이거나 잔액 부족 시
        RuntimeError: 가격 조회 실패 시
    """
    if quantity <= 0:
        raise ValueError("구매 수량은 1 이상이어야 합니다.")

    price = get_current_price(ticker)
    total_cost = price * quantity

    # 잔액 확인
    balance = game.get_balance(user_id)
    if balance < total_cost:
        raise ValueError(
            f"도토리가 부족합니다! (필요: {total_cost:,} / 보유: {balance:,})"
        )

    conn = _get_connection()
    cursor = conn.cursor()

    # 1. 기존 보유 확인
    cursor.execute(
        "SELECT quantity, avg_price FROM stock_holdings WHERE user_id = ? AND ticker = ?",
        (user_id, ticker)
    )
    row = cursor.fetchone()

    if row:
        old_qty, old_avg = row
        new_qty = old_qty + quantity
        # 평균 매수가 재계산: (기존금액 + 신규금액) / 총수량
        new_avg = (old_avg * old_qty + price * quantity) // new_qty
        cursor.execute(
            "UPDATE stock_holdings SET quantity = ?, avg_price = ? WHERE user_id = ? AND ticker = ?",
            (new_qty, new_avg, user_id, ticker)
        )
    else:
        cursor.execute(
            "INSERT INTO stock_holdings (user_id, ticker, quantity, avg_price) VALUES (?, ?, ?, ?)",
            (user_id, ticker, quantity, price)
        )

    # 2. 거래 기록
    cursor.execute(
        "INSERT INTO stock_transactions (user_id, ticker, quantity, price_at_deal, is_buy) VALUES (?, ?, ?, ?, 1)",
        (user_id, ticker, quantity, price)
    )

    conn.commit()
    conn.close()

    # 3. game_data.db 잔액 차감
    _deduct_balance(user_id, total_cost)

    balance_after = game.get_balance(user_id)
    display_name = get_stock_display_name(ticker)

    return {
        'ticker': ticker,
        'display_name': display_name,
        'price': price,
        'quantity': quantity,
        'total_cost': total_cost,
        'balance_after': balance_after
    }


def sell_stock(user_id: str, ticker: str, quantity: int) -> dict:
    """
    주식을 판매한다.
    
    Args:
        user_id: 유저 ID (str)
        ticker: 종목 티커
        quantity: 판매 수량
    
    Returns:
        dict: {
            'ticker', 'display_name', 'price', 'quantity',
            'total_revenue', 'avg_buy_price', 'profit', 'profit_rate',
            'balance_after'
        }
    
    Raises:
        ValueError: 보유하지 않거나 수량 초과 시
        RuntimeError: 가격 조회 실패 시
    """
    if quantity <= 0:
        raise ValueError("판매 수량은 1 이상이어야 합니다.")

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT quantity, avg_price FROM stock_holdings WHERE user_id = ? AND ticker = ?",
        (user_id, ticker)
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        display_name = get_stock_display_name(ticker)
        raise ValueError(f"'{display_name}'({ticker})을(를) 보유하고 있지 않습니다.")

    held_qty, avg_price = row
    if held_qty < quantity:
        conn.close()
        raise ValueError(
            f"보유 수량이 부족합니다. (보유: {held_qty}주 / 요청: {quantity}주)"
        )

    price = get_current_price(ticker)
    total_revenue = price * quantity
    profit = (price - avg_price) * quantity
    profit_rate = ((price - avg_price) / avg_price * 100) if avg_price > 0 else 0.0

    new_qty = held_qty - quantity
    if new_qty == 0:
        cursor.execute(
            "DELETE FROM stock_holdings WHERE user_id = ? AND ticker = ?",
            (user_id, ticker)
        )
    else:
        cursor.execute(
            "UPDATE stock_holdings SET quantity = ? WHERE user_id = ? AND ticker = ?",
            (new_qty, user_id, ticker)
        )

    # 거래 기록
    cursor.execute(
        "INSERT INTO stock_transactions (user_id, ticker, quantity, price_at_deal, is_buy) VALUES (?, ?, ?, ?, 0)",
        (user_id, ticker, quantity, price)
    )

    conn.commit()
    conn.close()

    # game_data.db 잔액 증가
    _add_balance(user_id, total_revenue)

    balance_after = game.get_balance(user_id)
    display_name = get_stock_display_name(ticker)

    return {
        'ticker': ticker,
        'display_name': display_name,
        'price': price,
        'quantity': quantity,
        'total_revenue': total_revenue,
        'avg_buy_price': avg_price,
        'profit': profit,
        'profit_rate': profit_rate,
        'balance_after': balance_after
    }


def get_portfolio(user_id: str) -> list:
    """
    유저의 보유 주식 목록을 반환한다.
    
    Returns:
        list of dict: [{'ticker', 'display_name', 'quantity', 'avg_price'}, ...]
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ticker, quantity, avg_price FROM stock_holdings WHERE user_id = ? ORDER BY ticker",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    result = []
    for ticker, qty, avg_price in rows:
        result.append({
            'ticker': ticker,
            'display_name': get_stock_display_name(ticker),
            'quantity': qty,
            'avg_price': avg_price
        })
    return result


def get_portfolio_with_prices(user_id: str) -> dict:
    """
    유저의 보유 주식 목록에 현재가를 추가하여 반환한다.
    각 종목별 현재가를 On Demand로 조회한다.
    
    Returns:
        dict: {
            'holdings': [
                {
                    'ticker', 'display_name', 'quantity', 'avg_price',
                    'current_price', 'profit', 'profit_rate',
                    'eval_amount', 'invest_amount'
                }, ...
            ],
            'total_invest': int,
            'total_eval': int,
            'total_profit': int,
            'total_profit_rate': float
        }
    """
    portfolio = get_portfolio(user_id)

    if not portfolio:
        return {
            'holdings': [],
            'total_invest': 0,
            'total_eval': 0,
            'total_profit': 0,
            'total_profit_rate': 0.0
        }

    holdings = []
    total_invest = 0
    total_eval = 0

    for item in portfolio:
        ticker = item['ticker']
        qty = item['quantity']
        avg_price = item['avg_price']

        try:
            current_price = get_current_price(ticker)
        except RuntimeError:
            current_price = 0  # 조회 실패 시 0으로 표시

        invest_amount = avg_price * qty
        eval_amount = current_price * qty
        profit = eval_amount - invest_amount
        profit_rate = ((current_price - avg_price) / avg_price * 100) if avg_price > 0 else 0.0

        holdings.append({
            'ticker': ticker,
            'display_name': item['display_name'],
            'quantity': qty,
            'avg_price': avg_price,
            'current_price': current_price,
            'profit': profit,
            'profit_rate': profit_rate,
            'eval_amount': eval_amount,
            'invest_amount': invest_amount
        })

        total_invest += invest_amount
        total_eval += eval_amount

    total_profit = total_eval - total_invest
    total_profit_rate = ((total_eval - total_invest) / total_invest * 100) if total_invest > 0 else 0.0

    return {
        'holdings': holdings,
        'total_invest': total_invest,
        'total_eval': total_eval,
        'total_profit': total_profit,
        'total_profit_rate': total_profit_rate
    }


# ---------------------------------------------------------------------------
# game_data.db 잔액 조작 헬퍼 (game.py 활용)
# ---------------------------------------------------------------------------

def _deduct_balance(user_id: str, amount: int):
    """game_data.db에서 잔액을 차감한다."""
    game_conn = sqlite3.connect(os.path.join(BASE_DIR, 'game_data.db'))
    game_cursor = game_conn.cursor()

    # money 테이블이 있는지 확인 (game.init_db()가 이미 호출된 상태 가정)
    game_cursor.execute(
        "UPDATE money SET current_amount = current_amount - ? WHERE user_id = ?",
        (amount, user_id)
    )
    # game_result에 기록
    game_cursor.execute(
        "INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)",
        (user_id, -amount)
    )

    game_conn.commit()
    game_conn.close()


def _add_balance(user_id: str, amount: int):
    """game_data.db에서 잔액을 증가시킨다."""
    game_conn = sqlite3.connect(os.path.join(BASE_DIR, 'game_data.db'))
    game_cursor = game_conn.cursor()

    game_cursor.execute(
        """INSERT INTO money (user_id, current_amount) VALUES (?, ?)
           ON CONFLICT(user_id) DO UPDATE SET current_amount = current_amount + ?""",
        (user_id, amount, amount)
    )
    game_cursor.execute(
        "INSERT INTO game_result (user_id, money_fluctuation) VALUES (?, ?)",
        (user_id, amount)
    )

    game_conn.commit()
    game_conn.close()
