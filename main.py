import asyncio
from datetime import datetime
import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_PATH = os.path.join(BASE_DIR, "alarm.mp3")
FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg.exe")


@bot.event
async def on_ready():
  print(f"Logged in successfully as {bot.user.name}")


@bot.command()
async def alarm(ctx, time_str: str, *, label: str = "Time's up!"):
  if not ctx.author.voice:
    await ctx.send("❌ Sumali ka muna sa Voice Channel!")
    return

  try:
    # Kunin ang kasalukuyang oras at i-parse ang target time (24-hour format HH:MM)
    now = datetime.now()
    target_time = datetime.strptime(time_str, "%H:%M").time()

    # Buuin ang full datetime object para sa target
    target_datetime = datetime.combine(now.date(), target_time)

    # Kung nakalipas na ang oras ngayong araw, i-set ito para sa bukas
    if target_datetime <= now:
      await ctx.send("⚠️ Nakalipas na ang oras na 'yan ngayong araw!")
      return

    # Hitain ang natitirang segundo
    delay_seconds = (target_datetime - now).total_seconds()

    await ctx.send(
        f"⏰ Alarm set para sa **{time_str}** (mga {int(delay_seconds // 60)} minuto mula ngayon)."
    )
    await asyncio.sleep(delay_seconds)

    # Pagpasok sa voice channel at pagpapatugtog ng alarm
    voice_channel = ctx.author.voice.channel
    vc = (
        ctx.voice_client
        if ctx.voice_client is not None
        else await voice_channel.connect()
    )

    await ctx.send(f"🚨 {ctx.author.mention} **ALARM:** {label}")

    executable = FFMPEG_PATH if os.path.exists(FFMPEG_PATH) else "ffmpeg"
    source = discord.FFmpegPCMAudio(
        AUDIO_PATH,
        executable=executable,
        options="-vn -loglevel warning -ar 48000 -ac 2",
    )

    vc.play(source)

    while vc.is_playing():
      await asyncio.sleep(1)

    await vc.disconnect()

  except ValueError:
    await ctx.send(
        "❌ Mali ang format ng oras! Gamitin ang 24-hour format (halimbawa: `!alarm 10:30 Subok lang` o `!alarm 14:15 Gising na`)."
    )
  except Exception as e:
    await ctx.send(f"⚠️ Error: {e}")


bot.run("MTUzODM2MjAwNzA1MTU2NzEzNA.GCOYHA.mDZ0CYxr8rEX_5heZyTFB0E7wpdRTdmYAE7VxI")

