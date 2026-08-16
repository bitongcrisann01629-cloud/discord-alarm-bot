import os
import asyncio
from datetime import datetime, timedelta
import zoneinfo
import discord
from discord.ext import commands
from discord.ui import Button, View

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

class AlarmView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Stop Alarm 🛑", style=discord.ButtonStyle.red)
    async def stop_button(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.voice_client:
            interaction.guild.voice_client.stop()
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("🛑 Napatay na ang alarm!", ephemeral=False)
            self.stop()
        else:
            await interaction.response.send_message("❌ Walang tumutunog na alarm o wala ang bot sa voice channel.", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.command()
async def alarm(ctx, time_str: str, *, message: str = "Gising na!"):
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
            
            # Subukang kumonekta nang may timeout handler
            try:
                if ctx.voice_client:
                    await ctx.voice_client.disconnect()
                vc = await channel.connect(timeout=20.0, reconnect=True)
            except Exception as e:
                await ctx.send(f"❌ Hindi nakakonekta sa Voice Channel: {e}")
                return
            
            if os.path.exists("alarm.mp3"):
                vc.play(discord.FFmpegPCMAudio("alarm.mp3", options="-stream_loop -1"))
                view = AlarmView()
                await ctx.send(
                    content=f"🔔 **ALARM!** {ctx.author.mention} - {message}\nI-click ang button sa ibaba para patayin:",
                    view=view
                )
            else:
                await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message} *(Wala ang alarm.mp3)*")
        else:
            await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message} *(Pumasok ka muna sa voice channel!)*")
            
    except ValueError:
        await ctx.send("❌ Maling format! Gamitin ang 24-hour time (halimbawa: `!alarm 13:15 Subok lang`)")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 Napatay na ang alarm!")
    else:
        await ctx.send("❌ Walang tumutunog na alarm.")

bot.run(os.environ.get("DISCORD_TOKEN"))
