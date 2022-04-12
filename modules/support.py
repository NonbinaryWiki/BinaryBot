import discord
from discord.commands import slash_command
from discord.ext import commands

import requests

class SupportCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="ping")
    async def ping(self, ctx):
        """Confirms the bot is listening and pings the Nonbinary Wiki and the NBDb."""
        await ctx.respond("Pong! :ping_pong: ({0}ms)".format(round(self.bot.latency * 1000)))
        
        wikiping = await ctx.send("_Calculating pings to the Nonbinary Wiki and the NBDb..._")
        nbw_ping = requests.get('https://nonbinary.wiki').elapsed.total_seconds()*1000
        nbdb_ping = requests.get('https://data.nonbinary.wiki').elapsed.total_seconds()*1000
        
        await discord.Message.delete(wikiping)
        await ctx.send(f"Nonbinary Wiki: {int(nbw_ping)}ms // NBDb: {int(nbdb_ping)}ms")

    @slash_command(name="support")
    async def support(self, ctx):
        """Sends a link to the bot's Ko-fi page."""
        await ctx.respond(":coffee: You can support the Nonbinary Wiki and this bot through Ko-fi!\n<https://ko-fi.com/nonbinarywiki>")
        
    @slash_command(name="invite")
    async def invite(self, ctx):
        """Sends an invite link for the bot."""
        await ctx.respond(":raised_hands: Use the following link to invite me to your server! Please note that you will need the _Manage Server_ permission in order to invite me. <https://discord.com/oauth2/authorize?client_id=521031266762489857&permissions=0&scope=bot>")

def setup(bot):
    bot.add_cog(SupportCog(bot))
