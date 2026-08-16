import os
import asyncio
from datetime import datetime, time
from aiohttp import web
import discord
from discord.ext import commands
from discord.ui import Button, View

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

class AlarmView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Stop Alarm 🛑", style=discord.ButtonStyle.red)
    async def stop_button(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.voice_client:
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
        # I-parse ang oras mula sa format na HH:MM (halimbawa: 10:30)
        alarm_time = datetime.strptime(time_str, "%H:%M").time()
        
        await ctx.send(f"⏰ Alarm set for **{time_str}** - '{message}'")
        
        while True:
            now = datetime.now().time()
            # Kunin lang ang hour at minute para magtugma
            if now.hour == alarm_time.hour and now.minute == alarm_time.minute:
                break
            await asyncio.sleep(10) # Magse-check kada 10 segundo
        
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            vc = await channel.connect()
            
            audio_path = "alarm.mp3"
            if os.path.exists(audio_path):
                audio_source = discord.FFmpegPCMAudio(audio_path, before_options="-stream_loop -1")
                vc.play(audio_source)
                
                await ctx.send(
                    content=f"🔔 **ALARM!** {ctx.author.mention} - {message}",
                    view=AlarmView()
                )
            else:
                await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message} *(Wala ang alarm.mp3 file!)*")
        else:
            await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message} *(Pumasok ka muna sa voice channel!)*")
            
    except ValueError:
        await ctx.send("❌ Mali ang format ng oras! Gamitin ang 24-hour format (Halimbawa: `!alarm 10:30` o `!alarm 22:30`).")
    except Exception as e:
        await ctx.send(f"❌ Error: `{e}`")

async def main():
    await start_dummy_server()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
