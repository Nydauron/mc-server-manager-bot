import discord
from discord.ext import commands
import config
import asyncio
import signal
import sys

intents = discord.Intents.default()

bot = commands.Bot(command_prefix=(config.BOT_PREFIX), case_insensitive=True, intents=intents)

@bot.event
async def on_message(message):
    if message.author == bot.user or message.webhook_id:
        return
    print(message.content)
    await bot.process_commands(message)

async def signal_int_handler():
    bot.unload_extension("servermanager") # Shutsdown server if on
    await asyncio.sleep(0)
    sys.exit(0)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.idle, activity=None)
    for signame in ('SIGINT', 'SIGTERM'):
        bot.loop.add_signal_handler(getattr(signal, signame),
                                    lambda: asyncio.create_task(signal_int_handler()))
    print("Bot logged in!")

bot.load_extension("servermanager")
bot.run(config.BOT_TOKEN)