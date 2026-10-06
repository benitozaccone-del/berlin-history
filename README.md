# Berlin History Walks

Mobile audioguide covering 31 sites from WWI, Weimar, the Third Reich, WWII and the Cold War.
It's a static site with no database or backend. All content lives in `data/places.json`.

## Generate the audio (once)

**Azure (recommended, free tier is plenty):**
1. In the Azure portal, create a **Speech** resource (Free F0 tier). Copy *Key 1* and the *Region*.
2. Run:
   ```
   export AZURE_SPEECH_KEY=xxxx
   export AZURE_SPEECH_REGION=westeurope
   python3 scripts/generate_audio.py
   ```
   The default voice is `en-GB-RyanNeural`. To try others: `--voice en-US-AndrewNeural`, `--voice en-GB-SoniaNeural`.

**Speechify:** `export SPEECHIFY_API_KEY=xxxx` then `python3 scripts/generate_audio.py --provider speechify --voice george`

Use `--only reichstag` to test a single place, and `--force` to regenerate files. Until the MP3s exist, the app falls back to your phone's built-in voice.

## Edit content
Edit `data/places.json` (text, coordinates, `wiki` page for the photo, or `photo_search` to pick a Commons photo by search).
Then re-run `scripts/fetch_photos.py` and `scripts/generate_audio.py --only <id> --force`.

## Put it on your phone
The site needs HTTPS for GPS and offline mode, so host it for free:
- **Netlify Drop:** drag this folder onto https://app.netlify.com/drop
- **GitHub Pages:** push the folder to a repo, then Settings → Pages → deploy from `main`.

Open the URL on your phone, then use Share → **Add to Home Screen**. Open it once on Wi‑Fi. The service worker caches every photo and MP3, so it works without signal afterwards. Map tiles are cached only for the areas you have viewed.

## Local preview
`python3 -m http.server 8765`, then open http://localhost:8765
