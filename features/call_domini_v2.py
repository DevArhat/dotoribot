import discord
from discord import app_commands
from discord.ext import commands


import io


from genai_module_v2 import DotoriGemini


async def send_generated_image(ctx, content: str, image_file: discord.File):
    """기존 로딩 메시지를 생성 이미지 응답으로 교체."""
    interaction = (
        ctx
        if isinstance(ctx, discord.Interaction)
        else getattr(ctx, "interaction", None)
    )
    if interaction:
        return await interaction.edit_original_response(
            content=content,
            attachments=[image_file],
        )

    loading_message = getattr(ctx, "_last_bot_msg", None)
    if loading_message:
        return await loading_message.edit(
            content=content,
            attachments=[image_file],
        )

    return await ctx.send(content=content, file=image_file)


def domini_v2_commands(bot, bot_msg, bot_defer):
    gemini_service = DotoriGemini()

    @bot.hybrid_command(
        name="이미지생성",
        description="제미나이에게 이미지를 생성하도록 요청합니다. 5분당 10회만 사용 가능합니다.",
    )
    @commands.cooldown(10, 300, commands.BucketType.user)
    @app_commands.describe(
        프롬프트="생성할 이미지 설명"
    )
    async def generate_gemini_image(ctx, 프롬프트: str):
        request_query = 프롬프트[:30] + "..." if len(프롬프트) > 30 else 프롬프트
        response_header = f"원본 요청: `{request_query}`"

        await bot_defer(ctx, defer_msg="제미나이가 이미지를 그리고 있어요...")
        image_data = await gemini_service.generate_image(프롬프트)
        bot.add_log(ctx, "/이미지생성", 프롬프트)

        with io.BytesIO(image_data) as image_stream:
            image_file = discord.File(image_stream, filename="gemini_image.jpg")
            await send_generated_image(ctx, response_header, image_file)

    @generate_gemini_image.error
    async def generate_gemini_image_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await bot_msg(
                ctx,
                f"🐿️ 5분당 10회만 쓸 수 있어요... "
                f"{error.retry_after:.2f}초 후에 다시 요청해주세요.",
            )
            return

        await bot_msg(ctx, "❌ 이미지를 생성하지 못했어요. 잠시 후 다시 요청해주세요.")

    @bot.hybrid_command(name="제미나이", description="제미나이에게 질문하기. 5분당 10회만 사용 가능합니다. 예고 없이 사라질 수 있음!")
    @commands.cooldown(10, 300, commands.BucketType.user)    
    @app_commands.describe(
        질문="질문 내용"
    )
    async def ask_gemini(ctx, 질문: str):
        request_query = ''
        if len(질문) > 30:
            request_query = 질문[:30] + "..."
        else:
            request_query = 질문
        response_header = f"원본 질문: `{request_query}`"
        await bot_defer(ctx, defer_msg="제미나이가 답변을 생성하고 있어요...")
        response = await gemini_service.call_genai(질문, persona=None)
        response = response_header + "\n\n" + response
        bot.add_log(ctx, "/제미나이", 질문 + " // " + response)
        await bot_msg(ctx, response)
    
    @ask_gemini.error   
    async def ask_gemini_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await bot_msg(ctx, f"🐿️ 5분당 10회만 쓸 수 있어요... {error.retry_after:.2f}초 후에 다시 물어봐주세요.")


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
        response = await gemini_service.call_genai(질문)
        response = response_header + "\n\n" + response
        bot.add_log(ctx, "/도미나이", 질문 + " // " + response)
        await bot_msg(ctx, response)
    
    @ask_domini.error
    async def ask_domini_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await bot_msg(ctx, f"🐿️ 도미나이는 잠시 쉴래요... {error.retry_after:.2f}초 후에 다시 물어봐주세요.")


    @bot.hybrid_command(name="파이논봇", description="파이논봇에게 질문하기. 5분당 10회만 사용 가능합니다. 예고 없이 사라질 수 있음!")
    @commands.cooldown(10, 300, commands.BucketType.user)    
    @app_commands.describe(
        질문="질문 내용"
    )
    async def ask_phainon(ctx, 질문: str):
        request_query = ''
        if len(질문) > 30:
            request_query = 질문[:30] + "..."
        else:
            request_query = 질문
        response_header = f"원본 질문: `{request_query}`"
        await bot_defer(ctx, defer_msg="🔥🏃 [ 불을 쫓는 여정 중 ]...")
        response = await gemini_service.call_genai(질문, persona='PhainonBot')
        response = response_header + "\n\n" + response
        bot.add_log(ctx, "/파이논봇", 질문 + " // " + response)
        await bot_msg(ctx, response)
    
    @ask_phainon.error
    async def ask_phainon_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await bot_msg(ctx, f"🔥 33550335 번째 윤회 중 ... 완료까지 시스템 시간으로 {error.retry_after:.2f}초")
