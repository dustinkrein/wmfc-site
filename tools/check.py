#!/usr/bin/env python3
"""
WMFC preflight — run before every commit.

    python3 tools/check.py

Validates that the site's published numbers match its data, that every
finding carries a source and an honest check date, and that nothing has
silently drifted between the JSON spine and the HTML that renders it.

Exit code 0 = safe to commit. 1 = something is wrong.

Why this exists: on 25 Aug 2026 the Atlas displayed "134 Not yet coded"
in its legend and "146 Not yet coded" in its stat strip, on the same
page. Both numbers were reachable from the data; nothing caught the
contradiction. For a site whose whole claim is that its numbers can be
checked, that class of error is the expensive one. Everything below is
mechanical, so no future pass has to remember to look.
"""

import json
import os
import re
import sys
import datetime
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = datetime.date.today()

FAILS = []
WARNS = []
LINES = []


def rel(*p):
    return os.path.join(ROOT, *p)


def ok(msg):
    LINES.append(("ok", msg))


def fail(msg):
    FAILS.append(msg)
    LINES.append(("fail", msg))


def warn(msg):
    WARNS.append(msg)
    LINES.append(("warn", msg))


def load(path):
    try:
        with open(rel(path), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        fail("%s is missing" % path)
    except json.JSONDecodeError as e:
        fail("%s is not valid JSON — line %d: %s" % (path, e.lineno, e.msg))
    return None


def read(path):
    try:
        with open(rel(path), encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()


# --------------------------------------------------------------------
# 1. Filename guard — Windows 8.3 mangling has broken this repo before
# --------------------------------------------------------------------
def check_filenames():
    bad = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if ".git" in dirpath:
            continue
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for n in filenames + dirnames:
            if "~" in n:
                bad.append(os.path.relpath(os.path.join(dirpath, n), ROOT))
    if bad:
        fail("8.3-mangled filenames present (these silently 404): %s"
             % ", ".join(sorted(bad)))
    else:
        ok("no 8.3-mangled filenames")


# --------------------------------------------------------------------
# 2. Preparation Index rows
# --------------------------------------------------------------------
VALID_TIERS = {"Tier 0", "Tier 1", "Tier 2", "Tier 3"}


def check_scan(scan):
    if not scan:
        return None
    inst = scan.get("institutions")
    if not isinstance(inst, list) or not inst:
        fail("scan-2026.json has no institutions array")
        return None

    missing_src, bad_tier, bad_date, future, stale = [], [], [], [], []
    for r in inst:
        name = r.get("name", "<unnamed>")
        if not r.get("source", "").startswith("http"):
            missing_src.append(name)
        if r.get("tier") not in VALID_TIERS:
            bad_tier.append("%s (%r)" % (name, r.get("tier")))
        raw = r.get("checked", "")
        try:
            d = datetime.date.fromisoformat(raw)
            if d > TODAY:
                future.append("%s (%s)" % (name, raw))
            elif (TODAY - d).days > 365:
                stale.append("%s (%s)" % (name, raw))
        except (ValueError, TypeError):
            bad_date.append("%s (%r)" % (name, raw))

    if missing_src:
        fail("Index rows without a live source URL: %s" % ", ".join(missing_src))
    if bad_tier:
        fail("Index rows with an invalid tier: %s" % ", ".join(bad_tier))
    if bad_date:
        fail("Index rows with an unparseable checked date: %s" % ", ".join(bad_date))
    if future:
        # A forward-dated check means nobody actually read the page that day.
        fail("Index rows checked in the future: %s" % ", ".join(future))
    if stale:
        warn("%d Index rows last checked over a year ago (recheck before citing): %s"
             % (len(stale), ", ".join(stale[:5]) + (" …" if len(stale) > 5 else "")))

    # Coverage: every state carrying rows must declare how deeply it was read.
    # Without this a placeholder row and a systematic pass look identical.
    states = {r.get("state") for r in inst}
    cov = scan.get("coverage") or {}
    depths = scan.get("depths") or {}
    if not cov:
        fail("scan-2026.json has no coverage block — states cannot declare their depth")
    else:
        undeclared = sorted(s for s in states if s not in cov)
        orphan = sorted(s for s in cov if s not in states)
        bad_depth = sorted("%s (%r)" % (s, cov[s].get("depth"))
                           for s in cov if cov[s].get("depth") not in depths)
        nonote = sorted(s for s in cov if not cov[s].get("note"))
        if undeclared:
            fail("states with rows but no coverage entry: %s" % ", ".join(undeclared))
        if orphan:
            warn("coverage entries for states with no rows: %s" % ", ".join(orphan))
        if bad_depth:
            fail("coverage entries with an unknown depth: %s" % ", ".join(bad_depth))
        if nonote:
            fail("coverage entries with no note explaining what was covered: %s" % ", ".join(nonote))
        if not (undeclared or bad_depth or nonote):
            byd = {}
            for s in cov:
                byd.setdefault(cov[s]["depth"], []).append(s)
            ok("coverage declared for all %d states (%s)"
               % (len(cov), ", ".join("%d %s" % (len(v), k) for k, v in sorted(byd.items()))))

    if not (missing_src or bad_tier or bad_date or future):
        ok("Index: %d rows, %d states, all sourced, all check dates sane"
           % (len(inst), len(states)))
    return inst


# --------------------------------------------------------------------
# 3. Atlas rows
# --------------------------------------------------------------------
TIER1_REQUIRED = ["mechanism", "summary", "findings", "code", "code_label", "mech_type"]


def check_atlas(world):
    if not world:
        return None
    t1 = {k: v for k, v in world.items() if v.get("tier") == 1}
    t2 = {k: v for k, v in world.items() if v.get("tier") == 2}
    t3 = {k: v for k, v in world.items() if v.get("tier") == 3}

    if len(t1) + len(t2) + len(t3) != len(world):
        fail("Atlas: some rows carry a tier outside {1,2,3}")

    incomplete, unsourced = [], []
    for k, v in sorted(t1.items()):
        miss = [f for f in TIER1_REQUIRED if not v.get(f)]
        if miss:
            incomplete.append("%s missing %s" % (k, "/".join(miss)))
        for f in v.get("findings", []):
            if not f.get("src") or not f.get("checked"):
                unsourced.append(k)
                break
    if incomplete:
        fail("Atlas coded rows incomplete: %s" % "; ".join(incomplete))
    if unsourced:
        fail("Atlas coded rows with an unsourced finding: %s" % ", ".join(sorted(set(unsourced))))

    # House standard: a named reason is accountable, "coding is planned" is not.
    noreason = sorted(v.get("name", k) for k, v in t2.items() if not v.get("shortlist_reason"))
    if noreason:
        warn("Atlas shortlisted rows with no shortlist_reason (%d): %s"
             % (len(noreason), ", ".join(noreason)))

    leaky = sorted(k for k, v in t3.items() if v.get("findings") or v.get("summary"))
    if leaky:
        warn("Atlas rows marked 'not yet coded' that carry content: %s" % ", ".join(leaky))

    if not (incomplete or unsourced):
        ok("Atlas: %d countries — %d coded, %d shortlisted, %d not yet coded"
           % (len(world), len(t1), len(t2), len(t3)))
    return {"total": len(world), "t1": len(t1), "t2": len(t2), "t3": len(t3)}


# --------------------------------------------------------------------
# 4. Field Notes — JSON, generated pages and sitemap must agree
# --------------------------------------------------------------------
NOTE_FIELDS = ["n", "slug", "tag", "date", "title", "standfirst", "body", "sources"]
VALID_TAGS = {"Workforce", "Institutions", "The seam"}


def check_notes(fn, sitemap):
    if fn is None:
        return
    notes = fn if isinstance(fn, list) else fn.get("notes", [])
    if not notes:
        warn("field-notes.json holds no notes")
        return

    problems = []
    seen_n, seen_slug = set(), set()
    for note in notes:
        label = "note %s" % note.get("n", "?")
        miss = [f for f in NOTE_FIELDS if not note.get(f)]
        if miss:
            problems.append("%s missing %s" % (label, "/".join(miss)))
        if note.get("tag") not in VALID_TAGS:
            problems.append("%s has tag %r (expected one of %s)"
                            % (label, note.get("tag"), ", ".join(sorted(VALID_TAGS))))
        if note.get("n") in seen_n:
            problems.append("duplicate note number %s" % note.get("n"))
        seen_n.add(note.get("n"))
        if note.get("slug") in seen_slug:
            problems.append("duplicate slug %s" % note.get("slug"))
        seen_slug.add(note.get("slug"))

        nn = str(note.get("n", "")).zfill(2)
        page = os.path.join("notes", nn, "index.html")
        if not os.path.exists(rel(page)):
            problems.append("%s has no generated page at /notes/%s/ — run tools/build-notes.py"
                            % (label, nn))
        elif sitemap and "/notes/%s/" % nn not in sitemap:
            problems.append("/notes/%s/ is not in sitemap.xml" % nn)

    if problems:
        for p in problems:
            fail("Field Notes: %s" % p)
    else:
        ok("Field Notes: %d notes, all with pages and sitemap entries" % len(notes))


# --------------------------------------------------------------------
# 5. Published numbers vs the data that backs them
# --------------------------------------------------------------------
DERIVE_RE = re.compile(
    r"<(\w+)((?:[^>]*?\sdata-derive=\"([^\"]+)\")[^>]*)>(.*?)</\1>", re.S)


def derived_values(inst):
    st = {r.get("state") for r in inst}

    def count(fn):
        return sum(1 for r in inst if fn(r))

    return {
        "total": len(inst),
        "states": len(st),
        "tier1": count(lambda r: r.get("tier") == "Tier 1"),
        "tier1.prep": count(lambda r: r.get("tier") == "Tier 1" and "program" in (r.get("engagement") or [])),
        "tier1.ops": count(lambda r: r.get("tier") == "Tier 1" and "program" not in (r.get("engagement") or [])),
        "tier2": count(lambda r: r.get("tier") == "Tier 2"),
        "tier3": count(lambda r: r.get("tier") == "Tier 3"),
        "tier0": count(lambda r: r.get("tier") == "Tier 0"),
        "fl.total": count(lambda r: r.get("state") == "Florida"),
        "fl.tier2": count(lambda r: r.get("state") == "Florida" and r.get("tier") == "Tier 2"),
        "fl.tier1": count(lambda r: r.get("state") == "Florida" and r.get("tier") == "Tier 1"),
        "mi.total": count(lambda r: r.get("state") == "Michigan"),
        "aggregates": count(lambda r: r.get("scope") == "aggregate"),
        "institutions": count(lambda r: r.get("scope") != "aggregate"),
    }


def check_fallbacks(inst, atlas_counts, html_files):
    """The HTML ships hardcoded numbers so nothing goes blank if a fetch
    fails. That safety net is only safe while it agrees with the data."""
    if not inst:
        return
    vals = derived_values(inst)
    bad = []

    for path in html_files:
        src = read(path)
        if not src:
            continue
        for tag, attrs, key, inner in DERIVE_RE.findall(src):
            if key not in vals:
                bad.append("%s: data-derive=\"%s\" is not a key wmfc.js knows" % (path, key))
                continue
            expected = vals[key]
            m = re.search(r"data-count=\"([^\"]*)\"", attrs)
            if m:
                shown, where = m.group(1), "data-count"
            else:
                tpl = re.search(r"data-derive-tpl=\"([^\"]*)\"", attrs)
                shown, where = strip_tags(inner), "text"
                if tpl:
                    expect_text = tpl.group(1).replace("{n}", str(expected))
                    if shown != expect_text:
                        bad.append("%s: data-derive=\"%s\" fallback reads %r, data says %r"
                                   % (path, key, shown, expect_text))
                    continue
            if shown.strip() != str(expected):
                bad.append("%s: data-derive=\"%s\" %s fallback is %r, data says %d"
                           % (path, key, where, shown, expected))

    # Atlas stat strip — the exact bug this script was written for.
    if atlas_counts:
        src = read(os.path.join("atlas", "index.html")) or ""
        expect = {
            "statCoded": atlas_counts["t1"],
            "statTotal": atlas_counts["total"],
            "statPending": atlas_counts["t3"],
        }
        for el, want in expect.items():
            m = re.search(r"id=\"%s\"[^>]*>([^<]*)<" % el, src)
            if not m:
                bad.append("atlas/index.html: #%s not found" % el)
            elif m.group(1).strip() != str(want):
                bad.append("atlas/index.html: #%s fallback is %r, data says %d"
                           % (el, m.group(1).strip(), want))
        # The legend and the stat strip must not label two numbers the same way.
        if src.count("Not yet coded") and expect["statPending"] != atlas_counts["t3"]:
            bad.append("atlas/index.html: 'Not yet coded' is used for two different values")

    if bad:
        for b in bad:
            fail(b)
    else:
        ok("published numbers match the data spine")


# --------------------------------------------------------------------
# 5b. University scan: headline numbers on any page must match the data
# --------------------------------------------------------------------
U_RE = re.compile(r"<(\w+)([^>]*\sdata-u=\"([^\"]+)\"[^>]*)>([^<]*)</\1>")
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}


def check_universities(html_files):
    """Added 31 Oct 2026: the Universities page shipped '32 respond / 6
    compete' for weeks after Correction 04 made it 49 / 18. Nothing here
    caught it because this file only checked the Preparation Index."""
    U = load(os.path.join("data", "universities-2026.json"))
    if not U:
        return
    R = U.get("institutions", [])
    fl = [r for r in R if r.get("state") == "FL"]
    vals = {
        "total": len(R),
        "respond": sum(1 for r in R if r.get("direction") != "none"),
        "compete": sum(1 for r in R if r.get("direction") == "compete"),
        "none": sum(1 for r in R if r.get("direction") == "none"),
        "fl.none": sum(1 for r in fl if r.get("direction") == "none"),
    }
    bad = []
    for path in html_files:
        src = read(path)
        if not src:
            continue
        for tag, attrs, key, inner in U_RE.findall(src):
            if key not in vals:
                bad.append("%s: data-u=\"%s\" is not a known key" % (path, key))
                continue
            m = re.search(r"data-n=\"([^\"]*)\"", attrs)
            for shown in ([m.group(1)] if m else []) + [inner.strip()]:
                if shown != str(vals[key]):
                    bad.append("%s: data-u=\"%s\" shows %r, data says %d" % (path, key, shown, vals[key]))
        # Prose claims that are easy to leave stale.
        if "show no response we could find" in src and "About <em>half</em>" in src:
            share = vals["none"] / float(vals["total"] or 1)
            if not 0.42 <= share <= 0.58:
                bad.append("%s: says 'about half' show no response; data says %.0f%%" % (path, 100 * share))
        m = re.search(r"In Florida, (\w+) of seven", src)
        if m and WORDS.get(m.group(1).lower()) != vals["fl.none"]:
            bad.append("%s: says %s of seven Florida universities show none; data says %d" % (path, m.group(1), vals["fl.none"]))
    # Evidence states (added 1 Nov 2026): every row carries one, and they agree with direction.
    from collections import Counter
    es = Counter(r.get("evidence_state") for r in R)
    for r in R:
        st = r.get("evidence_state")
        if st not in ("documented", "searched", "unresolved", "unchecked"):
            bad.append("universities-2026.json: %s has no valid evidence_state" % r.get("name"))
        elif (r.get("direction") != "none") != (st == "documented"):
            bad.append("universities-2026.json: %s evidence_state %s disagrees with direction %s" % (r.get("name"), st, r.get("direction")))
    m = read(os.path.join("method", "index.html")) or ""
    want = "%d documented, %d searched with none found, %d unresolved, %d not yet checked" % (es["documented"], es["searched"], es["unresolved"], es["unchecked"])
    if "evidence_state" in m and want not in m:
        bad.append("method/index.html: evidence-state counts do not match the data (%s)" % want)
    # Homepage waffle (added 1 Nov 2026): one square per university, and legend counts, must match the data.
    home = read("index.html") or ""
    if "home-waffle" in home:
        for d in ("compete", "supply", "fortify", "evidence", "none"):
            want = sum(1 for r in R if r.get("direction") == d)
            got = len(re.findall(r'class="cell %s"' % d, home))
            m = re.search(r'data-dir="%s">(\d+)<' % d, home)
            if got != want or (m and int(m.group(1)) != want):
                bad.append("index.html waffle: %s shows %d squares / legend %s, data says %d" % (d, got, m.group(1) if m else "?", want))
    if bad:
        for b in bad:
            fail(b)
    else:
        ok("University scan: %d institutions, %d respond, %d compete — pages agree" % (vals["total"], vals["respond"], vals["compete"]))


def check_supply():
    """Added 31 Oct 2026 with the timing fix on the Florida supply chart:
    every derived percentage in that section is recomputed here."""
    d = load(os.path.join("data", "supply-florida-2026.json"))
    # The supply chart moved from the homepage to /explore/ on 1 Nov 2026.
    src = read(os.path.join("explore", "index.html")) or ""
    also = read(os.path.join("what-we-know", "index.html")) or ""
    if not d:
        return
    Y = {r["year"]: r for r in d["years"] if not r.get("excluded")}
    a, z, pre = Y["2010–11"], Y["2023–24"], Y["2022–23"]
    nc = lambda r: r["district_charter"] + r["private_noncollege"]
    claims = {
        "60% fewer": round(100 * (1 - z["colleges_total"] / a["colleges_total"])) == 60,
        "That is 89% of the total drop": round(100 * (a["colleges_total"] - pre["colleges_total"]) / (a["colleges_total"] - z["colleges_total"])) == 89,
        "pipeline fell 53%": round(100 * (1 - z["total"] / a["total"])) == 53,
        "from 652 to 819": (nc(a), nc(z)) == (652, 819),
        "from 8% of new teachers to 22%": (round(100 * nc(a) / a["total"]), round(100 * nc(z) / z["total"])) == (8, 22),
        "to 3,453 by 2022–23": pre["colleges_total"] == 3453,
    }
    bad = [k for k, v in claims.items() if k in src and not v] + [k for k in claims if k not in src]
    bad += ["what-we-know: " + k for k, v in claims.items() if k in also and not v]
    if bad:
        for b in bad:
            fail("explore/index.html supply section: %r is missing or no longer matches the data" % b)
    else:
        ok("Florida supply section: %d derived figures match the data" % len(claims))


def check_snapshots():
    """Added 1 Nov 2026: the no-JavaScript table snapshots must match the data."""
    r = subprocess.run([sys.executable, rel("tools", "build-tables.py"), "--check"],
                       capture_output=True, text=True)
    if r.returncode:
        fail("table snapshot is stale; run python3 tools/build-tables.py (%s)" % r.stdout.strip())
    else:
        ok("no-JavaScript table snapshots match the data")


# --------------------------------------------------------------------
# 6. Structural HTML sanity
# --------------------------------------------------------------------
def check_html(html_files):
    bad = []
    for path in html_files:
        src = read(path)
        if not src:
            continue
        for tag in ("div", "a", "script", "style", "table", "section"):
            o = len(re.findall(r"<%s[\s>]" % tag, src))
            c = len(re.findall(r"</%s>" % tag, src))
            if o != c:
                bad.append("%s: <%s> %d open vs %d close" % (path, tag, o, c))
    if bad:
        for b in bad:
            fail(b)
    else:
        ok("HTML tag balance across %d pages" % len(html_files))


INLINE_JS = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S)


def _node_check(src, label):
    """Syntax-check a chunk of JS by writing it out and running node --check.

    Writes to the system temp dir, never inside the repo: a scratch file in a
    cloud-synced working tree can end up staged, and on OneDrive may refuse to
    delete at all."""
    fd, tmp = tempfile.mkstemp(suffix=".js")
    os.close(fd)
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(src)
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
        if r.returncode != 0:
            detail = ""
            for line in r.stderr.strip().splitlines():
                if "SyntaxError" in line:
                    detail = line.strip()
                    break
            fail("%s: %s" % (label, detail or "syntax error"))
            return False
        return True
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def check_js(html_files):
    js = rel("assets", "wmfc.js")
    if not os.path.exists(js):
        fail("assets/wmfc.js is missing")
        return
    try:
        subprocess.run(["node", "--version"], capture_output=True)
    except FileNotFoundError:
        warn("node not available — skipped all JavaScript syntax checks")
        return

    good = True
    r = subprocess.run(["node", "--check", js], capture_output=True, text=True)
    if r.returncode != 0:
        line = next((l for l in r.stderr.splitlines() if "SyntaxError" in l), "syntax error")
        fail("assets/wmfc.js: %s" % line.strip())
        good = False

    # Pages carry substantial inline JS that node never sees otherwise.
    inline = 0
    for path in html_files:
        src = read(path)
        if not src:
            continue
        for i, block in enumerate(INLINE_JS.findall(src)):
            if not block.strip():
                continue
            inline += 1
            if not _node_check(block, "%s inline script %d" % (path, i + 1)):
                good = False

    if good:
        ok("JavaScript parses — wmfc.js and %d inline script(s)" % inline)


# --------------------------------------------------------------------
# Florida public teacher-preparation census (teacher-prep page)
# --------------------------------------------------------------------
def check_census():
    D = load(os.path.join("data", "prep-census-2026.json"))
    if not D:
        return
    I, C = D.get("institutions", []), D.get("codes", {})
    bad = []
    for r in I:
        nm = r.get("name", "<unnamed>")
        if r.get("code") not in C:
            bad.append("%s: unknown code %r" % (nm, r.get("code")))
        if not str(r.get("url", "")).startswith("http"):
            bad.append("%s: no source URL" % nm)
        ev = r.get("ev")
        if ev not in ("live", "prior", "pending", "searched"):
            bad.append("%s: unknown evidence state %r" % (nm, ev))
        if ev in ("live", "prior"):
            try:
                d = datetime.date.fromisoformat(r.get("checked") or "")
                if d > TODAY:
                    bad.append("%s: checked in the future" % nm)
            except ValueError:
                bad.append("%s: live/prior row without a checked date" % nm)
        if ev in ("pending", "searched") and r.get("checked"):
            bad.append("%s: %s row must not carry a checked date" % (nm, ev))
        if ev in ("pending", "searched") and not r.get("searched"):
            bad.append("%s: %s row without a searched date" % (nm, ev))
        if r.get("code") in ("private", "public", "jobs", "district") and not r.get("quote"):
            bad.append("%s: coded %s without a quote" % (nm, r.get("code")))
    sus = sum(1 for r in I if r.get("sys") == "SUS")
    fcs = sum(1 for r in I if r.get("sys") == "FCS")
    if (sus, fcs) != (12, 28):
        bad.append("census should hold 12 SUS and 28 FCS institutions, has %d and %d" % (sus, fcs))
    if len({r.get("name") for r in I}) != len(I):
        bad.append("duplicate institution names in the census")
    page = read(os.path.join("teacher-prep", "index.html")) or ""
    n = lambda k: sum(1 for r in I if r.get("code") == k)
    want = "<em>%d of %d</em> name private schools as a place to train. %d say nothing we could find." % (n("private"), len(I), n("none"))
    if want not in page:
        bad.append("teacher-prep fallback line disagrees with the data; expected: %s" % want)
    if bad:
        for b in bad:
            fail("Census: " + b)
    else:
        pend = [r["name"] for r in I if r.get("ev") == "pending"]
        ok("Census: %d institutions, %d quoted from live pages, %d pending a live check, page agrees"
           % (len(I), sum(1 for r in I if r.get("ev") in ("live", "prior") and r.get("quote")), len(pend)))
        if pend:
            warn("Census: %d row(s) quote a search-index snippet not yet read live: %s" % (len(pend), ", ".join(pend)))


# --------------------------------------------------------------------
def main():
    html_files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for n in filenames:
            if n.endswith(".html"):
                html_files.append(os.path.relpath(os.path.join(dirpath, n), ROOT))
    html_files.sort()

    check_filenames()
    scan = load(os.path.join("data", "scan-2026.json"))
    world = load(os.path.join("data", "world-choice-2026.json"))
    fn = load(os.path.join("data", "field-notes.json"))
    sitemap = read("sitemap.xml")

    inst = check_scan(scan)
    atlas_counts = check_atlas(world)
    check_notes(fn, sitemap)
    check_fallbacks(inst, atlas_counts, html_files)
    check_universities(html_files)
    check_supply()
    check_census()
    check_snapshots()
    check_html(html_files)
    check_js(html_files)

    print("\nWMFC preflight — %s\n" % TODAY.isoformat())
    for kind, msg in LINES:
        print("  %-5s %s" % ({"ok": "ok", "fail": "FAIL", "warn": "warn"}[kind], msg))

    print()
    if FAILS:
        print("%d problem(s) must be fixed before committing." % len(FAILS))
        if WARNS:
            print("%d warning(s) — judgment calls, not blockers." % len(WARNS))
        return 1
    if WARNS:
        print("Clean, with %d warning(s) to weigh." % len(WARNS))
    else:
        print("Clean. Safe to commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
