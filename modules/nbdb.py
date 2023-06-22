import discord
from discord.ext import commands
from discord.commands import slash_command, Option
import urllib, json, requests
import random
import re
import traceback
import os

footer = "This data is user-contributed. Run /feedback to suggest a new identity, flag, or pronoun set to be added!"
notfounderror = ":warning: I couldn't find this in my database—check for typos or try again later (I might not be synced the latest version)."

class NBDbCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="identity", description="Gives some information about the specified gender identity.")
    async def identity(self, ctx, identity: Option(str, "Name of the gender identity")):
        utilities = self.bot.get_cog("UtilitiesCog")

        index_file = os.path.join("data", "id-index.json")
        in_index = utilities.check_index(index_file, identity.lower())
        if not in_index:
            await ctx.respond(notfounderror)
            return
        
        main_id = in_index

        file = os.path.join("data", f'{main_id}.json')
        with open(file, "r") as f:
            data = json.load(f)
        name = data["name"]
        desc = data["description"]
        umbrella_data = data["umbrella term"]
        frequency_data = data["census percentage"]
        related_data = data["related identities"]
        flag_data = data["flag"]
        sitelink = data["wiki link"]

        # Default responses
        umbrella = related = "None"
        frequency = "No data"
        flag = "https://static.miraheze.org/nonbinarywiki/3/32/Wikilogo_new.png"

        if umbrella_data != [None]:
            umbrella = ", ".join(umbrella_data)

        if frequency_data != 0.0:
            frequency = str(frequency_data) + "%"

        if related_data != [None]:
            related = ", ".join(related_data)

        if flag_data != None:
            flag = flag_data[0]

        # Get interwiki for the nonbinary wiki
        if sitelink != None:
            interlink = sitelink[0]
        else: # fallback: link to the list of identities
            interlink = "https://nonbinary.wiki/wiki/List_of_nonbinary_identities"

        # Set embed
        embed = discord.Embed(title=':link: {0}'.format(name.title()), description=desc, url="{0}".format(interlink))
        embed.set_thumbnail(url=flag)
        if umbrella != "None":
            embed.add_field(name="Umbrella term", value="{0}".format(umbrella))
        if related != "None":
            embed.add_field(name="Related identities", value="{0}".format(related))
        embed.add_field(name="Gender Census", value="{0} of respondents".format(frequency))
        embed.add_field(name="Flag information", value=f"Use `/flag {name.title()}` to get more information about this flag.")
        embed.set_footer(text=footer)

        await ctx.respond(embed=embed)

    @slash_command(name="flag", description="Gives some information about the specified gender identity flag.")
    async def flag(self, ctx, identity: Option(str, "Name of the gender identity"), number: Option(int, "Number of the flag (to get a specific flag)", required=False)):
        utilities = self.bot.get_cog("UtilitiesCog")

        index_file = os.path.join("data", "id-index.json")
        in_index = utilities.check_index(index_file, identity.lower())
        if not in_index:
            await ctx.respond(notfounderror)
            return
        
        main_id = in_index

        file = os.path.join("data", f'{main_id}.json')
        with open(file, "r") as f:
            data = json.load(f)
        
        # Process data
        desc = data["description"]
        sitelink = data["wiki link"]

        if data["flag"] != None:
            main_flag = data["flag"][0]
        else:
            await ctx.respond("I found the identity, but it doesn't seem to have any associated pride flag in my database. Use `/identity {0}` to get more information about this identity.".format(identity))
            return False

        if data["alternative flags"] != None: # Look for alternative flags (data[3] is the P22 claim)
            alt_flags = str(len(data["alternative flags"]))
            flags_list = data["alternative flags"]
        else:
            alt_flags = "None"

        if number != None: # If there is a flag number specified, make sure that it actually exists
            flag_num = int(number)-1 # make it human and start counting from 1, not 0
            if int(number) > int(alt_flags):
                await ctx.respond(f"I found the identity, but it only has {alt_flags} alternative flags! Use a lower number.")
                return
            else:
                show_flag = flags_list[flag_num]
        else:
            show_flag = main_flag # use the default flag if no alternative flag is specified

        if show_flag.endswith('.svg'): # Apparently embeds don't like svg files
            await ctx.respond(f"I found this flag, but I can't display it due to technical limitations. You can view it in this URL: {show_flag}")
            return
        
        # Pick a page to link in the embed title (preferably the wiki article)
        if sitelink != None:
            interlink = sitelink[0]
        else: # fallback: link to the Pride Gallery
            interlink = f"https://nonbinary.wiki/wiki/Pride_Gallery"
        
        # Set embed
        embed = discord.Embed(title=f':link: {identity.title()}', description=desc, url="{0}".format(interlink))
        embed.set_image(url=show_flag)
        embed.add_field(name="Alternative flags", value=f"{alt_flags}\nUse the same command with a number to see them: `/flag {identity.title()} 2`")
        embed.set_footer(text=footer)

        await ctx.respond(embed=embed)
        
    @slash_command(name="pronoun", description="Gives information about the specified pronoun set.")
    async def pronoun(self, ctx, pronouns: Option(str, "Pronoun you want to look up. It can be simple (they) or complex (they/them).")):
        utilities = self.bot.get_cog("UtilitiesCog")

        index_file = os.path.join("data", "p-index.json")
        in_index = utilities.check_index(index_file, pronouns.lower())
        if not in_index:
            await ctx.respond(notfounderror)
            return

        main_id = in_index

        file = os.path.join("data", f'{main_id}.json')
        with open(file, "r") as f:
            data = json.load(f)
        # Process data
        desc = data["description"]
        freq = str(data["census percentage"]) + "%"
        num = '/'.join(data["number"]) if isinstance(data["number"], list) else "[unknown]" # a pronoun set can have multiple grammatical numbers
        subj = '/'.join(data["subject"]) if isinstance(data["subject"], list) else "[unknown]"
        obj = '/'.join(data["object"]) if isinstance(data["object"], list) else "[unknown]"
        posad = '/'.join(data["possessive adjective"]) if isinstance(data["possessive adjective"], list) else "[unknown]"
        pos= '/'.join(data["possessive"]) if isinstance(data["possessive"], list) else "[unknown]"
        ref = '/'.join(data["reflexive"]) if isinstance(data["reflexive"], list) else "[unknown]"

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
        utilities = self.bot.get_cog("UtilitiesCog")

        # Set up verb forms
        was_were = "was"
        is_are = "is"
        has_have = "has"
        s = "s"

        full_p_set = {
            "number": [],
            "subject": [],
            "object": [],
            "possessive adjective": [],
            "possessive": [],
            "reflexive": []
        }

        multiple = False
        if pronouns.lower() == "none": # No pronouns/name as pronouns option.
            data = [["singular"], [name.capitalize()], [name.capitalize()], [name.capitalize() + "'s"], [name.capitalize()], [name.capitalize() + "'s self"]]
        else: # Actual pronouns
            if "(" in pronouns or ")" in pronouns:
                await ctx.respond(":warning: Don't use parenthesis in your pronouns. Use slashes (/) to separate pronoun forms or multiple pronouns: `they/them`, `they/xe`.")
                return
            pronouns = pronouns.replace(" ", "/") # Backup in case user uses space as separator

            index_file = os.path.join("data", "p-index.json")
            pronoun_ids = utilities.check_index(index_file, pronouns.lower())
            print(pronoun_ids)
            if isinstance(pronoun_ids, list): # This means there are multiple pronouns
                multiple = True
                print("Can't find pronoun set. Trying multiple pronouns.")
                input_pronouns = pronouns.lower().split("/") # User-inputted pronouns
                if len(input_pronouns) == 5: # Manual full pronoun set
                    data = []
                    data.insert(0, "singular") # Manual pronouns are always treated as singular
                    for p in pronouns.split("/"):
                        data.append([p])
                elif len(input_pronouns) > 5:
                    await ctx.respond(":warning: To many pronouns! Pronoun sets need to have 5 forms or less.")
                    return
                else: # Automated multiple pronoun sets
                    if pronoun_ids == []:
                        await ctx.respond(notfounderror)
                        return
                    print(f"List of pronouns: {pronoun_ids}.")

                    all_forms = { # For random selection purposes
                        "subject": "",
                        "object": "",
                        "possessive adjective": "",
                        "possessive": "",
                        "reflexive": ""
                        }
                    
                    data = ["singular"]

                    for i in all_forms: # Assign a pronoun set ID to each form
                        choice = random.choice(pronoun_ids)
                        print(f"{i}: {choice}")
                        all_forms[i] = choice

                    for form in all_forms:
                        file = os.path.join("data", f'{all_forms[form]}.json')     
                        print(file)  
                        try:             
                            with open(file, "r") as f:
                                raw_data = json.load(f)
                                full_p_set[form] = raw_data[form]
                                data.append(raw_data[form])
                        except FileNotFoundError:
                            await ctx.respond(notfounderror)
                            return

            else: # Single-pronoun set

                file = os.path.join("data", f'{pronoun_ids}.json')    
                with open(file, "r") as f:
                    raw_data = json.load(f)
                    data = [raw_data["number"], raw_data["subject"], raw_data["object"], raw_data["possessive adjective"], raw_data["possessive"], raw_data["reflexive"]]

        # Set up final pronoun form
        full_p_set["number"] = '/'.join(data[0]) if isinstance(data[0], list) else "[unknown]" # a pronoun set can have multiple grammatical numbers
        full_p_set["subject"] = '/'.join(data[1]) if isinstance(data[1], list) else "[unknown]"
        full_p_set["object"] = '/'.join(data[2]) if isinstance(data[2], list) else "[unknown]"
        full_p_set["possessive adjective"] = '/'.join(data[3]) if isinstance(data[4], list) else "[unknown]"
        full_p_set["possessive"] = '/'.join(data[4]) if isinstance(data[4], list) else "[unknown]"
        full_p_set["reflexive"] = '/'.join(data[5]) if isinstance(data[5], list) else "[unknown]"

        if full_p_set["number"].lower() == "plural" or full_p_set["subject"] == "they":
            was_were = "were"
            is_are = "are"
            has_have = "have"
            s = ""
        
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
                subj = full_p_set["subject"],
                obj = full_p_set["object"],
                posad = full_p_set["possessive adjective"],
                pos = full_p_set["possessive"],
                pospro = full_p_set["possessive"],
                ref = full_p_set["reflexive"],
                was_were = was_were,
                is_are = is_are,
                has_have = has_have,
                s = s)

        final_story = []
        sentences = re.split('(?<=[.!?]) +', story) # split at each sentence, so it can be capitalized (in case of pronouns starting sentences)
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
            if multiple == True:
                manual_option = "\n_Want to fine-tune these results? Type the pronoun set in its full form: `they/him/its/zir/zirself`_"
                await ctx.respond(f"{final_story}{manual_option}", view=btn)
            else:
                await ctx.respond(f"{final_story}", view=btn)
        except:
            await ctx.respond("That term is not in my database! Maybe try typing it differently?")

    @slash_command(name="random", description="Gives some information about the specified gender identity.")
    async def random(self, ctx, type: Option(str, "'pronoun' or 'identity'")):
        if type.startswith("p"):
            index_file = os.path.join("data", "p-index.json")
        elif type.startswith("i") or type.startswith("f"):
            index_file = os.path.join("data", "id-index.json")
        else:
            await ctx.respond("Please tell me if you want a random pronoun or identity! For example: `/random identity`")
            return

        utilities = self.bot.get_cog("UtilitiesCog")
     
        with open(index_file, "r") as f:
            data = json.load(f)
        choice_id = random.choice(list(data.keys()))
        filename = index_file = os.path.join("data", choice_id + ".json")
        with open(filename, "r") as f:
            data = json.load(f)
        
        if type.startswith("i"):
            await self.identity(ctx, data["name"])
        else: #type.startswith("p")
            await self.pronoun(ctx, data["subject"][0])

        return
 

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
