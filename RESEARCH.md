# Research


## Source material

**MAPS: Netflix's Multimodal Asset Personalization at Scale**
https://netflixtechblog.com/maps-netflixs-multimodal-asset-personalization-at-scale-32f96320785e

Companion paper: **Multimedia Asset Personalization via Multimodal
Embeddings at Netflix** — https://arxiv.org/abs/2608.18322

### What the system does

Netflix personalizes which promotional asset (artwork, video preview) a
member sees per title. The old approach: separate per-canvas, ID-based
models, trained purely on interaction history. Problem — an ID-based model
knows nothing about a new title or a new asset until it accumulates
interaction data, so cold start is bad, and there's no knowledge transfer
between titles.

MAPS replaces this with a **two-tower model**: one tower encodes the member
(from behavior), the other encodes each candidate asset via a **CLIP image
embedding**. Because the item tower is content-aware (embeds what the image
*looks like*), a single model serves all five Netflix artwork canvas types,
gets meaningfully better cold-start behavior, and transfers knowledge across
titles that would otherwise share no interaction signal.

Video-preview personalization is a separate, tri-modal extension:
**MediaFM**, an in-house foundation model fusing visual (SeqCLIP), audio
(wav2vec 2.0), and timed-text signals, trained on a large corpus of shots
from Netflix's catalog. Evaluated online (A/B test) and offline via a proxy
task predicting popularity-based winners from embeddings alone.

### What this demo replicates, and what it doesn't

| MAPS (real system) | This demo |
|---|---|
| Two-tower model, trained on real Netflix interaction logs | No training — "user tower" is a simple average of CLIP embeddings over a few posters/titles the demo user says they like. Documented simplification, not a learned model. |
| CLIP-embedded artwork, 5 canvas types, Netflix's own asset library | CLIP-embedded TMDB poster images (public movie posters, not Netflix's proprietary multi-canvas assets) |
| Video preview personalization (MediaFM, tri-modal) | Out of scope — image/artwork only, per project scoping decision |
| Netflix-scale catalog + real A/B testing | ~150-300 title catalog, offline cosine-similarity sanity checks only, no live experiment |

The transferable idea worth demonstrating: **content-aware embeddings let
you personalize assets for titles/images you have never seen interaction
data for** — that's the core insight, and it holds at small scale with a
pretrained public CLIP model just as it does at Netflix's scale with their
in-house one.

## Data source: TMDB API

- https://developer.themoviedb.org/reference/intro/getting-started
- Free, requires a personal API key (sign up + request a key at
  themoviedb.org/settings/api). No cost at demo-scale request volumes.
- `/movie/{id}/images` returns **multiple poster variants per title** — the
  key field that makes a rerank-style demo possible at all, since MAPS's
  whole premise is choosing among *multiple* candidate assets per title.
- `/discover/movie` (filtered by genre, sorted by popularity) used to build
  a diverse seed catalog across genres, so different taste profiles produce
  visibly different rankings.

Alternatives considered:

| Source | Why not primary |
|---|---|
| Kaggle static movie-poster datasets | Fixed snapshot, no multiple poster variants per title (usually one poster per title) — doesn't support the rerank premise |
| OMDb API | Single poster per title only, same limitation |
| MovieLens | Great for real user rating data, but no poster images; would need pairing with TMDB anyway, and this demo doesn't use real user history (see simplifications above) |

## CLIP model

Pretrained, open-source CLIP (`clip-ViT-B-32` via `sentence-transformers`)
run offline via a Python script — no training, no GPU required for a few
hundred images on CPU. This mirrors the *use* of CLIP embeddings in MAPS's
item tower, without attempting to reproduce Netflix's specific two-tower
training setup.

**Embedding sanity check**: average within-genre poster similarity for
"Animated & Family" (0.615) is clearly higher than its cross-genre
similarity vs. "Horror" (0.506) — confirms CLIP is picking up real
visual-style signal, not noise. The same check for "Horror" vs. cross-genre
was much weaker (0.507 vs. 0.506) — horror posters in this catalog are
visually diverse (some minimalist, some illustrated), so genre alone
doesn't cluster them as tightly. Worth keeping in mind when a persona's
results look inconsistent. See `VALIDATION.md` for a more rigorous
(synthetic) check of whether the ranking mechanism itself recovers
preference, not just visual style.
