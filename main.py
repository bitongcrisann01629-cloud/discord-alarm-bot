import os
import asyncio
import discord
from discord.ext import commands

# System configuration
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("Bot is ready and running 24/7 on Cloud!")

@bot.command()
async def alarm(ctx, time_str: str, *, message: str = "Gising na!"):
    """Sets an alarm. Example: !alarm 07:00 Gising na pre!"""
    await ctx.send(f"Alarm set for **{time_str}** with message: '{message}'")
    
    # Simple timer logic (HH:MM format parsing)
    try:
        from datetime import datetime
        now = datetime.now()
        target_time = datetime.strptime(time_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        
        delay = (target_time - now).total_seconds()
        if delay < 0:
            delay += 86400  # Add 24 hours if time passed today
            
        await asyncio.sleep(delay)
        
        # Connect to voice channel and play audio
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            vc = await channel.connect()
            
            if os.path.exists("alarm.mp3"):
                vc.play(discord.FFmpegPCMAudio("alarm.mp3"))
                await ctx.send(f"⏰ **ALARM!** {ctx.author.mention} - {message}")
                while vc.is_playing():
                    await asyncio.sleep(1)
            else:
                await ctx.send(f"⏰ **ALARM!** {ctx.author.mention} - {message} *(alarm.mp3 not found)*")
                
            await vc.disconnect()
        else:
            await ctx.send(f"⏰ **ALARM!** {ctx.author.mention} - {message} *(Wala ka sa voice channel!)*")
            
    except ValueError:
        await ctx.send("❌ Maling format! Gamitin ang 24-hour time format (hal. `!alarm 07:30 Lumabas ka na`)")

# Reads the token safely from Render Environment Variables
token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("Error: DISCORD_TOKEN Environment Variable is missing!")
