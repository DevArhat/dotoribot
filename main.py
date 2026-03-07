# tmux new -s bot
# tmux attach -t bot


import random

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os
import math
import logic
from logic import LostArkGuardian

class DotoriBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
    async def setup_hook(self):
        await self.tree.sync()  # 슬래시 명령어 동기화
        
bot = DotoriBot()

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

print(str(TOKEN)[:5])

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

@bot.hybrid_command(name="사용법")
async def usage(ctx):
    help_text = """# 🐿️ 도토리봇 사용법
```markdown
[ 일반 명령어 ]
!사용법 : 도움말
!안녕   : 인사하기
!뒤집기 [문구] : 입력한 문구를 거꾸로 뒤집어서 출력
!빠직   : 앵그리코코 출력

[ 링크 제공 명령어 ]
!시트   : 도토리 레이드 시트 링크
!로아투두: 로아투두 링크
!인벤   : 로벤 링크
!10추   : 로벤 10추글 링크
!30추   : 로벤 30추글 링크

[ 슬래시 명령어 (채팅창에 / 입력 후 스페이스바) ]
/쌀 [가격] [인원수]
  ㄴ 최적입찰가 계산기
  ㄴ 인원수는 4, 8, 16인만
```"""
    await ctx.send(help_text)

# !안녕 명령어
@bot.command(name="안녕")
async def hello(ctx):
    sticker = discord.Object(id=1247156880124543059)
    await ctx.send(" ", stickers=[sticker])

# !뒤집기 [문구내용] 명령어
@bot.hybrid_command(name="뒤집기")
async def reverse_text(ctx, *, text: str):
    # 파이썬의 슬라이싱을 이용하여 문자열을 거꾸로 뒤집습니다.
    reversed_text = text[::-1]
    await ctx.send(reversed_text)
    
@bot.hybrid_command(name="빠직")
async def angry_koko(ctx):
    await ctx.send(f"<:AngryKoko:1421511652376842443>")
    
@bot.hybrid_command(name="시트", description="도토리 레이드 시트 링크")
async def send_sheet_link(ctx):
    await ctx.send(f"{os.getenv('DOTORI_RAID_SHEET')}")
    
@bot.hybrid_command(name="지옥효율", description="지옥 효율 계산 링크")
async def send_hell_efficiency_link(ctx):
    await ctx.send(f"https://www.gcalc.kr/hell")
    
@bot.hybrid_command(name="낙원추천", description="낙원 장비 시너지 추천기 링크")
async def send_paradise_recommendation_link(ctx):
    await ctx.send(f"https://codepen.io/ialgqfxp-the-animator/pen/NPrQxOx")
    
@bot.hybrid_command(name="로아투두", description="로아투두 링크")
async def send_lostark_todo_link(ctx):
    await ctx.send(f"https://www.loatodo.com/")
    
@bot.hybrid_command(name="인벤", description="인벤 링크")
async def send_inven_link(ctx):
    await ctx.send(f"https://lostark.inven.co.kr/")
    
@bot.hybrid_command(name="10추", description="10추글 링크")
async def send_10pull_link(ctx):
    await ctx.send(f"https://www.inven.co.kr/board/lostark/6271?my=chu")

@bot.hybrid_command(name="30추", description="30추글 링크")
async def send_30pull_link(ctx):
    await ctx.send(f"https://www.inven.co.kr/board/lostark/6271?my=chuchu")

@bot.hybrid_command(name="에이메스", description="에이메스 이미지")
async def send_image(ctx):
    image_urls = [
        "https://pbs.twimg.com/media/HAzrgy0aQAAftah?format=jpg",
        "https://pbs.twimg.com/media/HA4Sa_HaEAAmhZt?format=jpg",
        "https://pbs.twimg.com/media/HA9tYRVbsAkc1jf?format=jpg",
        "https://pbs.twimg.com/media/HCdXGoGaMAAo9N9?format=jpg"
    ]
    image_url = random.choice(image_urls)
    embed = discord.Embed(title="에이메스", description="제가 당신의 자랑이었으면 좋겠어요. 제가 당신을 실망시키지 않았으면 좋겠어요.", color=0xeb9cb9)
    embed.set_image(url=image_url)
    await ctx.send(embed=embed)


@bot.hybrid_command(name="이번주가디언", description="이번주 가디언 정보")
async def send_weekly_guardian_info(ctx):
    g = LostArkGuardian().get_lostark_weekly_info()
    
    msg = (f"""# {g[1]} ({g[2]})
{g[0]}""")
    await ctx.send(msg)

@bot.hybrid_command(name="다음주가디언", description="다음주 가디언 정보")
async def send_next_week_guardian_info(ctx):
    g = LostArkGuardian().get_lostark_weekly_info()
    
    msg = (f"""# {g[4]} ({g[5]})
{g[3]}""")
    await ctx.send(msg)

# 슬래시 명령어 생성: 
@bot.tree.command(name="쌀", description="경매 쌀산기")
# 스페이스바를 눌렀을 때 뜰 입력칸(파라미터)에 대한 설명입니다.
@app_commands.describe(
    price="경매템 가격",
    dotoris="몇인팟 컨텐츠임?"
)
async def calculate(interaction: discord.Interaction, price: int, dotoris: int):
    response_text = logic.calc_logic(price, dotoris)
        
    # interaction.response.send_message를 통해 답장을 보냅니다.
    await interaction.response.send_message(response_text)

    
    
@bot.tree.command(name="뽑기", description="뽑기 시뮬레이터")
@app_commands.describe(
    game="원신, 붕스, 젠존제, 명조, 엔필",
    dolpa="숫자만, 명함은 0"
)
async def pull(ctx, game: str, dolpa: int):
    game_key = ''
    if game == "원신":
        game_key = 'gen'
    elif game in ["붕스", "스타레일", "붕괴", "붕괴스타레일"]:
        game_key = 'hsr'
    elif game in ["젠존제", "찢", "젠레스", "젠레스존제로"]:
        game_key = 'zzz'
    elif game in ["명조", "띵조"]:
        game_key = 'wuwa'
    elif game in ["엔필", "엔드필드"]:
        game_key = 'end'

    await logic.run_vercel(ctx, game_key, dolpa)

@reverse_text.error
async def reverse_text_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("사용법: !뒤집기 [뒤집을 문구]")

bot.run(TOKEN) # type: ignore