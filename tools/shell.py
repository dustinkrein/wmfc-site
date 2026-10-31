"""The shared page shell — head, masthead and footer — for every WMFC page.

One place to change the navigation. Used by tools/build-notes.py and by
tools/build-pages.py. Pages that are hand-written copy the same markup.
"""

SITE = "https://www.whenmoneyfollowsthechild.org"
QUESTION = ("When K–12 funding follows the student, how do colleges and universities "
            "respond? And who is leading?")

# (href, label) — every item answers part of the question
NAV = [
    ("/universities/", "Universities"),
    ("/research/", "Preparation Index"),
    ("/leaders/", "Leaders"),
    ("/districts/", "Districts"),
    ("/atlas/", "Atlas"),
    ("/notes/", "Field Notes"),
    ("/navigator/", "Navigator"),
    ("/method/", "Method"),
    ("/about/", "About"),
]


def _e(s):
    return (s.replace("&", "&amp;").replace('"', "&quot;")
             .replace("<", "&lt;").replace(">", "&gt;"))


def head(title, desc, path, ogtype="website"):
    canonical = SITE + path
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="{ogtype}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="When Money Follows the Child">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/wmfc.css">
<script>try{{var t=localStorage.getItem("wmfc-theme");if(t)document.documentElement.setAttribute("data-theme",t)}}catch(e){{}}</script>
</head>
<body>
""".format(title=_e(title), desc=_e(desc), canonical=canonical, ogtype=ogtype)


def masthead(active=None):
    links = "".join(
        '<a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if h == active else "", l)
        for h, l in NAV)
    return """<div class="bar"></div>
<header><div class="w">
  <a class="wm" href="/">When Money <span class="f">Follows</span> the Child</a>
  <nav aria-label="Site">%s</nav>
  <button class="tog" id="tog" type="button" aria-label="Switch light or dark theme" title="Light / dark">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
  </button>
</div></header>
""" % links


def footer():
    return """<footer><div class="w"><div class="cols">
  <div>
    <div class="fwm">When Money <span class="f">Follows</span> the Child</div>
    <p style="margin:0 0 8px;max-width:40ch">Research on how colleges and universities respond when K–12 funding follows the student.</p>
    <a href="mailto:info@whenmoneyfollowsthechild.org">info@whenmoneyfollowsthechild.org</a>
  </div>
  <div><div class="fh">How universities respond</div>
    <a href="/universities/">Universities</a><a href="/research/">Preparation Index</a><a href="/leaders/">Leaders</a><a href="/atlas/">Atlas</a>
  </div>
  <div><div class="fh">The comparison and the record</div>
    <a href="/districts/">Districts</a><a href="/notes/">Field Notes</a><a href="/navigator/">Navigator</a><a href="/method/">Method &amp; data</a><a href="/about/">About</a>
  </div>
</div></div></footer>
<script src="/assets/wmfc.js"></script>
"""


def page(title, desc, path, active, body, scripts="", ogtype="website"):
    return (head(title, desc, path, ogtype) + masthead(active) + "<main>\n" + body
            + "\n</main>\n" + footer() + scripts + "</body>\n</html>\n")


def question_line(focus="respond"):
    """The site's question, with the part this page answers in oxblood.
    focus: "respond", "lead" or "compare" (school districts, the comparison)."""
    a, b = "how do colleges and universities respond?", "And who is leading?"
    if focus == "respond":
        a = '<span style="color:var(--ox)">%s</span>' % a
    if focus == "lead":
        b = '<span style="color:var(--ox)">%s</span>' % b
    tail = (' <span style="color:var(--ink3)">School districts are the comparison.</span>'
            if focus == "compare" else "")
    return ('<div class="qline"><b>The question</b><span>When K–12 funding follows the student, %s %s%s</span></div>'
            % (a, b, tail))
