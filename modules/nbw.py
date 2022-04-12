import discord
from discord.ext import commands
from discord.commands import slash_command, Option
import requests
import mwparserfromhell


class NBWCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="pinfo", description="Gives some technical information about a wiki page.")
    async def pinfo(self, ctx, page: Option(str, "Full title of the page.")):
        """ Gives some useful information about a wiki page: number of contributors, categories, protection level and useful links. """
        await ctx.defer()
        try:
            # Use the MediaWiki API to get the information in json format:
            protection_link = requests.get(
                url="https://nonbinary.wiki/w/api.php?action=query&titles={0}&prop=info&inprop=protection&format=json".format(
                    page))
            protection_info = next(iter(protection_link.json()['query']['pages'].values()))

            contribs_link = requests.get(
                url="https://nonbinary.wiki/w/api.php?action=query&titles={0}&prop=contributors&format=json".format(page))
            contribs_info = next(iter(contribs_link.json()['query']['pages'].values()))
            if not 'anoncontributors' in contribs_info:
                anon_contribs = 0
            else:
                anon_contribs = contribs_info['anoncontributors']
            user_contribs = len(contribs_info['contributors'])

            cats_link = requests.get(
                url="https://nonbinary.wiki/w/api.php?action=query&titles={0}&prop=categories&format=json".format(page))
            cats_info = next(iter(cats_link.json()['query']['pages'].values()))
            if 'categories' in cats_info:
                raw_cats = cats_info['categories']
                cats = []
                for cat in raw_cats:
                    cats.append(cat['title'])  # Make a list of categories
            else:  # For pages without categories
                cats = ["Uncategorized page"]

            # Get protection information:
            if protection_info['protection'] == []:
                protected = False  # If page is not protected, the value is an empty list
                protect_value = ":unlock: Not protected"
            else:
                edit_protected = protection_info['protection'][0]['level'] + \
                                ' (' + protection_info['protection'][0]['expiry'] + ')'
                move_protected = protection_info['protection'][1]['level'] + \
                                ' (' + protection_info['protection'][1]['expiry'] + ')'
                protect_value = ":lock: Edit: {0}; Move: {1}".format(edit_protected, move_protected)

            # Let's create the embed with the information:
            embed = discord.Embed(title=':page_facing_up: {0}'.format(page),
                                description=":link: [Article](https://nonbinary.wiki/wiki/{0}) - [Talk page](https://nonbinary.wiki/wiki/Talk:{0}) - [History](https://nonbinary.wiki/w/index.php?title={0}&action=history)".format(
                                    page.replace(' ', '_')),
                                color=discord.Colour.purple())
            embed.add_field(name=":busts_in_silhouette: Contributors",
                            value="Anonymous: {0}; Registered: {1}.".format(anon_contribs, user_contribs))
            embed.add_field(name=":key: Protection", value=protect_value)
            embed.add_field(name=":chains: Categories", value="{0}".format(', '.join(cats)), inline=False)

            await ctx.respond(embed=embed)
        except:  # In case there's an unwanted error, send this message:
            await ctx.respond(":bug: There was an error. " + \
                        "Maybe the specified page doesn't exist. Check your spelling!")
            raise

def setup(bot):
    bot.add_cog(NBWCog(bot))
