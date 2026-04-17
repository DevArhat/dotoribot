import discord
from discord import app_commands, ui
from discord.ext import commands

from logic import LostArkGuardian, SpaceController, calc_logic, calc_logic_v2
from logic import show_time_table_for_individual as stt
from logic import show_schedule_for_individual as ssfi
import lostark_api_module as api_module

sc = SpaceController()

def lostark_utils_commands(bot, bot_msg, bot_defer):

    @bot.hybrid_command(name="이번주가디언", description="이번주 가디언 정보")
    async def send_weekly_guardian_info(ctx):
        bot.add_log(ctx, "/이번주가디언")
        g = LostArkGuardian().get_lostark_weekly_info()
        add_msg = ''
        if g[1] == "스콜라키아":
            add_msg = '안녕하세요이슬비기상술사입니다스콜은제가배럭으로도자주찾는가디언이고제가사랑하는정말경이로운가디언이죠이쿨감의매력을이천삼십년저와함께찾아보시지않겠어요스콜에서만나요편린을위하여다함께나가자1750가디언스콜라키아'
        msg = (f"# {g[1]} ({g[2]})\n{g[0]}\n{add_msg}")
        await bot_msg(ctx, msg)

    @bot.hybrid_command(name="다음주가디언", description="다음주 가디언 정보")
    async def send_next_week_guardian_info(ctx):
        bot.add_log(ctx, "/다음주가디언")
        g = LostArkGuardian().get_lostark_weekly_info()
        add_msg = ''
        if g[4] == "스콜라키아":
            add_msg = '안녕하세요이슬비기상술사입니다스콜은제가배럭으로도자주찾는가디언이고제가사랑하는정말경이로운가디언이죠이쿨감의매력을이천삼십년저와함께찾아보시지않겠어요스콜에서만나요편린을위하여다함께나가자1750가디언스콜라키아'
        
        msg = (f"# {g[4]} ({g[5]})\n{g[3]}\n{add_msg}")
        await bot_msg(ctx, msg)

    @bot.tree.command(name="가디언예측", description="특정 날짜 가디언 예측하기")
    @app_commands.describe(
        year="년 (예: 2026)",
        month="월 (예: 3)",
        day="일 (예: 5)"
    )
    async def predict_guardian(ctx, year: int, month: int, day: int):
        bot.add_log(ctx, "/가디언예측", f"{year}-{month}-{day}")
        g = LostArkGuardian().get_lostark_weekly_info_predict(year, month, day)
        
        msg = (f"""# {g[1]} ({g[2]})\n{g[0]}""")
        await bot_msg(ctx, msg)

    @bot.hybrid_command(name="골드설정", description="레벨별로 어느 컨텐츠 골드를 끄고 켤지 알랴줌")
    async def show_gold_setting(ctx):
        summary_msg = "## 선요약\n1710: 성당X\n1720: 세노X\n1730,1740: 성당X\n1750: 4하X"

        with open('gold_settings.jpg', 'rb') as f:
            picture = discord.File(f)
            await ctx.send(summary_msg, file=picture)
        
    @bot.hybrid_command(name="내시간표", description="내 시간표 보기 ※ 수동 입력이라 부정확할 수 있음")
    async def show_my_time_table(ctx):
        bot.add_log(ctx, "/내시간표")
        await bot_msg(ctx, stt(ctx), ephemeral=True)

    @bot.hybrid_command(name="내일정", description="내 시간표 보기 (요일별 정리) ※ 수동 입력이라 부정확할 수 있음")
    async def show_my_schedule(ctx):
        bot.add_log(ctx, "/내일정")
        result = ssfi(ctx)

        # Embed 생성
        embed = discord.Embed(
            title=f"📅 {result['period']}",
            description=f"**주의: 부정확할 수 있습니다. 꼭 /시트 를 확인해 주세요!!**",
            color=discord.Color.blue(),
        )

        # 오늘 일정 필드
        embed.add_field(
            name=f"🐿️ 오늘의 일정 ({result['today_count']}개)",
            value=result['today_msg'] if result['today_msg'] else "오늘은 일정이 없어요! 🐿️",
            inline=False,
        )

        # 요일별 필드 (mm/dd(요일) 형태 타이틀)
        for day_name, entries in result['schedule_by_day'].items():
            field_title = result['day_labels'].get(day_name, day_name)
            field_value = "\n".join(entries) if entries else "일정 없는 날 🐿️"
            embed.add_field(
                name=field_title,
                value=field_value,
                inline=True,
            )

        embed.set_footer(text=f"이번주 일정: {result['total_remaining']}개")

        await bot_msg(ctx, content=f"<@{result['user_id']}> 님의 일정", embed=embed, ephemeral=True)


    @bot.hybrid_command(name="쌀", description="경매 쌀산기")
    @app_commands.describe(
        거래소="경매템 가격",
        컨텐츠인원="몇인팟 컨텐츠임?"
    )
    async def calculate(ctx, 거래소: int, 컨텐츠인원: int):
        logic_response = calc_logic(거래소, 컨텐츠인원)
        
        response_text = logic_response[0]
        response_tuple = logic_response[1]
        
        if type(response_tuple) == tuple:
            bot.add_log(ctx,
                    "/쌀",
                    f"가격: {거래소}, 인원수: {컨텐츠인원}, 추천입찰가: {response_tuple[1]:,}G, 분배금: {response_tuple[2]:,}G, 판매금: {response_tuple[3]:,}G")
            await bot_msg(ctx, response_text)
        else:
            bot.add_log(ctx,
                        "/쌀",
                        f"가격: {거래소}, 인원수: {컨텐츠인원}, 응답: {logic_response}"
                        )
            await bot_msg(ctx, logic_response)


    @bot.hybrid_command(name="선점쌀", description="경매 쌀산기 (선점가)")
    @app_commands.describe(
        거래소="경매템 가격",
        컨텐츠인원="몇인팟 컨텐츠임?"
    )
    async def calculate_v2(ctx, 거래소: int, 컨텐츠인원: int):
        logic_response = calc_logic_v2(거래소, 컨텐츠인원)
        
        response_text = logic_response[0]
        response_tuple = logic_response[1]
        
        if type(response_tuple) == tuple:
            bot.add_log(ctx,
                    "/쌀",
                    f"가격: {거래소}, 인원수: {컨텐츠인원}, 추천입찰가: {response_tuple[1]:,}G, 분배금: {response_tuple[2]:,}G, 판매금: {response_tuple[3]:,}G")
            # interaction.response.send_message를 통해 답장을 보냅니다.
            await bot_msg(ctx, response_text)
        else:
            bot.add_log(ctx,
                        "/쌀",
                        f"가격: {거래소}, 인원수: {컨텐츠인원}, 응답: {logic_response}"
                        )
            await bot_msg(ctx, logic_response) # type: ignore

    @bot.hybrid_command(name="정보", description="전투정보실 기본정보를 가져옵니다")
    @app_commands.describe(
        캐릭터명="캐릭터명"
    )
    async def show_character_info(ctx, 캐릭터명: str):
        await bot_defer(ctx, "전정실 검색 중... ⌨️️🐿️")

        lapi = api_module.Lostark_Api(bot.session)
        result = await lapi.get_info(캐릭터명)

        if isinstance(result, str):
            bot.add_log(ctx, "/정보", f"[실패] {result}")
            return await bot_msg(ctx, result, ephemeral=True)
        
        parsed_result = api_module.parse_character(result)
        embed_result = api_module.char_result_to_embed(parsed_result)
        bot.add_log(ctx, "/정보", f"[성공] {parsed_result['char_name']}")


        await bot_msg(ctx, content="전정실 보고왔다! 🐿️", embed=embed_result)

    @bot.hybrid_command(name="부캐", description="전투레벨이 60 이상인 부캐 목록")
    @app_commands.describe(
        캐릭터명="캐릭터명"
    )
    async def get_siblings(ctx, 캐릭터명: str):
        await bot_defer(ctx, "호구조사 중... 📊🐿️")

        lapi = api_module.Lostark_Api(bot.session)
        result = await lapi.get_siblings(캐릭터명)

        if isinstance(result, str):
            bot.add_log(ctx, f"/부캐 {캐릭터명}", f"[실패] {result}")
            return await bot_msg(ctx, result, ephemeral=True)
        
        parsed_result = api_module.parse_siblings_list(result)
        embed_result = api_module.siblings_list_to_embed(parsed_result)
        bot.add_log(ctx, f"/부캐 {캐릭터명}", f"[성공]")


        await bot_msg(ctx, content="호구조사 완료! 🐿️", embed=embed_result)

    
    @bot.hybrid_command(name="깐평", description="닉네임을 공백이나 쉼표로 구분해서 입력 (2~7)")
    @app_commands.describe(
        캐릭터명="캐릭터명을 공백 or 쉼표로 구분해서 입력"
    )
    async def average_power(ctx, *, 캐릭터명: str):
        # 쉼표를 공백으로 바꾼 뒤 리스트화 및 중복 제거
        name_list = list(dict.fromkeys(캐릭터명.replace(',', ' ').split()))
        count = len(name_list)

        # 2~7명 제한 체크
        if not (2 <= count <= 7):
            return await bot_msg(ctx, f"❌ 닉네임은 2~7개 사이로 입력해주세요! (현재 {count}개)", ephemeral=True)

        await bot_defer(ctx, "깐평 계산 중... 🐿️")

        lapi = api_module.Lostark_Api(bot.session)
        
        import asyncio
        tasks = [lapi.get_info(name) for name in name_list]
        results = await asyncio.gather(*tasks)

        powers = []
        found_names = []
        failed_names = []

        for name, result in zip(name_list, results):
            if isinstance(result, dict) and 'ArmoryProfile' in result:
                profile = result.get('ArmoryProfile')
                if profile and profile.get('CombatPower') is not None:
                    try:
                        # 전투력 문자열에서 쉼표 제거 후 float 변환
                        cp = float(str(profile['CombatPower']).replace(',', ''))
                        powers.append(cp)
                        found_names.append(name)
                        continue
                    except (ValueError, TypeError):
                        pass
            
            failed_names.append(name)

        if not powers:
            return await bot_msg(ctx, "캐릭터 정보를 가져오는데 실패했습니다. 닉네임을 확인해주세요.")

        avg_power = sum(powers) / len(powers)
        
        msg = f"## 깐평!\n"
        msg += f"📊 **평균투력: {avg_power:,.2f}**\n"
        
        # 각 캐릭터별 전투력 나열
        for name, result in zip(name_list, results):
            if isinstance(result, dict) and 'ArmoryProfile' in result:
                profile = result.get('ArmoryProfile')
                if profile and profile.get('CombatPower') is not None:
                    try:
                        official_name = profile.get('CharacterName', name)
                        cp = float(str(profile['CombatPower']).replace(',', ''))
                        msg += f"{official_name}: {cp:,.2f}\n"
                    except (ValueError, TypeError):
                        pass

        if failed_names:
            msg += f"\n❌ 실패: {', '.join(failed_names)}\n"
        
        bot.add_log(ctx, "/깐평", f"평균: {avg_power:,.2f} ({len(found_names)}명)")
        await bot_msg(ctx, msg)

    @bot.hybrid_command(name="쌀섬", description="오늘 or 가까운 날짜의 쌀섬")
    async def show_gold_island(ctx):
        await bot_defer(ctx, "쌀섬 찾으러 다녀올게! 🐿️")

        lapi = api_module.Lostark_Api(bot.session)
        result = await lapi.get_gold_island()

        if isinstance(result, str):
            bot.add_log(ctx, "/쌀섬", f"[실패] {result}")
            return await bot_msg(ctx, result, ephemeral=True)
        
        parsed_result = api_module.parse_gold_island_data(result)
        embed_result = api_module.gold_island_to_embed(parsed_result)
        bot.add_log(ctx, "/쌀섬", f"[성공] {embed_result.title}")

        await bot_msg(ctx, content="쌀섬 다녀왔다! 🐿️", embed=embed_result)


    @bot.hybrid_command(name="아비도스", description="거래소에서 아비도스 가격 검색")
    async def show_abydos(ctx):
        await bot_defer(ctx, "거래소 검색 중... 🐿️")

        lapi = api_module.Lostark_Api(bot.session)
        result = await lapi.get_abydos_price()

        if isinstance(result, str):
            bot.add_log(ctx, "/아비도스", f"[실패] {result}")
            return await bot_msg(ctx, result, ephemeral=True)
        
        data = result.get('Items') or []
        if not data:
            bot.add_log(ctx, "/아비도스", "[실패] Items가 비어있음")
            return await bot_msg(ctx, "아비도스 검색 결과가 없어요! 🐿️", ephemeral=True)

        embeds = []
       
        
        for item in data:
            embed_temp = discord.Embed(
                title=item['Name'],
                description="조사 완료! 🐿️",
                color=discord.Color.gold(),
            )
            embed_temp.add_field(
                name="현재 최저가",
                value=f"{item['CurrentMinPrice']}",
                inline=True
            )
            embed_temp.add_field(
                name="어제 평균가",
                value=f"{item['YDayAvgPrice']}",
                inline=True
            )
            embed_temp.add_field(
                name="최근 거래가",
                value=f"{item['RecentPrice']}",
                inline=True
            )
            embed_temp.set_thumbnail(url=item['Icon'])
            embeds.append(embed_temp)
        await bot_msg(ctx, content="아비도스 가격 조사 완료! 🐿️", embeds=embeds)