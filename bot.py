import discord
from discord.ext import commands
import urllib, json, requests, os
import pytumblr
import logging
import mwparserfromhell
import csv

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

### Commands:

bot = commands.Bot(command_prefix='!')
bot.remove_command('help')


def read_csv(csvfile):
    with open(csvfile) as csv_file:
        mylist = list(csv.reader(csv_file))
    return mylist


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def ping(ctx):
    """ Pongs (and confirms that the bot is listening). """
    await ctx.send("Pong! :ping_pong:")


### WIKI-RELATED COMMANDS ###

@bot.command()
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


@bot.command()
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
        await bot.say(
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


@bot.command()
async def identity(ctx, *, arg):
    """ Gives some information about the specified identity, including an excerpt, the flag and some data from the Gender Census. """
    article = arg
    extract_link = requests.get(
        url="https://nonbinary.wiki/w/api.php?action=query&prop=extracts&explaintext&exsentences=2&titles={0}&redirects&format=json".format(
            article))
    extract = next(iter(extract_link.json()['query']['pages'].values()))
    article = extract['title']  # handle redirects
    # Get infobox data
    raw_article = requests.get(url="https://nonbinary.wiki/wiki/{0}?action=raw".format(article))
    wikitext = mwparserfromhell.parse(raw_article.text)
    templates = wikitext.filter_templates()
    for template in templates:
        print(template)
        if template.name == "infobox identity\n":
            popularity = template.get(" percentage ").value.strip()
            gallery = template.get(" gallery_link ").value.strip()
            flag = template.get(" flag ").value.strip()
    print("THE FLAG NAME IS {0}".format(flag))
    flag_link = requests.get(
        url="https://nonbinary.wiki/w/api.php?action=query&titles=File:{0}&prop=imageinfo&iiprop=url&format=json".format(
            flag))
    flagdict = next(iter(flag_link.json()['query']['pages'].values()))
    print(str(flagdict))
    if flagdict == "-1":
        flag = 'File:Wikilogo_new.png'
    else:
        flag = flagdict['imageinfo'][0]['url']

    # Set embed
    embed = discord.Embed(title=':link: {0}'.format(article.title()), description=extract['extract'],
                          url="https://nonbinary.wiki/wiki/{0}".format(article))
    embed.set_thumbnail(url=flag)
    embed.add_field(name="Gender Census", value="{0}% of respondents".format(popularity))
    embed.add_field(name="Pride Gallery",
                    value="[Click here!](https://nonbinary.wiki/wiki/{0})".format(gallery.replace(" ", "_")))
    embed.set_footer(text="This command is still work in progress; bugs are expected! Ping @Ondo if you see an error.")
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx, command="list"):
    if str.lower(command) == "pronoun":
        embed = discord.Embed(title=':grey_question: !pronoun <pronoun set>', color=discord.Colour.purple(),
                              description="Type !pronoun followed by a pronoun set to get some information about the given pronouns. \
                        Please, give the bot the first two pronouns of the set only")
        embed.add_field(name="Example", value="!pronoun they/them")
        await ctx.send(embed=embed)
    elif str.lower(command) == "pronountest":
        embed = discord.Embed(
            title=':grey_question: !pronountest <name> <pronoun>',
            color=discord.Colour.purple(),
            description="!pronountest, followed by the following arguments (if you're entering \
                              more than one word, please enter them in quotes \"like this.\"")
        embed.add_field(name="Name", value="Your name.", inline=True)
        embed.add_field(name="Pronoun",
                        value="Can be both the subject form (i.e. 'they') or subject+object (i.e. 'they/them')", inline=True)
        await ctx.send(embed=embed)
    elif str.lower(command) == "pinfo":
        embed = discord.Embed(title=':grey_question: !pinfo <page>', color=discord.Colour.purple(),
                              description="Type !pinfo followed by the name of an existing Nonbinary Wiki page to get some useful \
                             technical information about the page, such as the amount of contributors, protection status and categorization.")
        embed.add_field(name="Example", value="!pinfo nonbinary")
        await ctx.send(embed=embed)
    elif str.lower(command) == "flag":
        embed = discord.Embed(title=':grey_question: !flag <identity>', color=discord.Colour.purple(),
                              description="Type !flag followed by a nonbinary identity to get its most common pride flag and a short \
                             description of the identity. You will also get a link to the pride gallery for that identity, so that you \
                             can see alternative flags for your identity.")
        embed.add_field(name="Example", value="!flag nonbinary")
        await ctx.send(embed=embed)
    elif str.lower(command) == "identity":
        embed = discord.Embed(title=':grey_question: !identity <identity>', color=discord.Colour.purple(),
                              description="Type !identity followed by a nonbinary identity to get a short description of the identity \
                             as well as some useful data, such as its popularity in the Gender Census. You will also get a link to the \
                             wiki page about this identity.")
        embed.add_field(name="Example", value="!identity nonbinary")
        await ctx.send(embed=embed)
    elif str.lower(command) == "ping":
        embed = discord.Embed(title=':grey_question: !ping', color=discord.Colour.purple(),
                              description="Ping?")
        embed.add_field(name="Example", value="!ping")
        embed.set_footer(text="(pong.)")
        await ctx.send(embed=embed)
    elif str.lower(command) == "help":
        embed = discord.Embed(title=':grey_question: !help [command]', color=discord.Colour.purple(),
                              description="Sends a list of all available commands from the bot. You can specify a command as a parameter \
                             to get more information on it, as well as an example.")
        embed.add_field(name="Example", value="!help ping")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title=':grey_question: List of commands', color=discord.Colour.purple())
        embed.add_field(name="!flag <identity>",
                        value="Returns the most common pride flag for the identity and a short description.")
        embed.add_field(name="!help [command]", value="This message!")
        embed.add_field(name="!identity <identity>",
                        value="Gets some information about the specified identity from the Nonbinary Wiki.")
        embed.add_field(name="!pinfo <page>",
                        value="Returns useful technical information about the specified wiki page.")
        embed.add_field(name="!ping",
                        value="Use this command to check if the bot is listening and can talk in the curent channel.")
        embed.add_field(name="!pronoun <pronoun set>",
                        value="Gives some useful information about the specified pronoun set.")
        embed.add_field(name="!pronountest <name> <gender> <kin> <singular/plural> <pronouns>",
                        value="Tests the given data in a predefined sentence (this command is WIP).")
        embed.set_footer(text="Use !help [command] to get more information on a specific command.")
        await ctx.send(embed=embed)

def getdataheader(arg):
    article = arg
    extract_link = requests.get(
        url="https://data.nonbinary.wiki/w/api.php?action=wbsearchentities&search={0}&language=en&format=json".format(
            article))
    jsonresponse = extract_link.json()
    return jsonresponse

def getdatabody(arg):
    article = arg
    extract_link = requests.get(
        url="https://data.nonbinary.wiki/w/api.php?action=wbgetentities&ids={0}&format=json".format(article))
    jsonresponse = extract_link.json()
    return jsonresponse

def stripstring(arg):
    #arg = str(arg).strip("['")
    #arg = str(arg).strip(",']")

    #return arg
    if arg != None:
       return arg[0]
    else:
        return None

def getitemdata(arg, p=[]):
    # gets all the requested values (p) for a given item (arg) and puts them in plist in the requested order, with title and description first
    plist = []
    # Gets the header information.
    myjson = getdataheader(arg)
    # Uses a class for easier nested searching.
    # Stripstring gets rid of excess chars.
    json_id = stripstring(DictQuery(myjson).get("search/id"))
    json_title = stripstring(DictQuery(myjson).get("search/title"))
    json_desc = stripstring(DictQuery(myjson).get("search/description"))
    plist.append(json_title)
    plist.append(json_desc)
    
    # Gets the actual information for that item
    jsonbody = getdatabody(json_id)
    for i in p:
        try:
            plist.append(DictQuery(jsonbody).get("entities/{0}/claims/{1}/mainsnak/datavalue/value".format(json_id, i)))
        except:
            plist.append("[unknown]")
    
    return plist

@bot.command()
async def pronoun(ctx, arg = None):
    if arg == None:
        await ctx.send(":warning: You need to specify a pronoun! Example: `!pronoun they/them`.")
        return
    message = await ctx.send("Give me a moment. I will search the NBDb...")
    properties = ["P4", "P5", "P6", "P7", "P8", "P9", "P11"] # Properties for conjugation, pronoun forms and frequency
    try:
        data = getitemdata(arg, properties)    
    except:
        await ctx.send("That term is not in the NBDb! Maybe try typing it differently?")

    title = ''.join(data[0])
    desc = ''.join(data[1])
    freq = ''.join(data[8])
    num = ' or '.join(data[2]) # a pronoun set can have multiple grammatical numbers
    subj = ' or ',join(data[3])
    obj = ' or ',join(data[4])
    posad = ' or ',join(data[5])
    pos= ' or ',join(data[6])
    ref = ' or ',join(data[7])
    
    embed = discord.Embed(title="Information about the " + subj + "/" + obj + " pronoun.", description=desc)
    embed.add_field(name="Conjugation", value=num, inline=True)
    embed.add_field(name="Subjective", value="**{}** ate the cake.".format(subj.capitalize()), inline=True)
    embed.add_field(name="Objective", value="I like **{}**.".format(obj), inline=True)
    embed.add_field(name="Possessive Determiner", value="**{}** smile is pretty.".format(posad.capitalize()), inline=True)
    embed.add_field(name="Possessive Pronoun", value="The book is **{}**.".format(pos), inline=True)
    embed.add_field(name="Reflexive", value="{} did by **{}**.".format(subj.capitalize(), ref), inline=True)
    embed.add_field(name="Frequency", value=freq, inline=True)
    embed.set_footer(text="Remember! If you are not sure, just ask!")

    await discord.Message.delete(message)
    await ctx.send(embed=embed)


@bot.command()
async def pronountest(ctx, name, arg = None):
    if arg == None:
        await ctx.send(":warning: You need to specify a name and a pronoun! Example: `!pronountest John she/her`")
        return
    message = await ctx.send("Give me a moment. I will search the NBDb...")
    properties = ["P4", "P5", "P6", "P7", "P8", "P9", "P11"] # Properties for conjugation, pronoun forms and frequency
    try:
        data = getitemdata(arg)
    # Cheatsheet:
    # title: 0
    # desc: 1
    # Grammatical number: 2
    # Subject: 3
    # Object: 4
    # Possessive adjective: 5
    # Possessive: 6
    # Reflexive: 7
    # Frequency: 8
    except:
        await ctx.send("That term is not in the NBDb! Maybe try typing it differently?")
        await discord.Message.delete(message)
    try:
        con1 = data[2][0]
        con2 = data[2][1]
    except:
        con1 = data[2][0]
        con2 = "Null"

    mystory1 = ""
    mystory2 = ""

    await discord.Message.delete(message)
    if(con1 == "Plural" or con2 == "Plural"):
        mystory2 = "Plural Conjugation: It wasn't too long ago when {0} found {5} in a sticky situation. Quite literally, actually. ".format( 
            name, data[3], data[4], data[5], data[6], data[7]) + data[3].capitalize() + " were trying to open a bottle of honey, when all of a sudden, {1} lost {3} grip on the bottle and the honey squirted all over those wonderful clothes of {4} and the rest of {5}!".format(name,data[3],data[4],data[5],data[6],data[7])
    if(con1 == "Singular" or con2 == "Singular"):
        mystory1 = "Singular Conjugation: It wasn't too long ago when {0} found {5} in a sticky situation. Quite literally, actually. ".format(
            name, data[3], data[4], data[5], data[6], data[7]) + data[3].capitalize() + " was trying to open a bottle of honey, when all of a sudden, {1} lost {3} grip on the bottle and the honey squirted all over those wonderful clothes of {4} and the rest of {5}!".format(
            name, data[3], data[4], data[5], data[6], data[7])
        
    if(con == "[unknown]"):
        mystory2 = "Plural Conjugation: It wasn't too long ago when {0} found {5} in a sticky situation. Quite literally, actually. ".format(
            name, data[3], data[4], data[5], data[6], data[7]) + data[3].capitalize() + " were trying to open a bottle of honey, when all of a sudden, {1} lost {3} grip on the bottle and the honey squirted all over those wonderful clothes of {4} and the rest of {5}!".format(
            name, data[3], data[4], data[5], data[6], data[7])
        mystory1 = "Singular Conjugation: It wasn't too long ago when {0} found {5} in a sticky situation. Quite literally, actually. ".format(
            name, data[3], data[4], data[5], data[6], data[7]) + data[3].capitalize() + " was trying to open a bottle of honey, when all of a sudden, {1} lost {3} grip on the bottle and the honey squirted all over those wonderful clothes of {4} and the rest of {5}!".format(
            name, data[3], data[4], data[5], data[6], data[7])
    try:
        await ctx.send(mystory1 + "\n\n" + mystory2)
    except:
        await ctx.send("That term is not in the NBDb! Maybe try typing it differently?")

class DictQuery(dict):
    def get(self, path, default = None):
        keys = path.split("/")
        val = None

        for key in keys:
            if val:
                if isinstance(val, list):
                    val = [ v.get(key, default) if v else None for v in val]
                else:
                    val = val.get(key, default)
            else:
                val = dict.get(self, key, default)

            if not val:
                break;

        return val

bot.run(os.environ['TOKEN'])
