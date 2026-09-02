"""Compute CLIP embeddings for every cached poster image.

Usage:
    python scripts/embed_posters.py

Reads data/catalog.json (from fetch_catalog.py). Writes data/embeddings.json:
    { "<movie_id>/<poster_index>": [float, ...] }  # normalized 512-d CLIP vector
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def main() -> None:
    catalog = json.loads((DATA_DIR / "catalog.json").read_text())
    model = SentenceTransformer("clip-ViT-B-32")

    embeddings: dict[str, list[float]] = {}
    for title in catalog:
        for i, poster_rel_path in enumerate(title["posters"]):
            image = Image.open(ROOT / poster_rel_path).convert("RGB")
            vector = model.encode(image, normalize_embeddings=True)
            embeddings[f"{title['id']}/{i}"] = np.asarray(vector, dtype=np.float32).round(5).tolist()
        print(f"Embedded: {title['title']}")

    (DATA_DIR / "embeddings.json").write_text(json.dumps(embeddings))
    print(f"Saved {len(embeddings)} poster embeddings to data/embeddings.json")


if __name__ == "__main__":
    main()
