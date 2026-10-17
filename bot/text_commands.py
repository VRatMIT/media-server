import matrix
from discord.ext import commands


class TextCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="set_message", description="Sets a scrolling message below the video.")
    async def set_message(self, ctx: commands.Context, message: str):
        matrix.action_queue.put(("message", message))
        await ctx.send(f"Message set to {message} by {ctx.author.display_name}.")

    @commands.hybrid_command(name="remove_message", description="Removes the current message from the board.")
    async def remove_message(self, ctx: commands.Context):
        matrix.action_queue.put(("message", None))
        await ctx.send("Removed the current message.")

async def setup(bot: commands.Bot):
    await bot.add_cog(TextCommands(bot))
