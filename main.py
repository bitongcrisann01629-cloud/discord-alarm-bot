import os
import asyncio
from datetime import datetime, timedelta
import zoneinfo
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.command()
async def alarm(ctx, time_str: str, *, message: str = "Gising na!"):
    """Example: !alarm 13:15 Gising na pre!"""
    try:
        ph_tz = zoneinfo.ZoneInfo("Asia/Manila")
        now = datetime.now(ph_tz)
        
        target_time = datetime.strptime(time_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day, tzinfo=ph_tz
        )
        
        if target_time < now:
            target_time += timedelta(days=1)
            
        delay = (target_time - now).total_seconds()
        
        await ctx.send(f"⏰ Alarm set for **{time_str}** (PH Time) - '{message}'")
        await asyncio.sleep(delay)
        
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            vc = await channel.connect()
            
            if os.path.exists("alarm.mp3"):
                vc.play(discord.FFmpegPCMAudio("alarm.mp3"))
                await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message}")
                while vc.is_playing():
                    await asyncio.sleep(1)
            else:
                await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message} *(Wala ang alarm.mp3)*")
                
            await vc.disconnect()
        else:
            await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message} *(Pumasok ka muna sa voice channel!)*")
            
    except ValueError:
        await ctx.send("❌ Maling format! Gamitin ang 24-hour time (halimbawa: `!alarm 13:15 Subok lang`)")

bot.run(os.environ.get("DISCORD_TOKEN"))
