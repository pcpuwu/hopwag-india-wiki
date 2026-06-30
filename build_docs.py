#!/usr/bin/env python3
"""Assemble the HoPWaG India notes + transcripts into a MkDocs docs/ tree + nav.
Source of truth stays in poopie/random/history of philosophy/; this only reads it.
Re-run any time the notes change, then `mkdocs gh-deploy --force`.
"""
import re
import shutil
from pathlib import Path

SRC = Path("/home/purubuntu/projects/poopie/random/history of philosophy")
NOTES = SRC / "notes"
TRANSCRIPTS = SRC / "transcripts" / "india"
OUT = Path(__file__).parent / "docs"

CODE = re.compile(r"hpi-(\d+)", re.I)
# chapter -> inclusive episode range (fallback if a note omits front-matter)
CHAPTERS = [
    ("Origins", range(1, 18)),
    ("Age of the Sūtra", range(18, 43)),
    ("Buddhists & Jains", range(43, 63)),
]
OFFICIAL = "https://historyofphilosophy.net/india"


def ep_num(name):
    m = CODE.search(name)
    return int(m.group(1)) if m else None


def chapter_for(n):
    for name, rng in CHAPTERS:
        if n in rng:
            return name
    return "India"


def parse_note(md_path):
    """-> (meta:dict, body:str). meta has episode/chapter/hosts(list)/guest."""
    text = md_path.read_text(encoding="utf-8")
    meta, body = {}, text
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        for line in fm.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = body.lstrip("\n")
    hosts = meta.get("hosts", "").strip().strip("[]")
    meta["hosts"] = [h.strip() for h in hosts.split(",") if h.strip()]
    meta["guest"] = meta.get("guest", "").strip()
    return meta, body


def clean_title(md_path):
    """-> just the episode title, e.g. 'Begin at the End: An Introduction…'."""
    for line in md_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            t = line[2:].strip().replace("HoPWaG India · ", "").replace('"', "")
            return re.sub(r"^Ep\s*\d+\s*[—-]\s*", "", t).strip()
    return md_path.stem


def who(meta):
    """Combined people string for the filter data attribute + the byline."""
    people = list(meta["hosts"])
    if meta["guest"]:
        people.append(meta["guest"])
    return people


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    india = OUT / "india"
    tdir = india / "transcripts"
    tdir.mkdir(parents=True, exist_ok=True)

    transcripts = {ep_num(t.name): t for t in TRANSCRIPTS.glob("*.txt") if ep_num(t.name)}

    notes = sorted(
        (p for p in NOTES.glob("hpi-*.md") if ep_num(p.name)),
        key=lambda p: ep_num(p.name),
    )
    order = [ep_num(p.name) for p in notes]

    def nav_bar(n):
        i = order.index(n)
        left = (
            f"[← Ep {order[i-1]}](hpi-{order[i-1]:02d}.md){{ .md-button }}"
            if i > 0 else "<span></span>"
        )
        right = (
            f"[Ep {order[i+1]} →](hpi-{order[i+1]:02d}.md){{ .md-button }}"
            if i < len(order) - 1 else "<span></span>"
        )
        return f'<div class="ep-nav" markdown>\n\n{left}\n\n{right}\n\n</div>'

    # per-chapter nav + index listing
    chap_eps = {name: [] for name, _ in CHAPTERS}
    transcript_nav = []

    for note in notes:
        n = ep_num(note.name)
        meta, body = parse_note(note)
        chap = chapter_for(n)  # authoritative: chapter fixed by episode range, not front-matter
        title = clean_title(note)
        people = who(meta)
        byline = (
            f"Peter Adamson with {meta['guest']}"
            if meta["guest"] else " & ".join(meta["hosts"]) or "Peter Adamson"
        )

        listen = (
            f"> 🎧 **Listen:** [:material-web: official page]({OFFICIAL}){{target=_blank}}"
            f" · 👤 {byline}"
        )

        if n in transcripts:
            tname = f"hpi-{n:02d}.md"
            hard = transcripts[n].read_text(encoding="utf-8").strip().replace("\n", "  \n")
            (tdir / tname).write_text(
                f"# {title} — Transcript\n\n{listen}\n"
                f"> 📄 **[Episode notes](../hpi-{n:02d}.md)**\n\n{hard}\n",
                encoding="utf-8",
            )
            transcript_nav.append(f'        - "Ep {n}": india/transcripts/{tname}')
            header = listen + f"\n> 📄 **[Read the full transcript](transcripts/hpi-{n:02d}.md)**\n\n"
        else:
            header = listen + "\n\n"

        bar = nav_bar(n)
        first, _, rest = body.partition("\n")
        page = f"{first}\n\n{bar}\n\n{header}{rest.lstrip(chr(10))}\n\n{bar}\n"
        (india / f"hpi-{n:02d}.md").write_text(page, encoding="utf-8")
        chap_eps[chap].append((n, title, people))

    # map page
    have_map = (NOTES / "india-map.md").exists()
    if have_map:
        shutil.copy(NOTES / "india-map.md", india / "map.md")

    # ---- nav tree ----
    nav = [
        "  - Home: index.md",
        "  - About & Methodology: about.md",
        "  - Transcription Corrections: corrections.md",
    ]
    if have_map:
        nav.append("  - Map of Indian Philosophy: india/map.md")
    nav.append("  - Episodes:")
    for name, _ in CHAPTERS:
        eps = chap_eps[name]
        if not eps:
            continue
        nav.append(f"    - {name}:")
        for n, title, _ in eps:
            nav.append(f'      - "Ep {n} — {title}": india/hpi-{n:02d}.md')
    if transcript_nav:
        nav.append("    - Transcripts:")
        nav.extend(transcript_nav)

    write_index(chap_eps, have_map)
    write_about()
    write_corrections(notes)
    write_assets()
    write_config("\n".join(nav))


def episode_corrections(md_path):
    """Parentheticals on the narration-order line, or [] if none itemised."""
    for line in md_path.read_text(encoding="utf-8").splitlines()[:12]:
        if "speech-to-text" in line.lower():
            return re.findall(r"\(([^)]*)\)", line)
    return []


def write_corrections(notes):
    lines = [
        "# Transcription Corrections",
        "",
        "The transcripts are raw [Whisper](about.md) `large-v3` output. When writing "
        "the notes, Claude normalized **Sanskrit names and terms** to standard "
        "transliteration and fixed obvious speech-to-text slips against context.",
        "",
        "!!! note \"What this page is (and isn't)\"",
        "    This is **not** a complete change-log. The notes are summaries rather than "
        "verbatim text, and Sanskrit terms were normalized throughout, so there is no "
        "full diff. Listed below are the fixes **itemised per episode** — typically "
        "`Correct ≈ \"what Whisper wrote\"`. Episodes marked *“normalized against "
        "context (not itemised)”* were also cleaned up, but those edits were not logged.",
        "",
    ]
    for ep in notes:
        title = clean_title(ep)
        items = [c for c in episode_corrections(ep) if c.strip()]
        if items:
            lines.append(f"- **{title}** — " + " · ".join(items))
        else:
            lines.append(f"- **{title}** — _normalized against context (not itemised)_")
    (OUT / "corrections.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_index(chap_eps, have_map):
    parts = [
        "# History of Philosophy in India — Listening Companion\n",
        "Read-along notes and full transcripts for the **India** series of Peter "
        "Adamson's *History of Philosophy Without Any Gaps* (co-presented with "
        "**Jonardon Ganeri**).\n",
        "Each episode has narration-order notes with `[hh:mm:ss]` jump points, the "
        "argument preserved, a glossary of the thinkers/texts/terms it introduces — "
        "plus the **full transcript**.\n",
        "## How to use this\n",
        "- Pick an episode below (or from the left sidebar), play it, and read along — "
        "the `[hh:mm:ss]` markers line up with the audio.\n"
        "- Use the **filter** under each chapter to show only Peter Adamson's lectures, "
        "Jonardon Ganeri's, or a particular interview guest.\n"
        "- Use the **search box** (top) to find any thinker, text, or term across the "
        "whole series."
        + ("\n- See the **[Map of Indian Philosophy](india/map.md)** for the "
           "chronological spine across all episodes.\n" if have_map else "\n"),
        "## Episodes\n",
        '<p class="filter-label">Filter by host or guest</p>\n',
        '<div id="host-filter"></div>\n',
    ]
    for name, _ in CHAPTERS:
        eps = chap_eps[name]
        if not eps:
            continue
        parts.append(f"### {name}\n")
        parts.append('<div class="ep-list" markdown>\n')
        for n, title, people in eps:
            data = ", ".join(people)
            parts.append(
                f'<a class="ep-item" data-who="{data}" href="india/hpi-{n:02d}/">'
                f"Ep {n} — {title}</a>"
            )
        parts.append("\n</div>\n")
    parts.append(
        "---\n\n*Unofficial fan companion. All credit for the scholarship belongs to "
        "the show. Listen officially at "
        "[historyofphilosophy.net](https://historyofphilosophy.net).*\n"
    )
    (OUT / "index.md").write_text("\n".join(parts), encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")


def write_about():
    (OUT / "about.md").write_text(
        "# About & Methodology\n\n"
        "This is an **unofficial fan companion** to the *History of Philosophy Without "
        "Any Gaps* India series (Peter Adamson & Jonardon Ganeri) — a transparency-"
        "first set of read-along notes and transcripts. Here's exactly how it was made.\n\n"
        "!!! warning \"Read this first\"\n"
        "    The transcripts and notes are **machine-generated** (speech-to-text + an "
        "AI language model). They are a study aid, **not** an authoritative record — "
        "especially for the spelling of Sanskrit names and terms. When something "
        "matters, **trust the audio**, not this site.\n\n"
        "## 1. Transcription — OpenAI Whisper (distil-large-v3)\n\n"
        "Each episode's audio was transcribed locally with the open-source **Whisper** "
        "model — `distil-large-v3` via `faster-whisper` (int8, CPU, ~4x real-time). "
        "The series is dense with **Sanskrit proper nouns** that stress speech-to-text, "
        "so each episode was **seeded** with the key terms from its own title to prime "
        "the decoder, and the terms were then normalized to standard transliteration "
        "when the notes were written.\n\n"
        "- Timestamps (`[hh:mm:ss]`) are Whisper-generated and approximate.\n"
        "- Whisper still mishears Sanskrit terms; these were normalized to standard "
        "transliteration when the notes were written.\n\n"
        "## 2. Notes — Anthropic's Claude (Opus)\n\n"
        "The episode notes were written by **Claude (Opus)** from **one input only: the "
        "Whisper transcript of that episode**. The model worked to a fixed format spec:\n\n"
        "- Follow the episode's **narration order**, not reordered chronology.\n"
        "- Anchor points to the audio with `[hh:mm:ss]`.\n"
        "- Preserve the **argument** — positions, objections, examples, jokes.\n"
        "- **Don't invent facts.** Everything traces to the transcript. Sanskrit terms "
        "are normalized to standard transliteration.\n"
        "- End each note with a glossary of the **thinkers, texts & terms** the "
        "episode introduces.\n\n"
        "**No outside sources were used** — unlike some companions, there is no "
        "external bibliography. Every note reflects only what that episode itself says, "
        "so treat it as a *high-quality summary that can still be wrong*.\n\n"
        "## 3. How this site is built & published\n\n"
        "Notes and transcripts are compiled locally by a small Python script into a "
        "static site with **[MkDocs](https://www.mkdocs.org/) + the Material theme**, "
        "published free on **GitHub Pages**. No server, database, tracking, or ads. "
        "The site is `noindex` — meant to be shared by link, not found in search.\n\n"
        "## 4. Credit & contact\n\n"
        "All scholarship belongs to **Peter Adamson, Jonardon Ganeri, and their guest "
        "contributors**. Please **support the podcast** at "
        "**[historyofphilosophy.net](https://historyofphilosophy.net)** (and the "
        "accompanying OUP books). If you're affiliated with the show and would like "
        "this changed or taken down, that request will be honored via the repository "
        "it's published from.\n",
        encoding="utf-8",
    )


def write_assets():
    (OUT / "extra.css").write_text(
        ".ep-nav { display: flex; justify-content: space-between; gap: 1rem;\n"
        "          align-items: center; margin: 1rem 0; }\n"
        ".ep-nav .md-button { margin: 0; }\n"
        ".ep-list { display: flex; flex-direction: column; gap: .25rem; margin: .5rem 0 1.5rem; }\n"
        ".ep-item { padding: .35rem .6rem; border-radius: .3rem; text-decoration: none;\n"
        "           border: 1px solid var(--md-default-fg-color--lightest); }\n"
        ".ep-item:hover { background: var(--md-default-fg-color--lightest); }\n"
        ".filter-label { font-weight: 700; font-size: .72rem; text-transform: uppercase;\n"
        "                letter-spacing: .07em; opacity: .6; margin: 1.2rem 0 .4rem; }\n"
        "#host-filter { display: flex; flex-wrap: wrap; gap: .4rem; margin: .2rem 0 1rem; }\n"
        ".host-btn { cursor: pointer; padding: .25rem .7rem; border-radius: 1rem;\n"
        "            border: 1px solid var(--md-primary-fg-color); background: transparent;\n"
        "            color: var(--md-primary-fg-color); font-size: .8rem; }\n"
        ".host-btn.active { background: var(--md-primary-fg-color); color: var(--md-primary-bg-color); }\n",
        encoding="utf-8",
    )
    (OUT / "extra.js").write_text(
        "document.addEventListener('DOMContentLoaded', function () {\n"
        "  var items = Array.from(document.querySelectorAll('.ep-item'));\n"
        "  var bar = document.getElementById('host-filter');\n"
        "  if (!items.length || !bar) return;\n"
        "  var names = new Set();\n"
        "  items.forEach(function (el) {\n"
        "    (el.dataset.who || '').split(',').forEach(function (n) {\n"
        "      n = n.trim(); if (n) names.add(n);\n"
        "    });\n"
        "  });\n"
        "  function show(name) {\n"
        "    bar.querySelectorAll('.host-btn').forEach(function (b) {\n"
        "      b.classList.toggle('active', b.dataset.name === name);\n"
        "    });\n"
        "    items.forEach(function (el) {\n"
        "      var who = (el.dataset.who || '').split(',').map(function (s) { return s.trim(); });\n"
        "      el.style.display = (name === 'All' || who.indexOf(name) > -1) ? '' : 'none';\n"
        "    });\n"
        "  }\n"
        "  function mk(name) {\n"
        "    var b = document.createElement('button');\n"
        "    b.className = 'host-btn'; b.textContent = name; b.dataset.name = name;\n"
        "    b.onclick = function () { show(name); };\n"
        "    bar.appendChild(b);\n"
        "  }\n"
        "  mk('All');\n"
        "  Array.from(names).sort().forEach(mk);\n"
        "  show('All');\n"
        "});\n",
        encoding="utf-8",
    )


def write_config(nav):
    (Path(__file__).parent / "mkdocs.yml").write_text(
        "site_name: History of Philosophy in India — Companion\n"
        "site_description: Read-along notes and transcripts for the HoPWaG India series\n"
        "theme:\n"
        "  name: material\n"
        "  custom_dir: overrides\n"
        "  palette:\n"
        "    - scheme: slate\n"
        "      primary: deep orange\n"
        "      accent: deep orange\n"
        "      toggle:\n"
        "        icon: material/weather-night\n"
        "        name: Light mode\n"
        "    - scheme: default\n"
        "      primary: deep orange\n"
        "      accent: deep orange\n"
        "      toggle:\n"
        "        icon: material/weather-sunny\n"
        "        name: Dark mode\n"
        "  features:\n"
        "    - navigation.instant\n"
        "    - navigation.tracking\n"
        "    - navigation.top\n"
        "    - navigation.indexes\n"
        "    - search.highlight\n"
        "    - search.suggest\n"
        "    - content.code.copy\n"
        "    - toc.follow\n"
        "plugins:\n"
        "  - search\n"
        "extra_css:\n"
        "  - extra.css\n"
        "extra_javascript:\n"
        "  - extra.js\n"
        "markdown_extensions:\n"
        "  - admonition\n"
        "  - attr_list\n"
        "  - md_in_html\n"
        "  - tables\n"
        "  - pymdownx.emoji:\n"
        "      emoji_index: !!python/name:material.extensions.emoji.twemoji\n"
        "      emoji_generator: !!python/name:material.extensions.emoji.to_svg\n"
        "  - toc:\n"
        "      permalink: true\n"
        "nav:\n" + nav + "\n",
        encoding="utf-8",
    )
    ov = Path(__file__).parent / "overrides"
    ov.mkdir(exist_ok=True)
    (ov / "main.html").write_text(
        '{% extends "base.html" %}\n'
        "{% block extrahead %}\n"
        '  <meta name="robots" content="noindex, nofollow">\n'
        "{% endblock %}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
    print(f"Built {sum(1 for _ in OUT.rglob('*.md'))} pages into {OUT}")
