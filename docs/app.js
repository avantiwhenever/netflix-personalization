// All personalization math happens here, client-side, over the precomputed
// CLIP vectors in data/titles.json. Vectors are already L2-normalized, so
// cosine similarity is just a dot product.

const PICKER_SAMPLE_SIZE = 30;

let titles = [];
let tasteVector = null;

function dot(a, b) {
  let sum = 0;
  for (let i = 0; i < a.length; i++) sum += a[i] * b[i];
  return sum;
}

function averageVector(vectors) {
  const dim = vectors[0].length;
  const avg = new Array(dim).fill(0);
  for (const v of vectors) for (let i = 0; i < dim; i++) avg[i] += v[i];
  for (let i = 0; i < dim; i++) avg[i] /= vectors.length;
  // Re-normalize so scores stay comparable to individual poster vectors.
  const norm = Math.sqrt(avg.reduce((s, x) => s + x * x, 0));
  return avg.map((x) => x / norm);
}

function defaultPoster(title) {
  return title.posters.find((p) => p.isDefault) || title.posters[0];
}

function buildPersonas() {
  const byGenre = {};
  for (const t of titles) {
    (byGenre[t.genre] ||= []).push(t);
  }

  const container = document.getElementById("personas");
  for (const [genre, group] of Object.entries(byGenre)) {
    const seeds = [...group]
      .sort((a, b) => b.popularity - a.popularity)
      .slice(0, 5)
      .map((t) => defaultPoster(t).embedding);
    if (seeds.length === 0) continue;

    const btn = document.createElement("button");
    btn.className = "persona-btn";
    btn.textContent = genre;
    btn.addEventListener("click", () => {
      document.querySelectorAll(".persona-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      document.querySelectorAll(".poster-card.selected").forEach((c) => c.classList.remove("selected"));
      setTasteVector(averageVector(seeds), `"${genre}" persona (top 5 titles in that genre)`);
    });
    container.appendChild(btn);
  }
}

function buildPickerGrid() {
  const grid = document.getElementById("picker-grid");
  const shuffled = [...titles].sort(() => Math.random() - 0.5).slice(0, PICKER_SAMPLE_SIZE);

  const selected = new Map(); // titleId -> embedding

  for (const t of shuffled) {
    const poster = defaultPoster(t);
    const card = document.createElement("div");
    card.className = "poster-card";
    card.title = t.title;
    card.innerHTML = `<img src="${poster.url}" alt="${t.title} poster" loading="lazy" />`;
    card.addEventListener("click", () => {
      document.querySelectorAll(".persona-btn").forEach((b) => b.classList.remove("active"));
      card.classList.toggle("selected");
      if (card.classList.contains("selected")) {
        selected.set(t.id, poster.embedding);
      } else {
        selected.delete(t.id);
      }
      const rankButton = document.getElementById("rank-button");
      rankButton.disabled = selected.size === 0;
      document.getElementById("profile-status").textContent = selected.size
        ? `${selected.size} poster(s) selected`
        : "";
    });
    grid.appendChild(card);
  }

  document.getElementById("rank-button").addEventListener("click", () => {
    if (selected.size === 0) return;
    setTasteVector(averageVector([...selected.values()]), `${selected.size} hand-picked poster(s)`);
  });
}

function setTasteVector(vector, description) {
  tasteVector = vector;
  document.getElementById("profile-status").textContent = `Taste profile: ${description}`;
  renderResults();
}

function renderResults() {
  const resultsSection = document.getElementById("results");
  const grid = document.getElementById("results-grid");
  grid.innerHTML = "";
  resultsSection.hidden = false;

  for (const t of titles) {
    const scored = t.posters
      .map((p) => ({ ...p, score: dot(tasteVector, p.embedding) }))
      .sort((a, b) => b.score - a.score);

    const top = scored[0];
    const def = defaultPoster(t);
    const sameAsDefault = top.url === def.url;

    const card = document.createElement("div");
    card.className = "result-card";

    const compareHtml = sameAsDefault
      ? `<div class="compare">
          <figure class="is-same">
            <img src="${top.url}" alt="${t.title} poster" loading="lazy" />
            <figcaption>Personalized pick = default poster for this profile (score ${top.score.toFixed(3)})</figcaption>
          </figure>
        </div>`
      : `<div class="compare">
          <figure>
            <img src="${top.url}" alt="${t.title} personalized poster" loading="lazy" />
            <figcaption>For you — <span class="score">${top.score.toFixed(3)}</span></figcaption>
          </figure>
          <figure>
            <img src="${def.url}" alt="${t.title} default poster" loading="lazy" />
            <figcaption>Default — <span class="score">${dot(tasteVector, def.embedding).toFixed(3)}</span></figcaption>
          </figure>
        </div>`;

    card.innerHTML = `
      <h3>${t.title}</h3>
      <div class="genre">${t.genre}</div>
      ${compareHtml}
    `;
    grid.appendChild(card);
  }
}

async function init() {
  try {
    const resp = await fetch("data/titles.json");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    titles = await resp.json();
  } catch (err) {
    document.getElementById("loading").textContent =
      "Couldn't load data/titles.json — run the data pipeline first (see HOWTO.md).";
    return;
  }

  document.getElementById("loading").hidden = true;
  buildPersonas();
  buildPickerGrid();
}

init();
