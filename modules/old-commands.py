import discord
from discord.ext import commands

msg = "I've migrated to slash commands. **Please, use the same command but with a `/` instead of an `!`.** This change is due to new limitations implemented by Discord."

class OldCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def identity(self, ctx):
        await ctx.send(msg)

    @commands.command()
    async def pronoun(self, ctx):
        await ctx.send(msg)

    @commands.command()
    async def pronountest(self, ctx):
        await ctx.send(msg)

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(msg)

    @commands.command()
    async def help(self, ctx):
        await ctx.send("I've migrated to slash commands due to new limitations implemented by Discord. To see all of my commands, **type `/` and click on my logo.**")

    @commands.command()
    async def flag(self, ctx):
        await ctx.send(msg)

def setup(bot):
    bot.add_cog(OldCog(bot))