from discord import app_commands
from discord.ext import commands

import os

from logic import BASE_DIR
from genai_module import call_genai

PROMPT_PATH = os.path.join(BASE_DIR, "system_prompts.json")

def domini_commands(bot, bot_msg, bot_defer):
    @bot.hybrid_command(name="도미나이", description="도미나이에게 질문하기. 5분당 10회만 사용 가능합니다. 예고 없이 사라질 수 있음!")
    @commands.cooldown(10, 300, commands.BucketType.user)    
    @app_commands.describe(
        질문="질문 내용"
    )
    async def ask_domini(ctx, 질문: str):
        request_query = ''
        if len(질문) > 30:
            request_query = 질문[:30] + "..."
        else:
            request_query = 질문
        response_header = f"원본 질문: `{request_query}`"
        await bot_defer(ctx, defer_msg="🐿️🤔 [ 생 각 도 ]...")
        response = call_genai(질문)
        response = response_header + "\n\n" + response
        bot.add_log(ctx, "/도미나이", 질문 + " // " + response)
        await bot_msg(ctx, response)
    
    @ask_domini.error
    async def ask_domini_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await bot_msg(ctx, f"🐿️ 도미나이는 잠시 쉴래요... {error.retry_after:.2f}초 후에 다시 물어봐주세요.")