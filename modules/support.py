
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
        await ctx.send("Pong! :ping_pong: ({0}ms)".format(round(self.bot.latency * 1000)))

    @commands.command(
        help="Thank you, random citizen!",
        description="Thank you, random citizen!")
    async def thank(self, ctx):
        """ Send "Thank you random citizen" gif and a link to the patreon """
        await ctx.send("You can support the Nonbinary Wiki and this bot through Ko-fi!\n<https://ko-fi.com/nonbinarywiki>")
        await ctx.send(file=discord.File('random_citizen.gif'))

        
    @commands.command(
        help="Use this command to invite the bot to your own server.",
        description="Gives a link that can be used to invite the bot to your server if you have the Manage Server permission."
    )
    async def invite(self, ctx):
        """ Send an invite link for the bot. """
        await ctx.send("Use the following link to invite me to your server! Please note that you will need the _Manage Server_ permission in order to invite me. <https://discord.com/oauth2/authorize?client_id=521031266762489857&permissions=0&scope=bot>")
        
    @commands.command(
        help="This message!",
        description="Sends a list of all available commands from the self.bot. " \
                    "You can specify a command as a parameter to get more information on it, as well as an example.",
        usage="[command]",
        brief="ping"
        )
    async def help(self, ctx, arg="list"):
        cmds = [getattr(cmd, "name") for cmd in self.bot.commands]
        prefix = "!"
        
        """ a primer:
        command.help is the text that appears when calling !help with no arguments
        command.description is the longer text that appears when calling !help with a specific command
        command.usage should be self-explanatory. don't include the name of the command in it, though!
        command.brief is the text to use in the example- this also shouldn't include the command's name
        """
        
        if arg.lower() in cmds:
            command = self.bot.get_command(arg.lower())
            usage = command.usage if command.usage is not None else '' # prevents lack of args from appearing as None, e.g. "!thanks None"
            embed = discord.Embed(
                title=":grey_question: {0}{1} {2}".format(prefix, command.name, usage),
                color=discord.Colour.purple(),
                description=command.description)
            if command.usage is not None: # display this field only if the command actually takes arguments
                embed.add_field(name="Example", value="{0}{1} {2}".format(prefix, command.name, command.brief))
            await ctx.send(embed=embed)
            
        elif arg.lower() == "list":
            embed = discord.Embed(title=':grey_question: List of commands', color=discord.Colour.purple())
            for command in self.bot.commands:
                if not command.hidden: # i don't expect that this bot will have any hidden commands, i'm just preventing unexpected behavior
                    usage = command.usage if command.usage is not None else ''
                    embed.add_field(name="{0}{1} {2}".format(prefix, command.name, usage), value=command.help)
            embed.set_footer(text="Use {0}help [command] to get more information on a specific command.".format(prefix))
            await ctx.send(embed=embed)
            
        else:
            await ctx.send("I couldn't find a command named '{0}'.".format(arg.lower()))

def setup(bot):
    bot.add_cog(SupportCog(bot))
