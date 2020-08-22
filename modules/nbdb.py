import discord
from discord.ext import commands
import urllib, json, requests
import random
import re

footer = "This data has been extracted from the NBDb (data.nonbinary.wiki), a project by the Nonbinary Wiki (nonbinary.wiki)." # Used as credit in embeds

class NBDbCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help="Gets some information about the specified identity from the Nonbinary Wiki.",
        description="Enter a nonbinary identity to get a short description of the identity as well as some useful data, " \
                    "such as its popularity in the Gender Census. You will also get a link to the wiki page about this identity.",
        usage="<identity>",
        brief="nonbinary"
    )
    async def identity(self, ctx, *, arg):
        """ Gives some information about the specified identity, including an excerpt, the flag and some data from the Gender Census. """
        # Example JSONFM response: https://data.nonbinary.wiki/w/api.php?action=wbgetentities&ids=Q20&format=jsonfm
        utilities = self.bot.get_cog("UtilitiesCog")
        if arg == None:
            await ctx.send(":warning: You need to specify an identity! Example: `!identity nonbinary`.")
            return
        message = await ctx.send("Give me a moment. I will search the NBDb...")
        properties = ["P14", "P11", "P15", "P21", "P37"] # Properties for umbrella term, frequency, related identities, main flag, and pride gallery link.
        
        try:
            data = utilities.getitemdata(arg, properties)    
        except:
            await ctx.send("That term is not in the NBDb! Maybe it's not added to the database, or you made a typo.")
            return
        
        print(str(data))
        
        # Process data
        desc = data[1]
        main_id = data[0].split(':')[1] # data[0] is Item:Qid
        
        if data[2] != None: # Check if it has a P14 claim (umbrella term)
            umbrella_id = data[2][0]['id'] # this is a Qid
            umbrella_json = utilities.getdataheader(umbrella_id)
            umbrella = utilities.stripstring(utilities.DictQuery(umbrella_json).get("search/label")) # this is the item's label
        else:
            umbrella = "None"
        
        if data[3] != None: # Check if it has a P11 claim (Gender Census percentage)
            frequency = data[3][0] # this is a number with the % symbol
        else:
            frequency = "No data"
        
        if data[4] != None: #Check if it has a P15 claim (related identities)
            related_id = data[4][0]['id'] # this is a Qid
            related_json = utilities.getdataheader(related_id)
            related = utilities.stripstring(utilities.DictQuery(related_json).get("search/label")) # this is the item's label
        else:
            related = "None"
        
        if data[5] != None: # Check if it has a P21 claim (main pride flag)
            flag = data[5][0] # list, should have a single item but just in case
        else:
            flag = "https://static.miraheze.org/nonbinarywiki/3/32/Wikilogo_new.png"
            
        if data[6] != None: # check if it has a P37 claim (pride gallery link)
            gallery = data[6][0]
        else:
            gallery = "None"
        
        # Get interwiki for the nonbinary wiki
        interlink_json = utilities.getdatabody(main_id)
        sitelinks = utilities.DictQuery(interlink_json).get("entities/{0}/sitelinks".format(main_id))
        if "nonbinarywiki" in sitelinks:
            sitelink = utilities.DictQuery(interlink_json).get("entities/{0}/sitelinks/nonbinarywiki/title".format(main_id))
            interlink = "https://nonbinary.wiki/wiki/{0}".format(sitelink)
        else: # fallback: link to the nbdb item page
            interlink = "https://data.nonbinary.wiki/wiki/Item:{0}".format(main_id)
        
        # Set embed
        embed = discord.Embed(title=':link: {0}'.format(arg.title()), description=desc, url="{0}".format(interlink))
        embed.set_thumbnail(url=flag)
        if umbrella != "None":
            embed.add_field(name="Umbrella term", value="{0}".format(umbrella))
        if related != "None":
            embed.add_field(name="Related identities", value="{0}".format(related))
        embed.add_field(name="Gender Census", value="{0} of respondents".format(frequency))
        if gallery != "None":
            embed.add_field(name="Pride flag gallery", value="[Click here!]({0})".format(gallery))
        embed.set_footer(text=footer)
        
        await discord.Message.delete(message)
        await ctx.send(embed=embed)

    @commands.command(
        help="Gets some information about the specified flag from the Nonbinary Wiki.",
        description="Enter a nonbinary identity to get its flag and its meaning, as well as alternative flags if there are any. You may use a number" \
                    " after the identity to get an alternative flag; this number can be anything from 1 to the number of available alternative flags.",
        usage="<identity> [number]",
        brief="nonbinary"
    )
    async def flag(self, ctx, arg, flag = None):
        """ Gives some information about the specified identity flag. """
        utilities = self.bot.get_cog("UtilitiesCog")
        if arg == None:
            await ctx.send(":warning: You need to specify an identity! Example: `!identity nonbinary`.")
            return
        message = await ctx.send("Give me a moment. I will search the NBDb...")
        properties = ["P21", "P22"] # Properties for main flag and alternative flags.
        
        try:
            data = utilities.getitemdata(arg, properties)
            print(str(data))
        except:
            await discord.Message.delete(message)
            await ctx.send("That term is not in the NBDb! Maybe it's not added to the database, or you made a typo.")
            return
        
        # Process data
        desc = data[1]
        main_id = data[0].split(':')[1] # data[0] is Item:Qid
        
        if data[2] != None: # Look for the main flag (data[2] is the P21 claim)
            main_flag = data[2][0]
        else:
            await discord.Message.delete(message)
            await ctx.send("I found the identity on the NBDb, but it doesn't seem to have any associated pride flag. Use `!identity {0}` to get more information about this identity.".format(arg))
            return
        
        if data[3] != None: # Look for alternative flags (data[3] is the P22 claim)
            alt_flags = str(len(data[3]))
            flags_list = data[3]
        else:
            alt_flags = "None"
        
        if flag != None: # If there is a flag number specified, make sure that it actually exists
            flag_num = int(flag)-1 # make it human and start counting from 1, not 0
            if int(flag) > int(alt_flags):
                await discord.Message.delete(message)
                await ctx.send("I found the identity on the NBDb, but it only has {0} alternative flags! Use a lower number.".format(alt_flags))
                return
            else:
                show_flag = flags_list[flag_num]
        else:
            show_flag = main_flag # use the default flag if no alternative flag is specified
            
        if show_flag.endswith('.svg'): # Apparently embeds don't like svg files
            await discord.Message.delete(message)
            await ctx.send("I found this flag, but I can't display it. You may view it in this URL: {0}".format(show_flag))
            return
            
        data_json = utilities.getdatabody(main_id)
        
        # Pick a page to link in the embed title (preferably the wiki article)
        sitelinks = utilities.DictQuery(data_json).get("entities/{0}/sitelinks".format(main_id))
        if "nonbinarywiki" in sitelinks:
            sitelink = utilities.DictQuery(data_json).get("entities/{0}/sitelinks/nonbinarywiki/title".format(main_id))
            interlink = "https://nonbinary.wiki/wiki/{0}".format(sitelink)
        else: # fallback: link to the nbdb item page for the identity
            interlink = "https://data.nonbinary.wiki/wiki/Item:{0}".format(main_id)
        
        # Choose which flag to get
        if flag == None: # Get the default flag + meaning (default behaviour)
            meaning_json = utilities.DictQuery(data_json).get("entities/{0}/claims/P21".format(main_id))
            try:
                meaning = meaning_json[0]["qualifiers"]["P38"][0]["datavalue"]["value"]
            except KeyError:
                meaning = "Unknown"
        else: # Get the specified alternative flag (if any). "flag" is the second argument of the command
            meaning_json = utilities.DictQuery(data_json).get("entities/{0}/claims/P22".format(main_id))
            try:
                meaning = meaning_json[flag_num]["qualifiers"]["P38"][0]["datavalue"]["value"]
            except KeyError:
                meaning = "Unknown"         
        
        # Set embed
        embed = discord.Embed(title=':link: {0}'.format(arg.title()), description=desc, url="{0}".format(interlink))
        embed.set_image(url=show_flag)
        embed.add_field(name="Flag meaning", value="{0}".format(meaning))
        embed.add_field(name="Alternative flags", value="{0}".format(alt_flags))
        embed.set_footer(text=footer)
        
        await discord.Message.delete(message)
        await ctx.send(embed=embed)
        
    @commands.command(
        help="Gives some useful information about the specified pronoun set.",
        description="Get some information about the given pronouns. Please, give the bot the first two pronouns of the set only",
        usage="<pronoun set>",
        brief="they/them"
    )
    async def pronoun(self, ctx, arg = None):
        utilities = self.bot.get_cog("UtilitiesCog")
        if arg == None:
            await ctx.send(":warning: You need to specify a pronoun! Example: `!pronoun they/them`.")
            return
        message = await ctx.send("Give me a moment. I will search the NBDb...")
        properties = ["P4", "P5", "P6", "P7", "P8", "P9", "P11"] # Properties for conjugation, pronoun forms and frequency
        
        try:
            data = utilities.getitemdata(arg, properties)    
        except:
            await ctx.send("That term is not in the NBDb! Maybe it's not added to the database, or you made a typo.")
            return
        
        # Process data
        #title = ''.join(data[0]) 
        desc = ''.join(data[1]) 
        freq = ''.join(data[8]) if isinstance(data[8], list) else "[unknown]"
        num = '/'.join(data[2]) if isinstance(data[2], list) else "[unknown]" # a pronoun set can have multiple grammatical numbers
        subj = '/'.join(data[3]) if isinstance(data[3], list) else "[unknown]"
        obj = '/'.join(data[4]) if isinstance(data[4], list) else "[unknown]"
        posad = '/'.join(data[5]) if isinstance(data[5], list) else "[unknown]"
        pos= '/'.join(data[6]) if isinstance(data[6], list) else "[unknown]"
        ref = '/'.join(data[7]) if isinstance(data[7], list) else "[unknown]"
        
        # Set embed
        embed = discord.Embed(title="Information about the " + subj + "/" + obj + " pronoun.", description=desc)
        embed.add_field(name="Conjugation", value=num, inline=True)
        embed.add_field(name="Subjective", value="**{}** ate the cake.".format(subj.capitalize()), inline=True)
        embed.add_field(name="Objective", value="I like **{}**.".format(obj), inline=True)
        embed.add_field(name="Possessive Determiner", value="**{}** smile is pretty.".format(posad.capitalize()), inline=True)
        embed.add_field(name="Possessive Pronoun", value="The book is **{}**.".format(pos), inline=True)
        embed.add_field(name="Reflexive", value="{} did it by **{}**.".format(subj.capitalize(), ref), inline=True)
        embed.add_field(name="Frequency", value=freq, inline=True)
        embed.set_footer(text=footer)

        await discord.Message.delete(message)
        await ctx.send(embed=embed)


    @commands.command(
        help="Tests the given data in a predefined sentence (this command is WIP).",
        description="Try on some new pronouns and see if they fit you!\n" \
                    "Pronouns can be entered as both the subject form (i.e. 'they') or subject/object (i.e. 'they/them')\n" \
                    "If you're entering more than one word, please enter them in quotes \"like this\".",
        usage="<name> <pronoun>",
        brief="John she/her"
    )
    async def pronountest(self, ctx, name = None, arg = None):
        utilities = self.bot.get_cog("UtilitiesCog")
        if arg == None or name == None:
            await ctx.send(":warning: You need to specify a name and a pronoun! Example: `!pronountest John she/her`")
            return
        
        message = await ctx.send("Give me a moment. I will search the NBDb...")
        properties = ["P4", "P5", "P6", "P7", "P8", "P9", "P11"] # Properties for conjugation, pronoun forms and frequency
        
        try:
            data = utilities.getitemdata(arg, properties)
        except:
            await ctx.send("That term is not in the NBDb! Maybe it's not added to the database, or you made a typo.")
            await discord.Message.delete(message)
            return
        
        print(str(data))
        
        # Process data
        #title = ''.join(data[0]) 
        #desc = ''.join(data[1]) 
        num = '/'.join(data[2]) if isinstance(data[2], list) else "[unknown]" # a pronoun set can have multiple grammatical numbers
        subj = '/'.join(data[3]) if isinstance(data[3], list) else "[unknown]"
        obj = '/'.join(data[4]) if isinstance(data[4], list) else "[unknown]"
        posad = '/'.join(data[5]) if isinstance(data[5], list) else "[unknown]"
        pos= '/'.join(data[6]) if isinstance(data[6], list) else "[unknown]"
        ref = '/'.join(data[7]) if isinstance(data[7], list) else "[unknown]"
        
        # Make sure that the verbs are conjugated according to the item's P4 claim (conjugation)
        if num.lower() == "singular": # this is a bit clunky, can it be improved?
            was_were = "was"
            is_are = "is"
        elif num.lower() == "plural":
            was_were = "were"
            is_are = "are"
        else:
            was_were = "was/were"
            is_are = "is/are"
        
        # Randomly choose and create a story
        with open('stories.txt') as stories:
            stories_ls = stories.read().splitlines() # .readlines() leaves the trailing newline, .splitlines() does not
        
        story = random.choice(stories_ls).format(
            name = name.capitalize(),
            subj = subj,
            obj = obj,
            posad = posad,
            pos = pos,
            ref = ref,
            was_were = was_were,
            is_are = is_are)
        
        sentences = re.split('(?<=[.!?]) +', story)                 # split at each sentence, so it can be capitalized (in case of pronouns starting sentences)
        story = ' '.join([i[0].upper() + i[1:] for i in sentences]) # .capitalize() isn't used here because it converts every other letter in the sentence to lowercase,
                                                                    # which is undesirable in the case of "I"
        await discord.Message.delete(message)

        try:
            await ctx.send(story)
        except:
            await ctx.send("That term is not in the NBDb! Maybe try typing it differently?")
            await discord.Message.delete(message)

def setup(bot):
    bot.add_cog(NBDbCog(bot))
