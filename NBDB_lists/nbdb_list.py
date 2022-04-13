from wikibase_api import Wikibase
import requests
import os
import json

wb = Wikibase("https://data.nonbinary.wiki/w/api.php")

def cleanup():
    files = os.listdir(".")
    for f in files:
        if f.endswith(".json"):
            os.remove(f)
    print("All files have been cleared")

def get_instance(id):
    iteminfo = wb.entity.get(id)
    #print(str(iteminfo))
    try:
        instanceof = iteminfo["entities"][id]["claims"]["P1"][0]["mainsnak"]["datavalue"]["value"]["id"]
        allinfo = iteminfo["entities"][id]
        if instanceof == "Q3": # Q3 = Standard personal pronoun
            print("{0} is a STANDARD PRONOUN".format(id))
            return ["sp", allinfo]
        elif instanceof == "Q15": # Q15 = Neopronoun
            print("{0} is a NEOPRONOUN".format(id))
            return ["neop", allinfo]
        elif instanceof == "Q68": # Q68 = Nounself pronoun
            print("{0} is a NOUNSELF NEOPRONOUN".format(id))
            return ["nounp", allinfo]
        elif instanceof == "Q7":
            print("{0} is a GENDER IDENTITY".format(id))
            return ["id", allinfo]
        else:
            #print("{0} is NOT a pronoun nor a gender identity".format(id))
            return ["other", allinfo]
    except KeyError:
        print("{0} doesn't have P1".format(id))
        return ["unknown"]

def write_items():
    cleanup() # reset the lists

    itemlist = "https://data.nonbinary.wiki/w/api.php?action=query&list=allpages&apnamespace=860&aplimit=500&format=json"

    index = {
        "sp": "p-index.json",
        "neop": "p-index.json",
        "nounp": "p-index.json",
        "id": "id-index.json"
    }

    data_json = requests.get(itemlist).json()
    cleanitems = data_json["query"]["allpages"]
    #print(cleanitems)
    
    for item in cleanitems:
        id = item["title"].replace("Item:", "")
        for attempts in range(3):
            try:
                type = get_instance(id)
                break
            except requests.exceptions.RequestException as e:
                print(f"Error while querying {item}: {e}\nRetrying.")
                continue
        if type[0] == "other" or type[0] == "unknown":
            continue
        #print(str(type))
        aliaslist = type[1]["aliases"]
        if "en" in aliaslist: # check if it has aliases in English
            aliases = [i["value"] for i in aliaslist["en"]] # Creates a list of aliases
        else:
            aliases = [] # Sometimes there are no aliases, but we still need the list
        if "en" in type[1]["labels"]: # check if it has a label in English
            aliases.insert(0, type[1]["labels"]["en"]["value"]) # add item title to the aliases list
        if aliases == []:
            continue # If there are no aliases and no label, we skip the item
        open(index[type[0]], "a").close() #Open and close immediately in case the index is not created
        with open(index[type[0]], "r") as findex:
            if os.path.getsize(index[type[0]]):
                data = json.load(findex)
                data[id] = aliases # Replaces value or adds new key/value if not there
            else:
                print("file empty")
                data = {}
                data[id] = aliases
        with open(index[type[0]], "w") as findex:
            json.dump(data, findex, indent=4) # Update index with the new index
        #print('Updated index')
        filename = id + ".json"
        with open(filename, "w") as fitem:
            json.dump(type[1], fitem, indent=4)
        print(f'Created file {filename}')

write_items()