#!/usr/bin/env python3
"""Generate /notes/ and each Field Note permalink page from data/field-notes.json.

Usage, from the repo root:   python3 tools/build-notes.py

Add a note to the top of data/field-notes.json (newest first), rerun, add the
new /notes/NN/ URL to sitemap.xml, commit, push. The page shell (masthead,
navigation, footer) comes from tools/shell.py, shared with every page.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shell import page, question_line  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "field-notes.json")
SITE = "https://www.whenmoneyfollowsthechild.org"

# Which part of the site's question each tag speaks to
PART = {}  # every note answers the respond part of the question


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
    canonical = "%s/notes/%s/" % (SITE, note["slug"])
    body = """
<div class="hero sm"><div class="w">
  <div class="crumb"><a href="/notes/">Field Notes</a></div>
  <h1 style="font-size:clamp(30px,4.4vw,48px);max-width:900px">%s</h1>
  <p class="lead2">%s</p>
  %s
</div></div>

<section><div class="w"><div class="prose">
""" % (note["title"], note["standfirst"], question_line("respond"))

    for para in note["body"]:
        body += "  <p>%s</p>\n" % para

    body += '\n  <h2>Sources</h2>\n  <ul class="srcs">\n'
    for s in note["sources"]:
        body += '    <li><a href="%s">%s</a></li>\n' % (s["url"], s["label"])
    body += "  </ul>\n"
    body += ('\n  <p class="fine" style="margin-top:22px">Cite as: When Money Follows the Child. '
             '<i>%s</i> Field Note %s, %s. %s Accessed [date].</p>\n'
             % (strip_tags(note["title"]).rstrip("."), note["n"], note["date"], canonical))

    links = []
    links.append('<a href="/notes/%s/">&larr; Field Note %s</a>' % (next_note["slug"], next_note["n"])
                 if next_note else "<span></span>")
    links.append('<a href="/notes/">All Field Notes</a>')
    links.append('<a href="/notes/%s/">Field Note %s &rarr;</a>' % (prev_note["slug"], prev_note["n"])
                 if prev_note else "<span></span>")
    body += '  <div class="notenav">%s</div>\n</div></div></section>\n' % "".join(links)

    return page("Field Note %s — %s" % (note["n"], strip_tags(note["title"])),
                strip_tags(note["standfirst"])[:300],
                "/notes/%s/" % note["slug"], "/notes/", body, ogtype="article")


def index_page(notes):
    tags = []
    for n in notes:
        if n["tag"] not in tags:
            tags.append(n["tag"])
    chips = '<button class="chip" type="button" data-k="all" aria-pressed="true">All <span class="n">%d</span></button>' % len(notes)
    for t in tags:
        chips += ('<button class="chip" type="button" data-k="%s" aria-pressed="false">%s <span class="n">%d</span></button>'
                  % (esc_attr(t), t, sum(1 for n in notes if n["tag"] == t)))
    cards = ""
    for n in notes:
        cards += """    <div class="col" data-tag="%s"><div class="k">%s</div>
      <h3><a href="/notes/%s/">%s</a></h3>
      <p>%s</p>
      <div class="d">Field Note %s &middot; %s</div></div>
""" % (esc_attr(n["tag"]), n["tag"], n["slug"], n["title"], n["standfirst"], n["n"], n["date"])

    body = """
<div class="hero sm"><div class="w">
  <h1>Short findings, <span class="f">between</span> editions.</h1>
  <p class="lead2">One number, institution or pattern, with its evidence and its limits. Every note has a permanent address so it can be cited, checked and argued with.</p>
  %s
</div></div>

<section class="alt"><div class="w">
  <div class="tools" id="tags">%s</div>
  <div class="cols3" id="notes" style="grid-template-columns:repeat(3,1fr)">
%s  </div>
</div></section>
""" % (question_line("respond"), chips, cards)

    scripts = """<script>
(function(){
"use strict";
var chips=document.querySelectorAll("#tags .chip"),cards=document.querySelectorAll("#notes .col");
Array.prototype.forEach.call(chips,function(c){c.addEventListener("click",function(){
  Array.prototype.forEach.call(chips,function(x){x.setAttribute("aria-pressed",String(x===c));});
  Array.prototype.forEach.call(cards,function(n){n.hidden=c.dataset.k!=="all"&&n.dataset.tag!==c.dataset.k;});
});});
})();
</script>
<style>@media (max-width:900px){#notes{grid-template-columns:1fr 1fr!important}}@media (max-width:560px){#notes{grid-template-columns:1fr!important}}#notes .col[hidden]{display:none}</style>
"""
    return page("Field Notes — When Money Follows the Child",
                "Short findings published between editions: one number, institution or pattern, with its evidence and limits.",
                "/notes/", "/notes/", body, scripts)


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
        prev_note = notes[i - 1] if i > 0 else None               # newer
        next_note = notes[i + 1] if i + 1 < len(notes) else None  # older
        d = os.path.join(ROOT, "notes", note["slug"])
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "index.html")
        open(p, "w", encoding="utf-8", newline="\n").write(note_page(note, prev_note, next_note))
        written.append(p)

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
