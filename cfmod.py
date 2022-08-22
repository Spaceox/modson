import cloudscraper  # type: ignore[import]
from bs4 import BeautifulSoup  # type: ignore[import]
import time

scraper = cloudscraper.create_scraper()


def parseCurseForge(mod: str) -> dict[str, str]:
    while True:
        soup = BeautifulSoup(scraper.get(mod).text, features="lxml")
        modName = (
            soup.title.string.replace(" - Mods - Minecraft - CurseForge", "")
            .lstrip(" ")
            .rstrip(" ")
        )
        if modName == "Just a moment...":
            print("Cloudflare detected. Retrying in 10 seconds...")
            time.sleep(10)
            continue
        else:
            break
    modJson = {
        "name": modName,
        "link": mod,
        "sides": {
            "server": "unknown",
            "client": "unknown",
        },
    }

    return modJson
