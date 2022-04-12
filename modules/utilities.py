from discord.ext import commands
import csv
import requests
import json
import os

class UtilitiesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def read_csv(self, csvfile):
        with open(csvfile) as csv_file:
            mylist = list(csv.reader(csv_file))
        return mylist

    def check_index(self, file, identity):
        """Checks if the provided identity is in the provided file"""
        with open(file, "r") as f:
            data = json.load(f)
            for id in data:
                aliases = data[id]
                print(str(aliases))
                if identity in [alias.lower() for alias in aliases]:
                    return id
        return False

    def getlocaldata(self, arg, p=[]):
        plist = []
        file = os.path.join("NBDB_lists", f'{arg}.json')
        with open(file, "r") as f:
            data = json.load(f)
            json_id = self.DictQuery(data).get("id")
            #json_title = self.DictQuery(data).get("title") #That's the full title ("Item:Q1")
            json_desc = self.DictQuery(data).get("descriptions/en/value")
            plist.append(json_id)
            plist.append(json_desc)
            for i in p:
                try:
                    plist.append(self.DictQuery(data).get(f"claims/{i}/mainsnak/datavalue/value"))
                except:
                    plist.append("[unknown]")
            try:
                plist.append(self.DictQuery(data).get(f"sitelinks/nonbinarywiki/title"))
            except:
                plist.append("[unknown]")

        return plist
    
    def getqualifierdata(self, arg, property, qualifier):
        file = os.path.join("NBDB_lists", f'{arg}.json')
        with open(file, "r") as f:
            data = json.load(f)
            try:
                result = self.DictQuery(data).get(f"claims/{property}/qualifiers/{qualifier}")
                return result
            except:
                return None
                
    def getdataheader(self, arg):
        article = arg
        extract_link = requests.get(
            url="https://data.nonbinary.wiki/w/api.php?action=wbsearchentities&search={0}&language=en&format=json".format(
                article))
        jsonresponse = extract_link.json()
        if jsonresponse['search'] == []:
            extract_link = requests.get(
            url="https://data.nonbinary.wiki/w/api.php?action=wbsearchentities&search={0}&language=en&format=json".format(
                article.capitalize())) #Capitalization is not consistent in the NBDb
            jsonresponse = extract_link.json()
        return jsonresponse

    def getdatabody(self, arg):
        article = arg
        extract_link = requests.get(
            url="https://data.nonbinary.wiki/w/api.php?action=wbgetentities&ids={0}&format=json".format(article))
        jsonresponse = extract_link.json()
        return jsonresponse

    def stripstring(self, arg):
        #arg = str(arg).strip("['")
        #arg = str(arg).strip(",']")

        #return arg
        print(str(arg))
        if arg != None:
            return arg[0]
        else:
            return None

    def getitemdata(self, arg, p=[]):
        # gets all the requested values (p) for a given item (arg) and puts them in plist in the requested order, with title and description first
        plist = []
        # Gets the header information.
        myjson = self.getdataheader(arg)
        # Uses a class for easier nested searching.
        # Stripstring gets rid of excess chars.
        print(str(myjson))
        json_id = self.stripstring(self.DictQuery(myjson).get("search/id"))
        #json_title = self.stripstring(self.DictQuery(myjson).get("search/title"))
        json_desc = self.stripstring(self.DictQuery(myjson).get("search/description"))
        plist.append(json_id)
        plist.append(json_desc)
        
        # Gets the actual information for that item
        jsonbody = self.getdatabody(json_id)
        for i in p:
            try:
                plist.append(self.DictQuery(jsonbody).get("entities/{0}/claims/{1}/mainsnak/datavalue/value".format(json_id, i)))
            except:
                plist.append("[unknown]")
        
        return plist

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
                    break
                    
            return val

def setup(bot):
    bot.add_cog(UtilitiesCog(bot))
