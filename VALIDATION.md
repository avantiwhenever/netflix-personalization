# Validation: does the ranking mechanism beat naive baselines?


## Why this exists

Showing that CLIP embeddings encode visual style (within-genre similarity
beats cross-genre — see `RESEARCH.md`'s "Embedding sanity check") is not
the same as showing the ranking mechanism recovers anything resembling
*preference*. Without any real interaction data, there was nothing to
check the personalized ranking against — it was "personalization-shaped,"
not validated.

`scripts/validate_ranking.py` closes that gap the only honest way available
without real user data: a **synthetic proxy task**, in the same spirit as
MAPS's own offline proxy (predicting the popularity-winning asset from
embeddings alone, before online A/B testing). This is explicitly not a
claim that real people would behave this way — it's a check that the
mechanism (`averageVector()` + dot-product ranking, `docs/app.js:16-24,
104-109`) does something non-trivial and noise-sensitive, not something
spurious.

## Method

1. **Ground truth, per synthetic member**: anchor their "true" taste to one
   specific title's poster embedding — they secretly love one particular
   movie. For a held-out title, the ground-truth preferred poster variant
   is the one most similar to that anchor, plus injected Gaussian noise
   (`sigma`) to simulate real-world choice stochasticity.
2. **What the model observes**: NOT the anchor. Only 3 posters from other
   titles in the anchor's genre — genre-level signal, mirroring exactly
   what the real product exposes (personas are genre-level averages; the
   hand-pick flow is a small sample of liked posters). The model's taste
   vector is built with the *exact same function* the product uses
   (`average_vector()` in the script mirrors `averageVector()` in
   `app.js`).
3. **Why this isn't circular**: genre-level signal is a lossy predictor of
   one person's specific-movie taste. The model cannot reach 100% accuracy
   even at zero noise — it can only do meaningfully better than guessing,
   if the embedding space is doing real work.
4. **Baselines**:
   - *popularity* — always predict TMDB's default poster, ignoring the
     member entirely.
   - *random* — uniform over that title's variants.
   - *same-genre-random* — one **unaveraged** poster from the anchor's
     genre (not the 3-sample average), standing in for "correct genre,
     but none of the averaging step." This isolates whether averaging
     three liked posters adds anything beyond just being in the right
     genre at all.
5. 300 synthetic members x 10 held-out titles each = up to 3,000 scored
   decisions per noise level, swept across `sigma in [0, 0.05, 0.1, 0.2, 0.4]`.

## Result (actual run, 2026-09-01, catalog of 128 titles / 614 posters)

| noise σ | content model (3-avg) | same-genre-random (1, unaveraged) | popularity baseline | random baseline |
|---:|---:|---:|---:|---:|
| 0.00 | **0.486** | 0.415 | 0.218 | 0.194 |
| 0.05 | 0.346 | 0.314 | 0.223 | 0.214 |
| 0.10 | 0.284 | 0.270 | 0.209 | 0.207 |
| 0.20 | 0.266 | 0.243 | 0.213 | 0.218 |
| 0.40 | 0.220 | 0.224 | 0.223 | 0.206 |

Reproduce with: `python scripts/validate_ranking.py` (needs
`docs/data/titles.json`, already committed — no TMDB key required).

## Reading the result honestly

The content model more than doubles the popularity baseline's accuracy at
zero noise (0.486 vs 0.218), but the same-genre-random baseline is what
explains *why*: it scores 0.415 on its own — almost as high as the full
content model, and both are worlds above popularity. That means:

- **Most of the win over popularity is just being in the right genre**,
  not the averaging step. A single, unaveraged same-genre poster already
  recovers most of the signal. This makes sense in hindsight: posters
  within a genre cluster visually (see `RESEARCH.md`'s embedding sanity
  check), so *any* same-genre poster is already much closer to a
  same-genre anchor than an arbitrary popular title is.
- **Averaging three liked posters does add something real, but it's a
  second-order effect, not the main event.** The content model beats
  same-genre-random consistently at low-to-moderate noise — by about 7
  points at σ=0 (0.486 vs 0.415), 3 points at σ=0.05, 1.4 points at
  σ=0.10, 2 points at σ=0.20 — before both collapse into the noise floor
  together by σ=0.40 (0.220 vs 0.224, indistinguishable). A consistent,
  if modest, edge across four noise levels is more convincing than a
  single lucky number would be, but it's honest to say: **averaging is a
  refinement on top of genre-matching, not the primary source of the
  ranking's advantage over a non-personalized default.**
- **As noise rises, both content model and same-genre-random degrade
  toward the popularity/random baselines**, while popularity itself stays
  flat (~0.21–0.22) because it never looks at the ground-truth signal at
  all. That shared monotonic collapse is still the strongest evidence
  here that both mechanisms are tracking a real signal rather than
  reporting noise — a spurious result wouldn't degrade this smoothly.
- **What this does NOT prove**: that real Netflix (or any real) viewers'
  preferences behave like "similarity to an anchor movie plus Gaussian
  noise," or that this ranking would show any engagement lift with actual
  humans. The ground truth here is manufactured, not observed. This is a
  necessary sanity check, not a substitute for the online A/B test that
  would be required to make a real claim.

## Honest limits, for the next person who reads this

- Single synthetic-preference model (anchor + Gaussian noise). A more
  rigorous version would try multiple ground-truth generating processes
  (e.g., multi-title anchors, non-Gaussian noise, genre-blend members) and
  check the result is robust across all of them, not just one.
- The same-genre-random baseline shows most of the demo's "personalized
  vs. default" advantage is really "genre-matched vs. genre-agnostic,"
  with individual-level averaging contributing a smaller, second-order
  effect. Worth a follow-up: does that averaging edge grow with more
  liked-seed samples (5, 10) instead of 3? If it doesn't grow much, that
  would say individual-level signal is close to exhausted at genre
  granularity in this embedding space, which would be a real limit on how
  "personalized" (vs. "genre-filtered") this mechanism actually is.
- 128-title catalog, one canvas type — small enough that noise in which
  titles happen to get sampled could matter; the `SEED = 42` makes this
  run reproducible but not necessarily representative of every possible
  catalog draw.
