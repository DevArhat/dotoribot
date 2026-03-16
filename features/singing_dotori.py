import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
from logic import SpaceController, RhythmDotori

sc = SpaceController()
rd = RhythmDotori()

def singing_dotori_commands(bot, bot_msg):
    music_queues = {}
    inactive_timers = {}

    async def start_inactivity_timer(ctx, voice_client):
        # 기존에 돌고 있는 타이머가 있다면 취소
        if ctx.guild.id in inactive_timers:
            inactive_timers[ctx.guild.id].cancel()

        async def timer():
            try:
                await asyncio.sleep(10)
                if voice_client.is_connected() and not voice_client.is_playing() and not voice_client.is_paused():
                    await voice_client.disconnect()
                    await ctx.send("나 나간다! 🐿️💨")
            except asyncio.CancelledError:
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

    @bot.hybrid_command(name="노래", aliases=["음악", "풍악", "리듬"], description="유튜브 URL을 주면 도토리가 노래를 해요")
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

        msg = await bot_msg(ctx, "노래 외우는 중.. 잠시만 기다려주세요...")

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
                await msg.edit(content=f"**{title}**\n📝 대기열에 추가했어요 ")
            else:
                default_volume = 0.15
                audio_source = discord.FFmpegPCMAudio(stream_url, **rd.ffmpeg_options) # type: ignore
                volume_transformer = discord.PCMVolumeTransformer(audio_source, volume=default_volume)
                
                # after 콜백을 연결하여 현재 곡이 끝나면 play_next 함수가 실행되도록 함
                voice_client.play(volume_transformer, after=lambda e: play_next(e, ctx, voice_client))
                
                bot.add_log(ctx, "/노래", f"input: {url}, title: {title}, url: {stream_url}")
                await msg.edit(content=f"**{title}**\n🎶 오케이! 한번 불러볼게요.")
            
        except Exception as e:
            bot.add_log(ctx, "/노래", f"input: {url}, error: {e}")
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
            
    @bot.hybrid_command(name="일시정지", aliases=["잠깐", "멈춤", "pause"], description="현재 재생 중인 노래를 일시정지합니다")
    async def pause_music(ctx):
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            bot.add_log(ctx, "/일시정지", "성공")
            await bot_msg(ctx, "⏸️ 노래를 잠깐 멈췄어요. (/재생 을 입력해 이어들을 수 있어요)")
        elif voice_client and voice_client.is_paused():
            await bot_msg(ctx, "이미 멈춰있어요! 🤔")
        else:
            await bot_msg(ctx, "지금 재생 중인 노래가 없어요! 🤔")

    @bot.hybrid_command(name="재생", aliases=["이어듣기", "재생계속", "resume"], description="일시정지된 노래를 마저 재생합니다")
    async def resume_music(ctx):
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            bot.add_log(ctx, "/재생", "성공")
            await bot_msg(ctx, "▶️ 멈췄던 노래를 이어서 부를게요!")
        elif voice_client and voice_client.is_playing():
            await bot_msg(ctx, "이미 부르고 있어요! 🎵")
        else:
            await bot_msg(ctx, "현재 멈춰있는 노래가 없어요! 🤔")

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