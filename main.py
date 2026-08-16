import os
import asyncio
from datetime import datetime, timedelta
import zoneinfo
from aiohttp import web
import discord
from discord.ext import commands
from discord.ui import Button, View

# Mini web server para magkaroon ng port si Render
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

# Discord Bot Setup
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
            await interaction.response.send_message("❌ Walang tumutunog na alarm.", ephemeral=True)

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
            vc = await channel.connect()
            
            if os.path.exists("alarm.mp3"):
                vc.play(discord.FFmpegPCMAudio("alarm.mp3", options="-stream_loop -1"))
                await ctx.send(
                    content=f"🔔 **ALARM!** {ctx.author.mention} - {message}",
                    view=AlarmView()
                )
            else:
                await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message} *(Wala ang alarm.mp3)*")
        else:
            await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message} *(Pumasok ka muna sa voice channel!)*")
            
    except ValueError:
        await ctx.send("❌ Maling format! Gamitin ang 24-hour time (halimbawa: `!alarm 13:30 Subok lang`)")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 Napatay na ang alarm!")

async def main():
    await start_dummy_server()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
