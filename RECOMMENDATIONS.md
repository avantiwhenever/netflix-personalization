# Recommendations


## Architecture

```
scripts/fetch_catalog.py     TMDB API -> data/catalog.json + data/posters/*.jpg
scripts/embed_posters.py     data/posters/*.jpg -> data/embeddings.json (CLIP vectors)
scripts/build_static_data.py data/catalog.json + data/embeddings.json -> docs/data/*.json
docs/                          static HTML/CSS/JS, reads docs/data/*.json, all
                               taste-vector math done client-side (cosine
                               similarity over precomputed vectors). Served
                               directly by GitHub Pages and HF Spaces —
                               same folder, two hosts, no build step.
```

No backend, no database, no build step for the front end — same shape as
`recs-engine-2026`. The only "server" work is the offline data-prep
pipeline, run once (or re-run to refresh the catalog) and committed as
static JSON.

### Why client-side ranking instead of a server

The math involved (dot products over a few hundred low-dimensional vectors)
is cheap enough to do in plain JS in the browser instantly. This avoids
hosting a backend entirely — the whole thing deploys free on GitHub Pages,
matching the $0-infra approach from the prior project.

### Why an averaged-embedding "user tower" instead of a trained one

Building a real two-tower model needs labeled interaction data (impressions,
clicks, plays) that doesn't exist for a personal demo project. Averaging the
CLIP embeddings of a few liked posters is a defensible zero-training proxy
for "what does this viewer's taste look like in embedding space" — good
enough to visibly demonstrate the *personalization* effect (different
profiles → different top-ranked poster), while being honest that it isn't
what Netflix actually trains.

## Roadmap / possible follow-ups

- Swap the averaged-vector proxy for an actual lightweight trained ranker
  (e.g. logistic regression over embedding similarity + a few features),
  using synthetic click data as labels, to get closer to a real two-tower
  setup. `scripts/validate_ranking.py`'s synthetic click generator is a
  starting point for producing that training signal, not just an eval set.
- Extend `scripts/validate_ranking.py`'s synthetic ground truth beyond a
  single anchor+Gaussian-noise model (see VALIDATION.md's "honest limits").
- The same-genre-random baseline (added) showed most of the ranking's
  advantage over popularity is genre-matching, not the averaging step —
  worth testing whether the averaging edge grows with more liked-seed
  samples (5, 10 instead of 3), per VALIDATION.md's follow-up note.
- Add a second modality: trailer thumbnail frames as a stand-in for video
  preview personalization (MAPS's MediaFM half), scored the same way as
  posters.
- Add a "why this profile" panel showing nearest-neighbor titles in
  embedding space to the current taste vector, for better explainability.
- If the catalog grows large, move `docs/data/*.json` to a CDN-hosted blob
  rather than committing to the repo.

## Deployment

Two free static hosts, same `docs/` content, no build step for either:

- **GitHub Pages** — repo is public, deploys `docs/` on `main` via the
  classic branch-based source. Pushing to `main` redeploys automatically.
  https://avantiwhenever.github.io/netflix-personalization/
- **Hugging Face Spaces** (Static SDK, free tier — no compute cost, just
  served files). `docs/README.md`'s YAML frontmatter declares `sdk:
  static`. Deployed via `huggingface_hub.HfApi.upload_folder()`, not git
  push — see HOWTO.md for the redeploy snippet.
  https://huggingface.co/spaces/avantiwhenever/netflix-personalization
