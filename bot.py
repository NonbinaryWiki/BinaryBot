import discord
from discord.ext import commands
import urllib, json, requests, os, subprocess
import pytumblr
import logging
import mwparserfromhell
import csv
import random
import re

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

footer = "This data has been extracted from the NBDb (data.nonbinary.wiki), a project by the Nonbinary Wiki (nonbinary.wiki)." # Used as credit in embeds

### Commands:

bot = commands.Bot(command_prefix='!')
bot.remove_command('help')


def read_csv(csvfile):
    with open(csvfile) as csv_file:
        mylist = list(csv.reader(csv_file))
    return mylist

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

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command(
    help="Use this command to check if the bot is listening and can talk in the current channel.",
    description="Ping?",
)
async def ping(ctx):
    """ Pongs (and confirms that the bot is listening). """
    await ctx.send("Pong! :ping_pong: ({0}ms)".format(round(bot.latency * 1000)))


@bot.command(
    help="Thank you, random citizen!",
    description="Thank you, random citizen!")
async def thank(ctx):
    """ Send "Thank you random citizen" gif and a link to the patreon """
    await ctx.send("If you have the funds, help us keep the wiki alive!\n<https://www.patreon.com/nonbinarywiki>")
    await ctx.send(file=discord.File('random_citizen.gif'))


### WIKI-RELATED COMMANDS ###

@bot.command(
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


@bot.command(
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


@bot.command(
    help="Gets some information about the specified identity from the Nonbinary Wiki.",
    description="Enter a nonbinary identity to get a short description of the identity as well as some useful data, " \
                "such as its popularity in the Gender Census. You will also get a link to the wiki page about this identity.",
    usage="<identity>",
    brief="nonbinary"
)
async def identity(ctx, *, arg):
    """ Gives some information about the specified identity, including an excerpt, the flag and some data from the Gender Census. """
    # Example JSONFM response: https://data.nonbinary.wiki/w/api.php?action=wbgetentities&ids=Q20&format=jsonfm
    if arg == None:
        await ctx.send(":warning: You need to specify an identity! Example: `!identity nonbinary`.")
        return
    message = await ctx.send("Give me a moment. I will search the NBDb...")
    properties = ["P14", "P11", "P15", "P21", "P37"] # Properties for umbrella term, frequency, related identities, and main flag.
    try:
        data = getitemdata(arg, properties)    
    except:
        await ctx.send("That term is not in the NBDb! Maybe try typing it differently?")
    
    print(str(data))
    
    desc = data[1]
    main_id = data[0].split(':')[1] # data[0] is Item:Qid
    
    if data[2] != None:
        umbrella_id = data[2][0]['id'] #this is a Qid
        umbrella_json = getdataheader(umbrella_id)
        umbrella = stripstring(DictQuery(umbrella_json).get("search/label"))
    else:
        umbrella = "None"
    
    if data[3] != None:
        frequency = data[3][0]
    else:
        frequency = "No data"
    
    if data[4] != None:
        related_id = data[4][0]['id'] #this is a Qid
        related_json = getdataheader(related_id)
        related = stripstring(DictQuery(related_json).get("search/label"))
    else:
        related = "None"
    
    if data[5] != None:
        flag = data[5][0] # list, should have a single item but just in case
    else:
        flag = "https://static.miraheze.org/nonbinarywiki/3/32/Wikilogo_new.png"
        
    if data[6] != None:
        gallery = data[6][0]
    else:
        gallery = "None"
    
    interlink_json = getdatabody(main_id)
    sitelinks = DictQuery(interlink_json).get("entities/{0}/sitelinks".format(main_id))
    if "nonbinarywiki" in sitelinks:
        sitelink = DictQuery(interlink_json).get("entities/{0}/sitelinks/nonbinarywiki/title".format(main_id))
        interlink = "https://nonbinary.wiki/wiki/{0}".format(sitelink)
    else:
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

@bot.command(
    help="This message!",
    description="Sends a list of all available commands from the bot. " \
                "You can specify a command as a parameter to get more information on it, as well as an example.",
    usage="[command]",
    brief="ping"
    )
async def help(ctx, arg="list"):
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


@bot.command(
    help="Gives some useful information about the specified pronoun set.",
    description="Get some information about the given pronouns. Please, give the bot the first two pronouns of the set only",
    usage="<pronoun set>",
    brief="they/them"
)
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
    freq = ''.join(data[8]) if isinstance(data[8], list) else "[unknown]"
    num = '/'.join(data[2]) if isinstance(data[2], list) else "[unknown]" # a pronoun set can have multiple grammatical numbers
    subj = '/'.join(data[3]) if isinstance(data[3], list) else "[unknown]"
    obj = '/'.join(data[4]) if isinstance(data[4], list) else "[unknown]"
    posad = '/'.join(data[5]) if isinstance(data[5], list) else "[unknown]"
    pos= '/'.join(data[6]) if isinstance(data[6], list) else "[unknown]"
    ref = '/'.join(data[7]) if isinstance(data[7], list) else "[unknown]"
    
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


@bot.command(
    help="Tests the given data in a predefined sentence (this command is WIP).",
    description="Try on some new pronouns and see if they fit you!\n" \
                "Pronouns can be entered as both the subject form (i.e. 'they') or subject/object (i.e. 'they/them')\n" \
                "If you're entering more than one word, please enter them in quotes \"like this\".",
    usage="<name> <pronoun>",
    brief="John she/her"
)
async def pronountest(ctx, name = None, arg = None):
    if arg == None or name == None:
        await ctx.send(":warning: You need to specify a name and a pronoun! Example: `!pronountest John she/her`")
        return
    
    await ctx.send(":warning: This command is currently broken. Ondo is investigating the issue, but they are busy with real life. If you know Python, you're free to look at it in <https://github.com/NeoMahler/BinaryBot/blob/master/bot.py#L404>. Thanks for your patience!")

    message = await ctx.send("Give me a moment. I will search the NBDb...")
    properties = ["P4", "P5", "P6", "P7", "P8", "P9", "P11"] # Properties for conjugation, pronoun forms and frequency
    try:
        data = getitemdata(arg, properties)
    except:
        await ctx.send("That term is not in the NBDb! Maybe try typing it differently?")
        await discord.Message.delete(message)
    print(str(data))
    title = ''.join(data[0]) 
    desc = ''.join(data[1]) 
    num = '/'.join(data[2]) if isinstance(data[2], list) else "[unknown]" # a pronoun set can have multiple grammatical numbers
    subj = '/'.join(data[3]) if isinstance(data[3], list) else "[unknown]"
    obj = '/'.join(data[4]) if isinstance(data[4], list) else "[unknown]"
    posad = '/'.join(data[5]) if isinstance(data[5], list) else "[unknown]"
    pos= '/'.join(data[6]) if isinstance(data[6], list) else "[unknown]"
    ref = '/'.join(data[7]) if isinstance(data[7], list) else "[unknown]"

    if num.lower() == "singular": # this is a bit clunky, can it be improved?
        was_were = "was"
        is_are = "is"
    elif num.lower() == "plural":
        was_were = "were"
        is_are = "are"
    else:
        was_were = "was/were"
        is_are = "is/are"
    
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

@bot.command(
    help="Updates the bot to the latest version. Admin-only command",
    description="Pulls the latest version of the code from the GitHub repository. Only Ondo can use this command",
    usage="",
    brief=""
)
async def update(ctx):
    if ctx.message.author.id == 192011575777951744: #That's Ondo's Discord user ID
        output = subprocess.check_output("git pull", shell=True)
        await ctx.send("Pulling latest version from GitHub: ```" + str(output) + "```")
    else:
        await ctx.send("You don't have permission to use this command.")

bot.run(os.environ['TOKEN'])
