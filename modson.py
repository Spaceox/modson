import json
import httpx
import argparse
import os

headers = {"user-agent": "github_com/Spaceox/modson"}

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
client = httpx.Client(headers=headers)
fullOut = args.out + "/modson.json"


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
    r = client.request("GET", f"https://api.github.com/repos/{mod[3]}/{mod[4]}")
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


def defineMod(mod: str) -> dict[str, str]:
    try:
        r = client.request("HEAD", mod)
        if r.status_code >= 400:
            if "modrinth.com" in mod:
                print("Modrinth link detected.")
                return parseModrinth(mod, True)
            elif "github.com" in mod:
                print("Github link detected.")
                return parseGithub(mod)
            elif "curseforge.com" in mod:
                print("Curseforge link detected.")
                try:
                    import cfmod

                    modInfo = cfmod.parseCurseForge(mod)
                except ImportError:
                    raise ImportError(
                        "cfmod.py wasn't found. Curseforge links are not supported without it."
                    )
                return modInfo
            else:
                raise ValueError(f"This site is not supported yet, sorry. URL: '{mod}'")
        else:
            raise ConnectionError(
                f"Check that the url is typed correctly and try again later. URL: '{mod}'"
            )
    except httpx.HTTPError:
        print("This doesn't seem like an url, treating as modrinth mod.")
        return parseModrinth(mod, False)


try:
    with open(fullOut, "r") as f:
        modsonOut = json.load(f)
except FileNotFoundError:
    print("It seems like the json file doesn't exist, creating it.")
    modsonOut = json.loads('{"mods": []}')

if args.f:
    with open(args.mods, "r") as f:
        for line in f:
            mod = line.rstrip("\n")
            modsonOut["mods"].append(defineMod(mod))
else:
    modsonOut["mods"].append(defineMod(args.mods))

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
