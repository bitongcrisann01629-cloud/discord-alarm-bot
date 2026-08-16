import os
import asyncio
from aiohttp import web
import discord
from discord.ext import commands

# Mini web server para sa Render
async def handle(request):
    return web.Response(text="Bot is online!")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.command()
async def alarm(ctx, seconds: int, *, message: str = "Gising na!"):
    try:
        await ctx.send(f"⏰ Alarm set for **{seconds} seconds** from now - '{message}'")
        
        await asyncio.sleep(seconds)
        
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            vc = await channel.connect()
            
            audio_path = "alarm.mp3"
            if os.path.exists(audio_path):
                # Inayos natin ang FFmpeg options para maiwasan ang pipe error
                audio_source = discord.FFmpegPCMAudio(audio_path, before_options="-stream_loop -1")
                vc.play(audio_source)
                await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message} *(I-type ang `!stop` para patayin ang tunog)*")
            else:
                await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message} *(Wala ang alarm.mp3 file sa repository!)*")
        else:
            await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message} *(Pumasok ka muna sa voice channel!)*")
            
    except Exception as e:
        await ctx.send(f"❌ Error: `{e}`")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 Napatay na ang alarm!")
    else:
        await ctx.send("❌ Walang tinutugtog ang bot.")

async def main():
    await start_dummy_server()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
