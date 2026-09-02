"""Fetch a curated, multi-genre movie catalog + poster variants from TMDB.

Usage:
    python scripts/fetch_catalog.py

Requires TMDB_API_KEY in a .env file (see .env.example / HOWTO.md).
"""
import json
import time
from pathlib import Path

from dotenv import load_dotenv
import os
import requests

load_dotenv()

API_KEY = os.environ.get("TMDB_API_KEY")
if not API_KEY:
    raise SystemExit("Set TMDB_API_KEY in a .env file (see .env.example) before running this.")

BASE = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
POSTERS_DIR = DATA_DIR / "posters"

# TMDB genre_id -> label. Chosen to span visually distinct poster styles so
# different taste profiles produce visibly different personalized rankings.
GENRES = {
    16: "Animated & Family",
    27: "Horror",
    53: "Thriller",
    10749: "Romance",
    878: "Sci-Fi",
    18: "Drama",
    28: "Action",
    35: "Comedy",
}

TITLES_PER_GENRE = 25
MAX_POSTERS_PER_TITLE = 5
PAGES_PER_GENRE = 2  # 20 results/page


def discover_titles(genre_id: str) -> list[dict]:
    titles = []
    for page in range(1, PAGES_PER_GENRE + 1):
        resp = requests.get(
            f"{BASE}/discover/movie",
            params={
                "api_key": API_KEY,
                "with_genres": genre_id,
                "sort_by": "popularity.desc",
                "page": page,
                "include_adult": "false",
            },
            timeout=15,
        )
        resp.raise_for_status()
        titles.extend(resp.json().get("results", []))
    return titles


def fetch_poster_paths(movie_id: int) -> list[str]:
    resp = requests.get(
        f"{BASE}/movie/{movie_id}/images",
        params={"api_key": API_KEY},
        timeout=15,
    )
    resp.raise_for_status()
    posters = resp.json().get("posters", [])
    # Prefer English/language-neutral posters, then whatever's left.
    posters.sort(key=lambda p: 0 if p.get("iso_639_1") in (None, "en") else 1)
    return [p["file_path"] for p in posters[:MAX_POSTERS_PER_TITLE]]


def download(file_path: str, dest: Path) -> None:
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(f"{IMG_BASE}{file_path}", timeout=30)
    resp.raise_for_status()
    dest.write_bytes(resp.content)


def main() -> None:
    catalog: dict[int, dict] = {}

    for genre_id, genre_label in GENRES.items():
        print(f"Discovering: {genre_label}")
        results = discover_titles(str(genre_id))[:TITLES_PER_GENRE]
        for movie in results:
            movie_id = movie["id"]
            if movie_id in catalog:
                continue

            poster_paths = fetch_poster_paths(movie_id)
            if not poster_paths:
                continue

            local_posters = []
            for i, file_path in enumerate(poster_paths):
                dest = POSTERS_DIR / str(movie_id) / f"{i}.jpg"
                download(file_path, dest)
                local_posters.append(str(dest.relative_to(ROOT)))

            catalog[movie_id] = {
                "id": movie_id,
                "title": movie["title"],
                "overview": movie.get("overview", ""),
                "genre": genre_label,
                "popularity": movie.get("popularity", 0),
                "posters": local_posters,
            }
            time.sleep(0.05)  # be polite to the API

    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "catalog.json").write_text(json.dumps(list(catalog.values()), indent=2))
    print(f"Saved {len(catalog)} titles to data/catalog.json")


if __name__ == "__main__":
    main()
