# Paper vs. demo: a component-by-component comparison


This is the honest accounting of how this project relates to Netflix's
[MAPS: Multimodal Asset Personalization at Scale](https://netflixtechblog.com/maps-netflixs-multimodal-asset-personalization-at-scale-32f96320785e)
(companion paper: [arXiv:2608.18322](https://arxiv.org/abs/2608.18322)) —
what's a faithful small-scale reproduction of the real mechanism, what's a
deliberate documented simplification, and what isn't implemented at all.
Every claim below points at the actual code, not just a description of it.

`RESEARCH.md` has the background research and data-source notes.
`VALIDATION.md` has the offline evaluation of the ranking mechanism. This
file is the map between the two: which parts of the paper map to which
parts of the code, and what evidence backs each claim.

## What MAPS actually claims

1. Replace per-canvas, **ID-based** artwork-selection models with a
   **two-tower model**: a member tower (behavior) + an item tower (CLIP
   image embedding of the asset).
2. Score = similarity between member vector and item vector — content-based
   matching, not a lookup table keyed by member/asset ID.
3. **Cold start**: a brand-new title or asset has no interaction history,
   but it has pixels — so the item tower can score it from day one.
4. **Cross-title knowledge transfer**: one shared embedding space lets
   taste learned via one title inform scoring on a title it's never
   co-occurred with in any interaction log.
5. One model replaces five canvas-specific models, because the item tower
   doesn't care which canvas it's looking at, only what the image depicts.
6. An offline proxy eval (predict the popularity-winning asset from
   embeddings alone) precedes online A/B testing.
7. Separately: tri-modal video-preview personalization (MediaFM, fusing
   visual/audio/timed-text) — a distinct half of the paper.

## Component-by-component

| # | Paper component | This demo | Status |
|---|---|---|---|
| 1 | Item tower = CLIP image embeddings | `scripts/embed_posters.py:22,28` — real pretrained CLIP (`clip-ViT-B-32`) run on real TMDB poster images | **Real** |
| 2 | Content-based matching (similarity, not ID lookup) | `docs/app.js:10-14` `dot()`, used in `renderResults()` (`app.js:104-109`) as argmax over cosine similarity | **Real mechanism**, same primitive |
| 3 | Cold start via content embeddings | No ID-embedding table exists anywhere in this codebase — see "Cold start" below | **Real, structurally**, with a concrete example |
| 4 | Cross-title knowledge transfer | Taste vector built from a handful of titles applies to all 128 titles, including titles from unrelated interaction contexts (there are none) | **Real mechanism**, small scale |
| 5 | One model, multiple canvas types | `scripts/fetch_catalog.py:66-76` pulls up to 5 poster *variants* per title | **Analogous, not identical** — one canvas type (poster), not Netflix's 5 |
| 6 | Trained two-tower member model | `docs/app.js:16-24` `averageVector()` — mean of a few liked posters, zero training | **Not real** — the one load-bearing simplification |
| 7 | Offline proxy eval vs. outcome data | `scripts/validate_ranking.py` — synthetic click-based baseline (see VALIDATION.md) | **Adapted proxy**, synthetic ground truth, not real outcomes |
| 8 | Video preview / MediaFM (tri-modal) | Not built | **Out of scope**, by explicit scoping decision |
| 9 | Query-aware text-CLIP search extension | Not built | **Out of scope** |
| 10 | Online A/B test | Not possible without real traffic | **Not applicable** to a personal demo |

## 1. Embedding generation — real, not simulated

`scripts/embed_posters.py:22` loads actual pretrained CLIP weights and runs
a real forward pass on every downloaded poster:

```python
model = SentenceTransformer("clip-ViT-B-32")
...
vector = model.encode(image, normalize_embeddings=True)          # embed_posters.py:28
```

614 real images, downloaded from TMDB's CDN (`fetch_catalog.py:83`, inside
`download()`), got 614 real 512-d vectors — not placeholders, not hashes.

## 2. Matching — the same primitive MAPS uses at serving time

```js
function dot(a, b) {                      // app.js:10-14
  let sum = 0;
  for (let i = 0; i < a.length; i++) sum += a[i] * b[i];
  return sum;
}
```

Every embedding is L2-normalized at embed time, so this dot product *is*
cosine similarity. `renderResults()` (`app.js:104-109`) scores every poster
variant against the taste vector and takes the argmax. That's
nearest-neighbor retrieval in embedding space — the same mechanism a
trained two-tower model uses once both towers are frozen at serving time.
No hardcoded genre-to-image mapping exists anywhere in `app.js`.

## 3. Cold start — real, with a concrete number

The sharpest test of MAPS's cold-start claim: can a model score a title
it's never seen any interaction data for, exactly as well as an
established title? There's no ID-embedding table anywhere in this repo —
`catalog.json`'s `id` field is only ever used as a dict key to join files
(`scripts/build_static_data.py:27-29`), never as a learned parameter. The
only thing that produces a score is `dot(taste_vector, poster_embedding)`,
and `poster_embedding` comes 100% from pixels.

Concretely (persona = "Animated & Family," built from 5 seed titles: *Toy
Story 5, Minions & Monsters, Batman: Knightfall, Demon Slayer: Infinity
Castle, Avatar Aang*), scoring three titles **not** in that seed set:

| Title | Age / real-world interaction history | Score |
|---|---|---|
| Spirited Away | 2001, globally famous, decades of data | 0.679 |
| Coco | 2017, established Pixar classic | 0.771 |
| Zootopia 2 | 2025, brand-new, ~zero interaction history anywhere | **0.788** |

The brand-new title scores *higher* than the 24-year-old classic. That's
the direct, checkable consequence of an architecture with no ID-based path
— reproduced faithfully at small scale, even though this demo never
trained anything.

**What this does NOT show** (see the critique in section 6): that this
score is *good* — correlated with what would actually make someone choose
to watch something — only that a score exists on day one regardless of
age. MAPS validated the "good" part with real A/B tests; this demo
validates it, at a much smaller and synthetic level, in `VALIDATION.md`.

## 4. Cross-title transfer — real mechanism, small scale

A "Horror" taste vector, built purely from 5 horror posters' pixels
(`app.js:38-41`), gets applied to all 128 titles, including titles from
other genres with zero interaction-log overlap (there are no interaction
logs at all). That only works because every embedding lives in one shared
space — the same reason MAPS's transfer works, just unvalidated against
real outcomes at this scale.

## 5. Multi-canvas — analogous, not identical

`fetch_poster_paths()` (`fetch_catalog.py:66-76`) pulls up to 5 poster
variants per title from TMDB's `/movie/{id}/images`. This mirrors "multiple
candidate assets per title" — the structural precondition for a rerank
problem to exist at all — but it's 5 variants of *one* canvas type
(poster), not Netflix's 5 distinct canvas types (billboard, tile,
jaw-jaw, etc.).

## 6. What's honestly not real — the "user tower"

```js
function averageVector(vectors) {          // app.js:16-24
  const dim = vectors[0].length;
  const avg = new Array(dim).fill(0);
  for (const v of vectors) for (let i = 0; i < dim; i++) avg[i] += v[i];
  for (let i = 0; i < dim; i++) avg[i] /= vectors.length;
  const norm = Math.sqrt(avg.reduce((s, x) => s + x * x, 0));
  return avg.map((x) => x / norm);
}
```

MAPS's member tower is a trained neural network, learned jointly with the
item tower via a ranking loss over real interaction logs (impressions,
clicks, plays). This is the mean of a few liked posters' embeddings,
re-normalized. No training step exists anywhere in this repo. This is a
zero-shot heuristic standing in for a trained tower, and it's the single
biggest gap from the paper — everything downstream of it (the matching,
the cold-start property) is real; the input to it is not learned.

A related, sharper critique surfaced during review: raw CLIP space is
organized around visual-semantic content aligned to text captions, not
around "taste" as a linear, additive quantity — averaging liked posters
assumes taste is a direction you can add up in that space, which is an
assumption, not something this project trained or verified. Also, the
persona mechanism's seed titles are chosen by TMDB popularity
(`app.js:39`), which quietly reintroduces a popularity prior into a
demo whose whole thesis is "we don't need popularity/interaction history"
— a small, self-undermining detail flagged here rather than hidden.

## 7. Offline proxy eval — adapted, not the same task, and it changed the story

MAPS's offline proxy predicts the popularity-winning asset from embeddings
alone, checked against real outcome data, before online A/B testing. This
demo has no real outcome data, so `scripts/validate_ranking.py` builds a
**synthetic** proxy instead: manufacture a ground truth (anchor a synthetic
member's taste to one specific title, add tunable noise), and check
whether the production ranking mechanism recovers it better than naive
baselines.

The full methodology and numbers are in `VALIDATION.md`; the headline,
including the finding that changed after adding a same-genre-random
baseline:

| noise σ | content model (3-avg) | same-genre-random (1) | popularity | random |
|---:|---:|---:|---:|---:|
| 0.00 | 0.486 | 0.415 | 0.218 | 0.194 |
| 0.40 | 0.220 | 0.224 | 0.223 | 0.206 |

Most of the "beats popularity" effect turned out to be genre-matching, not
the averaging step — a same-genre-random single poster nearly matches the
full model. Averaging still adds a real, consistent, but second-order edge
on top of that. This is the kind of finding a rigorous evaluation is
supposed to surface, including when it complicates the original, cleaner
story — see `VALIDATION.md`'s "reading the result honestly" section.

## Bottom line

The parts of MAPS that are checkable by running code — embedding
generation, embedding-space matching, and the cold-start property that
falls out of using content embeddings instead of ID embeddings — are real
here, backed by numbers anyone can reproduce (`docs/data/titles.json`,
`scripts/validate_ranking.py`). The part that isn't real is the learned
member model: this demo substitutes a zero-shot averaging heuristic, and
the synthetic validation shows that heuristic does meaningfully better
than naive baselines, but mostly through genre-matching rather than
individual-level preference recovery. That's flagged everywhere in this
repo rather than hidden, including in the places where the evidence
complicated the story rather than confirming it.
