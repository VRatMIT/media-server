from discord.ext import commands


class VideoCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="play", description="Plays a selected video from the library")
    async def play(self, ctx):
        pass

    @commands.hybrid_command(name="queue", description="Queues a selected video from the library")
    async def queue(self, ctx):
        pass

async def setup(bot: commands.Bot):
    await bot.add_cog(VideoCommands(bot))
