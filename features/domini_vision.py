import discord
from discord import app_commands
from discord.ext import commands

from domini_vision_engine import DominiVisionEngine


def domini_vision_commands(bot, bot_msg, bot_defer):
    vision_engine = DominiVisionEngine()

    @bot.hybrid_command(
        name="이미지검색",
        description="도미나이 이미지 검색",
    )
    @commands.cooldown(5, 600, commands.BucketType.user)
    @app_commands.describe(
        이미지="검색할 이미지",
        프롬프트="이미지에 관한 질문",
        이미지2="추가 검색 이미지",
        이미지3="추가 검색 이미지",
        이미지4="추가 검색 이미지",
    )
    async def search_images(
        ctx,
        이미지: discord.Attachment,
        프롬프트: str,
        이미지2: discord.Attachment | None = None,
        이미지3: discord.Attachment | None = None,
        이미지4: discord.Attachment | None = None,
    ):
        attachments = [
            attachment
            for attachment in [이미지, 이미지2, 이미지3, 이미지4]
            if attachment is not None
        ]

        await bot_defer(
            ctx,
            defer_msg="🐿️ 이미지의 흔적을 웹에서 찾고 있어요...",
        )
        images = [
            (
                await attachment.read(),
                (attachment.content_type or "image/jpeg").split(
                    ";",
                    maxsplit=1,
                )[0],
            )
            for attachment in attachments
        ]
        response = await vision_engine.search_images(프롬프트, images)
        request_query = (
            프롬프트[:30] + "..."
            if len(프롬프트) > 30
            else 프롬프트
        )
        bot.add_log(
            ctx,
            "/이미지검색",
            f"input: {프롬프트}, image_count: {len(attachments)}",
        )
        await bot_msg(ctx, f"원본 질문: `{request_query}`\n\n{response}")

    @search_images.error
    async def search_images_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await bot_msg(
                ctx,
                f"🐿️ 10분당 5회만 쓸 수 있어요... "
                f"{error.retry_after:.2f}초 후에 다시 요청해주세요.",
            )
            return

        print(f"[ERROR][DOMINI_VISION_COMMAND] {error}")
        await bot_msg(ctx, "❌ 이미지를 검색하지 못했어요. 잠시 후 다시 요청해주세요.")
