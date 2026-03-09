# tmux new -s bot
# tmux attach -t bot


import random
import os
import json

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from logic import *

class DotoriBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
    async def setup_hook(self):
        await self.tree.sync()  # 슬래시 명령어 동기화
        
bot = DotoriBot()

load_dotenv()

sc = SpaceController()

TOKEN = os.getenv('DISCORD_TOKEN')

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# LOG_PATH = os.path.join(BASE_DIR, 'bot.log')
# TIME_TABLE_PATH = os.path.join(BASE_DIR, 'time_table.json')

# def add_log(target, command, details='No Details'):
#     timezone_kst = datetime.timezone(datetime.timedelta(hours=9))
#     now = datetime.datetime.now(timezone_kst).strftime('%Y-%m-%dT%H:%M:%S+09:00')
#     if hasattr(target, 'author'):
#         user = target.author
#     else:
#         user = target.user
#     msg = f"[{now}] {user}({user.id}) | {command} | {details}"

#     with open(LOG_PATH, 'a', encoding='utf-8') as log_file:
#         log_file.write(msg + '\n')

# def load_time_table():
#     if os.path.exists(TIME_TABLE_PATH):
#         try:
#             with open(TIME_TABLE_PATH, 'r', encoding='utf-8') as f:
#                 return json.load(f)
#         except json.JSONDecodeError:
#             print("Error decoding JSON from time_table.json")
#             return {}
#     return {}

# def refresh_time_table(data):
#     try:
#         with open(TIME_TABLE_PATH, 'w', encoding='utf-8') as f:
#             json.dump(data, f, ensure_ascii=False, indent=2)
#     except Exception as e:
#         print(f"Error writing to time_table.json: {e}")

TIME_TABLE = load_time_table()

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
  ㄴ 최적입찰가 계산기 (공평분배 기준)
  
/가디언예측 [년] [월] [일]
  ㄴ 특정 날짜 가디언 예측하기

/뽑기 [게임명] [돌파]
  ㄴ 뽑기 시뮬레이터 (게임명 잘못 쓰면 붕스가 기본값됨)

# 기타 잡다한 명령어
!안녕   : 인사하기
!뒤집기 [문구] : 입력한 문구를 거꾸로 뒤집어서 출력
!빠직   : 앵그리코코 출력
/에이메스 : 에이메스 이미지 랜덤 출력

# 구현 도전 중
/시간표 : 내가 가는 레이드 시간 보여주기
```"""
    await ctx.send(help_text)

# !안녕 명령어
@bot.command(name="안녕")
async def hello(ctx):
    add_log(ctx, "!안녕")
    sticker = discord.Object(id=1247156880124543059)
    await ctx.send(" ", stickers=[sticker])

# !뒤집기 [문구내용] 명령어
@bot.hybrid_command(name="뒤집기")
async def reverse_text(ctx, *, text: str):
    # 파이썬의 슬라이싱을 이용하여 문자열을 거꾸로 뒤집습니다.
    reversed_text = text[::-1]
    add_log(ctx, "/뒤집기", f"입력: {text}, 결과: {reversed_text}")
    await ctx.send(reversed_text)
    
@bot.hybrid_command(name="빠직")
async def angry_koko(ctx):
    add_log(ctx, "/빠직")
    await ctx.send(f"<:AngryKoko:1421511652376842443>")
    
@bot.hybrid_command(name="시트", description="도토리 레이드 시트 링크")
async def send_sheet_link(ctx):
    add_log(ctx, "/시트")
    await ctx.send(f"# [도토리 레이드 시트]({os.getenv('DOTORI_RAID_SHEET')})")
    
@bot.hybrid_command(name="지옥효율", description="지옥 효율 계산 링크")
async def send_hell_efficiency_link(ctx):
    add_log(ctx, "/지옥효율")
    await ctx.send(f"# [지옥효율 바로가기](https://www.gcalc.kr/hell)")
    
@bot.hybrid_command(name="낙원추천", description="낙원 장비 시너지 추천기 링크")
async def send_paradise_recommendation_link(ctx):
    add_log(ctx, "/낙원추천")
    await ctx.send(f"# [낙원추천 바로가기](https://codepen.io/ialgqfxp-the-animator/pen/NPrQxOx)")
    
@bot.hybrid_command(name="로아투두", description="로아투두 링크")
async def send_lostark_todo_link(ctx):
    add_log(ctx, "/로아투두")
    await ctx.send(f"# [로아투두 바로가기](https://www.loatodo.com/)")
    
@bot.hybrid_command(name="인벤", description="인벤 링크")
async def send_inven_link(ctx):
    add_log(ctx, "/인벤")
    await ctx.send(f"# [인벤 바로가기](https://lostark.inven.co.kr/)")
    
@bot.hybrid_command(name="10추", description="10추글 링크")
async def send_10pull_link(ctx):
    add_log(ctx, "/10추")
    await ctx.send(f"# [10추글 바로가기](https://www.inven.co.kr/board/lostark/6271?my=chu)")

@bot.hybrid_command(name="30추", description="30추글 링크")
async def send_30pull_link(ctx):
    add_log(ctx, "/30추")
    await ctx.send(f"# [30추글 바로가기](https://www.inven.co.kr/board/lostark/6271?my=chuchu)")

@bot.hybrid_command(name="에이메스", description="에이메스 이미지")
async def send_image(ctx):
    add_log(ctx, "/에이메스")
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
    add_log(ctx, "/이번주가디언")
    g = LostArkGuardian().get_lostark_weekly_info()
    
    msg = (f"""# {g[1]} ({g[2]})
{g[0]}""")
    await ctx.send(msg)

@bot.hybrid_command(name="다음주가디언", description="다음주 가디언 정보")
async def send_next_week_guardian_info(ctx):
    add_log(ctx, "/다음주가디언")
    g = LostArkGuardian().get_lostark_weekly_info()
    
    msg = (f"""# {g[4]} ({g[5]})
{g[3]}""")
    await ctx.send(msg)

@bot.tree.command(name="가디언예측", description="특정 날짜 가디언 예측하기")
@app_commands.describe(
    year="년 (예: 2024)",
    month="월 (예: 6)",
    day="일 (예: 30)"
)
async def predict_guardian(ctx, year: int, month: int, day: int):
    add_log(ctx, "/가디언예측", f"{year}-{month}-{day}")
    g = LostArkGuardian().get_lostark_weekly_info_predict(year, month, day)
    
    msg = (f"""# {g[1]} ({g[2]})
{g[0]}""")
    await ctx.response.send_message(msg)

# 슬래시 명령어 생성: 
@bot.tree.command(name="쌀", description="경매 쌀산기")
# 스페이스바를 눌렀을 때 뜰 입력칸(파라미터)에 대한 설명입니다.
@app_commands.describe(
    price="경매템 가격",
    dotoris="몇인팟 컨텐츠임?"
)
async def calculate(interaction: discord.Interaction, price: int, dotoris: int):
    response_text = calc_logic(price, dotoris)[0]
    response_tuple = calc_logic(price, dotoris)[1]
    
    add_log(interaction,
            "/쌀",
            f"가격: {price}, 인원수: {dotoris}, 추천입찰가: {response_tuple[1]:,}G, 분배금: {response_tuple[2]:,}G, 판매금: {response_tuple[3]:,}G")
    # interaction.response.send_message를 통해 답장을 보냅니다.
    await interaction.response.send_message(response_text)
    
@bot.hybrid_command(name="refresh_time_table", description="시간표 갱신하기")
@app_commands.describe(
    data="시간표 정리 JSON"
)
async def refresh_time_table_command(ctx, data: str):
    try:
        json_data = json.loads(data)
        TIME_TABLE.update(json_data)
        refresh_time_table(json_data)
        sc.replace_space(data)
        add_log(ctx, "/시간표갱신", f"성공 // 입력 데이터: {data}")
        await ctx.send("시간표가 성공적으로 갱신되었습니다.")
    except json.JSONDecodeError:
        sc.remove_space(data)
        add_log(ctx, "/시간표갱신", f"실패 // 입력 데이터: {data}")
        await ctx.send("유효한 JSON 형식이 아닙니다. 다시 시도해주세요.")
        
@bot.hybrid_command(name="시간표", description="내가 갈 레이드, 요일, 시간")
async def get_time_table(ctx):
    user_id = str(ctx.author.id)
    if user_id in TIME_TABLE:
        user_info = TIME_TABLE[user_id]
        response_text = f"<@{user_id}> 의 레이드 시간표입니다:\n```markdown\n"
        for raid in user_info:
            response_text += f"- {raid['name']}: {raid['day']}요일 {raid['time']}시\n"
        response_text += "```"
        add_log(ctx, "/시간표조회", f"성공 // 사용자 ID: {user_id}")
        await ctx.send(response_text)
    else:
        add_log(ctx, "/시간표조회", f"실패 // 사용자 ID: {user_id} (정보 없음)")
        await ctx.send("시간표 정보가 없습니다 ㅠㅠ")

@bot.hybrid_command(name="전체시간표", description="저장되어 있는 전체 시간표 보기")
async def get_everyone_time_table(ctx):
    add_log(ctx, "/전체시간표")
    for user_id, raid_list in TIME_TABLE.items():
        user_obj = await bot.fetch_user(int(user_id))
        nick = user_obj.display_name

        response_text = f"**{nick}** 의 레이드 시간표입니다:\n```markdown\n"
        for raid in raid_list:
            response_text += f"- {raid['name']}: {raid['day']}요일 {raid['time']}시\n"
        response_text += "```"
        
        await ctx.send(response_text)
    
    
@bot.tree.command(name="뽑기", description="뽑기 시뮬레이터")
@app_commands.describe(
    game="원신, 붕스, 젠존제, 명조, 엔필",
    dolpa="숫자만, 명함은 0"
)
async def pull(ctx, game: str, dolpa: int):
    game_key = get_game_key(game)
    
    add_log(ctx, "/뽑기", f"게임: {game}(매칭결과: {game_key}), 돌파: {dolpa}")

    await run_vercel(ctx, game_key, dolpa)

@bot.event
async def on_command_error(ctx, error):
    # 명령어 객체가 존재하지 않을 수 있으므로(예: 존재하지 않는 명령어 입력 시) 방어적 코드 작성
    command_name = ctx.command.name if ctx.command else "알 수 없는 명령어"
    error_type = type(error).__name__

    # 1. 모든 함수에 대해 전역 오류 핸들러로 동작
    await ctx.send("👀 저를부르셨나요? /사용법 을 써보세요. 아니라면? ㅈㅅ합니다.")
    add_log(ctx, str(error), f"오류 발생 함수: {command_name}, 오류 타입: {error_type}")
    
    # 2. 오류가 발생한 함수와 발생 오류 타입을 print
    print(f"오류 발생 함수: {command_name}")
    print(f"오류 타입: {error_type}")

bot.run(TOKEN) # type: ignore