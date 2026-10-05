from discord.ext import commands


class TextCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="set_message", description="Sets a scrolling message below the video.")
    async def set_message(self, ctx):
        pass

    @commands.hybrid_command(name="remove_messsage", description="Removes the current message from the board.")
    async def remove_message(self, ctx):
        pass

async def setup(bot: commands.Bot):
    await bot.add_cog(TextCommands(bot))
