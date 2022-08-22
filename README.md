# modson

Categorizes MC mods in a JSON file.
Currently supports Modrinth, Github and (kinda) Curseforge.

Requires `requests`

You can comment links out by putting #!# before the link

## Curseforge
Curseforge doesn't have a public API and since this app just needs to know the mod's name (and I don't want to force people to create a key for this application), modson tries to get the page title, instead of calling the API.

This function can be found in `cfmod.py` and requires `bs4`, `cloudscraper` and `lxml`

The file is completely optional and if you don't need mods from Curseforge, you can delete it.

Note: Try to open a page from Curseforge in your browser if it continually fails while getting the mod name.