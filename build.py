#!/usr/bin/env python3
"""Build the published Harness Papers Daily site.

Only papers with relevance 4 or 5 are published.
Source notes stay in _analyses so lower-tier intake notes can be re-reviewed later.
The public reader uses one paper.html page plus papers-data.js. Mermaid diagrams
render in the browser.
"""
import os, re, json, html, shutil
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "_analyses")
START = date(2026, 9, 30)
MIN_RELEVANCE = 4
SCHED_PATH = os.path.join(ROOT, "schedule.json")

STYLE = r"""
:root {
  --bg:#0d1117; --panel:#161b22; --panel2:#0f141b; --border:#30363d;
  --fg:#e6edf3; --muted:#8b949e; --accent:#58a6ff; --green:#3fb950;
}
* { box-sizing:border-box; }
body {
  margin:0; background:var(--bg); color:var(--fg);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  line-height:1.68;
}
a { color:var(--accent); text-decoration:none; }
a:hover { text-decoration:underline; }
.wrap { max-width:940px; margin:0 auto; padding:0 22px 64px; }
header.site { padding:28px 0 18px; border-bottom:1px solid var(--border); margin-bottom:26px; }
.brand { color:var(--muted); font-size:13px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }
h1 { font-size:32px; line-height:1.2; margin:8px 0; }
h2 { margin-top:34px; font-size:22px; padding-bottom:8px; border-bottom:1px solid var(--border); }
h3 { font-size:17px; margin-top:26px; color:var(--accent); }
p { max-width:78ch; }
.meta, .muted { color:var(--muted); font-size:14px; }
.card {
  background:var(--panel); border:1px solid var(--border); border-radius:12px;
  padding:20px 22px; margin:16px 0;
}
.card.core { border-color:#f778ba55; }
.card.high { border-color:#ffa65755; }
.badge {
  display:inline-block; border:1px solid var(--border); border-radius:999px;
  padding:2px 10px; font-size:12px; font-weight:700; margin-right:8px;
}
.badge.rel5 { color:#f778ba; border-color:#f778ba55; }
.badge.rel4 { color:#ffa657; border-color:#ffa65755; }
.kicker { color:var(--green); font-weight:700; font-size:13px; letter-spacing:.08em; text-transform:uppercase; }
table { width:100%; border-collapse:collapse; font-size:14px; }
th, td { text-align:left; padding:10px; border-bottom:1px solid var(--border); vertical-align:top; }
tr.today td { background:#3fb95014; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:12px; }
.grid .card { margin:0; }
.grid h3 { margin:0 0 8px; color:var(--fg); }
.reader { background:var(--panel); border:1px solid var(--border); border-radius:12px; padding:24px; }
.reader li { margin:6px 0; }
.reader code { background:var(--panel2); border:1px solid var(--border); border-radius:6px; padding:1px 6px; }
.mermaid {
  background:var(--panel2); border:1px solid var(--border); border-radius:10px;
  padding:16px; margin:18px 0; overflow-x:auto;
}
.nav { display:flex; justify-content:space-between; gap:16px; margin-top:28px; padding-top:18px; border-top:1px solid var(--border); }
footer { margin-top:48px; padding-top:16px; border-top:1px solid var(--border); color:var(--muted); font-size:13px; }
@media (max-width:700px) {
  table .datecol { display:none; }
  th, td { padding:8px 6px; }
  .nav { flex-direction:column; }
}
"""

def parse_md(path):
    raw = open(path, encoding="utf-8").read()
    fm, body = {}, raw
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
        body = m.group(2).strip()
    return fm, body

papers = []
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".md"):
        continue
    fm, body = parse_md(os.path.join(SRC, fn))
    relevance = int(fm.get("relevance", "1"))
    if relevance < MIN_RELEVANCE:
        continue
    papers.append({
        "id": fm.get("arxiv_id", fn[:-3]),
        "title": fm.get("title", fn[:-3]),
        "authors": fm.get("authors", "Unknown"),
        "published": fm.get("published", ""),
        "url": fm.get("arxiv_url", "https://arxiv.org/abs/" + fn[:-3]),
        "relevance": relevance,
        "body": body,
    })

old_sched = {}
if os.path.exists(SCHED_PATH):
    try:
        old_sched = json.load(open(SCHED_PATH, encoding="utf-8"))
    except Exception:
        old_sched = {}

papers.sort(key=lambda p: (old_sched.get(p["id"], 10**9), -p["relevance"], p["published"], p["id"]))
for i, p in enumerate(papers, start=1):
    p["day"] = i
    p["date"] = (START + timedelta(days=i - 1)).isoformat()

new_sched = {p["id"]: p["day"] for p in papers}
with open(SCHED_PATH, "w", encoding="utf-8") as f:
    json.dump(new_sched, f, indent=1)
    f.write("\n")

# The new reader does not need one generated HTML file per paper.
legacy_dir = os.path.join(ROOT, "papers")
if os.path.isdir(legacy_dir):
    for fn in os.listdir(legacy_dir):
        if fn.endswith(".html"):
            os.remove(os.path.join(legacy_dir, fn))

with open(os.path.join(ROOT, "papers-data.js"), "w", encoding="utf-8") as f:
    f.write("window.PAPERS = ")
    json.dump(papers, f, ensure_ascii=False)
    f.write(";\n")

labels = {5:"core mechanism", 4:"highly relevant"}
today = date.today()
rows = []
cards = []
for p in papers:
    pdate = date.fromisoformat(p["date"])
    cls = "today" if pdate == today else ""
    link = "paper.html?id=" + p["id"]
    badge = f'<span class="badge rel{p["relevance"]}">{labels[p["relevance"]]}</span>'
    rows.append(
        f'<tr class="{cls}"><td><strong>Day {p["day"]}</strong></td>'
        f'<td class="datecol">{pdate.strftime("%a %b %d")}</td>'
        f'<td><a href="{link}">{html.escape(p["title"])}</a></td><td>{badge}</td></tr>'
    )
    cards.append(
        f'<div class="card {"core" if p["relevance"] == 5 else "high"}">'
        f'<h3><a href="{link}">{html.escape(p["title"])}</a></h3>'
        f'<div class="meta">{html.escape(p["authors"].split(",")[0])} et al.</div>'
        f'<p>{badge}</p></div>'
    )

first = papers[0]
index_html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Harness Papers Daily</title><style>{STYLE}</style></head>
<body><div class="wrap">
<header class="site"><div class="brand">Harness Papers Daily</div>
<h1>Core papers for RHEvolution</h1>
<p class="muted">A focused reading set on agent-harness optimization and adaptive decomposition.</p></header>
<p>This site publishes only papers already labeled <strong>core mechanism</strong> or <strong>highly relevant</strong>.
Each explanation starts with the true novelty, then gives an implementation-oriented loop, experiment details, concrete results, ablations, limits, and RHEvolution takeaways in simple technical English.</p>
<div class="card core"><div class="kicker">Start here · Day 1</div>
<h3><a href="paper.html?id={first["id"]}">{html.escape(first["title"])}</a></h3>
<p>{labels[first["relevance"]]}. This paper is the clearest starting point for component-level harness evolution.</p></div>
<h2>Reading schedule · {len(papers)} papers</h2>
<table><tr><th>Day</th><th class="datecol">Date</th><th>Paper</th><th>Relevance</th></tr>{''.join(rows)}</table>
<h2>Browse the focused set</h2><div class="grid">{''.join(cards)}</div>
<footer>Only relevance 4–5 papers are published. Lower-tier intake notes are not shown on the site.</footer>
</div></body></html>"""
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(index_html)

# paper.html is a hand-maintained dynamic reader. Do not overwrite it here.\n\nprint(f"built focused site with {len(papers)} papers")
