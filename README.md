# Harness Papers Daily

One deep-dive per day into research on optimizing **agent harnesses** — the code and
scaffolding around LLMs/agents (recursive self-improvement, harness evolution, memory,
routing, verification, cost control).

Each paper page covers: one-line summary, the problem, how the mechanism actually works,
key results, how it relates to **adaptive decomposition** (an agent discovering its own
decomposition of the harness rather than evolving a fixed human-designed structure), and
limits / open questions.

- `index.html` — reading schedule (one paper per day) + full index
- `papers/` — one page per paper
- `_analyses/` — source notes (markdown) for each paper
- `build.py` — regenerates the site from `_analyses/` (run: `python3 build.py`)

New papers are added automatically each morning from a daily arXiv sweep.
