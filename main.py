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

# Cute Hello Kitty pink hearts direct image link
HELLO_KITTY_IMAGE = "https://i.imgur.com/8354c0Y.jpg"

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
            content=f"🎀 Alarm successfully set for **{self.target_time}** (Philippine Time) - '{self.message}'\n{HELLO_KITTY_IMAGE}", 
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
                channel_voice = author.voice.channel if author.voice else None
                
                if channel_voice:
                    vc = await channel_voice.connect()
                    
                    audio_path = "alarm.mp3"
                    if os.path.exists(audio_path):
                        audio_source = discord.FFmpegPCMAudio(audio_path, before_options="-stream_loop -1")
                        vc.play(audio_source)
                        
                        send_method = ctx.channel.send if isinstance(ctx, discord.Interaction) else ctx.send
                        await send_method(
                            content=f"🎀 **ALARM NA! GISING NA!** {author.mention} - {message}\n{HELLO_KITTY_IMAGE}",
                            view=AlarmView(ctx)
                        )
                    else:
                        send_method = ctx.channel.send if isinstance(ctx, discord.Interaction) else ctx.send
                        await send_method(f"🔔 **ALARM!** {author.mention} - {message} *(Wala ang alarm.mp3 file!)*")
                else:
                    send_method = ctx.channel.send if isinstance(ctx, discord.Interaction) else ctx.send
                    await send_method(f"🔔 **ALARM!** {author.mention} - {message} *(Hindi ka nakakonekta sa voice channel!)*")
            except Exception as e:
                print(f"Error sa pag-trigger ng alarm: {e}")
                
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
        
        view = SetAlarmView(full_time_str, message)
        await ctx.send(
            f"🎀 Pindutin ang button para itakda ang alarm sa **{full_time_str}**:\n{HELLO_KITTY_IMAGE}", 
            view=view
        )
        
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
