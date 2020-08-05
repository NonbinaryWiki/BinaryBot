import discord
from discord.ext import commands 
import requests
import mwparserfromhell


class NBWCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help="Returns the most common pride flag for the identity and a short description.",
        description="Enter a nonbinary identity to get its most common pride flag and a short description of the identity.\n" \
                    "You will also get a link to the pride gallery for that identity, so that you can see alternative flags for your identity.",
        usage="<identity>",
        brief="nonbinary"
    )
    async def flag(ctx, *, arg):
        """ Returns a link to the Pride Gallery of the specified identity. """
        images = {
            'agender': 'https://static.miraheze.org/nonbinarywiki/thumb/8/83/Agender.png/300px-Agender.png',
            'androgyne': 'https://static.miraheze.org/nonbinarywiki/thumb/7/73/Androgyne.png/300px-Androgyne.png',
            'aporagender': 'https://static.miraheze.org/nonbinarywiki/4/48/Aporagender.png',
            'bigender': 'https://static.miraheze.org/nonbinarywiki/thumb/f/f2/Bigender.png/300px-Bigender.png',
            'demigender': 'https://static.miraheze.org/nonbinarywiki/thumb/e/ee/Deminonbinary.png/300px-Deminonbinary.png',
            'demiboy': 'https://static.miraheze.org/nonbinarywiki/thumb/5/5c/Demiboy.png/300px-Demiboy.png',
            'demigirl': 'https://static.miraheze.org/nonbinarywiki/thumb/8/80/Demigirl.png/300px-Demigirl.png',
            'deminonbinary': 'https://static.miraheze.org/nonbinarywiki/thumb/e/ee/Deminonbinary.png/300px-Deminonbinary.png',
            'demifluid': 'https://static.miraheze.org/nonbinarywiki/thumb/1/1f/Demifluid.png/300px-Demifluid.png',
            'demiflux': 'https://static.miraheze.org/nonbinarywiki/thumb/f/f3/Demiflux.png/300px-Demiflux.png',
            'genderfluid': 'https://static.miraheze.org/nonbinarywiki/thumb/1/12/Genderfluid.png/300px-Genderfluid.png',
            'genderflux': 'https://static.miraheze.org/nonbinarywiki/thumb/a/ae/Genderflux.png/300px-Genderflux.png',
            'fluidflux': 'https://static.miraheze.org/nonbinarywiki/thumb/5/51/Fluidflux.png/300px-Fluidflux.png',
            'genderqueer': 'https://static.miraheze.org/nonbinarywiki/thumb/b/b5/Genderqueer.png/300px-Genderqueer.png',
            'intergender': 'https://static.miraheze.org/nonbinarywiki/thumb/d/d3/Intergender.png/300px-Intergender.png',
            'maverique': 'https://static.miraheze.org/nonbinarywiki/thumb/e/e2/Maverique.png/300px-Maverique.png',
            'neutrois': 'https://static.miraheze.org/nonbinarywiki/thumb/c/c1/Neutrois.png/300px-Neutrois.png',
            'nonbinary': 'https://static.miraheze.org/nonbinarywiki/thumb/c/c0/Nonbinary.png/300px-Nonbinary.png',
            'non-binary': 'https://static.miraheze.org/nonbinarywiki/thumb/c/c0/Nonbinary.png/300px-Nonbinary.png',
            'pangender': 'https://static.miraheze.org/nonbinarywiki/thumb/b/bd/Pangender.png/300px-Pangender.png',
            'polygender': 'https://static.miraheze.org/nonbinarywiki/thumb/8/87/Polygender.png/300px-Polygender.png',
            'trigender': 'https://static.miraheze.org/nonbinarywiki/thumb/4/40/Trigender.png/300px-Trigender.png'
        }
        identity = arg
        extract_link = requests.get(
            url="https://nonbinary.wiki/w/api.php?action=query&prop=extracts&explaintext&exsentences=1&titles={0}&redirects&format=json".format(
                identity))
        extract = next(iter(extract_link.json()['query']['pages'].values()))
        if identity in images:
            prideflag = images[identity.lower()]
        else:
            # TODO: This should be improved (automatic image)
            prideflag = 'https://static.miraheze.org/nonbinarywiki/3/32/Wikilogo_new.png'
        if not identity:
            await ctx.send(
                'Take a look at our Pride Gallery! https://nonbinary.wiki/wiki/Pride_Gallery - You can also specify an identity after the command.')
        else:
            # Special cases
            if 'demi' in identity:
                link = "https://nonbinary.wiki/wiki/Pride_Gallery/Demigender"
            elif 'fluid' in identity or 'flux' in identity:
                link = "https://nonbinary.wiki/wiki/Pride_Gallery/Genderfluid,_genderflux_and_fluidflux"
            else:
                link = "https://nonbinary.wiki/wiki/Pride_Gallery/" + identity.capitalize()
        raw_article = requests.get(url=link + "?action=raw")
        wikitext = mwparserfromhell.parse(raw_article.text)
        print(wikitext)
        templates = wikitext.filter_templates()
        print(templates)
        for template in templates:
            print("TEMPLATEEEEEEEEE IT'S THIS ONE " + str(template.name))
            if template.name == "gallery page\n":
                hexcolor = template.get(" colour ").value.strip()
                embedcolor = discord.Color(int(hexcolor.replace('#', '0x'), 0))
                print(str(embedcolor))
        # Set embed
        embed = discord.Embed(title=':link: {0} Pride Gallery'.format(identity.title()), description=extract['extract'],
                            url=link, color=embedcolor)
        embed.set_thumbnail(url=prideflag)
        embed.set_footer(text="Use !identity for more information about this identity.")

        await ctx.send(embed=embed)

    @commands.command(
    help="Returns useful technical information about the specified wiki page.",
    description="Enter the name of an existing Nonbinary Wiki page to get some useful technical information about the page, " \
                "such as the amount of contributors, protection status and categorization.",
    usage="<page>",
    brief="nonbinary"
    )
    async def pinfo(ctx, *, arg):
        """ Gives some useful information about a wiki page: number of contributors, categories, protection level and useful links. """
        page = arg
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

            await ctx.send(embed=embed)
        except:  # In case there's an unwanted error, send this message:
            await ctx.send(":bug: There was an error. " + \
                        "Maybe the specified page doesn't exist. Check your spelling!")
            raise

def setup(bot):
    bot.add_cog(NBWCog(bot))