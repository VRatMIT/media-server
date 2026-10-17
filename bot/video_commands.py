import asyncio
import sqlite3

import db
import matrix
from discord import Colour, Embed
from download import download_video
from discord.ext import commands

MAX_LOOPS = 99

class VideoCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # @commands.hybrid_command(name="play", description="Plays a selected video from the library.")
    # async def play(self, ctx):
    #     pass

    @commands.hybrid_command(name="queue", description="Queues a selected video from the library")
    async def queue(self, ctx: commands.Context, video_title: str, loop: int = 1):
        loop = min(loop, MAX_LOOPS)
        for i in range(loop):
            matrix.video_queue.put((video_title, 0))
        await ctx.send(f"Q'd {video_title}{'.' if loop <= 1 else f' {loop} times.'}")

    @commands.hybrid_command(name="download", description="Downloads a video from a youtube link.")
    async def download(self, ctx: commands.Context, url: str, title: str):
        if not url.startswith(("https://", "http://")):
            await ctx.send("that's not a link (make sure to include http/https)", ephemeral=True)
            return
        if db.get_video(title):
            await ctx.send(f"`{title}` is already in the library.", ephemeral=True)
            return

        await ctx.defer()
        try:
            filename = await asyncio.to_thread(download_video, url)
        except Exception as e:
            await ctx.send(f"Download failed: {e}")
            return

        try:
            db.add_video(title, filename, ctx.author.id)
        except sqlite3.IntegrityError:
            (db.videos_dir() / filename).unlink()
            await ctx.send(f"`{title}` already in library")
            return
        await ctx.send(f"Added `{title}` to the library")

    @commands.hybrid_command(name="get_queue", description="Shows the upcoming videos in the queue.")
    async def get_queue(self, ctx: commands.Context, items: int = 5):
        items = min(items, 20)
        with matrix.video_queue.mutex:
            upcoming = list(matrix.video_queue.queue)[:items]

        if not upcoming:
            await ctx.send("Queue is empty!")
            return

        embed = Embed(title = "Queue",
                    color=Colour.random(),
                    description="".join([f"{i}. `{title}`\n" for i, (title, _) in enumerate(upcoming, start=1)]))
        await ctx.send(embed=embed)



async def setup(bot: commands.Bot):
    await bot.add_cog(VideoCommands(bot))
