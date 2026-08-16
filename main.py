import os
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
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

active_alarms = {}

class AlarmView(View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(label="Stop Alarm 🛑", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: Button):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("🛑 Napatay na ang alarm!", ephemeral=False)
            self.stop()
        else:
            await interaction.response.send_message("❌ Walang tumutunog na alarm.", ephemeral=True)

class SetAlarmView(View):
    def __init__(self, target_time, message):
        super().__init__(timeout=60)
        self.target_time = target_time
        self.message = message

    @discord.ui.button(label="Kumpirmahin ✅", style=discord.ButtonStyle.primary)
    async def confirm_button(self, interaction: discord.Interaction, button: Button):
        active_alarms[interaction.guild.id] = {
            "time": self.target_time,
            "ctx": interaction,
            "message": self.message
        }
        for child in self.children:
            child.disabled = True
            
        await interaction.response.edit_message(
            content=f"🎀 Alarm successfully set for **{self.target_time}** (Philippine Time) - '{self.message}'", 
            view=self
        )

    @discord.ui.button(label="Kanselahin ❌", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="❌ Na-cancel ang pag-set ng alarm.", view=self)

@tasks.loop(seconds=5)
async def check_alarms():
    now = datetime.now(ZoneInfo("Asia/Manila")).strftime("%I:%M %p")
    
    for guild_id, alarm_data in list(active_alarms.items()):
        target_time = alarm_data["time"]
        
        if now == target_time:
            ctx = alarm_data["ctx"]
            message = alarm_data["message"]
            
            try:
                author = ctx.user if isinstance(ctx, discord.Interaction) else ctx.author
                channel_voice = author.voice.channel if author and author.voice else None
                
                send_method = ctx.channel.send if isinstance(ctx, discord.Interaction) else ctx.send
                
                if channel_voice:
                    if not ctx.guild.voice_client:
                        vc = await channel_voice.connect()
                    else:
                        vc = ctx.guild.voice_client
                    
                    if os.path.exists("alarm.mp3"):
                        if not vc.is_playing():
                            audio_source = discord.FFmpegPCMAudio("alarm.mp3", before_options="-stream_loop -1")
                            vc.play(audio_source)
                
                # Hahanapin ang in-upload na hello.gif file nang ligtas
                gif_filename = "hello.gif"
                for f in os.listdir("."):
                    if f.lower() == "hello.gif":
                        gif_filename = f
                        break
                
                if os.path.exists(gif_filename):
                    file = discord.File(gif_filename, filename="hello.gif")
                    embed = discord.Embed(
                        title="🎀 ALARM NA! GISING NA! 🎀",
                        description=f"{author.mention} - {message}",
                        color=discord.Color.from_rgb(255, 105, 180)
                    )
                    embed.set_image(url="attachment://hello.gif")
                    await send_method(embed=embed, file=file, view=AlarmView(ctx))
                else:
                    await send_method(f"🎀 **ALARM NA! GISING NA!** {author.mention} - {message}", view=AlarmView(ctx))
                    
            except Exception as e:
                print(f"Error sa pag-trigger ng alarm: {e}")
                
            del active_alarms[guild_id]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    if not check_alarms.is_running():
        check_alarms.start()

@bot.command()
async def alarm(ctx, time_str: str, ampm: str, *, message: str = "Gising na baby ulann ko"):
    try:
        # Awtomatikong nilalagyan ng zero kung nakalimutan mo (halimbawa: 3:30 -> 03:30)
        parts = time_str.split(':')
        if len(parts) == 2 and len(parts[0]) == 1:
            time_str = f"0{time_str}"
            
        full_time_str = f"{time_str} {ampm.upper()}"
        datetime.strptime(full_time_str, "%I:%M %p")
        
        view = SetAlarmView(full_time_str, message)
        await ctx.send(
            f"🎀 Pindutin ang button para itakda ang alarm sa **{full_time_str}** (Mensahe: *{message}*):", 
            view=view
        )
        
    except ValueError:
        await ctx.send("❌ Mali ang format! Gamitin ang ganito: `!alarm 3:30 PM` o `!alarm 03:30 PM`.")
    except Exception as e:
        await ctx.send(f"❌ Error: `{e}`")

async def main():
    await start_dummy_server()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
