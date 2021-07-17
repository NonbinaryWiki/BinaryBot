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
        properties = ["P1", "P14", "P11", "P15", "P21", "P37"] # Properties for instance of, umbrella term, frequency, related identities, main flag, and pride gallery link.
        
        try:
            data = utilities.getitemdata(arg.capitalize(), properties)    
        except:
            await ctx.send("That term is not in the NBDb! Maybe it's not added to the database, or you made a typo.")
            return
        
        print(str(data))
        
        # Process data
        entry_title, desc, instance_of, umbrella_data, frequency_data, related_data, flag_data, gallery_data = data
        main_id = entry_title.split(':')[1] # entry_title is Item:Qid

        if instance_of == None or all(claim['id'] != "Q7" for claim in instance_of):
            embed = discord.Embed(description="If you believe the database entry at https://data.nonbinary.wiki/wiki/" + entry_title + " should be classified as an identity, consider editing it to include an `Instance of (P1)` property with the value `Gender identity (Q7)`.")
            await ctx.send(":warning: We found a matching result in the database but it does not seem to be a gender identity term. Example: `!identity nonbinary`. (Maybe you made a typo?)", embed=embed)
            await discord.Message.delete(message)
            return

        # Default responses 
        umbrella = related = gallery = "None"
        frequency = "No data"
        flag = "https://static.miraheze.org/nonbinarywiki/3/32/Wikilogo_new.png"
        
        if umbrella_data != None: # Check if it has a P14 claim (umbrella term)
            umbrella_id = umbrella_data[0]['id'] # this is a Qid
            umbrella_json = utilities.getdataheader(umbrella_id)
            umbrella = utilities.stripstring(utilities.DictQuery(umbrella_json).get("search/label")) # this is the item's label
        
        if frequency_data != None: # Check if it has a P11 claim (Gender Census percentage)
            frequency = frequency_data[0] # this is a number with the % symbol
        
        if related_data != None: #Check if it has a P15 claim (related identities)
            related_id = related_data[0]['id'] # this is a Qid
            related_json = utilities.getdataheader(related_id)
            related = utilities.stripstring(utilities.DictQuery(related_json).get("search/label")) # this is the item's label
        
        if flag_data != None: # Check if it has a P21 claim (main pride flag)
            flag = flag_data[0] # list, should have a single item but just in case
            
        if gallery_data != None: # check if it has a P37 claim (pride gallery link)
            gallery = gallery_data[0]
        
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
            data = utilities.getitemdata(arg.capitalize(), properties)
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
            data = utilities.getitemdata(arg.lower(), properties)    
        except:
            await ctx.send("That term is not in the NBDb! Maybe it's not added to the database, or you made a typo.")
            return
        
        # Process data
        #title = ''.join(data[0]) 
        print("data: " + str(data))
        if data[1] == None: # Workaround to an NBDb bug where the item description is not displayed.
            desc = ""
        else:
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
        help="Tests the given pronouns in a random sentence.",
        description="Try on some new pronouns and see if they fit you!\n" \
                    "Pronouns can be entered as both the subject form (i.e. 'they') or subject/object (i.e. 'they/them')\n" \
                    "Instead of a pronoun, you can also enter 'none' and the bot will use no pronouns (using the name instead)." \
                    "If you're entering more than one word for the name, please enter them in quotes \"like this\".",
        usage="<name> <pronoun|none> [story number]",
        brief="John she/her"
    )
    async def pronountest(self, ctx, name = None, arg = None, story_num = None):
        utilities = self.bot.get_cog("UtilitiesCog")
        if arg == None or name == None:
            await ctx.send(":warning: You need to specify a name and a pronoun! Example: `!pronountest John she/her`")
            return
        
        if arg.lower() == "none": #no pronouns/name as pronouns option.
            num = "singular"
            subj = name.capitalize()
            obj = name.capitalize()
            ref = name.capitalize() + "'s self"
            posad = name.capitalize() + "'s"
            pos = name.capitalize()
        else:
            message = await ctx.send("Give me a moment. I will search the NBDb...")
            properties = ["P4", "P5", "P6", "P7", "P8", "P9", "P11"] # Properties for conjugation, pronoun forms and frequency

            try:
                data = utilities.getitemdata(arg.lower(), properties)
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
            has_have = "has"
            s = "s"
        elif num.lower() == "plural":
            was_were = "were"
            is_are = "are"
            has_have = "have"
            s = ""
        else:
            was_were = "was/were"
            is_are = "is/are"
            has_have = "has/have"
            s = "(s)"
        
        # Randomly choose and create a story
        with open('stories.txt') as stories:
            stories_ls = stories.read().replace("\n", "").split('|') # Due to multi-line stories, we need to use a custom separator.
        
        
        if story_num:
            story_num = story_num.replace('#','') # The stories have a # before its number, so some users were using the # in front of the number.
            if int(story_num) <= len(stories_ls):
                chosen_story = stories_ls[int(story_num)-1]
            else:
                await ctx.send("There's no story with this number! Giving you a random story instead:")
                chosen_story = random.choice(stories_ls)
        else:
            chosen_story = random.choice(stories_ls)
        story = chosen_story.format(
                name = name.capitalize(),
                subj = subj,
                obj = obj,
                posad = posad,
                pos = pos,
                pospro = pos,
                ref = ref,
                was_were = was_were,
                is_are = is_are,
                has_have = has_have,
                s = s)
        
        sentences = re.split('(?<=[.!?]) +', story)                 # split at each sentence, so it can be capitalized (in case of pronouns starting sentences)
        story = ' '.join([i[0].upper() + i[1:] for i in sentences]) # .capitalize() isn't used here because it converts every other letter in the sentence to lowercase,
                                                                    # which is undesirable in the case of "I"
        if not arg.lower() == "none":
            await discord.Message.delete(message) # message doesn't exist if the no pronouns option is used

        try:
            await ctx.send(story)
        except:
            await ctx.send("That term is not in the NBDb! Maybe try typing it differently?")
            await discord.Message.delete(message)

def setup(bot):
    bot.add_cog(NBDbCog(bot))
