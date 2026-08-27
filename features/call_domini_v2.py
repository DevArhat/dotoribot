import discord
from discord import app_commands
from discord.ext import commands

import io
import mimetypes

from genai_module_v2 import DotoriGemini


EDIT_IMAGE_COUNT_LIMIT = 4
MAX_INLINE_IMAGE_BYTES = 14 * 1024 * 1024
SUPPORTED_IMAGE_MIME_TYPES = {
    "image/heic",
    "image/heif",
    "image/jpeg",
    "image/png",
    "image/webp",
}


def resolve_image_mime_type(attachment: discord.Attachment) -> str | None:
    """Discord 첨부 파일의 Gemini 지원 이미지 MIME 유형 확인."""
    content_type = attachment.content_type
    if content_type:
        mime_type = content_type.split(";", maxsplit=1)[0].lower()
        if mime_type in SUPPORTED_IMAGE_MIME_TYPES:
            return mime_type

    guessed_mime_type, _ = mimetypes.guess_type(attachment.filename)
    if guessed_mime_type in SUPPORTED_IMAGE_MIME_TYPES:
        return guessed_mime_type

    return None


def domini_v2_commands(bot, bot_msg, bot_defer):
    gemini_service = DotoriGemini()

    @bot.hybrid_command(
        name="이미지생성",
        description="제미나이로 이미지 만들기! 10분당 5회만 사용 가능합니다. (사용량 엄청 많이 먹음ㄷㄷ)",
    )
    @commands.cooldown(5, 600, commands.BucketType.user)
    @app_commands.describe(
        프롬프트="생성할 이미지 설명"
    )
    async def generate_gemini_image(ctx, 프롬프트: str):
        request_query = 프롬프트[:30] + "..." if len(프롬프트) > 30 else 프롬프트
        response_header = f"원본 요청: `{request_query}`"

        await bot_defer(ctx)
        msg = await bot_msg(ctx, "🤖 제미나이가 이미지를 그리고 있어요...")
        image_data = await gemini_service.generate_image(프롬프트)
        bot.add_log(ctx, "/이미지생성", 프롬프트)

        with io.BytesIO(image_data) as image_stream:
            image_file = discord.File(image_stream, filename="gemini_image.jpg")
            await msg.edit(content=response_header, attachments=[image_file])

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

    @bot.hybrid_command(
        name="이미지편집",
        description="첨부 이미지를 제미나이로 편집합니다. 이미지는 최대 4개까지 첨부 가능합니다.",
    )
    @commands.cooldown(5, 600, commands.BucketType.user)
    @app_commands.describe(
        프롬프트="이미지 편집 내용",
        이미지1="편집할 이미지",
        이미지2="추가 참고 이미지",
        이미지3="추가 참고 이미지",
        이미지4="추가 참고 이미지",
        이미지5="첨부 가능 개수 확인용 이미지",
    )
    async def edit_gemini_image(
        ctx,
        프롬프트: str,
        이미지1: discord.Attachment | None = None,
        이미지2: discord.Attachment | None = None,
        이미지3: discord.Attachment | None = None,
        이미지4: discord.Attachment | None = None,
        이미지5: discord.Attachment | None = None,
    ):
        command_attachments = [이미지1, 이미지2, 이미지3, 이미지4, 이미지5]
        interaction = getattr(ctx, "interaction", None)
        if interaction:
            attachments = [
                attachment
                for attachment in command_attachments
                if attachment is not None
            ]
        else:
            attachments = list(ctx.message.attachments)

        if len(attachments) > EDIT_IMAGE_COUNT_LIMIT:
            await bot_msg(
                ctx,
                f"❌ 이미지는 {EDIT_IMAGE_COUNT_LIMIT}개까지만 첨부할 수 있어요.",
            )
            return

        if not attachments:
            await bot_msg(ctx, "❌ 편집할 이미지를 1개 이상 첨부해주세요.")
            return

        image_mime_types = [
            resolve_image_mime_type(attachment)
            for attachment in attachments
        ]
        if any(image_mime_type is None for image_mime_type in image_mime_types):
            await bot_msg(
                ctx,
                "❌ PNG, JPEG, WEBP, HEIC, HEIF 이미지만 첨부할 수 있어요.",
            )
            return

        await bot_defer(ctx)
        msg = await bot_msg(ctx, "🤖 제미나이가 이미지를 편집하고 있어요...")
        image_data_list = [
            await attachment.read()
            for attachment in attachments
        ]

        if sum(len(image_data) for image_data in image_data_list) > MAX_INLINE_IMAGE_BYTES:
            await msg.edit(content="❌ 첨부 이미지의 전체 용량이 너무 커요.")
            return

        image_inputs = [
            (image_data, image_mime_type)
            for image_data, image_mime_type in zip(
                image_data_list,
                image_mime_types,
            )
            if image_mime_type is not None
        ]
        edited_image_data = await gemini_service.edit_image(
            프롬프트,
            image_inputs,
        )
        request_query = 프롬프트[:30] + "..." if len(프롬프트) > 30 else 프롬프트
        response_header = f"원본 요청: `{request_query}`"
        bot.add_log(
            ctx,
            "/이미지편집",
            f"input: {프롬프트}, image_count: {len(attachments)}",
        )

        with io.BytesIO(edited_image_data) as image_stream:
            image_file = discord.File(
                image_stream,
                filename="gemini_edited_image.jpg",
            )
            await msg.edit(content=response_header, attachments=[image_file])

    @edit_gemini_image.error
    async def edit_gemini_image_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await bot_msg(
                ctx,
                f"🐿️ 10분당 5회만 쓸 수 있어요... "
                f"{error.retry_after:.2f}초 후에 다시 요청해주세요.",
            )
            return

        await bot_msg(ctx, "❌ 이미지를 편집하지 못했어요. 잠시 후 다시 요청해주세요.")

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
        await bot_defer(ctx, defer_msg="🤖 제미나이가 답변을 생성하고 있어요...")
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
