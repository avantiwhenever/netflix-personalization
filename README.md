# Netflix MAPS-Inspired Artwork Personalization Demo

A small, independent demo exploring the idea behind Netflix's
[MAPS: Multimodal Asset Personalization at Scale](https://netflixtechblog.com/maps-netflixs-multimodal-asset-personalization-at-scale-32f96320785e)
— personalizing which poster/artwork variant of a title gets shown to a
viewer, using CLIP image embeddings instead of ID-based interaction history.

**This project is not affiliated with, endorsed by, or using any data from
Netflix.** All movie data and poster images come from [TMDB](https://www.themoviedb.org/).
It's a learning/demo project, not a reproduction of Netflix's actual model,
data, or scale.

🔗 **Live:** [GitHub Pages](https://avantiwhenever.github.io/netflix-personalization/) ·
[Hugging Face Spaces](https://huggingface.co/spaces/avantiwhenever/netflix-personalization)

## What it does

1. Pull a curated catalog of titles + multiple poster variants per title
   from the TMDB API.
2. Compute CLIP embeddings for every poster image.
3. In the browser: build a "taste profile" (pick a few posters you like, or
   a preset persona) and see which poster variant per title gets ranked
   highest for you vs. a generic, non-personalized pick — with the
   similarity score shown as the explanation.

No login, no tracking, no backend — everything after the offline data-prep
step runs as static files.

## For developers

- [`HOWTO.md`](./HOWTO.md) — get a TMDB API key, run the data pipeline,
  serve the demo locally, deploy
- [`RESEARCH.md`](./RESEARCH.md) — notes on the source paper/blog post, why
  TMDB was chosen, and the simplifications this demo makes vs. the real
  Netflix system
- [`COMPARISON.md`](./COMPARISON.md) — component-by-component: what's a
  real reproduction of MAPS's mechanism, what's simplified, what's not
  implemented, each claim backed by a file/line reference
- [`VALIDATION.md`](./VALIDATION.md) — does the ranking mechanism actually
  beat naive baselines? A synthetic-proxy evaluation, with results and
  honest limits
- [`RECOMMENDATIONS.md`](./RECOMMENDATIONS.md) — architecture decisions and
  roadmap
- [`SECURITY.md`](./SECURITY.md) — API key handling, what's in place

## License

MIT — see [`LICENSE`](./LICENSE).
