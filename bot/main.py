import asyncio
import os

import db
import discord
import dotenv
import matrix
from discord.ext import commands

dotenv.load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SERVER_ID = os.getenv("SERVER_ID")

EXTENSIONS = ["commands", "text_commands", "video_commands"]


class CaveMediaBot(commands.Bot):
    async def setup_hook(self):
        db.init()

        # We now load all our commands
        for ext in EXTENSIONS:
            await self.load_extension(ext)

        GUILD_ID = discord.Object(id=SERVER_ID) # aparently discord complains
        # if you don't use their own set of objects and pass an int.
        
        self.tree.copy_global_to(guild=GUILD_ID)
        await self.tree.sync(guild=GUILD_ID)

bot = CaveMediaBot(command_prefix="!", intents=discord.Intents.default())

@bot.event
async def on_ready():
    print(f"{bot.user}")

async def main():
    try:
        async with bot:
            await asyncio.gather( # run both till completion (never :3)
                bot.start(DISCORD_BOT_TOKEN),
                asyncio.to_thread(matrix.run),
            )
    finally:
        matrix.stop.set()

# discord.utils.setup_logging()
asyncio.run(main())
