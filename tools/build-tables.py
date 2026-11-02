#!/usr/bin/env python3
"""Write a static, no-JavaScript snapshot of the two big data tables.

    python3 tools/build-tables.py          # rewrite the snapshots
    python3 tools/build-tables.py --check  # exit 1 if a snapshot is stale

Readers without JavaScript, search engines and text-only tools used to see
"Loading the dataset..." and nothing else. The page scripts still replace
these rows on load; the snapshot only has to be correct, not interactive.
Rows sit between <!-- SNAPSHOT:START --> and <!-- SNAPSHOT:END --> markers.
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START, END = "<!-- SNAPSHOT:START -->", "<!-- SNAPSHOT:END -->"


def esc(s):
    return html.escape(html.unescape(re.sub(r"<[^>]+>", "", s or "")), quote=False)


def index_rows():
    S = json.load(open(os.path.join(ROOT, "data", "scan-2026.json"), encoding="utf-8"))
    cat, sp = S["categories"], S.get("tier1_split", {})
    out = []
    for r in S["institutions"]:
        eng = r.get("engagement") or []
        lab = cat[r["tier"]]["label"]
        if r["tier"] == "Tier 1" and sp:
            lab += " · " + sp["prep" if "program" in eng else "ops"]["short"]
        out.append('<tr><td class="nm">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                   % (esc(r["name"]), esc(r["state"]), esc(lab), esc(" · ".join(eng)) or "—", esc(r["checked"])))
    return "\n".join(out)


def university_rows():
    U = json.load(open(os.path.join(ROOT, "data", "universities-2026.json"), encoding="utf-8"))
    lab = {"compete": "Compete", "supply": "Supply", "fortify": "Fortify",
           "evidence": "Studies or debates it", "none": "Searched, none found"}
    lists = {"aau": "AAU", "innovative": "Most Innovative"}
    out = []
    for r in sorted(U["institutions"], key=lambda r: r["name"]):
        top = r["initiatives"][0]["name"] if r["initiatives"] else ("None found" if r.get("scored") else "Not yet scored")
        resp = "Unresolved, counted as none" if r.get("evidence_state") == "unresolved" else lab[r["direction"]]
        score = "%.1f" % r["portfolio"] if r.get("portfolio") is not None else "—"
        out.append('<tr><td class="nm">%s</td><td>%s</td><td>%s</td><td class="num">%s</td><td>%s</td></tr>'
                   % (esc(r["name"]) + " (" + esc(r["state"]) + ")", ", ".join(lists[l] for l in r["lists"] if l in lists),
                      esc(top), score, resp))
    return "\n".join(out)


TARGETS = [("research/index.html", index_rows), ("universities/index.html", university_rows)]


def render(src, rows):
    a, b = src.index(START), src.index(END)
    return src[:a + len(START)] + "\n" + rows + "\n" + src[b:]


def main():
    check = "--check" in sys.argv
    stale = []
    for path, fn in TARGETS:
        p = os.path.join(ROOT, path)
        src = open(p, encoding="utf-8").read()
        new = render(src, fn())
        if new != src:
            if check:
                stale.append(path)
            else:
                open(p, "w", encoding="utf-8").write(new)
                print("wrote snapshot:", path)
    if check and stale:
        print("stale snapshot: " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
