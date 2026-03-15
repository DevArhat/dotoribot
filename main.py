# tmux new -s bot
# tmux attach -t bot

import random
import os

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
import asyncio

from logic import *
import game

class DotoriBot(commands.Bot):

    def __init__(self, is_test, logger_func):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.voice_states = True
        super().__init__(command_prefix='!', intents=intents)
        self.add_log = logger_func
        self.angry_koko = os.getenv('ANGRY_KOKO')
        if is_test:
            self.CHAT_CHANNEL_ID = int(str(os.getenv('DOTORI_CHAT_CHANNEL_ID_TEST')))
        else:
            self.CHAT_CHANNEL_ID = int(str(os.getenv('DOTORI_CHAT_CHANNEL_ID')))
        
    async def setup_hook(self):
        await self.tree.sync()  # 슬래시 명령어 동기화
load_dotenv()

def build_bot(is_test, logger_func):        
    bot = DotoriBot(is_test, logger_func)
    sc = SpaceController()
    st = StockInfo()
    rd = RhythmDotori()
    game.init_db()
        

    @bot.event
    async def on_ready():
        try:
            midnight_interest_job.start()
            synced = await bot.tree.sync()
            print(f'{len(synced)}개의 명령어')  # type: ignore
        except Exception as e:
            print(f"Error syncing application commands: {e}")
        print(f'로그인 완료: {bot.user.name}')  # type: ignore
        print('--- 봇이 정상적으로 작동 중입니다 ---')
    

    # 응답 메시지 발송 공통 함수
    async def bot_msg(ctx, content="", embed=None, stickers=None, ephemeral=False):
        if isinstance(ctx, discord.Interaction):
            # @bot.tree.command 등에서 Interaction 객체가 직접 들어온 경우
            if ctx.response.is_done():
                await ctx.followup.send(content=content, embed=embed, ephemeral=ephemeral) # type: ignore
            else:
                await ctx.response.send_message(content=content, embed=embed, ephemeral=ephemeral) # type: ignore
        elif ctx.interaction:
            # hybrid_command를 통해 슬래시 명령어로 들어온 Context인 경우
            # Context.send는 내부적으로 interaction.response를 처리해줍니다.
            await ctx.send(content=content, embed=embed, stickers=stickers, ephemeral=ephemeral)
        else:
            # 일반 메시지 명령어(!명령어)로 들어온 Context인 경우
            await ctx.message.reply(content=content, embed=embed, stickers=stickers)


    @bot.hybrid_command(name="사용법")
    async def usage(ctx):
        help_text = """# 🐿️ 도토리봇 사용법
```markdown
# 일반 명령어
!사용법 : 도움말
/이번주가디언 : 이번주 가디언, 카드, 기간
/다음주가디언 : 다음주 가디언, 카드, 기간

# 링크 바로가기
/시트
/로아투두
/인벤, /10추, /30추
/지옥효율, /낙원추천

# 경매 계산기
/쌀 [가격] [인원수]
ㄴ 최적입찰가 계산기 (공평분배 기준)
/선점쌀 [가격] [인원수]
ㄴ 선점가 기준 최적입찰가 계산기

# 로아 유틸
/가디언예측 [년] [월] [일]
ㄴ 특정 날짜 가디언 예측하기

# 게임
/돈줘 : 도토리 100,000개 지급 (5분 쿨타임)
/게임 [베팅] : 도토리를 걸고 게임하기
/내돈 : 내 도토리 잔액 확인
/아이템 : 구매 가능한 아이템 목록 확인
/구매 [아이템] : 아이템 구매 (사기주사위, 적금통장)
/내템 : 내가 보유한 아이템 확인

# 음악
/노래 [유튜브 URL] : 노래 재생
/목록 : 현재 대기열 확인
/스킵 : 현재 곡 건너뛰기
/정지 : 재생 멈추고 대기열 초기화

# 뽑기 시뮬레이터
/뽑기 [게임명] [돌파]
ㄴ 원신, 붕스, 젠존제, 명조, 엔필 지원

# 주식
/주식 [티커 번호 or 회사명]
ㄴ 주가 보기 (KOSPI만 지원, ETF 일부 가능, 티커번호 권장)

# 로또
/로또추천 : 로또 번호 랜덤 추천

# 기타
!안녕 : 인사하기
/빠직 : 앵그리코코 출력
/에이메스 : 에이메스 이미지 4종 중 1개 랜덤 출력
/캡틴잭 : 그긴거 출력
/홀짝 : 홀 or 짝 출력
/뒤집기 [문구] : 입력한 문구를 거꾸로 뒤집어서 출력
```"""
        await ctx.send(help_text, ephemeral=True)



    # !안녕 명령어
    @bot.command(name="안녕")
    async def hello(ctx):
        bot.add_log(ctx, "!안녕")
        sticker = discord.Object(id=int(str(os.getenv('DOTORI_HI'))))
        await bot_msg(ctx, " ", stickers=[sticker])
        
    

    @bot.hybrid_command(name="뒤집기")
    async def reverse_text(ctx, *, text: str):
        # 파이썬의 슬라이싱을 이용하여 문자열을 거꾸로 뒤집습니다.
        reversed_text = text[::-1]
        bot.add_log(ctx, "/뒤집기", f"입력: {text}, 결과: {reversed_text}")
        await bot_msg(ctx, reversed_text)
        
    @bot.hybrid_command(name="빠직")
    async def angry_koko(ctx):
        bot.add_log(ctx, "/빠직")
        await bot_msg(ctx, f"<:AngryKoko:1421511652376842443>")
        
    @bot.hybrid_command(name="시트", description="도토리 레이드 시트 링크")
    async def send_sheet_link(ctx):
        bot.add_log(ctx, "/시트")
        await bot_msg(ctx, f"# [도토리 레이드 시트]({os.getenv('DOTORI_RAID_SHEET')})")
        
    @bot.hybrid_command(name="지옥효율", description="지옥 효율 계산 링크")
    async def send_hell_efficiency_link(ctx):
        bot.add_log(ctx, "/지옥효율")
        await bot_msg(ctx, f"# [지옥효율 바로가기](https://www.gcalc.kr/hell)")
        
    @bot.hybrid_command(name="낙원추천", description="낙원 장비 시너지 추천기 링크")
    async def send_paradise_recommendation_link(ctx):
        bot.add_log(ctx, "/낙원추천")
        await bot_msg(ctx, f"# [낙원추천 바로가기](https://codepen.io/ialgqfxp-the-animator/pen/NPrQxOx)")
        
    @bot.hybrid_command(name="로아투두", description="로아투두 링크")
    async def send_lostark_todo_link(ctx):
        bot.add_log(ctx, "/로아투두")
        await bot_msg(ctx, f"# [로아투두 바로가기](https://www.loatodo.com/)")
        
    @bot.hybrid_command(name="인벤", description="인벤 링크")
    async def send_inven_link(ctx):
        bot.add_log(ctx, "/인벤")
        await bot_msg(ctx, f"# [인벤 바로가기](https://lostark.inven.co.kr/)")
        
    @bot.hybrid_command(name="10추", description="10추글 링크")
    async def send_10pull_link(ctx):
        bot.add_log(ctx, "/10추")
        await bot_msg(ctx, f"# [10추글 바로가기](https://www.inven.co.kr/board/lostark/6271?my=chu)")

    @bot.hybrid_command(name="30추", description="30추글 링크")
    async def send_30pull_link(ctx):
        bot.add_log(ctx, "/30추")
        await bot_msg(ctx, f"# [30추글 바로가기](https://www.inven.co.kr/board/lostark/6271?my=chuchu)")

    @bot.hybrid_command(name="에이메스", description="에이메스 이미지")
    async def send_image(ctx):
        bot.add_log(ctx, "/에이메스")
        image_urls = [
            "https://pbs.twimg.com/media/HAzrgy0aQAAftah?format=jpg",
            "https://pbs.twimg.com/media/HA4Sa_HaEAAmhZt?format=jpg",
            "https://pbs.twimg.com/media/HA9tYRVbsAkc1jf?format=jpg",
            "https://pbs.twimg.com/media/HCdXGoGaMAAo9N9?format=jpg"
        ]
        image_url = random.choice(image_urls)
        embed = discord.Embed(title="에이메스", description="제가 당신의 자랑이었으면 좋겠어요. 제가 당신을 실망시키지 않았으면 좋겠어요.", color=0xeb9cb9)
        embed.set_image(url=image_url)
        await bot_msg(ctx, content="",embed=embed)

    @bot.hybrid_command(name="캡틴잭", description="캡틴잭 그긴거")
    async def send_captain_jack(ctx):
        try:
            with open(os.path.join(BASE_DIR, 'captain_jack.txt'), 'r', encoding='utf-8') as f:
                captain_jack = f.read()
            bot.add_log(ctx, "/캡틴잭")
        except FileNotFoundError:
            captain_jack = "이런! 캡틴잭이 제 저장장치를 부숴버렸어요!"
            bot.add_log(ctx, "/캡틴잭", "[오류] FileNotFoundError")
            
        await bot_msg(ctx, content=captain_jack)

    @bot.hybrid_command(name="이번주가디언", description="이번주 가디언 정보")
    async def send_weekly_guardian_info(ctx):
        bot.add_log(ctx, "/이번주가디언")
        g = LostArkGuardian().get_lostark_weekly_info()
        
        msg = (f"# {g[1]} ({g[2]})\n{g[0]}")
        await bot_msg(ctx, msg)

    @bot.hybrid_command(name="다음주가디언", description="다음주 가디언 정보")
    async def send_next_week_guardian_info(ctx):
        bot.add_log(ctx, "/다음주가디언")
        g = LostArkGuardian().get_lostark_weekly_info()
        
        msg = (f"# {g[4]} ({g[5]})\n{g[3]}")
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
        
        msg = (f"""# {g[1]} ({g[2]})
    {g[0]}""")
        await bot_msg(ctx, msg)

    # 슬래시 명령어 생성: 
    @bot.tree.command(name="쌀", description="경매 쌀산기")
    # 스페이스바를 눌렀을 때 뜰 입력칸(파라미터)에 대한 설명입니다.
    @app_commands.describe(
        거래소="경매템 가격",
        컨텐츠인원="몇인팟 컨텐츠임?"
    )
    async def calculate(interaction: discord.Interaction, 거래소: int, 컨텐츠인원: int):
        logic_response = calc_logic(거래소, 컨텐츠인원)
        
        response_text = logic_response[0]
        response_tuple = logic_response[1]
        
        if type(response_tuple) == tuple:
            bot.add_log(interaction,
                    "/쌀",
                    f"가격: {거래소}, 인원수: {컨텐츠인원}, 추천입찰가: {response_tuple[1]:,}G, 분배금: {response_tuple[2]:,}G, 판매금: {response_tuple[3]:,}G")
            # interaction.response.send_message를 통해 답장을 보냅니다.
            await bot_msg(interaction, response_text)
        else:
            bot.add_log(interaction,
                        "/쌀",
                        f"가격: {거래소}, 인원수: {컨텐츠인원}, 응답: {logic_response}"
                        )
            await bot_msg(interaction, logic_response) # type: ignore
    
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
    
        
    
    @bot.hybrid_command(name="홀짝", description="홀, 짝 중에 하나 띄워줌")
    async def odd_or_even(ctx):
        result = random.choice(["홀", "짝"])
        bot.add_log(ctx, "/홀짝", f"결과: {result}")
        await bot_msg(ctx, f"# {result}")
        

    @bot.tree.command(name="뽑기", description="뽑기 시뮬레이터")
    @app_commands.describe(
        game="원신, 붕스, 젠존제, 명조, 엔필",
        dolpa="숫자만, 명함은 0"
    )
    async def pull(ctx, game: str, dolpa: int):
        game_key = get_game_key(game)
        
        bot.add_log(ctx, "/뽑기", f"게임: {game}(매칭결과: {game_key}), 돌파: {dolpa}")

        result = run_vercel(game_key, dolpa)
        await bot_msg(ctx, result)
        
    @bot.hybrid_command(name="주식", description="주가 보기")
    @app_commands.describe(
        name="회사명 or 티커 번호"
    )
    async def get_stock_price(ctx, name):
        name = sc.remove_space(name).upper()
        data = st.get_stock_info(name)
        set_ephemeral = False
        if str(os.getenv('ANGRY_KOKO')) in data:
            bot.add_log(ctx, "/주식", f"실패 // 입력 데이터: {name} // Exception: {data.split('$')[1].strip()}")
            data = data.split('$')[0].strip()
            set_ephemeral = True
        else:
            bot.add_log(ctx, "/주식", f"성공 // 입력 데이터: {name}")
        await bot_msg(ctx, content=data, ephemeral=set_ephemeral)
    

    music_queues = {}
    inactive_timers = {}
    default_bot_volume=0.15

    async def start_inactivity_timer(ctx, voice_client):
        # 기존에 돌고 있는 타이머가 있다면 취소
        if ctx.guild.id in inactive_timers:
            inactive_timers[ctx.guild.id].cancel()

        async def timer():
            try:
                await asyncio.sleep(3)
                # 5분이 지났는데도 봇이 채널에 있고, 재생/일시정지 중이 아니라면 퇴장
                if voice_client.is_connected() and not voice_client.is_playing() and not voice_client.is_paused():
                    await voice_client.disconnect()
                    await ctx.send("나 나간다! 🐿️💨")
            except asyncio.CancelledError:
                # 누군가 5분 안에 새 노래를 틀어서 타이머가 취소된 경우
                pass

        # 타이머를 백그라운드 태스크로 실행하고 딕셔너리에 저장
        task = ctx.bot.loop.create_task(timer())
        inactive_timers[ctx.guild.id] = task

    def play_next(error, ctx, voice_client):
        if error:
            print(f"Player error: {error}")
        
        # 큐에 남은 곡이 있다면 다음 곡 재생
        if ctx.guild.id in music_queues and len(music_queues[ctx.guild.id]) > 0:
            next_song = music_queues[ctx.guild.id].pop(0)
            
            audio_source = discord.FFmpegPCMAudio(next_song['url'], **next_song['ffmpeg_options'])
            volume_transformer = discord.PCMVolumeTransformer(audio_source, volume=0.15) # 기본 볼륨 설정
            
            voice_client.play(volume_transformer, after=lambda e: play_next(e, ctx, voice_client))
            
            # 봇 루프를 사용해 Threadsafe하게 비동기 메시지 전송
            coro = next_song['ctx'].send(f"**{next_song['title']}**\n🎶 이어서 부를게요")
            asyncio.run_coroutine_threadsafe(coro, ctx.bot.loop)
        else:
            asyncio.run_coroutine_threadsafe(start_inactivity_timer(ctx, voice_client), ctx.bot.loop)

    @bot.hybrid_command(name="노래", aliases=["음악", "풍악", "재생", "리듬"], description="유튜브 URL을 주면 도토리가 노래를 해요")
    @app_commands.describe(
        url="유튜브 URL. 검색어도 되는데 검색결과가 부정확할 때가 있어요"
    )
    async def play_music(ctx, url: str):
        await ctx.defer()
        
        if not ctx.author.voice:
            await bot_msg(ctx, "어느 채널로 가야되는지 모르겠어! 😱")
            return
        channel = ctx.author.voice.channel
        voice_client = ctx.voice_client

        if voice_client is None:
            voice_client = await channel.connect()
        else:
            await voice_client.move_to(channel)

        msg = await ctx.send("노래 외우는 중.. 잠시만 기다려주세요...")

        # 3. yt-dlp로 스트리밍 URL 추출 (비동기 처리로 봇 멈춤 방지)
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: rd.ytdl.extract_info(url, download=False))
            
            if 'entries' in data:
                data = data['entries'][0]
                
            stream_url = data.get('url')
            title = data.get('title')
            
            # 곡 정보를 딕셔너리로 저장
            song_info = {
                'url': stream_url, 
                'title': title, 
                'ctx': ctx, 
                'ffmpeg_options': rd.ffmpeg_options
            }

            if ctx.guild.id not in music_queues:
                music_queues[ctx.guild.id] = []
                
            if ctx.guild.id in inactive_timers:
                inactive_timers[ctx.guild.id].cancel()
                del inactive_timers[ctx.guild.id]
            
            # 4. 이미 재생 중이거나 일시정지 상태인 경우 대기열에 추가
            if voice_client.is_playing() or voice_client.is_paused():
                music_queues[ctx.guild.id].append(song_info)
                await msg.edit(content=f"""**{title}**
📝 대기열에 추가했어요 """)
            else:
                # 볼륨 조절을 위해 PCMVolumeTransformer 사용 (기본값 0.5 = 50%)
                default_volume = 0.15
                audio_source = discord.FFmpegPCMAudio(stream_url, **rd.ffmpeg_options) # type: ignore
                volume_transformer = discord.PCMVolumeTransformer(audio_source, volume=default_volume)
                
                # after 콜백을 연결하여 현재 곡이 끝나면 play_next 함수가 실행되도록 함
                voice_client.play(volume_transformer, after=lambda e: play_next(e, ctx, voice_client))
                
                logger_func(ctx, "/노래", f"input: {url}, title: {title}, url: {stream_url}")
                await msg.edit(content=f"""**{title}**
🎶 오케이! 한번 불러볼게요.""")
            
        except Exception as e:
            logger_func(ctx, "/노래", f"input: {url}, error: {e}")
            await msg.edit(content="노래를 못찾겠어! 😱")

    @bot.hybrid_command(name="목록", aliases=["대기열", "큐", "queue"], description="현재 대기 중인 노래 목록")
    async def show_queue(ctx):
        if ctx.guild.id not in music_queues or not music_queues[ctx.guild.id]:
            await bot_msg(ctx, "신청곡 기다리는 중 🎵")
            return
        
        queue_list = music_queues[ctx.guild.id]
        queue_text = "📜 **현재 대기열** 📜\n"
        for i, song in enumerate(queue_list, 1):
            queue_text += f"**{i}.** `{song['title']}`\n"
        
        await bot_msg(ctx, queue_text)

    @bot.hybrid_command(name="스킵", aliases=["넘겨", "skip", "다음"], description="스킵")
    async def skip_music(ctx):
        voice_client = ctx.voice_client
        if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            voice_client.stop()
            await bot_msg(ctx, "알았어요. 다음 곡 부를게!")
        else:
            await bot_msg(ctx, "지금 재생 중인 노래가 없어! 🤔")
            
    @bot.hybrid_command(name="정지", aliases=["그만", "멈춰", "중지"], description="재생목록 비우기")
    async def clear_queue(ctx):
        voice_client = ctx.voice_client
        if voice_client:
            music_queues[ctx.guild.id] = []
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
                await bot_msg(ctx, "## ... (조용도토리)")
            else:
                await start_inactivity_timer(ctx, voice_client)
                await bot_msg(ctx, "노래를 다 까먹었어요!")
        else:
            await bot_msg(ctx, "지금 연결되어 있지 않아요!")
            
        
        

    @bot.event
    async def on_command_error(ctx, error):
        # 명령어 객체가 존재하지 않을 수 있으므로(예: 존재하지 않는 명령어 입력 시) 방어적 코드 작성
        command_name = ctx.command.name if ctx.command else "알 수 없는 명령어"
        error_type = type(error).__name__

        # 1. 모든 함수에 대해 전역 오류 핸들러로 동작
        await bot_msg(ctx, "👀 명령어를 알아들을 수 없거나 내부에서 오류가 발생했어요!")
        bot.add_log(ctx,f"/{command_name}", f"오류 발생 함수: {command_name}, 오류 타입: {error_type}, 오류 내용: {str(error)}")
        
        # 2. 오류가 발생한 함수와 발생 오류 타입을 print
        print(f"오류 발생 함수: {command_name}")
        print(f"오류 타입: {error_type}")
        
    @bot.event
    async def on_voice_state_update(member, before, after):
        """음성 채널에 봇만 남으면 대기열을 비우고 퇴장"""
        if member.bot:
            return 
        voice_client = member.guild.voice_client
        dotori_channel = bot.get_channel(bot.CHAT_CHANNEL_ID)
        
        if not voice_client:
            return
            
        if before.channel is not None and after.channel != before.channel:
            if before.channel.id == voice_client.channel.id:
                real_members = [m for m in voice_client.channel.members if not m.bot]
                
                if len(real_members) == 0:
                    if member.guild.id in music_queues:
                        music_queues[member.guild.id] = []
                    
                    if member.guild.id in inactive_timers:
                        inactive_timers[member.guild.id].cancel()
                        del inactive_timers[member.guild.id]
                    
                    await voice_client.disconnect()
                    if dotori_channel:
                        await dotori_channel.send("다들 어디간거야... 나도 나갈래 🐿️💦") # type: ignore

    ### 결투 시스템 ###

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
                c_change = f"+{self.bet:,}"
                o_change = f"-{self.bet:,}"
            elif result == "opponent_win":
                msg = f"## ⚔️ {self.opponent.display_name} 승리!\n{self.opponent.mention}이(가) {self.challenger.mention}을(를) 이겼습니다!"
                c_change = f"-{self.bet:,}"
                o_change = f"+{self.bet:,}"
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

    ### 가위바위보 게임 ###

    @bot.hybrid_command(name="돈줘", description="도토리 100,000개를 지급받습니다 (5분 쿨타임)")
    async def give_money(ctx):
        user_id = str(ctx.author.id)
        success, value, is_strong = game.give_money(user_id)

        if success:
            effect_text = "\n💪 **돈줘 강화** 효과 적용됨! (2배 지급)" if is_strong else ""
            amount_text = "200,000" if is_strong else "100,000"
            
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

    @bot.hybrid_command(name="돈많이줘", description="도토리 15,000,000개를 땡겨씁니다 (아이템 필요, 1일 1회)")
    async def give_money_loan(ctx):
        user_id = str(ctx.author.id)
        success, new_balance, msg = game.give_money_loan(user_id)
        
        if success:
            bot.add_log(ctx, "/돈많이줘", f"지급 후 잔액: {new_balance:,}")
            await bot_msg(ctx, f"💸 **15,000,000개** 땡겨쓰기 완료!\n🏦 현재 도토리: **{new_balance:,}개**")
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

        display_price = f"{베팅:,}개 -> {abs(fluctuation):,}" if player_has_item else f"{베팅:,}"

        bot.add_log(ctx, "/게임", f"베팅: {베팅:,}, 결과: {result}, 변동: {fluctuation:,}, 잔액: {balance:,}, 주사위보유: {player_has_item}, 황금도토리보유: {has_golden_acorn}" )
        await bot_msg(ctx, f"""## {emoji} {result_text}
```
베팅도토리: {display_price}개
현재도토리: {balance:,}개
```""")
    

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

        @discord.ui.button(label="적금 통장 (50만)", style=discord.ButtonStyle.primary, custom_id="buy_high_interest")
        async def btn_high_interest(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.process_purchase(interaction, "high_interest")

        @discord.ui.button(label="사기 주사위 (100만)", style=discord.ButtonStyle.danger, custom_id="buy_cheat_dice")
        async def btn_cheat_dice(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.process_purchase(interaction, "cheat_dice")

        @discord.ui.button(label="황금 도토리 (150만)", style=discord.ButtonStyle.success, custom_id="buy_golden_acorn")
        async def btn_golden_acorn(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.process_purchase(interaction, "golden_acorn")

        @discord.ui.button(label="돈줘 강화 (200만)", style=discord.ButtonStyle.primary, custom_id="buy_strong_acorn")
        async def btn_strong_acorn(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.process_purchase(interaction, "strong_acorn")

        @discord.ui.button(label="땡겨쓰기 (300만)", style=discord.ButtonStyle.success, custom_id="buy_acorn_loan")
        async def btn_acorn_loan(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.process_purchase(interaction, "acorn_loan")

    @bot.hybrid_command(name="상점", description="상점 UI를 열어 아이템 구매")
    async def buy_item_v2(ctx):
        view = ShopView()
        bot.add_log(ctx, "/상점")
        await ctx.send("# 상점! 구매를 원하는 아이템을 선택하세요\n" + game.show_item(), view=view, ephemeral=True)

    @bot.hybrid_command(name="구매", description="아이템 구매")
    @app_commands.describe(아이템="사기주사위, 적금통장, 황금도토리, 돈줘강화, 땡겨쓰기. /아이템 참고")
    async def buy_item(ctx, 아이템: str):
        아이템 = sc.remove_space(아이템).lower()
        if "적금" in 아이템 or "통장" in 아이템:
            item_key = "high_interest"
        elif "사기" in 아이템 or "주사위" in 아이템:
            item_key = "cheat_dice"
        elif "황금" in 아이템 or "도토리" in 아이템:
            item_key = "golden_acorn"
        elif "돈줘" in 아이템 or "강화" in 아이템:
            item_key = "strong_acorn"
        elif "땡겨쓰기" in 아이템:
            item_key = "acorn_loan"
        else:
            item_key = 아이템 # 잘못된 아이템 코드가 들어가면 로직이 알아서 False를 뱉는다.
        
        user_id = str(ctx.author.id)
        logic_result = game.buy_item(user_id, item_key)
        purchase_successed = logic_result[0]
        successed_text = "성공" if purchase_successed else "실패"
        user_balance = logic_result[1]
        logic_msg = logic_result[2]
        
        msg = f"[구매{successed_text}] " + logic_msg
        
        bot.add_log(ctx, "/구매", f"{successed_text}, 아이템: {item_key} ({아이템}), 잔액: {user_balance:,}")
        await bot_msg(ctx, msg)

    @bot.hybrid_command(name="판매", description="보유 중인 아이템을 판매합니다 (구매가의 60% 환급)")
    @app_commands.describe(아이템="판매할 아이템 이름 (사기주사위, 적금통장, 황금도토리)")
    async def sell_item_cmd(ctx, 아이템: str):
        아이템 = sc.remove_space(아이템).lower()
        if "적금" in 아이템 or "통장" in 아이템:
            item_key = "high_interest"
        elif "사기" in 아이템 or "주사위" in 아이템:
            item_key = "cheat_dice"
        elif "황금" in 아이템 or "도토리" in 아이템:
            item_key = "golden_acorn"
        else:
            item_key = 아이템

        user_id = str(ctx.author.id)
        logic_result = game.sell_item(user_id, item_key)
        sell_successed = logic_result[0]
        successed_text = "성공" if sell_successed else "실패"
        user_balance = logic_result[1]
        logic_msg = logic_result[2]

        msg = f"[판매{successed_text}] " + logic_msg + f"\n[현재잔고] **{user_balance:,}**개"

        bot.add_log(ctx, "/판매", f"{successed_text}, 아이템: {item_key} ({아이템}), 잔액: {user_balance:,}")
        await bot_msg(ctx, msg, ephemeral=not sell_successed)

    

    ### 테스트 중 ###

    @bot.hybrid_command(name="로또추천", description="님들아 로또 1등되면 뭐할거임?")
    async def lotto(ctx):
        
        numbers = sorted(random.sample(range(1, 46), 6))
        bonus_number = random.choice([i for i in range(1, 46) if i not in numbers])
        
        embed = discord.Embed(
            title="🐿️ 로또 번호 생각하는 중...",
            description="생각햇따!!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🍀 당첨 번호",
            value=f"**{' - '.join(map(str, numbers))}**",
            inline=False
        )
        
        embed.add_field(
            name="✨ 보너스 번호",
            value=f"**{bonus_number}**",
            inline=False
        )
        
        embed.add_field(
            name="💸 사러가기",
            value="[동행복권 사이트](https://www.dhlottery.co.kr/main)",
            inline=False
        )
        
        await bot_msg(ctx, embed=embed)

    @bot.hybrid_command(name="최신로또", description="가장 최근 로또 추첨번호를 알려줍니다.")
    async def latest_lotto(ctx):
        
        lt = Lotto()
        msg = lt.get_lotto_numbers()
        
        await bot_msg(ctx, msg)
        
    
    # st2 = StockInfoWithSqlite()
    # @bot.hybrid_command(name="주식2", description="주가 보기")
    # @app_commands.describe(
    #     name="회사명 or 티커 번호"
    # )
    # async def get_stock_price_v2(ctx, name):
    #     name = sc.remove_space(name).upper()
    #     data = st2.get_stock_info(name)
    #     set_ephemeral = False
    #     if str(os.getenv('ANGRY_KOKO')) in data:
    #         bot.add_log(ctx, "/주식2", f"실패 // 입력 데이터: {name} // Exception: {data.split('$')[1].strip()}")
    #         data = data.split('$')[0].strip()
    #         set_ephemeral = True
    #     else:
    #         bot.add_log(ctx, "/주식2", f"성공 // 입력 데이터: {name}")
    #     await bot_msg(ctx, data, ephemeral=set_ephemeral)

    @tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=9))))
    async def midnight_interest_job():
        count = game.claim_interest_for_all()
        print(f"자정 이자 지급 완료! 총 {count}명의 유저가 이자를 받았습니다.")


        
    return bot



def bot_run(is_test, logger_func):
    if is_test:
        token = os.getenv('DOTORI_BOT_TOKEN_TEST')
    else:
        token = os.getenv('DOTORI_BOT_TOKEN')
    token = str(token)
    
    bot = build_bot(is_test, logger_func)
    bot.run(token)