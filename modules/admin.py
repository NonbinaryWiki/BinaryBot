import discord
from discord.ext import commands
from discord.commands import slash_command, Option
import subprocess

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @slash_command(name="update", description="Pulls the latest version from GitHub (owner-only).", guild_ids=[551837071703146506])
    @commands.is_owner()
    async def update(self, ctx):
        await ctx.defer()
        output = subprocess.check_output("git pull", shell=True)
        await ctx.respond("Pulling latest version from GitHub: ```" + str(output) + "``` Remember to use the reload command for the changes to take effect.")

    @slash_command(name="load", description="Loads a previously unloaded module (owner-only).", guild_ids=[551837071703146506])
    @commands.is_owner()
    async def load(self, ctx, cog: Option(str, "Name of the module (without .py extension)")):
        module = "modules." + cog
        try:
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.respond(f':scream: Error: {type(e).__name__} - {e}')
        else:
            await ctx.respond('Module loaded! :tada:')

    @slash_command(name="unload", description="Unloads a previously loaded module (owner-only).", guild_ids=[551837071703146506])
    @commands.is_owner()
    async def unload(self, ctx, cog: Option(str, "Name of the module (without .py extension)")):
        module = "modules." + cog
        try:
            self.bot.unload_extension(module)
        except Exception as e:
            await ctx.respond(f':scream: Error: {type(e).__name__} - {e}')
        else:
            await ctx.respond('Module unloaded! :tada:')

    @slash_command(name="reload", description="Reloads a previously loaded module (owner-only).", guild_ids=[551837071703146506])
    @commands.is_owner()
    async def reload(self, ctx, cog: Option(str, "Name of the module (without .py extension)")):
        module = "modules." + cog
        try:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.respond(f':scream: Error: {type(e).__name__} - {e}')
        else:
            await ctx.respond('Module reloaded! :tada:')

    @slash_command(name="servers", description="Displays a list of all servers the bot is in (owner-only).", guild_ids=[551837071703146506])
    @commands.is_owner()
    async def servers(self, ctx):
        activeservers = self.bot.guilds
        servernames = []
        for guild in activeservers:
            servernames.append(guild.name)
        await ctx.respond("I'm in **{0}** servers:  {1}".format(len(servernames), ", ".join(servernames)))

    @slash_command(name="error", description="Forcibly causes the bot to error, for debugging purposes (owner-only).", guild_ids=[551837071703146506])
    @commands.is_owner()
    async def error(self, ctx):
        raise ValueError("Someone used !error.")
        await ctx.respond("Don't you DARE give me an error you dunce! :(")

    @commands.slash_command(name="botinfo", description="Get bot info!")
    @commands.is_owner()
    async def botinfo(self, ctx):
        amount = 0
        bot_channels = 0
        members = 0
        for i in self.bot.guilds:
            amount += 1
            bot_channels += len(i.channels)
            members += i.member_count
        embed = discord.Embed(
            title="Bot Info",
            description=f"I'm in {amount} servers, with a total of {bot_channels} channels and {members} users that can use my commands.",
            color=discord.Color.random()
        )
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(AdminCog(bot))
