import discord
from discord.ext import commands
import subprocess

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help="Updates the bot to the latest version. Admin-only command",
        description="Pulls the latest version of the code from the GitHub repository. Only the bot owner can use this command",
        hidden=True
    )
    @commands.is_owner()
    async def update(ctx):
        if ctx.message.author.id == 192011575777951744: #That's Ondo's Discord user ID
            output = subprocess.check_output("git pull", shell=True)
            await ctx.send("Pulling latest version from GitHub: ```" + str(output) + "```")
            await ctx.send("Remember to use the reload command for the changes to take effect.")
        else:
            await ctx.send("You don't have permission to use this command.")

    # Hidden means it won't show up on the default help.
    @commands.command(
        help="Loads a module. Admin-only command",
        description="Loads a module from the modules folder that has previously been unloaded. You need to use the dot path (e.g. modules.admin). Only the bot owner can use this command",
        hidden=True
    )
    @commands.is_owner()
    async def load(self, ctx, *, cog: str):

        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @commands.command(
        help="Unloads a module. Admin-only command",
        description="Unloads a module from the modules folder. You need to use the dot path (e.g. modules.admin). Only the bot owner can use this command",
        hidden=True
    )
    @commands.is_owner()
    async def unload(self, ctx, *, cog: str):
        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @commands.command(
        help="Reloads a module. Admin-only command",
        description="Unloads and then loads back a module from the modules folder. You need to use the dot path (e.g. modules.admin). Only the bot owner can use this command",
        hidden=True
    )
    @commands.is_owner()
    async def reload(self, ctx, *, cog: str):
        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

def setup(bot):
    bot.add_cog(AdminCog(bot))