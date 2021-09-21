import os

from discord.ext import commands
from dotenv import load_dotenv

startup_extensions = ["music_bot"]


bot = commands.Bot(command_prefix=commands.when_mentioned_or("$"),
                   description="shokie-bot ver. alpha")

if __name__ == '__main__':
    for extension in startup_extensions:
        bot.load_extension(extension)

load_dotenv('.\.env') # don't push this to vcs for obvious reasons
TOKEN = os.getenv('DISCORD_TOKEN')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.event
async def on_disconnect():
    print(f"Logging out")
    return

bot.run(TOKEN)