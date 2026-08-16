import os
import asyncio
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
async def alarm(ctx, seconds: int, *, message: str = "Gising na!"):
    try:
        await ctx.send(f"⏰ Alarm set for **{seconds} seconds** from now - '{message}'")
        
        await asyncio.sleep(seconds)
        
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
            
    except Exception as e:
        await ctx.send(f"❌ Error: `{e}`")

async def main():
    await start_dummy_server()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
