#!/usr/bin/env python3
"""Builds the blog. Source posts live in posts/*.md; output is plain HTML.

Post format (front matter between --- lines, then Markdown):

    ---
    title: Day 1 — Back under the bar
    date: 2026-11-16
    type: daily          # daily | weekly
    summary: One line shown on the home page.
    ---
    Markdown body...

Run:  python3 build.py
"""
import datetime as dt
import hashlib
import html
import pathlib
import re
import shutil

import markdown

ROOT = pathlib.Path(__file__).parent
POSTS = ROOT / "posts"
OUT = ROOT / "p"
SITE_TITLE = "Iron Protocol"
QUOTE = "I can accept failure, everyone fails at something. But I can\u2019t accept not trying."
QUOTE_BY = "Michael Jordan"
SITE_TAG = "Looking after myself for the people who love me. Learning to love myself on the way."


def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise SystemExit(f"{path.name}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.split("  #")[0].strip()
    meta["date"] = dt.date.fromisoformat(meta["date"])
    meta.setdefault("type", "daily")
    meta.setdefault("summary", "")
    meta.setdefault("tagline", "")
    meta["stats"] = [
        tuple(x.strip() for x in s.split("=", 1))
        for s in meta.get("stats", "").split("|") if "=" in s
    ]
    meta["slug"] = path.stem
    meta["body"] = markdown.markdown(
        m.group(2), extensions=["tables", "sane_lists", "smarty"]
    )
    return meta


def nice_date(d):
    return f"{d:%A} {d.day} {d:%B %Y}"


def page(title, body, depth):
    up = "../" * depth
    ver = hashlib.md5((ROOT / "style.css").read_bytes()).hexdigest()[:8]
    t = html.escape(title)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta name="referrer" content="no-referrer">
<title>{t}</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><rect width='16' height='16' rx='3' fill='%23b4532a'/></svg>">
<link rel="stylesheet" href="{up}style.css?v={ver}">
</head>
<body>
<header class="site"><a href="{up}index.html" class="brand">{SITE_TITLE}</a></header>
<main>
{body}
</main>
<footer class="site">Written anonymously.</footer>
</body>
</html>
"""


def label(kind):
    return '<span class="kind weekly">Weekly</span>' if kind == "weekly" else '<span class="kind">Daily</span>'


def build():
    posts = sorted((parse(p) for p in POSTS.glob("*.md")), key=lambda p: (p["date"], p["type"] == "weekly"), reverse=True)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    for i, p in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        nav = '<nav class="pager">'
        nav += f'<a href="../{older["slug"]}/index.html">← {html.escape(older["title"])}</a>' if older else "<span></span>"
        nav += f'<a href="../{newer["slug"]}/index.html">{html.escape(newer["title"])} →</a>' if newer else "<span></span>"
        nav += "</nav>"
        tag = f'<p class="tagline">{html.escape(p["tagline"])}</p>' if p["tagline"] else ""
        stats = ""
        if p["stats"]:
            stats = '<dl class="stats">' + "".join(
                f'<div><dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd></div>' for k, v in p["stats"]
            ) + "</dl>"
        body = f"""<article class="post {p['type']}">
<p class="meta">{label(p['type'])}<time datetime="{p['date']}">{nice_date(p['date'])}</time></p>
<h1>{html.escape(p['title'])}</h1>
{tag}{stats}<div class="prose">{p['body']}</div>
</article>
{nav}"""
        d = OUT / p["slug"]
        d.mkdir()
        (d / "index.html").write_text(page(f"{p['title']} · {SITE_TITLE}", body, 2), encoding="utf-8")

    items, month = [], None
    for p in posts:
        m = f"{p['date']:%B %Y}"
        if m != month:
            if month:
                items.append("</ol>")
            items.append(f'<h2 class="month">{m}</h2><ol class="list">')
            month = m
        line = p["tagline"] or p["summary"]
        summ = f'<p class="summary">{html.escape(line)}</p>' if line else ""
        items.append(
            f'<li class="{p["type"]}"><a href="p/{p["slug"]}/index.html">'
            f'<p class="meta">{label(p["type"])}<time datetime="{p["date"]}">{nice_date(p["date"])}</time></p>'
            f'<h3>{html.escape(p["title"])}</h3>{summ}</a></li>'
        )
    if month:
        items.append("</ol>")
    if not posts:
        items.append('<p class="empty">Day one starts soon.</p>')
    hero = (
        '<section class="hero"><img src="img/hero.jpg" srcset="img/hero-900.jpg 900w, img/hero.jpg 1600w" '
        'sizes="(max-width: 680px) 100vw, 680px" width="1600" height="893" alt="Silhouette doing a pull-up on a beach at sunset">'
        f'<div class="hero-text"><h1>{SITE_TITLE}</h1><blockquote class="mantra"><p>\u201c{QUOTE}\u201d</p><cite>{QUOTE_BY}</cite></blockquote></div></section>'
    )
    home = hero + f'<section class="intro"><p>{SITE_TAG}</p></section>\n' + "\n".join(items)
    (ROOT / "index.html").write_text(page(SITE_TITLE, home, 0), encoding="utf-8")
    (ROOT / "404.html").write_text(page("Not found", '<section class="intro"><h1>Not here.</h1><p><a href="/">Back to the log</a></p></section>', 0).replace('href="style.css', 'href="/style.css').replace('href="index.html"', 'href="/"'), encoding="utf-8")
    print(f"Built {len(posts)} post(s).")


if __name__ == "__main__":
    build()
