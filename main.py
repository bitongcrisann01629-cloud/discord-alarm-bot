import os
import asyncio
from aiohttp import web
import discord
from discord.ext import commands

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

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.command()
async def alarm(ctx, seconds: int, *, message: str = "Gising na!"):
    try:
        await ctx.send(f"⏰ Alarm set for **{seconds} seconds** from now - '{message}'")
        
        # Maghintay base sa seconds
        await asyncio.sleep(seconds)
        
        # Mag-tag sa chat kapag oras na
        await ctx.send(f"🔔 **ALARM!** {ctx.author.mention} - {message}")
            
    except Exception as e:
        await ctx.send(f"❌ Error: `{e}`")

async def main():
    await start_dummy_server()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
