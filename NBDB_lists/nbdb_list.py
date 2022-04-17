from wikibase_api import Wikibase
import requests
import os
import json
import dateutil.parser as dp
import datetime
import sys

wb = Wikibase("https://data.nonbinary.wiki/w/api.php")
index = {
        "sp": "p-index.json",
        "neop": "p-index.json",
        "nounp": "p-index.json",
        "id": "id-index.json"
    }

def get_instance(id):
    """
    Gets instance (P1) of the given item and returns a list.
    """
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

def check_deleted(allpages):
    """
    Compares the items in the NBDb against the downloaded ones. Then,
    returns list with all items that have a local file but not a wiki page.
    """
    files = os.listdir(".")
    localitems = []
    for f in files:
        if f.startswith("Q"): # Exclude indexes
            i = f.replace(".json", "")
            localitems.append(i)
    
    nbdbitems = []
    for item in allpages:
        i = item["title"].replace("Item:", "")
        nbdbitems.append(i)

    diff = list(set(localitems).difference(nbdbitems))

    if len(diff) == 0:
        print("No items have been deleted.")
        return None
    else:
        print(f"Items that have been deleted from the NBDb: {str(diff)}")
        return diff

def check_recentchanges():
    """
    Checks recent changes and returns all pages in Item namespace
    that have been updated in the last day.
    """
    apilink = "https://data.nonbinary.wiki/w/api.php?action=query&list=recentchanges&rctoponly=1&rclimit=500&rcnamespace=860&format=json"
    data_json = requests.get(apilink).json()
    allchanges = data_json["query"]["recentchanges"] # List of dictionaries

    modified = []
    today_ts = str(datetime.datetime.utcnow())
    today = dp.parse(today_ts).timestamp()
    day_ago = today-86400 # 86,400 seconds = 1 hour

    for change in allchanges:
        title = change["title"]
        timestamp = change["timestamp"]
        parsed_ts = dp.parse(timestamp)
        ts_seconds = parsed_ts.timestamp()
        if ts_seconds <= day_ago:
            print("Stopping, all other changes are older.")
            break
        else:
            modified.append(title)

    return modified

def update_item(item):
    """
    Updates local json file with NBDb item.
    item = string with format "Item:Q123".
    """

    id = item.replace("Item:", "")
    # Try connecting 3 times. If 3 errors, continue to next item.
    for attempt in range(3):
        try:
            type = get_instance(id)
            break
        except requests.exceptions.RequestException as e:
            print(f"Error while querying {item}: {e}\nRetrying.")
            continue

    if type[0] == "other" or type[0] == "unknown":
        return
    aliaslist = type[1]["aliases"]
    if "en" in aliaslist: # check if it has aliases in English
        aliases = [i["value"] for i in aliaslist["en"]] # Creates a list of aliases
    else:
        aliases = [] # Sometimes there are no aliases, but we still need the list
    if "en" in type[1]["labels"]: # check if it has a label in English
        aliases.insert(0, type[1]["labels"]["en"]["value"]) # add item title to the aliases list
    if aliases == []:
        return # If there are no aliases and no label, we skip the item
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
    print(f'Updated file {filename} and updated {index[type[0]]}')

def main(all=False):
    itemlist = "https://data.nonbinary.wiki/w/api.php?action=query&list=allpages&apnamespace=860&aplimit=500&format=json"
    data_json = requests.get(itemlist).json()
    allitems = data_json["query"]["allpages"]
    
    deleted = check_deleted(allitems)
    print(deleted)
    if deleted != None:
        for i in deleted:
            if i.startswith("Q"): # Double-check we're not deleting an index
                os.remove(i + ".json")
        print("Deleted items.")

    if all == True:
        print("Updating all items. This will probably take a while.")
        for i in allitems:
            item = i["title"]
            update_item(item)
    else:
        edited = check_recentchanges() # Returns lists
        for item in edited:
            update_item(item)


opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
if "-a" in opts:
    main(all=True)
else:
    main()