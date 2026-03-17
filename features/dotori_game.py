import discord
from discord import app_commands
from discord.ext import commands
import game
from logic import SpaceController
import random

sc = SpaceController()

def dotori_game_commands(bot, bot_msg):

    @bot.hybrid_command(name="돈줘", description="도토리 500만개를 지급받습니다 (5분 쿨타임)")
    async def give_money(ctx):
        user_id = str(ctx.author.id)
        success, value, is_strong = game.give_money(user_id)

        if success:
            effect_text = "\n💪 **돈줘 강화** 효과 적용됨! (2배 지급)" if is_strong else ""
            amount_text = "10,000,000" if is_strong else "5,000,000"
            
            bot.add_log(ctx, "/돈줘", f"지급 후 잔액: {value:,}")
            await bot_msg(ctx, f"💰 도토리 {amount_text}개가 지급되었습니다!{effect_text}\n🏦 현재 도토리: **{value:,}개**")
        else:
            import datetime as dt
            KST = dt.timezone(dt.timedelta(hours=9))
            now_kst = dt.datetime.now(KST)
            _, available_at = game.get_cooldown_info(user_id)
            if available_at:
                if available_at.date() > now_kst.date():
                    time_text = f"내일 {available_at.strftime('%H:%M:%S')}"
                else:
                    time_text = available_at.strftime('%H:%M:%S')
            else:
                time_text = "알 수 없음"
            bot.add_log(ctx, "/돈줘", f"쿨타임 중 ({time_text})")
            await bot_msg(ctx, f"{bot.angry_koko} 탕진좀 그만해!\n**{time_text}**에 줄게요.", ephemeral=True)

    @bot.hybrid_command(name="돈많이줘", description="도토리 150,000,000개를 땡겨씁니다 (아이템 필요, 1일 1회)")
    async def give_money_loan(ctx):
        user_id = str(ctx.author.id)
        success, new_balance, msg = game.give_money_loan(user_id)
        
        if success:
            bot.add_log(ctx, "/돈많이줘", f"지급 후 잔액: {new_balance:,}")
            await bot_msg(ctx, f"💸 **150,000,000개** 땡겨쓰기 완료!\n🏦 현재 도토리: **{new_balance:,}개**")
        else:
            bot.add_log(ctx, "/돈많이줘", f"실패 사유: {msg}")
            await bot_msg(ctx, f"❌ {msg}", ephemeral=True)

    @bot.hybrid_command(name="게임", description="도토리를 걸고 게임을 합니다.")
    @app_commands.describe(베팅="베팅할 도토리 갯수")
    async def play_game(ctx, 베팅: int):
        user_id = str(ctx.author.id)
        try:
            result, player_has_item, has_golden_acorn, fluctuation, balance = game.play_game(user_id, 베팅)
        except ValueError as e:
            bot.add_log(ctx, "/게임", f"실패: {e}")
            await bot_msg(ctx, f"❌ {e}", ephemeral=True)
            return
        item_info = ""
        if player_has_item:
            item_info = "\n사기 주사위 아이템을 보유하고 있어 강제 올인이 적용됩니다!"    

        if "win" in result:
            if "jackpot" in result:
                emoji = "🎇"
                result_text = f"✨✨황금 도토리의 축복! +{fluctuation:,}개✨✨"
            else:
                emoji = "🎉"
                result_text = f"승리! +{fluctuation:,}개"
        elif "lose" in result:
            emoji = "☠️"
            result_text = f"패배! {fluctuation:,}개"
        else:
            emoji = "🐿️"
            result_text = "무승부! 금액 변동 없음"

        result_text += item_info

        if balance == 0:
            result_text += "\n작은구름 밑에 묻어둔 도토리가 모두 사라졌습니다...😱"

        if player_has_item:
            actual_bet = balance - fluctuation
            display_price = f"{베팅:,}개 -> {actual_bet:,}개"
        else:
            display_price = f"{베팅:,}개"

        bot.add_log(ctx, "/게임", f"베팅: {베팅:,}, 결과: {result}, 변동: {fluctuation:,}, 잔액: {balance:,}, 주사위보유: {player_has_item}, 황금도토리보유: {has_golden_acorn}" )
        await bot_msg(ctx, f"""## {emoji} {result_text}
```
베팅도토리: {display_price}
현재도토리: {balance:,}개
```""")

    @bot.hybrid_command(name="반복게임", description="10회재련버튼")
    @app_commands.describe(베팅="베팅할 도토리 갯수", 반복="반복횟수 (기본 10, 1 ~ 10)")
    async def repeat_game(ctx, 베팅: int, 반복: int = 10):
        user_id = str(ctx.author.id)
        try:
            total_fluctuation, actual_rounds, wins, losses, draws, jackpot_count, has_cheat_dice, has_golden_acorn, balance = game.repeat_game(user_id, 베팅, 반복)
        except ValueError as e:
            bot.add_log(ctx, "/반복게임", f"실패: {e}")
            await bot_msg(ctx, f"❌ {e}", ephemeral=True)
            return

        # 결과 이모지 및 텍스트
        if total_fluctuation > 0:
            emoji = "🎉"
            change_text = f"+{total_fluctuation:,}"
        elif total_fluctuation < 0:
            emoji = "☠️"
            change_text = f"{total_fluctuation:,}"
        else:
            emoji = "🐿️"
            change_text = "±0"

        jackpot_text = f" (🎇황금도토리 {jackpot_count}회!)" if jackpot_count > 0 else ""
        item_text = " [사기 주사위 보유중]" if has_cheat_dice else ""

        if balance == 0:
            broke_text = "\n작은구름 밑에 묻어둔 도토리가 모두 사라졌습니다...😱"
        else:
            broke_text = ""
        if has_cheat_dice:
            result_bot_msg = f"""## {emoji} 반복게임 결과{item_text}{jackpot_text}
```
시행횟수: {actual_rounds}회 (승 {wins} / 패 {losses} / 무 {draws})
총 변동 : {change_text}개
현재잔액: {balance:,}개
```{broke_text}"""
        else:
            result_bot_msg = f"""## {emoji} 반복게임 결과{item_text}{jackpot_text}
```
베팅금액: {베팅:,}개
시행횟수: {actual_rounds}회 (승 {wins} / 패 {losses} / 무 {draws})
총 변동 : {change_text}개
현재잔액: {balance:,}개
```{broke_text}"""

        bot.add_log(ctx, "/반복게임", f"베팅: {베팅:,}, 시행: {actual_rounds}/{반복}, 총변동: {total_fluctuation:,}, 잔액: {balance:,}, 황금도토리: {has_golden_acorn}, 사기주사위: {has_cheat_dice}")
        await bot_msg(ctx, result_bot_msg)
    

    @bot.hybrid_command(name="내돈", description="내 도토리 확인")
    async def my_money(ctx):
        user_id = str(ctx.author.id)
        balance = game.get_balance(user_id)
        can_claim, available_at = game.get_cooldown_info(user_id)
        if can_claim:
            cooldown_text = "🟢 돈줘 **가능**"
        else:
            cooldown_text = f"🔴 돈줘 가능 시각: **{available_at.strftime('%H:%M:%S')}**"
        bot.add_log(ctx, "/내돈", f"잔액: {balance:,}")
        await bot_msg(ctx, f"🏦 현재 도토리: **{balance:,}개**\n{cooldown_text}")
    
    @bot.hybrid_command(name="랭킹", description="도토리 보유 랭킹")
    async def ranking(ctx):
        await ctx.defer()
        rows = game.get_ranking(10)
        if not rows:
            await bot_msg(ctx, "아직 아무도 도토리를 가지고 있지 않아요!")
            return
        
        medals = ["🥇", "🥈", "🥉"]
        ranking_text = "## 🏆 도토리 랭킹\n```markdown\n"
        for i, (user_id, amount) in enumerate(rows):
            medal = medals[i] if i < 3 else f"{i+1}."
            try:
                member = ctx.guild.get_member(int(user_id)) or await ctx.guild.fetch_member(int(user_id))
                name = member.display_name
            except Exception:
                name = f"유저({user_id})"
            ranking_text += f"{medal} {name} : {amount:,}개\n"
        ranking_text += "```"
        
        bot.add_log(ctx, "/랭킹")
        await bot_msg(ctx, content=ranking_text)

    @bot.hybrid_command(name="불법도토리", description="저번 시즌의 불법도토리 유통규모 확인")
    async def rich_players(ctx):
        illegal_acorns = "지난 시즌 유통된 도토리는 1,209,088,405,857,655,800,000 개입니다.\n"
        illegal_acorns += "(약 12해 908경 개)\n\n"
        illegal_acrons += "이것은 지구상에 있는 모든 모래알의 합계보다 약 1000배 많은 도토리입니다!"

        await bot_msg(ctx, content=illegal_acorns)
        
    @bot.hybrid_command(name="내템", description="내가 구매한 아이템 확인")
    async def my_item(ctx):
        user_id = str(ctx.author.id)
        logic_result = game.get_inventory_by_userid(user_id)
        msg = logic_result[0]
        items = logic_result[1]
        bot.add_log(ctx, "/내템", f"아이템: {items}")
        await bot_msg(ctx, msg)
        
        
    @bot.hybrid_command(name="아이템", description="존재하는 아이템 종류 확인")
    async def show_items(ctx):
        items_info_msg = game.show_item()
        bot.add_log(ctx, "/아이템")
        await bot_msg(ctx, items_info_msg)

    class ShopView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            for item_key, item_data in game.ITEMS.items(): 
                # 버튼 인스턴스 생성
                button = discord.ui.Button(
                    label=f"{item_data['name']} ({item_data['price'] // 10000}만)",
                    style=self._get_style(item_key),
                    custom_id=f"buy_{item_key}"
                )
                # 버튼 클릭 시 실행될 콜백 함수 연결
                button.callback = self.create_callback(item_key)
                self.add_item(button)
        def _get_style(self, item_key):
            """아이템 키에 따라 버튼 색상을 정해주는 헬퍼 함수"""
            if "cheat" in item_key:
                return discord.ButtonStyle.danger
            elif "golden" in item_key or "loan" in item_key:
                return discord.ButtonStyle.success
            return discord.ButtonStyle.primary

        def create_callback(self, item_key):
            """클로저를 사용하여 각 버튼에 맞는 콜백 함수를 생성"""
            async def callback(interaction: discord.Interaction):
                await self.process_purchase(interaction, item_key)
            return callback

        async def process_purchase(self, interaction: discord.Interaction, item_key: str):
            user_id = str(interaction.user.id)
            logic_result = game.buy_item(user_id, item_key)
            purchase_successed = logic_result[0]
            successed_text = "성공" if purchase_successed else "실패"
            user_balance = logic_result[1]
            logic_msg = logic_result[2]
            
            msg = f"[구매{successed_text}] " + logic_msg + f"\n[현재잔고] **{user_balance:,}**개"
            
            item_name = game.ITEMS.get(item_key, {}).get("name", item_key)
            bot.add_log(interaction, "/상점", f"{successed_text}, 아이템: {item_key} ({item_name}), 잔액: {user_balance:,}")
            await bot_msg(interaction, msg, ephemeral=True)

        # @discord.ui.button(label="적금 통장 (50만)", style=discord.ButtonStyle.primary, custom_id="buy_high_interest")
        # async def btn_high_interest(self, interaction: discord.Interaction, button: discord.ui.Button):
        #     await self.process_purchase(interaction, "high_interest")

        # @discord.ui.button(label="사기 주사위 (100만)", style=discord.ButtonStyle.danger, custom_id="buy_cheat_dice")
        # async def btn_cheat_dice(self, interaction: discord.Interaction, button: discord.ui.Button):
        #     await self.process_purchase(interaction, "cheat_dice")

        # @discord.ui.button(label="황금 도토리 (150만)", style=discord.ButtonStyle.success, custom_id="buy_golden_acorn")
        # async def btn_golden_acorn(self, interaction: discord.Interaction, button: discord.ui.Button):
        #     await self.process_purchase(interaction, "golden_acorn")

        # @discord.ui.button(label="돈줘 강화 (200만)", style=discord.ButtonStyle.primary, custom_id="buy_strong_acorn")
        # async def btn_strong_acorn(self, interaction: discord.Interaction, button: discord.ui.Button):
        #     await self.process_purchase(interaction, "strong_acorn")

        # @discord.ui.button(label="땡겨쓰기 (300만)", style=discord.ButtonStyle.success, custom_id="buy_acorn_loan")
        # async def btn_acorn_loan(self, interaction: discord.Interaction, button: discord.ui.Button):
        #     await self.process_purchase(interaction, "acorn_loan")

    @bot.hybrid_command(name="상점", description="상점 UI를 열어 아이템 구매")
    async def buy_item_v2(ctx):
        view = ShopView()
        bot.add_log(ctx, "/상점")
        await ctx.send("# 상점! 구매를 원하는 아이템을 선택하세요\n" + game.show_item(), view=view, ephemeral=True)

    @bot.hybrid_command(name="구매", description="아이템 구매 (/상점 과 동일)")
    async def buy_item(ctx):
        await ctx.invoke(buy_item_v2)

    # @bot.hybrid_command(name="판매", description="보유 중인 아이템을 판매합니다 (구매가의 60% 환급)")
    # @app_commands.describe(아이템="판매할 아이템 이름 (사기주사위, 적금통장, 황금도토리)")
    # async def sell_item_cmd(ctx, 아이템: str):
    #     아이템 = sc.remove_space(아이템).lower()
    #     if "적금" in 아이템 or "통장" in 아이템:
    #         item_key = "high_interest"
    #     elif "사기" in 아이템 or "주사위" in 아이템:
    #         item_key = "cheat_dice"
    #     elif "황금" in 아이템 or "도토리" in 아이템:
    #         item_key = "golden_acorn"
    #     else:
    #         item_key = 아이템

    #     user_id = str(ctx.author.id)
    #     logic_result = game.sell_item(user_id, item_key)
    #     sell_successed = logic_result[0]
    #     successed_text = "성공" if sell_successed else "실패"
    #     user_balance = logic_result[1]
    #     logic_msg = logic_result[2]
    #     penalty_triggered = logic_result[3]

    #     msg = f"[판매{successed_text}] " + logic_msg + f"\n[현재잔고] **{user_balance:,}**개"
    #     if penalty_triggered:
    #         msg = f"{bot.angry_koko} **사기 주사위를 통한 도토리 불법 복제가 적발되었습니다!**\n도토리의 절반을 벌금으로 냈습니다.\n{msg}"

    #     bot.add_log(ctx, "/판매", f"{successed_text}, 아이템: {item_key} ({아이템}), 잔액: {user_balance:,}, 페널티: {penalty_triggered}")
    #     await bot_msg(ctx, msg, ephemeral=not sell_successed)

    class SellView(discord.ui.View):
        def __init__(self, items_list):
            super().__init__(timeout=60)
            
            options = []
            for item_id in items_list:
                item_name = game.ITEMS.get(item_id, {}).get("name", item_id)
                options.append(discord.SelectOption(label=item_name, value=item_id))
            
            if not options:
                self.stop()
                return

            self.select = discord.ui.Select(placeholder="판매할 아이템을 선택하세요", options=options)
            self.select.callback = self.select_callback
            self.add_item(self.select)

        async def select_callback(self, interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            item_key = self.select.values[0]
            
            logic_result = game.sell_item(user_id, item_key)
            sell_successed = logic_result[0]
            successed_text = "성공" if sell_successed else "실패"
            user_balance = logic_result[1]
            logic_msg = logic_result[2]
            penalty_triggered = logic_result[3]

            msg = f"[판매{successed_text}] " + logic_msg + f"\n[현재잔고] **{user_balance:,}**개"
            if penalty_triggered:
                msg = f"{bot.angry_koko} **사기 주사위를 통한 도토리 불법 복제가 적발되었습니다!**\n도토리의 절반을 벌금으로 냈습니다.\n{msg}"

            bot.add_log(interaction, "/판매", f"{successed_text}, 아이템: {item_key}, 잔액: {user_balance:,}, 페널티: {penalty_triggered}")
            
            # 모든 버튼 비활성화
            self.select.disabled = True
            await interaction.response.edit_message(view=self)
            await bot_msg(interaction, msg, ephemeral=not sell_successed)
            self.stop()

    @bot.hybrid_command(name="판매", description="보유 중인 아이템을 선택하여 판매합니다 (구매가의 60% 환급)")
    async def sell_item_v2(ctx):
        user_id = str(ctx.author.id)
        inventory_msg, items_list = game.get_inventory_by_userid(user_id)
        
        if not items_list:
            await bot_msg(ctx, "판매할 아이템이 없습니다.", ephemeral=True)
            return

        view = SellView(items_list)
        bot.add_log(ctx, "/판매")
        await ctx.send("# 어떤 아이템을 판매하시겠습니까?\n" + inventory_msg, view=view, ephemeral=True)







    @bot.hybrid_command(name="선물", description="다른 유저에게 도토리를 선물합니다. (수수료 5%)")
    @app_commands.describe(상대="선물할 상대방", 갯수="선물할 도토리 갯수")
    async def gift_command(ctx, 상대: discord.Member, 갯수: int):
        if 상대.bot:
            await bot_msg(ctx, "봇에게는 선물할 수 없어요! 🐿️", ephemeral=True)
            return
        if 상대.id == ctx.author.id:
            await bot_msg(ctx, "자기 자신에게 선물할 수 없어요! 🤔", ephemeral=True)
            return
        if 갯수 <= 0:
            await bot_msg(ctx, "선물할 갯수는 0보다 커야 해요! 🤔", ephemeral=True)
            return

        try:
            s_bal, r_bal, actual = game.gift(str(ctx.author.id), str(상대.id), 갯수)
        except ValueError as e:
            if "sender_insufficient" in str(e):
                await bot_msg(ctx, f"❌ {ctx.author.display_name}의 잔고가 {갯수:,}보다 적습니다.", ephemeral=True)
            else:
                await bot_msg(ctx, f"❌ 선물 중 오류가 발생했습니다.", ephemeral=True)
            return

        bot.add_log(ctx, "/선물", f"보낸사람: {ctx.author.display_name}, 받는사람: {상대.display_name}, 금액: {갯수:,}, 실지급액: {actual:,}")
        
        msg = f"## 🎁 선물 도착!\n{ctx.author.mention}이(가) {상대.mention}에게 도토리를 선물했습니다!"
        balance_msg = f"```\n[선물 내역]\n보낸 금액: {갯수:,}개 (수수료 5%)\n받은 금액: {actual:,}개\n\n{ctx.author.display_name} 잔액: {s_bal:,}개\n{상대.display_name} 잔액: {r_bal:,}개\n```"
        
        await bot_msg(ctx, msg + "\n" + balance_msg)


    class DuelView(discord.ui.View):
        def __init__(self, challenger, opponent, bet):
            super().__init__(timeout=30)
            self.challenger = challenger
            self.opponent = opponent
            self.bet = bet
            self.result = None

        @discord.ui.button(label="⚔️ 수락", style=discord.ButtonStyle.green)
        async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.opponent.id:
                await interaction.response.send_message("이 결투는 당신에게 온 것이 아닙니다!", ephemeral=True)
                return

            try:
                result, c_bal, o_bal = game.duel(str(self.challenger.id), str(self.opponent.id), self.bet)
            except ValueError as e:
                for child in self.children:
                    child.disabled = True  # type: ignore
                if "challenger" in str(e):
                    fail_msg = f"❌ {self.challenger.display_name}의 잔고가 {self.bet:,}보다 적습니다."
                else:
                    fail_msg = f"❌ {self.opponent.display_name}의 잔고가 {self.bet:,}보다 적습니다."
                await interaction.response.edit_message(content=fail_msg, view=self)
                self.stop()
                return

            if result == "challenger_win":
                msg = f"## ⚔️ {self.challenger.display_name} 승리!\n{self.challenger.mention}이(가) {self.opponent.mention}을(를) 이겼습니다!"
                c_change = f"+{game.apply_win_fee(self.bet):,}"
                o_change = f"-{self.bet:,}"
            elif result == "opponent_win":
                msg = f"## ⚔️ {self.opponent.display_name} 승리!\n{self.opponent.mention}이(가) {self.challenger.mention}을(를) 이겼습니다!"
                c_change = f"-{self.bet:,}"
                o_change = f"+{game.apply_win_fee(self.bet):,}"
            else:
                msg = f"## 🤝 무승부!\n{self.challenger.mention}과(와) {self.opponent.mention}의 결투가 무승부로 끝났습니다!"
                c_change = "±0"
                o_change = "±0"

            balance_msg = f"```\n베팅: {self.bet:,}개\n{self.challenger.display_name}: {c_change} → 잔액 {c_bal:,}개\n{self.opponent.display_name}: {o_change} → 잔액 {o_bal:,}개\n```"

            self.result = result
            for child in self.children:
                child.disabled = True  # type: ignore
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(msg + "\n" + balance_msg)
            self.stop()

        @discord.ui.button(label="🏳️ 거절", style=discord.ButtonStyle.red)
        async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.opponent.id:
                await interaction.response.send_message("이 결투는 당신에게 온 것이 아닙니다!", ephemeral=True)
                return

            for child in self.children:
                child.disabled = True  # type: ignore
            await interaction.response.edit_message(content=f"🏳️ {self.opponent.display_name}이(가) 결투를 거절했습니다.", view=self)
            self.stop()

        async def on_timeout(self):
            for child in self.children:
                child.disabled = True  # type: ignore
            # timeout 시 메시지 수정은 별도 처리 필요 (message 참조가 없으므로 pass)

    @bot.hybrid_command(name="결투", description="다른 유저에게 결투를 신청합니다")
    @app_commands.describe(상대="결투를 신청할 상대방", 베팅="베팅할 도토리 갯수")
    async def duel_command(ctx, 상대: discord.Member, 베팅: int):
        if 상대.bot:
            await bot_msg(ctx, "봇에게는 결투를 신청할 수 없어요! 🐿️")
            return
        if 상대.id == ctx.author.id:
            await bot_msg(ctx, "자기 자신에게 결투를 신청할 수 없어요! 🤔")
            return
        if 베팅 <= 0:
            await bot_msg(ctx, "베팅 금액은 0보다 커야 해요! 🤔", ephemeral=True)
            return

        challenger_balance = game.get_balance(str(ctx.author.id))
        if challenger_balance < 베팅:
            await bot_msg(ctx, f"❌ {ctx.author.display_name}의 잔고가 {베팅:,}보다 적습니다.", ephemeral=True)
            return

        view = DuelView(ctx.author, 상대, 베팅)
        bot.add_log(ctx, "/결투", f"도전자: {ctx.author.display_name}, 상대: {상대.display_name}, 베팅: {베팅:,}")
        msg = await ctx.send(f"## ⚔️ 결투 신청!\n{ctx.author.mention}이(가) {상대.mention}에게 **{베팅:,}개**의 도토리를 걸고 결투를 신청했습니다!\n30초 안에 수락 또는 거절해주세요.", view=view)

        timed_out = await view.wait()
        if timed_out:
            for child in view.children:
                child.disabled = True  # type: ignore
            await msg.edit(content=f"⏰ 결투 신청이 만료되었습니다.", view=view)    


    @bot.hybrid_command(name="강화", description="도토리 갑옷을 강화합니다.")
    @app_commands.describe(파괴방지="15, 16강에서 파괴 방지 적용 여부 (비용 2배)")
    async def starforce_cmd(ctx, 파괴방지: bool = False):
        user_id = str(ctx.author.id)
        try:
            is_success, log_messages, new_balance = game.attempt_user_starforce(user_id, 파괴방지)
        except ValueError as e:
            bot.add_log(ctx, "/강화", f"실패: {e}")
            await bot_msg(ctx, f"❌ {e}", ephemeral=True)
            return
            
        emoji = "✅" if is_success else "❌"
        if any("도토리묵" in msg for msg in log_messages):
            emoji = "💥"
            
        result_text = "\n".join(log_messages)
        
        bot.add_log(ctx, "/강화", f"성공여부: {is_success}, 파괴방지: {파괴방지}, 잔액: {new_balance:,}")
        await bot_msg(ctx, f"## {emoji} 강화 시도 결과\n```\n{result_text}\n\n현재 도토리: {new_balance:,}개\n```")

    # 원시고대 도토리게임
    @bot.hybrid_command(name="홀짝", description="홀, 짝 중에 하나 띄워줌")
    async def odd_or_even(ctx):
        result = random.choice(["홀", "짝"])
        bot.add_log(ctx, "/홀짝", f"결과: {result}")
        await bot_msg(ctx, f"# {result}")