from typing import final
import discord
from discord.ext import commands
import csv
import requests
import json
import os
import random

class UtilitiesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_index(self, file, identity):
        """Checks if the provided identity is in the provided file"""
        all_matches = [] # Support for multiple pronouns
        checked_forms = []

        with open(file, "r") as f:
            id_list = json.load(f)

            for id in id_list:
                aliases = id_list[id]
                #print(str(aliases))
                for form in identity.split("/"):
                    if form in [alias.lower() for alias in aliases] and not form in checked_forms:
                        if not form in all_matches:
                            checked_forms.append(form)
                            all_matches.append(id)
        
        if len(all_matches) == 1:
            return all_matches[0]
        else:
            return all_matches
    
    def stripstring(self, arg):
        #arg = str(arg).strip("['")
        #arg = str(arg).strip(",']")

        #return arg
        print(str(arg))
        if arg != None:
            return arg[0]
        else:
            return None

def setup(bot):
    bot.add_cog(UtilitiesCog(bot))
