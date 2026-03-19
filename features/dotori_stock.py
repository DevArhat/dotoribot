import discord
from discord import app_commands
from discord.ext import commands

import os

import dotori_stock_core as stock_core

def dotori_stock_commands(bot, bot_msg, bot_defer):

    @bot.hybrid_command(name="주식구매", description="주식을 구매합니다 (1원 = 1도토리)")
    @app_commands.describe(
        종목="회사명 or 티커 번호",
        수량="구매할 주식 수"
    )
    async def buy_stock_cmd(ctx, 종목: str, 수량: int):
        await bot_defer(ctx, defer_msg="🐿️ 주식 사러 가는 중...")
        user_id = str(ctx.author.id)

        try:
            ticker = stock_core.resolve_ticker(종목)
        except ValueError as e:
            bot.add_log(ctx, "/주식구매", f"실패 // 종목: {종목} // {e}")
            await bot_msg(ctx, f"❌ {e}", ephemeral=True)
            return

        try:
            result = stock_core.buy_stock(user_id, ticker, 수량)
        except (ValueError, RuntimeError) as e:
            bot.add_log(ctx, "/주식구매", f"실패 // 종목: {종목}({ticker}) // {e}")
            await bot_msg(ctx, f"❌ {e}", ephemeral=True)
            return

        profit_emoji = "📈"
        msg = f"""## {profit_emoji} 주식 구매 완료!
```
종목명: {result['display_name']} ({result['ticker']})
매수가: {result['price']:,}원
수  량: {result['quantity']:,}주
총비용: {result['total_cost']:,} 도토리
잔  액: {result['balance_after']:,} 도토리
```"""
        bot.add_log(ctx, "/주식구매", f"성공 // {result['display_name']}({ticker}) x{수량} @ {result['price']:,} // 잔액: {result['balance_after']:,}")
        await bot_msg(ctx, msg)

    @bot.hybrid_command(name="주식판매", description="보유 주식을 판매합니다 (1원 = 1도토리)")
    @app_commands.describe(
        종목="회사명 or 티커 번호",
        수량="판매할 주식 수"
    )
    async def sell_stock_cmd(ctx, 종목: str, 수량: int):
        await bot_defer(ctx, defer_msg="🐿️ 주식 팔러 가는 중...")
        user_id = str(ctx.author.id)

        try:
            ticker = stock_core.resolve_ticker(종목)
        except ValueError as e:
            bot.add_log(ctx, "/주식판매", f"실패 // 종목: {종목} // {e}")
            await bot_msg(ctx, f"❌ {e}", ephemeral=True)
            return

        try:
            result = stock_core.sell_stock(user_id, ticker, 수량)
        except (ValueError, RuntimeError) as e:
            bot.add_log(ctx, "/주식판매", f"실패 // 종목: {종목}({ticker}) // {e}")
            await bot_msg(ctx, f"❌ {e}", ephemeral=True)
            return

        # 수익/손실 이모지
        if result['profit'] > 0:
            profit_emoji = "📈"
            profit_text = f"+{result['profit']:,}"
        elif result['profit'] < 0:
            profit_emoji = "📉"
            profit_text = f"{result['profit']:,}"
        else:
            profit_emoji = "➖"
            profit_text = "0"

        msg = f"""## {profit_emoji} 주식 판매 완료!
```
종목명: {result['display_name']} ({result['ticker']})
매도가: {result['price']:,}원
수  량: {result['quantity']:,}주
매수가: {result['avg_buy_price']:,}원 (평균)
손  익: {profit_text} 도토리 ({result['profit_rate']:+.2f}%)
총수익: {result['total_revenue']:,} 도토리
잔  액: {result['balance_after']:,} 도토리
```"""
        bot.add_log(ctx, "/주식판매", f"성공 // {result['display_name']}({ticker}) x{수량} @ {result['price']:,} // 손익: {profit_text} // 잔액: {result['balance_after']:,}")
        await bot_msg(ctx, msg)

    @bot.hybrid_command(name="내주식", description="보유 주식 및 수익률 확인")
    async def my_stocks_cmd(ctx):
        await bot_defer(ctx, defer_msg="🐿️ 포트폴리오 조회 중...")
        user_id = str(ctx.author.id)

        try:
            data = stock_core.get_portfolio_with_prices(user_id)
        except Exception as e:
            bot.add_log(ctx, "/내주식", f"실패: {e}")
            await bot_msg(ctx, f"❌ 포트폴리오 조회 중 오류가 발생했습니다: {e}", ephemeral=True)
            return

        if not data['holdings']:
            bot.add_log(ctx, "/내주식", "보유 주식 없음")
            await bot_msg(ctx, "📋 보유 중인 주식이 없습니다.", ephemeral=True)
            return

        # 포트폴리오 테이블 구성
        lines = []
        for h in data['holdings']:
            if h['profit'] > 0:
                pl_text = f"+{h['profit']:,}"
                rate_text = f"+{h['profit_rate']:.2f}%"
            elif h['profit'] < 0:
                pl_text = f"{h['profit']:,}"
                rate_text = f"{h['profit_rate']:.2f}%"
            else:
                pl_text = "0"
                rate_text = "0.00%"

            lines.append(
                f"{h['display_name']} ({h['ticker']})\n"
                f"  보유: {h['quantity']:,}주 | 매수가: {h['avg_price']:,} | 현재가: {h['current_price']:,}\n"
                f"  평가금액: {h['eval_amount']:,} | 손익: {pl_text} ({rate_text})"
            )

        holdings_text = "\n\n".join(lines)

        # 총합 수익률
        if data['total_profit'] > 0:
            total_emoji = "📈"
            total_pl = f"+{data['total_profit']:,}"
        elif data['total_profit'] < 0:
            total_emoji = "📉"
            total_pl = f"{data['total_profit']:,}"
        else:
            total_emoji = "➖"
            total_pl = "0"

        msg = f"""## {total_emoji} 내 주식 포트폴리오
```
{holdings_text}

────────────────────────
총 투자금액: {data['total_invest']:,} 도토리
총 평가금액: {data['total_eval']:,} 도토리
총 손익    : {total_pl} 도토리 ({data['total_profit_rate']:+.2f}%)
```"""
        bot.add_log(ctx, "/내주식", f"종목 {len(data['holdings'])}개 // 총투자: {data['total_invest']:,} // 총평가: {data['total_eval']:,} // 총손익: {data['total_profit']:,}")
        await bot_msg(ctx, msg)
