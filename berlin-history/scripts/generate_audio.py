#!/usr/bin/env python3
"""Generate one MP3 per place from data/places.json.

Azure (default):
  export AZURE_SPEECH_KEY=...  AZURE_SPEECH_REGION=westeurope
  python3 scripts/generate_audio.py
Speechify:
  export SPEECHIFY_API_KEY=...
  python3 scripts/generate_audio.py --provider speechify --voice george

Existing files are skipped; use --force to regenerate, --only <id> for one place.
"""
import argparse, base64, hashlib, json, random, os, sys, urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

# 50/50 male/female: genders are shuffled with a fixed seed (stable across reruns),
# then each place picks one of that gender's voices.
AZURE_VOICES = {"male": ["en-GB-RyanNeural", "en-GB-ThomasNeural"], "female": ["en-GB-SoniaNeural", "en-GB-LibbyNeural"]}
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "places.json"
OUT = ROOT / "audio"


def load_env():
    """Read KEY=value lines from berlin-history/.env (may be a symlink to another project's .env)."""
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            k, sep, v = line.partition("=")
            if sep and not k.strip().startswith("#"):
                os.environ.setdefault(k.strip(), v.strip().strip('"\''))


def post(url, body, headers):
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode(errors='ignore')[:500]}")


def azure(text, voice):
    key, region = os.environ["AZURE_SPEECH_KEY"], os.environ.get("AZURE_SPEECH_REGION", "westeurope")
    ssml = (f'<speak version="1.0" xml:lang="en-GB" xmlns="http://www.w3.org/2001/10/synthesis">'
            f'<voice name="{voice}"><prosody rate="-5%">{escape(text)}</prosody></voice></speak>')
    return post(f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1", ssml.encode(), {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3",
        "User-Agent": "berlin-history",
    })


def speechify(text, voice):
    body = json.dumps({"input": text, "voice_id": voice, "audio_format": "mp3", "language": "en-US"}).encode()
    res = post("https://api.sws.speechify.com/v1/audio/speech", body, {
        "Authorization": f"Bearer {os.environ['SPEECHIFY_API_KEY']}",
        "Content-Type": "application/json",
    })
    return base64.b64decode(json.loads(res)["audio_data"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["azure", "speechify"], default="azure")
    ap.add_argument("--voice", help="Force one voice (default: random mix per place)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    load_env()
    need = "AZURE_SPEECH_KEY" if a.provider == "azure" else "SPEECHIFY_API_KEY"
    if not os.environ.get(need):
        sys.exit(f"{need} not set (add it to .env or export it)")
    places = json.loads(DATA.read_text())["places"]
    genders = (["male", "female"] * len(places))[:len(places)]
    random.Random(1945).shuffle(genders)
    tts = azure if a.provider == "azure" else speechify

    OUT.mkdir(exist_ok=True)
    for p, gender in zip(places, genders):
        if a.only and p["id"] != a.only:
            continue
        f = OUT / f"{p['id']}.mp3"
        if f.exists() and not a.force:
            print(f"skip  {f.name}")
            continue
        pool = AZURE_VOICES[gender] if a.provider == "azure" else ["george"]
        voice = a.voice or pool[int(hashlib.md5(p["id"].encode()).hexdigest(), 16) % len(pool)]
        text = f"{p['name']}. {p['script']}"
        f.write_bytes(tts(text, voice))
        print(f"done  {f.name}  {voice}  ({len(text)} chars)")


if __name__ == "__main__":
    main()
