# How to run this

## 1. Get a TMDB API key

Sign up at https://www.themoviedb.org/signup, then request a free API key
at https://www.themoviedb.org/settings/api ("Developer" use is fine for a
personal demo). Copy `.env.example` to `.env` and paste your key in:

```
cp .env.example .env
# edit .env: TMDB_API_KEY=your_key_here
```

## 2. Install dependencies

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Run the data pipeline

```
python scripts/fetch_catalog.py      # TMDB -> data/catalog.json + data/posters/
python scripts/embed_posters.py      # posters -> data/embeddings.json (CLIP vectors)
python scripts/build_static_data.py  # -> docs/data/titles.json + docs/posters/
```

`fetch_catalog.py` takes a few minutes (network + TMDB rate limits).
`embed_posters.py` runs CLIP on CPU — expect it to take a few minutes for a
few hundred images the first time (it also downloads the pretrained model
weights once).

## 4. Serve the demo locally

```
cd docs && python3 -m http.server 8000
```

Open http://localhost:8000 — pick a persona or build your own taste
profile, and compare the personalized vs. default poster pick per title.

## 5. Deploy

Deployed in two places, both free, both serving the same `docs/` folder:

- **GitHub Pages** — repo is public, Pages deploys `docs/` on `main`
  automatically on push. Live at
  https://avantiwhenever.github.io/netflix-personalization/
- **Hugging Face Spaces** (Static SDK, free — no compute cost) — `docs/`
  doubles as the Space's root; `docs/README.md`'s YAML frontmatter
  (`sdk: static`) is what makes it a valid Space. Live at
  https://huggingface.co/spaces/avantiwhenever/netflix-personalization
  (direct static URL:
  https://avantiwhenever-netflix-personalization.static.hf.space/index.html).
  To redeploy after regenerating `docs/`:
  ```
  hf auth login   # once, needs a write-scoped token
  python3 -c "
  from huggingface_hub import HfApi
  HfApi().upload_folder(folder_path='docs', repo_id='avantiwhenever/netflix-personalization', repo_type='space')
  "
  ```

## Refreshing the catalog

Re-run all three scripts anytime to pull a fresh/larger TMDB catalog;
`build_static_data.py` regenerates `docs/data/titles.json` and
`docs/posters/` from scratch each time. Push to `main` to redeploy GitHub
Pages; re-run the `upload_folder` snippet above to redeploy the HF Space.
