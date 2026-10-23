import asyncio

import bluetooth
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
    async def set_brightness(self, ctx: commands.Context, brightness: commands.Range[int, 1, 100]):
        matrix.action_queue.put(("brightness", brightness))
        await ctx.send(f"Brightness set to {brightness}.")

    @commands.hybrid_command(name="audio", description="Turns sound on the room speaker on or off.")
    async def audio(self, ctx: commands.Context, on: bool):
        await ctx.defer() #allow more time for bt to respond
        if not on:
            matrix.action_queue.put(("audio", False))
            await asyncio.to_thread(bluetooth.disconnect)
            await ctx.send("Audio turned off.")
            return

        if not await asyncio.to_thread(bluetooth.connect):
            await ctx.send("connection failed")
            return
        matrix.action_queue.put(("audio", True))
        await ctx.send("Audio toggled on. The next video will play audio")

async def setup(bot: commands.Bot):
    await bot.add_cog(ControlCommands(bot))
