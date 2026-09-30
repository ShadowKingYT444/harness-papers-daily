#!/usr/bin/env python3
"""Build a static GitHub-Pages-ready site from _analyses/*.md.

Output: site/ directory with index.html + papers/<id>.html + style.css
Daily digest: papers ordered by (relevance desc, published desc), one per day,
starting 2026-09-30.
"""
import os, re, html
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = "/home/hatch/workspace/harness-papers-daily/_analyses"
OUT = "/home/hatch/workspace/harness-papers-daily"
PAPERS_OUT = os.path.join(OUT, "papers")
START = date(2026, 9, 30)

# ---------- minimal markdown -> html ----------
def md_inline(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s

def md_block(text):
    out, para, in_list = [], [], False
    def flush_para():
        if para:
            out.append("<p>" + " ".join(md_inline(l) for l in para) + "</p>")
            para.clear()
    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False
    for line in text.split("\n"):
        line = line.rstrip()
        if not line.strip():
            flush_para(); close_list(); continue
        m = re.match(r"^#{2,3}\s+(.*)", line)
        if m:
            flush_para(); close_list()
            lvl = 2 if line.startswith("## ") else 3
            out.append(f"<h{lvl}>{md_inline(m.group(1))}</h{lvl}>")
            continue
        if re.match(r"^[-*]\s+", line):
            flush_para()
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append("<li>" + md_inline(re.sub(r"^[-*]\s+", "", line)) + "</li>")
            continue
        if re.match(r"^\d+\.\s+", line):
            flush_para()
            out.append("<p class='num'>" + md_inline(line) + "</p>")
            continue
        para.append(line)
    flush_para(); close_list()
    return "\n".join(out)

def parse(path):
    raw = open(path, encoding="utf-8").read()
    fm, body = {}, raw
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
        body = m.group(2)
    return fm, body

# ---------- load papers ----------
papers = []
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".md"):
        continue
    fm, body = parse(os.path.join(SRC, fn))
    papers.append({
        "id": fm.get("arxiv_id", fn[:-3]),
        "title": fm.get("title", fn[:-3]),
        "authors": fm.get("authors", "Unknown"),
        "published": fm.get("published", ""),
        "url": fm.get("arxiv_url", "https://arxiv.org/abs/" + fn[:-3]),
        "relevance": int(fm.get("relevance", "1")),
        "body": body,
    })

# digest order: relevance desc, then published desc
papers.sort(key=lambda p: (-p["relevance"], p["published"]), reverse=False)
for i, p in enumerate(papers):
    p["day"] = i + 1
    p["date"] = START + timedelta(days=i)

os.makedirs(PAPERS_OUT, exist_ok=True)

# ---------- shared chrome ----------
CSS = open(os.path.join(ROOT, "assets_stub.css")).read() if os.path.exists(os.path.join(ROOT, "assets_stub.css")) else ""

STYLE = """
:root { --bg:#0d1117; --panel:#161b22; --border:#30363d; --fg:#e6edf3; --muted:#8b949e;
        --accent:#58a6ff; --accent2:#3fb950; --warn:#d29922; }
* { box-sizing:border-box; }
body { background:var(--bg); color:var(--fg); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
       margin:0; line-height:1.65; }
a { color:var(--accent); text-decoration:none; } a:hover { text-decoration:underline; }
.wrap { max-width:860px; margin:0 auto; padding:0 20px 60px; }
header.site { border-bottom:1px solid var(--border); padding:28px 0 18px; margin-bottom:28px; }
header.site .brand { font-size:15px; color:var(--muted); letter-spacing:.12em; text-transform:uppercase; }
header.site h1 { margin:8px 0 4px; font-size:30px; }
header.site p { color:var(--muted); margin:6px 0 0; max-width:640px; }
.card { background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:20px 22px; margin:16px 0; }
.card.today { border-color:var(--accent2); }
.badge { display:inline-block; font-size:12px; font-weight:600; padding:2px 10px; border-radius:20px;
         border:1px solid var(--border); color:var(--muted); margin-right:8px; }
.badge.rel5 { color:#f778ba; border-color:#f778ba55; } .badge.rel4 { color:#ffa657; border-color:#ffa65755; }
.badge.rel3 { color:var(--accent); border-color:#58a6ff55; } .badge.rel2,.badge.rel1 { color:var(--muted); }
.meta { color:var(--muted); font-size:14px; }
h2 { margin-top:34px; font-size:22px; border-bottom:1px solid var(--border); padding-bottom:8px; }
h3 { font-size:17px; margin-top:26px; color:var(--accent); }
code { background:#0d1117; border:1px solid var(--border); border-radius:6px; padding:1px 6px; font-size:13px; }
pre code { display:block; padding:14px; overflow-x:auto; }
table.sched { width:100%; border-collapse:collapse; font-size:14px; }
table.sched th, table.sched td { text-align:left; padding:9px 10px; border-bottom:1px solid var(--border); }
table.sched tr.today td { background:#3fb95014; }
table.sched tr.past td { color:var(--muted); }
.nav { display:flex; justify-content:space-between; margin-top:34px; padding-top:18px; border-top:1px solid var(--border); }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:12px; }
.grid .card { margin:0; padding:14px 16px; } .grid .card h4 { margin:0 0 6px; font-size:15px; }
.grid .card .meta { font-size:12.5px; }
footer { margin-top:50px; color:var(--muted); font-size:13px; border-top:1px solid var(--border); padding-top:16px; }
.kicker { color:var(--accent2); font-size:13px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; }
"""

def page(title, body_html, extra_head=""):
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — Harness Papers Daily</title>
<style>{STYLE}</style>{extra_head}</head>
<body><div class="wrap">
<header class="site">
<div class="brand"><a href="../index.html" style="color:inherit">Harness Papers Daily</a></div>
<h1>{html.escape(title)}</h1>
</header>
{body_html}
<footer>Deep-dive notes on agent-harness optimization research, one paper a day.
Analyses are study notes, not affiliated with the papers' authors. Links point to arXiv.</footer>
</div></body></html>"""

def rel_badge(r):
    labels = {5: "core mechanism", 4: "highly relevant", 3: "relevant", 2: "context", 1: "background"}
    return f'<span class="badge rel{r}">{labels.get(r,"")}</span>'

# ---------- per-paper pages ----------
for i, p in enumerate(papers):
    prev_l = f'<a href="{papers[i-1]["id"]}.html">← Day {papers[i-1]["day"]}: {html.escape(papers[i-1]["title"][:60])}</a>' if i > 0 else ""
    next_l = f'<a href="{papers[i+1]["id"]}.html">Day {papers[i+1]["day"]}: {html.escape(papers[i+1]["title"][:60])} →</a>' if i < len(papers)-1 else ""
    body = f"""
<div class="kicker">Day {p['day']} · {p['date'].strftime('%b %d, %Y')}</div>
<h1 style="margin-top:6px">{html.escape(p['title'])}</h1>
<p class="meta">{html.escape(p['authors'])} · published {p['published']} · <a href="{p['url']}">arXiv:{p['id']}</a></p>
<p>{rel_badge(p['relevance'])}</p>
<div class="card">{md_block(p['body'])}</div>
<div class="nav"><span>{prev_l}</span><span><a href="../index.html">All papers</a></span><span>{next_l}</span></div>
"""
    open(os.path.join(PAPERS_OUT, p["id"] + ".html"), "w", encoding="utf-8").write(page(p["title"], body))

# ---------- index ----------
today_idx = None
sched_rows = []
for p in papers:
    cls = ""
    if p["date"] == date.today():
        cls, today_idx = "today", p
    elif p["date"] < date.today():
        cls = "past"
    sched_rows.append(
        f'<tr class="{cls}"><td><strong>Day {p["day"]}</strong></td>'
        f'<td>{p["date"].strftime("%a %b %d")}</td>'
        f'<td><a href="papers/{p["id"]}.html">{html.escape(p["title"])}</a></td>'
        f'<td>{rel_badge(p["relevance"])}</td></tr>')

hero = ""
first = papers[0]
hero = f"""
<div class="card today">
<div class="kicker">Start here — Day 1 · {first['date'].strftime('%b %d, %Y')}</div>
<h3 style="margin:8px 0"><a href="papers/{first['id']}.html">{html.escape(first['title'])}</a></h3>
<p class="meta">{html.escape(first['authors'])} · <a href="{first['url']}">arXiv:{first['id']}</a></p>
<p>{rel_badge(first['relevance'])}</p>
</div>"""

grid = "\n".join(
    f'<div class="card"><h4><a href="papers/{p["id"]}.html">{html.escape(p["title"])}</a></h4>'
    f'<p class="meta">Day {p["day"]} · {html.escape(p["authors"].split(",")[0])} et al.</p>'
    f'<p>{rel_badge(p["relevance"])}</p></div>' for p in papers)

index_body = f"""
<p>39 papers on optimizing the code around AI agents — recursive self-improvement, harness
evolution, memory, routing, verification. One deep-dive per day, ordered by how directly each
paper speaks to <strong>adaptive decomposition</strong> (the agent discovering its own
decomposition of the harness, instead of evolving a fixed human-designed structure).</p>
{hero}
<h2>Reading schedule</h2>
<table class="sched"><tr><th>Day</th><th>Date</th><th>Paper</th><th>Relevance</th></tr>
{''.join(sched_rows)}
</table>
<h2>Browse all papers</h2>
<div class="grid">{grid}</div>
"""
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
    page("Harness Papers Daily", index_body).replace('../index.html', 'index.html'))

print(f"built {len(papers)} paper pages + index -> {OUT}")
