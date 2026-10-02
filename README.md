# Harness Papers Daily

A focused reading site for research that directly supports **RHEvolution** and adaptive agent-harness decomposition.

The public site now publishes only papers already labeled:

- **core mechanism** (relevance 5)
- **highly relevant** (relevance 4)

Each published paper uses simple technical English. It defines important sub-concepts, shows a compact Mermaid diagram of the main loop, explains the mechanism step by step, and states both its relevance and its limits.

## Repository structure

- `index.html` — focused public reading schedule
- `paper.html` — shared paper reader
- `papers-data.js` — generated data for published papers
- `_analyses/` — source notes
- `schedule.json` — stable order for the published relevance 4–5 set
- `build.py` — rebuilds the site from `_analyses/`

Lower-tier intake notes can remain in `_analyses/` for later review, but they are not published.

Run:

```bash
python3 build.py
```

The builder uses repository-relative paths, filters to relevance 4–5, renumbers the reading schedule, removes legacy per-paper HTML pages, and creates the Mermaid-enabled reader.
