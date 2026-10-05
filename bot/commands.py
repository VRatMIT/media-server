import matrix
from discord.ext import commands


# General control
class ControlCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="on", description="Turns the matrix on (if off).")
    async def on(self, ctx: commands.Context):
        if matrix.state["power"]:
            await ctx.send("The matrix is already on.", ephemeral=True)
            return

        matrix.action_queue.put(("power", True))
        await ctx.send("Matrix turned on.")

    @commands.hybrid_command(name="off", description="Turns the matrix off (if on). Also clears the queue.")
    async def off(self, ctx: commands.Context):
        if not matrix.state["power"]:
            await ctx.send("The matrix is already off.", ephemeral=True)
            return

        matrix.action_queue.put(("power", False))
        matrix.clear_video_queue()
        await ctx.send("Matrix turned off.")

    @commands.hybrid_command(name="set_brightness", description="Sets the matrix's brightness.")
    async def set_brightness(self, ctx):
        pass

async def setup(bot: commands.Bot):
    await bot.add_cog(ControlCommands(bot))
