# tmux new -s bot
# tmux attach -t bot

import random
import os

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from features import *

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

    game.init_db()

    # 응답 메시지 발송 공통 함수
    async def bot_msg(ctx, content="", embed=None, stickers=None, ephemeral=False):
        if isinstance(ctx, discord.Interaction):
            # @bot.tree.command 등에서 Interaction 객체가 직접 들어온 경우
            if ctx.response.is_done():
                return await ctx.followup.send(content=content, embed=embed, ephemeral=ephemeral) # type: ignore
            else:
                await ctx.response.send_message(content=content, embed=embed, ephemeral=ephemeral) # type: ignore
                return await ctx.original_response()
        elif ctx.interaction:
            # hybrid_command를 통해 슬래시 명령어로 들어온 Context인 경우
            # Context.send는 내부적으로 interaction.response를 처리해줍니다.
            return await ctx.send(content=content, embed=embed, stickers=stickers, ephemeral=ephemeral)
        else:
            # 일반 메시지 명령어(!명령어)로 들어온 Context인 경우
            return await ctx.message.reply(content=content, embed=embed, stickers=stickers)        

    # commands 내부의 명령어 등록
    load_all_commands(bot, bot_msg)



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
        await bot_msg(ctx, f"{bot.angry_koko}")



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


    
    





    @tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=9))))
    async def midnight_interest_job():
        tz_kst = datetime.timezone(datetime.timedelta(hours=9))
        now = datetime.datetime.now(tz_kst)
        count = game.claim_interest_for_all()
        bot.add_log(bot.user, "/적금통장", f"{count}명 이자 지급 완료")
        print(f"자정 이자 지급 완료! 총 {count}명의 유저가 이자를 받았습니다. @ {now.strftime('%Y-%m-%d %H:%M:%S')}")


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
        


        
    return bot



def bot_run(is_test, logger_func):
    if is_test:
        token = os.getenv('DOTORI_BOT_TOKEN_TEST')
    else:
        token = os.getenv('DOTORI_BOT_TOKEN')
    token = str(token)
    
    bot = build_bot(is_test, logger_func)
    bot.run(token)