import discord
from discord.ext import commands
from discord.commands import slash_command, Option
import urllib, json, requests
import random
import re
import traceback
import os

footer = "This data has been extracted from the NBDb (data.nonbinary.wiki), a project by the Nonbinary Wiki (nonbinary.wiki)." # Used as credit in embeds
notfounderror = "I couldn't find this in my database—check for typos or try again later (I might not be synced the latest version)."

class NBDbCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="identity", description="Gives some information about the specified identity pulled from the NBDb.")
    async def identity(self, ctx, identity: Option(str, "Name of the gender identity")):
        await ctx.defer()
        # Example JSONFM response: https://data.nonbinary.wiki/w/api.php?action=wbgetentities&ids=Q20&format=jsonfm
        properties = ["P1", "P14", "P11", "P15", "P21", "P37"] # Properties for instance of, umbrella term, frequency, related identities, main flag, and pride gallery link.
        utilities = self.bot.get_cog("UtilitiesCog")

        index_file = os.path.join("NBDB_lists", "id-index.json")
        in_index = utilities.check_index(index_file, identity.lower())
        if in_index:
            print("Identity in local databases " + in_index)
            data = utilities.getlocaldata(in_index, properties)
        else:
            await ctx.respond(notfounderror)
            return
        
        print(str(data))
        main_id, desc, instance_of, umbrella_data, frequency_data, related_data, flag_data, gallery_data, sitelink = data

        if instance_of == None or all(claim['id'] != "Q7" for claim in instance_of):
            embed = discord.Embed(description="If you believe the database entry at https://data.nonbinary.wiki/wiki/" + entry_title + " should be classified as an identity, consider editing it to include an `Instance of (P1)` property with the value `Gender identity (Q7)`.")
            await ctx.respond(":warning: We found a matching result in the database but it does not seem to be a gender identity term. Example: `/identity nonbinary`. (Maybe you made a typo?)", embed=embed)
            return

        # Default responses
        umbrella = related = gallery = "None"
        frequency = "No data"
        flag = "https://static.miraheze.org/nonbinarywiki/3/32/Wikilogo_new.png"

        if umbrella_data != "[unknown]" and umbrella_data != None: # Check if it has a P14 claim (umbrella term)
            umbrella_terms = []
            for i in umbrella_data:
                id = i['id']
                with open(index_file, "r") as f:
                    dict = json.load(f)
                    term = dict[id][0]
                    umbrella_terms.append(term)
            umbrella = ", ".join(umbrella_terms)

        if frequency_data != None: # Check if it has a P11 claim (Gender Census percentage)
            frequency = frequency_data[0] # this is a number with the % symbol

        if related_data != "[unknown]" and related_data != None: #Check if it has a P15 claim (related identities)
            related_terms = []
            for i in related_data:
                id = i['id']
                with open(index_file, "r") as f:
                    dict = json.load(f)
                    term = dict[id][0]
                    related_terms.append(term)
            related = ", ".join(related_terms)

        if flag_data != None: # Check if it has a P21 claim (main pride flag)
            flag = flag_data[0] # list, should have a single item but just in case

        if gallery_data != None: # check if it has a P37 claim (pride gallery link)
            gallery = gallery_data[0]

        # Get interwiki for the nonbinary wiki
        if sitelink != "[unknown]":
            interlink = "https://nonbinary.wiki/wiki/{0}".format(sitelink)
        else: # fallback: link to the nbdb item page
            interlink = "https://data.nonbinary.wiki/wiki/Item:{0}".format(main_id)

        # Set embed
        embed = discord.Embed(title=':link: {0}'.format(identity.title()), description=desc, url="{0}".format(interlink))
        embed.set_thumbnail(url=flag)
        if umbrella != "None":
            embed.add_field(name="Umbrella term", value="{0}".format(umbrella))
        if related != "None":
            embed.add_field(name="Related identities", value="{0}".format(related))
        embed.add_field(name="Gender Census", value="{0} of respondents".format(frequency))
        if gallery != "None":
            embed.add_field(name="Pride flag gallery", value="[Click here!]({0})".format(gallery))
        embed.add_field(name="Flag information", value=f"Use `/flag {identity.title()}` to get more information about this flag.")
        embed.set_footer(text=footer)

        await ctx.respond(embed=embed)

    @slash_command(name="flag", description="Gives some information about the specified identity flag, pulled from the NBDb.")
    async def flag(self, ctx, identity: Option(str, "Name of the gender identity"), number: Option(int, "Number of the flag (to get a specific flag)", required=False)):
        await ctx.defer()
        utilities = self.bot.get_cog("UtilitiesCog")
        properties = ["P21", "P22"] # Properties for main flag and alternative flags.

        index_file = os.path.join("NBDB_lists", "id-index.json")
        in_index = utilities.check_index(index_file, identity.lower())
        if in_index:
            print("Identity in local databases " + in_index)
            data = utilities.getlocaldata(in_index, properties)
            #[main_id, desc, P21, P22, sitelink]
        else:
            await ctx.respond(notfounderror)
            return

        print(str(data))
        # Process data
        desc = data[1]
        id = data[0]
        sitelink = data[4]

        if data[2] != None: # Look for the main flag (data[2] is the P21 claim)
            main_flag = data[2][0]
        else:
            await ctx.respond("I found the identity on the NBDb, but it doesn't seem to have any associated pride flag. Use `!identity {0}` to get more information about this identity.".format(identity))
            return

        if data[3] != None: # Look for alternative flags (data[3] is the P22 claim)
            alt_flags = str(len(data[3]))
            flags_list = data[3]
        else:
            alt_flags = "None"

        if number != None: # If there is a flag number specified, make sure that it actually exists
            flag_num = int(number)-1 # make it human and start counting from 1, not 0
            if int(number) > int(alt_flags):
                await ctx.respond(f"I found the identity on the NBDb, but it only has {alt_flags} alternative flags! Use a lower number.")
                return
            else:
                show_flag = flags_list[flag_num]
        else:
            show_flag = main_flag # use the default flag if no alternative flag is specified

        if show_flag.endswith('.svg'): # Apparently embeds don't like svg files
            await ctx.respond(f"I found this flag, but I can't display it. You may view it in this URL: {show_flag}")
            return

        # Choose which flag to get
        if number == None: # Get the default flag + meaning (default behaviour)
            meaning_data = utilities.getqualifierdata(in_index, "P21", "P38")
            if meaning_data == [None]:
                meaning = None
            else:
                print(str(meaning_data))
                meaning = meaning_data[0][0]["datavalue"]["value"]
        else: # Get the specified alternative flag (if any). "flag" is the second argument of the command
            meaning_data = utilities.getqualifierdata(in_index, "P22", "P38")
            try:
                meaning = meaning_data[0][0]["datavalue"]["value"]
            except:
                meaning = None
        
        # Pick a page to link in the embed title (preferably the wiki article)
        print("sitelink: " + str(sitelink))
        if sitelink != "[unknown]" and sitelink != {}:
            interlink = f"https://nonbinary.wiki/wiki/{sitelink}"
        else: # fallback: link to the nbdb item page
            interlink = f"https://data.nonbinary.wiki/wiki/Item:{id}"
        
        # Set embed
        embed = discord.Embed(title=f':link: {identity.title()}', description=desc, url="{0}".format(interlink))
        embed.set_image(url=show_flag)
        if meaning != None:
            embed.add_field(name="Flag meaning", value=f"{meaning}")
        embed.add_field(name="Alternative flags", value=f"{alt_flags}\nUse the same command with a number to see them: `/flag {identity.title()} 2`")
        embed.set_footer(text=footer)

        await ctx.respond(embed=embed)

    @slash_command(name="pronoun", description="Gives information about the specified pronoun set from the NBDb.")
    async def pronoun(self, ctx, pronouns: Option(str, "Pronoun you want to look up. It can be simple (they) or complex (they/them).")):
        await ctx.defer()
        utilities = self.bot.get_cog("UtilitiesCog")
        properties = ["P4", "P5", "P6", "P7", "P8", "P9", "P11"] # Properties for conjugation, pronoun forms and frequency

        index_file = os.path.join("NBDB_lists", "p-index.json")
        in_index = utilities.check_index(index_file, pronouns.lower())
        if in_index:
            print("Identity in local databases " + in_index)
            data = utilities.getlocaldata(in_index, properties)
            print(data)
        else:
            await ctx.respond(notfounderror)
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

        await ctx.respond(embed=embed)

    @slash_command(name="pronountest", description="Try on some new pronouns with your name!")
    async def pronountest(self, ctx, name: Option(str, "Enter your name"), pronouns: Option(str, "It can be simple (they) or complex (they/them). Use 'none' for no pronouns/name as pronouns."), story: Option(int, "Story you want to use", required=False)):
        await ctx.defer()
        utilities = self.bot.get_cog("UtilitiesCog")
        if pronouns.lower() == "none": #no pronouns/name as pronouns option.
            num = "singular"
            subj = name.capitalize()
            obj = name.capitalize()
            ref = name.capitalize() + "'s self"
            posad = name.capitalize() + "'s"
            pos = name.capitalize()
        else:
            pronouns = pronouns.replace(" ", "/")
            properties = ["P4", "P5", "P6", "P7", "P8", "P9", "P11"] # Properties for conjugation, pronoun forms and frequency

            index_file = os.path.join("NBDB_lists", "p-index.json")
            in_index = utilities.check_index(index_file, pronouns.lower())
            print(in_index)
            if in_index:
                print("Identity in local databases " + in_index)
                data = utilities.getlocaldata(in_index, properties)
                print(data)
            else:
                print("Can't find pronoun set. Trying multiple pronouns.")
                pronouns = pronouns.lower().split("/")
                if len(pronouns) == 6:
                    data = []
                    data.insert(0, "MANUAL")
                    data.insert(0, "MANUAL")
                    for p in pronouns:
                        data.append([p])
                elif len(pronouns) > 6:
                    await ctx.respond(":warning: To many pronouns! Pronoun sets need to have 6 forms or less.")
                    return
                else:
                    multiple_p = []
                    for p in pronouns:
                        index_file = os.path.join("NBDB_lists", "p-index.json")
                        in_index = utilities.check_index(index_file, p)
                        print(in_index)
                        if in_index:
                            if in_index in multiple_p:
                                print(f"{p} already checked.")
                                continue
                            else:
                                print(f"{p} added to list.")
                                multiple_p.append(in_index)
                    print(f"List of pronouns: {multiple_p}.")

                    data = utilities.set_multiple_pronouns(multiple_p)
                    if data == "notenough":
                        await ctx.respond(":bug: Something went wrong and I couldn't find all pronoun forms [Not enough pronouns]. You can specify all forms manually too: `/pronountest NAME they/him/its/zir/theirs/zirself`")
                        return

            print(f"List of pronoun forms: {data}")

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
        if subj == "they":
            num = "plural" # Exception for they/them, as it's usually conjugated in plural
        
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
            was_were = "was"
            is_are = "is"
            has_have = "has"
            s = "s"

        # Randomly choose and create a story
        with open('stories.txt') as stories:
            stories_ls = stories.read().replace("\n", "").split('|') # Due to multi-line stories, we need to use a custom separator.


        if story: #story is the optional field (int)
            if int(story) <= len(stories_ls):
                chosen_story = stories_ls[int(story)-1]
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

        final_story = []
        sentences = re.split('(?<=[.!?]) +', story)                 # split at each sentence, so it can be capitalized (in case of pronouns starting sentences)
        print(sentences)
        for i in sentences:
            if i.startswith("**"):
                new_sentence = i[:2] + i[2].upper() + i[3:]
                final_story.append(new_sentence)
            else:
                final_story.append(i)
        final_story = " ".join(final_story)
        
        btn = discord.ui.View()
        params = [name, pronouns]
        btn.add_item(self.Button(ctx, params))

        try:
            if data[0] == "MULTIPLE":
                manual_option = "\n_Want to fine-tune these results? Type the pronoun set in its full form: `they/him/its/zir/theirs/zirself`_"
                await ctx.respond(f"{final_story}{manual_option}", view=btn)
            else:
                await ctx.respond(f"{final_story}", view=btn)
        except:
            await ctx.respond("That term is not in the NBDb! Maybe try typing it differently?")

    class Button(discord.ui.Button):
        def __init__(self, ctx, params):
            super().__init__(label="Run this command again", style=discord.ButtonStyle.primary, emoji="♻️")
            self.ctx = ctx
            self.params = params
            
        async def callback(self, interaction):
            self.ctx.interaction = interaction
            if isinstance(self.params[1], list): #Multiple pronouns are a list instead of a string.
                pronouns = "/".join(self.params[1])
            else:
                pronouns = self.params[1]
            await NBDbCog.pronountest(self.ctx, self.params[0], pronouns, None)
            return

def setup(bot):
    bot.add_cog(NBDbCog(bot))
