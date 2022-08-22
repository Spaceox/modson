import json
import time
import requests
import argparse
import os


parser = argparse.ArgumentParser(
    prog="modson",
    description="Gets Minecraft mod links and categorizes them into a JSON file.\nFully supports Modrinth and kinda supports Github and Curseforge.",
)

parser.add_argument(
    "mods",
    help="Can be a link, a mod's slug/id (from modrinth) or (if -f is passed) a txt file containing mods' slugs/ids (from modrinth) or links.",
)
parser.add_argument(
    "-f",
    help="If passed, 'mods' will be treated as a txt file.",
    action="store_true",
)
parser.add_argument(
    "-u",
    help="If passed, the script will remove duplicates from the output JSON file.",
    action="store_true",
)
parser.add_argument(
    "--out",
    help="Output file path (default is the current working folder).",
    default=os.getcwd(),
)

args = parser.parse_args()
client = requests.Session()
client.headers.update({"User-Agent": "github_com/Spaceox/modson"})
fullOut = args.out + "/modson.json"

modSource: dict[str, list[str]] = {
    "modrinth": [],
    "modrinthID": [],
    "github": [],
    "curseforge": [],
}


def parseModrinth(mod: str, isURL: bool) -> dict[str, str]:
    if isURL:
        mod = mod.replace("https://modrinth.com/mod/", "")

    r = client.request("GET", f"https://api.modrinth.com/v2/project/{mod}")
    if r.status_code >= 400:
        raise ValueError(
            f"Could not get modrinth mod {mod}. URL: https://api.modrinth.com/v2/project/{mod}"
        )

    modInfo = r.json()
    if modInfo["project_type"] == "modpack":
        print("Modpacks are not supported.")
        raise ValueError(
            f"Modpacks are not supported, sorry. Modpack: 'https://modrinth.com/modpack/{mod}'"
        )

    modJson = {
        "name": modInfo["title"],
        "link": f"https://modrinth.com/mod/{modInfo['slug']}",
        "sides": {
            "server": modInfo["server_side"],
            "client": modInfo["client_side"],
        },
    }
    return modJson


def parseGithub(mod: str) -> dict[str, str]:
    modApi = mod.split("/")
    r = client.request("GET", f"https://api.github.com/repos/{modApi[3]}/{modApi[4]}")
    modInfo = r.json()
    modJson = {
        "name": modInfo["name"],
        "link": modInfo["html_url"],
        "sides": {
            "server": "unknown",
            "client": "unknown",
        },
    }
    return modJson


def defineMod(mod: str) -> None:
    try:
        if "http" not in mod:
            modurl = f"https://{mod}"
        else:
            modurl = mod

        client.request("HEAD", modurl)
    except requests.exceptions.ConnectionError:
        print("This doesn't seem a valid url, treating as modrinth mod.")
        modSource["modrinthID"].append(mod)
        return

    if "modrinth.com" in mod:
        print("Modrinth link found.")
        modSource["modrinth"].append(modurl)
    elif "github.com" in mod:
        print("Github link found.")
        modSource["github"].append(modurl)
    elif "curseforge.com" in mod:
        print("Curseforge link found.")
        modSource["curseforge"].append(modurl)
    else:
        raise ValueError(f"This site is not supported yet, sorry. URL: '{mod}'")


try:
    with open(fullOut, "r") as f:
        modsonOut = json.load(f)
        print("Loaded modson.json")
except FileNotFoundError:
    print("The json file doesn't exist, creating one.")
    modsonOut = json.loads('{"mods": []}')

print("Categorizing links, this might take a while")
if args.f:
    with open(args.mods, "r") as f:
        for line in f:
            mod = line.rstrip("\n")
            defineMod(mod)
            time.sleep(2)
else:
    defineMod(args.mods)

for mod in modSource["modrinthID"]:
    modsonOut["mods"].append(parseModrinth(mod, False))
    if mod != modSource["modrinthID"][-1]:
        time.sleep(5)
for mod in modSource["modrinth"]:
    modsonOut["mods"].append(parseModrinth(mod, True))
    if mod != modSource["modrinth"][-1]:
        time.sleep(5)
for mod in modSource["github"]:
    modsonOut["mods"].append(parseGithub(mod))
    if mod != modSource["github"][-1]:
        time.sleep(5)

if modSource["curseforge"] != []:
    try:
        import cfmod

        for mod in modSource["curseforge"]:
            modsonOut["mods"].append(cfmod.parseCurseForge(mod))
            if mod != modSource["curseforge"][-1]:
                time.sleep(5)
    except ImportError:
        print(
            "cfmod.py wasn't found. Curseforge links are not supported without it\nSkipping Curseforge."
        )

if args.u:
    print(
        "Checking for duplicates, this might take a while depending on the amount of mods."
    )
    filteredMods = []
    for mod in modsonOut["mods"]:
        if mod not in filteredMods:
            filteredMods.append(mod)
    modsonOut["mods"] = filteredMods

with open(fullOut, "w", encoding="utf-8") as out:
    json.dump(modsonOut, out, ensure_ascii=False, indent=4)
