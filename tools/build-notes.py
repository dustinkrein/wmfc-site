#!/usr/bin/env python3
"""Generate /notes/ and each Field Note permalink page from data/field-notes.json.

Usage, from the repo root:   python3 tools/build-notes.py

Add a note to data/field-notes.json (newest first), rerun, commit, push.
Nothing else in the site needs editing — the homepage reads the same JSON at load.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "field-notes.json")
SITE = "https://www.whenmoneyfollowsthechild.org"

HEAD = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{ogtitle}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="{ogtype}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="When Money Follows the Child">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/wmfc.css">
</head><body>

<div class="rule"></div>
<header><div class="w">
  <a class="wm" href="/">WM<span class="f">F</span>C</a>
  <span class="wmsub">When Money Follows the Child</span>
  <nav>
    <a href="/research/">Readiness Index</a><a href="/atlas/">Atlas</a>
    <a href="/notes/"{notecur}>Field Notes</a>
    <a href="/method/">Method</a>
    <a href="/about/">About</a>
  </nav>
  <a class="btn" href="/#join">Become a member</a>
</div></header>
"""

FOOT = """
<footer>
  <div class="rule"></div>
  <div class="w">
    <div>
      <div class="fwm">When Money <span class="f">Follows</span> the Child</div>
      <p>Independent, nonpartisan research on how postsecondary institutions respond as K-12 education funding becomes portable.</p>
      <p><a href="mailto:info@whenmoneyfollowsthechild.org">info@whenmoneyfollowsthechild.org</a></p>
    </div>
    <div><div class="h">Research</div>
      <a href="/research/">Readiness Index</a>
      <a href="/atlas/">Portable-Funding Atlas</a><a href="/research/international-precedents/">International Precedents</a><a href="/notes/">Field Notes</a><a href="/data/">Data &amp; downloads</a>
      <a href="/method/#corrections">Corrections</a>
    </div>
    <div><div class="h">About</div>
      <a href="/method/">Method</a>
      <a href="/about/#independence">Funding &amp; independence</a>
      <a href="/about/#contact">Contact</a>
    </div>
  </div>
</footer>
<script src="/assets/wmfc.js"></script>
</body></html>
"""


def esc_attr(s):
    return (s.replace("&", "&amp;").replace('"', "&quot;")
             .replace("<", "&lt;").replace(">", "&gt;"))


def strip_tags(s):
    out, depth = [], 0
    for ch in s:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def note_page(note, prev_note, next_note):
    desc = esc_attr(strip_tags(note["standfirst"]))[:300]
    canonical = "%s/notes/%s/" % (SITE, note["slug"])
    html = HEAD.format(
        title="Field Note %s — %s" % (note["n"], esc_attr(strip_tags(note["title"]))),
        desc=desc,
        canonical=canonical,
        ogtitle=esc_attr(strip_tags(note["title"])),
        ogtype="article",
        notecur="",
    )
    html += """
<div class="hero short"><div class="w-narrow" style="padding:0">
  <div class="kick">Field Note %s &middot; %s</div>
  <h1>%s</h1>
  <p class="lede">%s</p>
</div></div>

<section><div class="w-narrow" style="padding:0">
""" % (note["n"], note["date"], note["title"], note["standfirst"])

    for para in note["body"]:
        html += "  <p>%s</p>\n" % para

    html += "\n  <h2>Sources</h2>\n  <ul>\n"
    for s in note["sources"]:
        html += '    <li><a href="%s">%s</a></li>\n' % (s["url"], s["label"])
    html += "  </ul>\n"

    html += ('\n  <p class="fine">Cite as: When Money Follows the Child. '
             '<i>%s.</i> Field Note %s, %s. %s Accessed [date].</p>\n'
             % (strip_tags(note["title"]), note["n"], note["date"], canonical))

    html += '\n  <p style="margin-top:26px">'
    links = []
    if next_note:
        links.append('<a href="/notes/%s/">&larr; Field Note %s</a>' % (next_note["slug"], next_note["n"]))
    links.append('<a href="/notes/">All Field Notes</a>')
    if prev_note:
        links.append('<a href="/notes/%s/">Field Note %s &rarr;</a>' % (prev_note["slug"], prev_note["n"]))
    html += " &nbsp;&middot;&nbsp; ".join(links)
    html += "</p>\n</div></section>\n"
    return html + FOOT


def index_page(notes):
    html = HEAD.format(
        title="Field Notes — When Money Follows the Child",
        desc="Short findings published between editions of the WMFC Readiness Index. Each one is a single number, institution or pattern, with its evidence.",
        canonical="%s/notes/" % SITE,
        ogtitle="Field Notes",
        ogtype="website",
        notecur=' aria-current="page"',
    )
    html += """
<div class="hero short"><div class="w-narrow" style="padding:0">
  <div class="kick">Field Notes</div>
  <h1>Short findings, between editions.</h1>
  <p class="lede">A single number, institution or pattern, with its evidence and its limits. Every note has a permanent address so it can be cited, checked and argued with.</p>
</div></div>

<section><div class="w-narrow" style="padding:0">
"""
    for note in notes:
        html += """  <div class="note" style="margin-bottom:18px">
    <div class="k">%s</div>
    <h3 style="margin:6px 0 8px"><a href="/notes/%s/">%s</a></h3>
    <p>%s</p>
    <div class="d">Field Note %s &middot; %s</div>
  </div>
""" % (note["tag"], note["slug"], note["title"], note["standfirst"], note["n"], note["date"])

    html += """  <p class="fine" style="margin-top:24px">Field Notes are free. Members receive them by email as they publish &mdash; <a href="/#join">sign up</a>.</p>
</div></section>
"""
    return html + FOOT


def homepage_block(notes):
    """The four newest notes, as static cards, for the homepage."""
    show = notes[:4]
    cls = "cols3 even" if len(show) % 2 == 0 else "cols3"
    out = ['  <div class="%s">' % cls]
    for n in show:
        out.append(
            '    <div class="col"><div class="k">%s</div>\n'
            '      <h3><a href="/notes/%s/">%s</a></h3>\n'
            '      <p>%s</p>\n'
            '      <div class="d">Field Note %s &middot; %s</div></div>'
            % (n["tag"], n["slug"], n["title"], n["standfirst"], n["n"], n["date"])
        )
    out.append("  </div>")
    return "\n".join(out)


def write_homepage(notes):
    p = os.path.join(ROOT, "index.html")
    s = open(p, encoding="utf-8").read()
    start = "<!-- FIELD-NOTES:START"
    end = "<!-- FIELD-NOTES:END -->"
    i, j = s.find(start), s.find(end)
    if i == -1 or j == -1:
        print("  ! homepage markers not found — skipped")
        return None
    i_end = s.find("-->", i) + 3
    s = s[:i_end] + "\n" + homepage_block(notes) + "\n  " + s[j:]
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    return p


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    notes = data["notes"]  # newest first
    seen = set()
    for n in notes:
        for k in ("n", "slug", "tag", "date", "iso", "title", "standfirst", "body", "sources"):
            if not n.get(k):
                sys.exit("Field Note %s is missing '%s'" % (n.get("n", "?"), k))
        if n["slug"] in seen:
            sys.exit("duplicate slug: %s" % n["slug"])
        seen.add(n["slug"])

    written = []
    for i, note in enumerate(notes):
        prev_note = notes[i - 1] if i > 0 else None          # newer
        next_note = notes[i + 1] if i + 1 < len(notes) else None  # older
        d = os.path.join(ROOT, "notes", note["slug"])
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "index.html")
        open(p, "w", encoding="utf-8", newline="\n").write(note_page(note, prev_note, next_note))
        written.append(p)

    os.makedirs(os.path.join(ROOT, "notes"), exist_ok=True)
    p = os.path.join(ROOT, "notes", "index.html")
    open(p, "w", encoding="utf-8", newline="\n").write(index_page(notes))
    written.append(p)

    hp = write_homepage(notes)
    if hp:
        written.append(hp)

    print("Wrote %d files:" % len(written))
    for p in written:
        print("  ", os.path.relpath(p, ROOT))
    print("\nRemember: add new URLs to sitemap.xml.")


if __name__ == "__main__":
    main()
