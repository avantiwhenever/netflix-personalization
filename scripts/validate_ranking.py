"""Offline synthetic validation: does the CLIP-similarity ranker beat naive
baselines at predicting a *simulated* preferred poster variant?

This is NOT validation against real human behavior -- this project has no
interaction data. It's a synthetic proxy, in the same spirit as MAPS's
offline "predict the popularity-winning asset from embeddings alone" proxy
task, adapted for personalization: we manufacture a ground-truth preference
signal (with tunable noise) and check whether the production ranking
mechanism (docs/app.js's averageVector() + dot product, reimplemented here
identically) recovers it better than a popularity-only or random baseline.

Design, to avoid a circular/trivial result:
  - Each synthetic member's TRUE taste is anchored to one specific title's
    poster embedding (they secretly love one particular movie).
  - What the model actually gets to OBSERVE is a few posters from OTHER
    titles in that same genre -- genre-level signal, not the anchor itself.
    This mirrors the real product (personas are genre-level averages, not
    per-individual) and means the model can't win by memorizing the
    ground truth -- genre-level signal is a lossy predictor of one
    person's specific-movie taste, so 100% accuracy is not achievable even
    at zero injected noise.
  - Ground-truth "preferred variant" per held-out title = the poster
    variant most similar to the anchor, plus Gaussian noise (simulating
    real-world choice stochasticity). Sweeping the noise level shows
    whether accuracy degrades the way a real signal should -- collapsing
    toward the random baseline as noise grows, rather than being an
    artifact of one lucky run.

Baselines:
  - popularity: always predict TMDB's default poster, ignoring the member.
  - random: uniform over that title's variants.
  - same-genre-random: predict using a SINGLE random same-genre poster's
    embedding (no averaging, no 3-sample sampling) as the taste vector.
    This isolates the averaging step's contribution -- if the 3-sample
    averaged model doesn't clearly beat this, "genre membership" alone
    would be doing the work, not the averaging.

Usage:
    python scripts/validate_ranking.py

Reads docs/data/titles.json. Prints an accuracy table across noise levels.
No side effects / no writes.
"""
import json
import random
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent

NUM_MEMBERS = 300
LIKED_SEEDS_PER_MEMBER = 3        # mirrors the "hand-pick a few posters" flow in app.js
HELD_OUT_TITLES_PER_MEMBER = 10   # titles the model never observes for this member
NOISE_LEVELS = [0.0, 0.05, 0.1, 0.2, 0.4]
SEED = 42


def load_titles() -> list[dict]:
    return json.loads((ROOT / "docs" / "data" / "titles.json").read_text())


def default_embedding(title: dict) -> np.ndarray:
    for p in title["posters"]:
        if p["isDefault"]:
            return np.array(p["embedding"])
    return np.array(title["posters"][0]["embedding"])


def average_vector(vectors: list[np.ndarray]) -> np.ndarray:
    """Mirrors docs/app.js's averageVector(): mean, then re-normalize."""
    avg = np.mean(vectors, axis=0)
    return avg / np.linalg.norm(avg)


def main() -> None:
    titles = load_titles()
    multi_variant_titles = [t for t in titles if len(t["posters"]) >= 2]
    by_genre: dict[str, list[dict]] = {}
    for t in titles:
        by_genre.setdefault(t["genre"], []).append(t)

    rng = random.Random(SEED)
    np_rng = np.random.default_rng(SEED)

    print(f"Catalog: {len(titles)} titles, {len(multi_variant_titles)} with >=2 poster variants")
    print(
        f"Synthetic members: {NUM_MEMBERS}, liked seeds/member: {LIKED_SEEDS_PER_MEMBER}, "
        f"held-out titles/member: {HELD_OUT_TITLES_PER_MEMBER}\n"
    )
    header = (
        f"{'noise sigma':>11} | {'content model':>13} | {'same-genre random':>18} | "
        f"{'popularity baseline':>20} | {'random baseline':>16} | n"
    )
    print(header)
    print("-" * len(header))

    for sigma in NOISE_LEVELS:
        model_correct = same_genre_correct = popularity_correct = random_correct = total = 0

        for _ in range(NUM_MEMBERS):
            anchor = rng.choice(titles)
            anchor_vec = default_embedding(anchor)

            genre_pool = [t for t in by_genre[anchor["genre"]] if t["id"] != anchor["id"]]
            if len(genre_pool) < LIKED_SEEDS_PER_MEMBER:
                continue
            liked = rng.sample(genre_pool, LIKED_SEEDS_PER_MEMBER)
            observed_vector = average_vector([default_embedding(t) for t in liked])
            # Same-genre-random baseline: one unaveraged same-genre poster,
            # standing in for "genre membership alone, no averaging step."
            same_genre_vector = default_embedding(rng.choice(genre_pool))

            excluded_ids = {anchor["id"]} | {t["id"] for t in liked}
            candidates = [t for t in multi_variant_titles if t["id"] not in excluded_ids]
            if len(candidates) < HELD_OUT_TITLES_PER_MEMBER:
                continue
            held_out = rng.sample(candidates, HELD_OUT_TITLES_PER_MEMBER)

            for title in held_out:
                embeddings = np.array([p["embedding"] for p in title["posters"]])
                true_affinity = embeddings @ anchor_vec
                noisy_affinity = true_affinity + np_rng.normal(0, sigma, size=len(true_affinity))
                ground_truth_idx = int(np.argmax(noisy_affinity))

                model_idx = int(np.argmax(embeddings @ observed_vector))
                same_genre_idx = int(np.argmax(embeddings @ same_genre_vector))
                popularity_idx = next(i for i, p in enumerate(title["posters"]) if p["isDefault"])
                random_idx = rng.randrange(len(title["posters"]))

                model_correct += model_idx == ground_truth_idx
                same_genre_correct += same_genre_idx == ground_truth_idx
                popularity_correct += popularity_idx == ground_truth_idx
                random_correct += random_idx == ground_truth_idx
                total += 1

        print(
            f"{sigma:>11.2f} | {model_correct/total:>13.3f} | {same_genre_correct/total:>18.3f} | "
            f"{popularity_correct/total:>20.3f} | {random_correct/total:>16.3f} | {total}"
        )

    print("\nThis is a SYNTHETIC proxy, not validation against real user behavior.")
    print("See VALIDATION.md for the methodology and its limits.")


if __name__ == "__main__":
    main()
