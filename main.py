import os
import asyncio
from datetime import datetime
from aiohttp import web
import discord
from discord.ext import commands, tasks
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

# Imbakang lalagyan ng naka-set na alarm
active_alarms = {}

class AlarmView(View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(label="Stop Alarm 🛑", style=discord.ButtonStyle.red)
    async def stop_button(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("🛑 Napatay na ang alarm!", ephemeral=False)
            self.stop()
        else:
            await interaction.response.send_message("❌ Walang tumutunog na alarm.", ephemeral=True)

@tasks.loop(seconds=5)
async def check_alarms():
    now = datetime.now().strftime("%I:%M %p") # Halimbawa: "03:30 PM"
    
    for guild_id, alarm_data in list(active_alarms.items()):
        target_time = alarm_data["time"]
        
        if now == target_time:
            ctx = alarm_data["ctx"]
            message = alarm_data["message"]
            
            try:
                if ctx.author.voice:
                    channel = ctx.author.voice.channel
                    vc = await channel.connect()
                    
                    audio_path = "alarm.mp3"
                    if os.path.exists(audio_path):
                        audio_source = discord.FFmpegPCMAudio(audio_path, before_options="-stream_loop -1")
                        vc.play(audio_source)
                        
                        await ctx.send(
                            content=f"🔔 **ALARM!** {ctx.author.mention} - {message}",
                            view=AlarmView(ctx)
                        )
                    else:
                        await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message} *(Wala ang alarm.mp3 file!)*")
                else:
                    await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message} *(Hindi ka nakakonekta sa voice channel!)*")
            except Exception as e:
                print(f"Error sa pag-trigger ng alarm: {e}")
                
            # Alisin na sa listahan para hindi maulit mamaya
            del active_alarms[guild_id]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    if not check_alarms.is_running():
        check_alarms.start()

@bot.command()
async def alarm(ctx, time_str: str, ampm: str, *, message: str = "Gising na!"):
    try:
        full_time_str = f"{time_str} {ampm.upper()}"
        datetime.strptime(full_time_str, "%I:%M %p")
        
        active_alarms[ctx.guild.id] = {
            "time": full_time_str,
            "ctx": ctx,
            "message": message
        }
        
        await ctx.send(f"⏰ Alarm set successfully for **{full_time_str}** - '{message}'")
        
    except ValueError:
        await ctx.send("❌ Mali ang format! Gamitin ang ganito: `!alarm 3:30 PM` o `!alarm 10:30 AM`.")
    except Exception as e:
        await ctx.send(f"❌ Error: `{e}`")

async def main():
    await start_dummy_server()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
