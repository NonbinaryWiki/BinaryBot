
import discord
from discord.ext import commands

class SupportCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help="Use this command to check if the bot is listening and can talk in the current channel.",
        description="Ping?"
    )
    async def ping(self, ctx):
        """ Pongs (and confirms that the bot is listening). """
        await ctx.send("Pong! :ping_pong: ({0}ms)".format(round(bot.latency * 1000)))

    @commands.command(
        help="Thank you, random citizen!",
        description="Thank you, random citizen!")
    async def thank(self, ctx):
        """ Send "Thank you random citizen" gif and a link to the patreon """
        await ctx.send("If you have the funds, help us keep the wiki alive!\n<https://www.patreon.com/nonbinarywiki>")
        await ctx.send(file=discord.File('random_citizen.gif'))

    @commands.command(
        help="This message!",
        description="Sends a list of all available commands from the bot. " \
                    "You can specify a command as a parameter to get more information on it, as well as an example.",
        usage="[command]",
        brief="ping"
        )
    async def help(cself, tx, arg="list"):
        cmds = [getattr(cmd, "name") for cmd in bot.commands]
        
        """ a primer:
        command.help is the text that appears when calling !help with no arguments
        command.description is the longer text that appears when calling !help with a specific command
        command.usage should be self-explanatory. don't include the name of the command in it, though!
        command.brief is the text to use in the example- this also shouldn't include the command's name
        """
        
        if arg.lower() in cmds:
            command = bot.get_command(arg.lower())
            usage = command.usage if command.usage is not None else '' # prevents lack of args from appearing as None, e.g. "!thanks None"
            embed = discord.Embed(
                title=":grey_question: {0}{1} {2}".format(bot.command_prefix, command.name, usage),
                color=discord.Colour.purple(),
                description=command.description)
            if command.usage is not None: # display this field only if the command actually takes arguments
                embed.add_field(name="Example", value="{0}{1} {2}".format(bot.command_prefix, command.name, command.brief))
            await ctx.send(embed=embed)
            
        elif arg.lower() == "list":
            embed = discord.Embed(title=':grey_question: List of commands', color=discord.Colour.purple())
            for command in bot.commands:
                if not command.hidden: # i don't expect that this bot will have any hidden commands, i'm just preventing unexpected behavior
                    usage = command.usage if command.usage is not None else ''
                    embed.add_field(name="{0}{1} {2}".format(bot.command_prefix, command.name, usage), value=command.help)
            embed.set_footer(text="Use {0}help [command] to get more information on a specific command.".format(bot.command_prefix))
            await ctx.send(embed=embed)
            
        else:
            await ctx.send("I couldn't find a command named '{0}'.".format(arg.lower()))

def setup(bot):
    bot.add_cog(SupportCog(bot))