"""Join catalog.json + embeddings.json into the flat JSON the front end reads.

Usage:
    python scripts/build_static_data.py

Writes docs/data/titles.json with each poster's CLIP vector inlined, so
ranking happens with plain JS dot products in the browser -- no model, no
server, at runtime. Also copies poster images into docs/posters/ so the
static site (served from docs/ via GitHub Pages) can serve them directly.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
WEB_DIR = ROOT / "docs"


def main() -> None:
    catalog = json.loads((DATA_DIR / "catalog.json").read_text())
    embeddings = json.loads((DATA_DIR / "embeddings.json").read_text())

    titles = []
    for title in catalog:
        posters = []
        for i, poster_rel_path in enumerate(title["posters"]):
            key = f"{title['id']}/{i}"
            if key not in embeddings:
                continue
            posters.append(
                {
                    "url": poster_rel_path.replace("data/posters", "posters"),
                    "embedding": embeddings[key],
                    # TMDB's own default ordering (index 0) stands in for
                    # "the generic, non-personalized pick" throughout the demo.
                    "isDefault": i == 0,
                }
            )
        if not posters:
            continue
        titles.append(
            {
                "id": title["id"],
                "title": title["title"],
                "genre": title["genre"],
                "overview": title["overview"],
                "popularity": title.get("popularity", 0),
                "posters": posters,
            }
        )

    (WEB_DIR / "data").mkdir(parents=True, exist_ok=True)
    (WEB_DIR / "data" / "titles.json").write_text(json.dumps(titles))
    print(f"Saved {len(titles)} titles to docs/data/titles.json")

    web_posters = WEB_DIR / "posters"
    if web_posters.exists():
        shutil.rmtree(web_posters)
    shutil.copytree(DATA_DIR / "posters", web_posters)
    print("Copied posters into docs/posters/")


if __name__ == "__main__":
    main()
