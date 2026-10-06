#!/usr/bin/env python3
"""Download the lead Wikipedia image for each place (from Wikimedia Commons)
and record author/license in data/credits.json. No API key needed."""
import json, re, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "berlin-history-trip/1.0 (personal travel guide)"}


def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == tries - 1:
                raise
            time.sleep(5 * 2 ** i)  # Wikimedia rate limit – back off


def strip(html):
    return re.sub(r"<[^>]+>", "", html or "").strip()


def main():
    places = json.loads((ROOT / "data/places.json").read_text())["places"]
    credits_file = ROOT / "data/credits.json"
    credits = json.loads(credits_file.read_text()) if credits_file.exists() else {}
    (ROOT / "img").mkdir(exist_ok=True)

    for p in places:
        dest = ROOT / "img" / f"{p['id']}.jpg"
        if dest.exists() and p["id"] in credits:
            print(f"skip  {p['id']}")
            continue
        if p.get("photo_search"):  # optional override: search Wikimedia Commons directly
            q = urllib.parse.urlencode({
                "action": "query", "format": "json", "list": "search", "srnamespace": 6,
                "srsearch": f"{p['photo_search']} filetype:bitmap", "srlimit": 1,
            })
            hits = json.loads(get(f"https://commons.wikimedia.org/w/api.php?{q}"))["query"]["search"]
            name = hits[0]["title"].removeprefix("File:") if hits else None
        else:
            q = urllib.parse.urlencode({
                "action": "query", "format": "json", "redirects": 1, "titles": p["wiki"],
                "prop": "pageimages", "piprop": "name", "pilicense": "free",
            })
            page = next(iter(json.loads(get(f"https://en.wikipedia.org/w/api.php?{q}"))["query"]["pages"].values()))
            name = page.get("pageimage")
        if not name:
            print(f"MISS  {p['id']} (no lead image)")
            continue
        q = urllib.parse.urlencode({
            "action": "query", "format": "json", "titles": f"File:{name}",
            "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 1000,
        })
        info = next(iter(json.loads(get(f"https://commons.wikimedia.org/w/api.php?{q}"))["query"]["pages"].values()))
        if "imageinfo" not in info:  # file hosted on en.wikipedia only (non-free) – skip
            print(f"MISS  {p['id']} (not on Commons)")
            continue
        ii = info["imageinfo"][0]
        meta = ii.get("extmetadata", {})
        dest.write_bytes(get(ii["thumburl"]))
        credits[p["id"]] = {
            "author": strip(meta.get("Artist", {}).get("value")) or "Unknown",
            "license": strip(meta.get("LicenseShortName", {}).get("value")),
            "source": ii["descriptionurl"],
        }
        print(f"done  {p['id']}  ← {name}")
        credits_file.write_text(json.dumps(credits, indent=2, ensure_ascii=False))
        time.sleep(2)

    credits_file.write_text(json.dumps(credits, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
