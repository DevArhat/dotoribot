# tmux new -s bot
# tmux attach -t bot

import random
import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

from logic import *
import game

class DotoriBot(commands.Bot):

    def __init__(self, is_test, logger_func):
        intents = discord.Intents.default()
        intents.message_content = True
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
        

    # 인텐트 설정 (메시지 내용을 읽기 위해 필수)
    intents = discord.Intents.default()
    intents.message_content = True


    @bot.event
    async def on_ready():
        try:
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

# 특수 명령어 (입력 인수 필요)
/쌀 [가격] [인원수]
ㄴ 최적입찰가 계산기 (공평분배 기준) 인원수는 비울 수 있음 (기본값 8인컨텐츠)

/가디언예측 [년] [월] [일]
ㄴ 특정 날짜 가디언 예측하기

/뽑기 [게임명] [돌파]
ㄴ 뽑기 시뮬레이터 (게임명 잘못 쓰면 붕스가 기본값됨)

/주식 [티커 번호 or 회사명]
ㄴ 주가 보기 (KOSPI만 지원, ETF도 몇개 됨, 티커번호 사용 권장)

/노래 [유튜브 주소]
ㄴ 노래 틀기 (검색어도 되는데 부정확해서 URL 추천)

# 기타 잡다한 명령어
!안녕 : 인사하기
!빠직 : 앵그리코코 출력
/에이메스 : 에이메스 이미지 4종 중 1개 랜덤 출력
/캡틴잭 : 그긴거 출력
/홀짝 : 홀 or 짝 출력
!뒤집기 [문구] : 입력한 문구를 거꾸로 뒤집어서 출력
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

    ### 가위바위보 게임 ###

    @bot.hybrid_command(name="돈줘", description="도토리 100,000개를 지급받습니다 (5분 쿨타임)")
    async def give_money(ctx):
        user_id = str(ctx.author.id)
        success, value = game.give_money(user_id)

        if success:
            bot.add_log(ctx, "/돈줘", f"지급 후 잔액: {value:,}")
            await bot_msg(ctx, f"💰 도토리 100,000개가 지급되었습니다!\n🏦 현재 도토리: **{value:,}개**")
        else:
            minutes, seconds = divmod(value, 60)
            bot.add_log(ctx, "/돈줘", f"쿨타임 중 ({value}초 남음)")
            await bot_msg(ctx, f"{bot.angry_koko} 탕진좀 그만해!\n**{minutes}분 {seconds}초** 후에 줄게요.", ephemeral=True)

    @bot.hybrid_command(name="게임", description="도토리를 걸고 게임을 합니다.")
    @app_commands.describe(베팅="베팅할 도토리 갯수")
    async def play_game(ctx, 베팅: int):
        user_id = str(ctx.author.id)
        try:
            result, fluctuation, balance = game.play_game(user_id, 베팅)
        except ValueError as e:
            bot.add_log(ctx, "/게임", f"실패: {e}")
            await bot_msg(ctx, f"❌ {e}", ephemeral=True)
            return

        if result == "win":
            emoji = "🎉"
            result_text = f"승리! +{fluctuation:,}개"
        elif result == "lose":
            emoji = "☠️"
            result_text = f"패배! {fluctuation:,}개"
        else:
            emoji = "🐿️"
            result_text = "무승부! 금액 변동 없음"

        if balance == 0:
            result_text += "\n작은구름 밑에 묻어둔 도토리가 모두 사라졌습니다...😱"

        bot.add_log(ctx, "/게임", f"베팅: {베팅:,}, 결과: {result}, 변동: {fluctuation:,}, 잔액: {balance:,}")
        await bot_msg(ctx, f"""## {emoji} {result_text}
```
베팅도토리: {베팅:,}개
현재도토리: {balance:,}개
```""")
    

    @bot.hybrid_command(name="내돈", description="내 도토리 확인")
    async def my_money(ctx):
        user_id = str(ctx.author.id)
        balance = game.get_balance(user_id)
        bot.add_log(ctx, "/내돈", f"잔액: {balance:,}")
        await bot_msg(ctx, f"🏦 현재 도토리: **{balance:,}개**")


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


        
    return bot



def bot_run(is_test, logger_func):
    if is_test:
        token = os.getenv('DOTORI_BOT_TOKEN_TEST')
    else:
        token = os.getenv('DOTORI_BOT_TOKEN')
    token = str(token)
    
    bot = build_bot(is_test, logger_func)
    bot.run(token)