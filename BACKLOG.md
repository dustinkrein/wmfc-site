# WMFC — working state

**Read this first when starting work. Update it last, before handing files back for commit.**

This file holds what changes: what's been coded, what's next, what's blocked and why.
The `wmfc-site` skill holds what doesn't change — coding schemes, house voice, brand,
repo layout. Rules live in the skill; state lives here, in version control, where it
shows up in every diff and can't drift silently.

Before any handoff: `python3 tools/check.py` must exit clean.

---

## Where the research stands

*Last updated: 26 August 2026*

| | Coverage |
|---|---|
| **Readiness Index** | 39 rows · 9 states · 34 single institutions, 5 summary rows · 11 Tier 1, 8 Tier 2, 7 Tier 3, 13 Tier 0 |
| **Index coverage depth** | 2 systematic passes (Florida, Michigan) · 1 partial (Ohio) · 6 placeholders |
| **Portable-Funding Atlas** | 175 countries · 29 coded, 12 shortlisted, 134 not yet coded |
| **Field Notes** | 09 published |
| **Corrections** | 02 published, both on the front page |

Index coverage is uneven and the site now says so on the page. `scan-2026.json` carries a
`coverage` block declaring each state's depth — systematic pass, partial pass, or
placeholder — rendered as a table above the scan and surfaced inline whenever a single
state is filtered. `tools/check.py` fails if a state has rows but no declared depth.

Five rows summarize a group rather than naming one institution ("California
institutions", "Ohio public universities", "WVU / Marshall University", "New York
institutions", "Michigan (system context)"). They carry `"scope": "aggregate"` so the
headline number can say 34 institutions and 5 summary rows instead of implying 39
institutions were read.

The Atlas has North and South America coded in full. Europe holds three coded cases
(Netherlands, Sweden, United Kingdom). Africa, Asia and Oceania are untouched.

---

## Open work, roughly in order of value

### 1. Six shortlisted countries have no `shortlist_reason`

Belgium, Denmark, India, Indonesia, Ireland, New Zealand — the pre-Americas shortlist,
added before the reason field became standard. The Atlas page now tells readers the
Americas were shortlisted "with a stated reason for each," so half the shortlist doesn't
meet the standard the page advertises.

Each needs a specific, sourced sentence naming why the country was set aside rather than
coded. Do not backfill these from memory: a plausible-sounding invented rationale is
worse than the blank, because it looks accountable and isn't. `tools/check.py` warns on
this until it's closed.

### 2. The schema can't tell a built program from an operating move

`scan-2026.json` has `tier`, and tier alone cannot distinguish *"this university built a
preparation program"* from *"this university authorizes charter schools."* Both can be
Tier 1, and they are different findings — the second is how most universities actually
entered this sector, and it never appears in a course catalog.

Consequence: three homepage numbers stay hardcoded because deriving them honestly is
impossible — "Programs built for the sector," "Operating & authorizing moves," and
"Verification coverage." Adding a field (`engagement_type`: `program` / `operates` /
`authorizes` / `none`) would unblock all three and sharpen H2 and H3. Requires recoding
all 11 Tier 1 rows, so it's a real pass, not a patch.

### 3. Thin states need full passes — the coverage table now names them publicly

Six states read `Placeholder` on the Index. That's honest, but it's also a public list of
what's undone, which raises the cost of leaving it undone.

Indiana, Arizona, Arkansas, West Virginia, California and New York are one row each.
Arizona is the highest value — the largest ESA program in the country and only ASU coded.
California and New York matter as low-choice controls: their Tier 0 rows are load-bearing
for the comparison and currently rest on a single institution each.

**Standing rule from Correction 02:** before coding any institution Tier 0, check the
state's official charter sponsor/authorizer registry. A program roster cannot tell you
what a board of trustees has authorized. This is how we got one wrong.

### 4. Atlas — Europe next

Denmark, Belgium and Ireland are already shortlisted and are the strongest uncoded cases:
long-running public funding of non-state schools, with workforce and credentialing data
available in English. Coding them would also close item 1 for three of the six.

Suriname is the highest-value shortlisted case outside Europe — it inherited the Dutch
*bijzonder onderwijs* model, which makes it a natural test of whether the Netherlands
pattern travels.

### 5. Email signup

The membership offer was removed sitewide (commit `8d64af7`), which also removed the
broken `FORM_ACTION_URL` form. There is currently **no way for a reader to subscribe.**
Decide whether that's intentional. If not, a Buttondown or Mailchimp account is needed
before any form goes back.

---

## Field Notes 08 and 09 — districts as a secondary line of inquiry

Published 26 August 2026. Both carry the same date and extend the project into a
**secondary research question**: how do school districts respond when the money moves?
The primary question is unchanged and postsecondary.

- **08 · Institutions** — *Three-quarters of Florida districts now sell to students they
  do not enroll.* Florida's a-la-carte adoption curve (roughly 1-in-3 to about 75% of 67
  districts in twelve months), set against Texas districts declining a $1,500-per-activity
  state allotment and a West Virginia near-zero.
- **09 · The seam** — *A Florida district needed a school model. It bought one from a
  microschool operator.* Polk County contracted WonderHere; Elizabeth City-Pasquotank
  built its design from visits to private microschools. Set against the Index's Florida
  finding of no education-school program built for the sector.

**Why the counter-cases are load-bearing.** Note 08 leads with Florida adaptation and then
spends three paragraphs on districts that refused. That is deliberate: adaptation reads as
a finding rather than advocacy precisely because it did not happen everywhere. Do not trim
the Texas and West Virginia material to tighten the note.

**Two open limits are stated in-text and should be closed, not quietly dropped.**
The West Virginia figure is a *near*-zero — the Hope provider directory was read across the
school block from roughly M through Y only, because the directory's search box is a
JavaScript postback that cannot be queried programmatically. Five minutes in a browser
resolves it. And no Florida district has published a-la-carte revenue, so Note 08's opening
limit stands until district Annual Financial Reports or records requests produce a number.

### Follow-on research queue

1. **Florida's enrolled 2026 GAA and implementing bill.** An enrollment-decline
   stabilisation supplement passed, but it is named three different ways across three
   sources — "Educational Enrollment Stabilization" (Senate), "Family Empowerment
   Scholarship Stabilization" (House implementing bill), "Public School Enrollment
   Stabilization Fund" (FEA). One name points at districts, another at the scholarship
   programme. If Florida has begun insulating districts from portability, it weakens the
   competitive premise underlying Note 08. **Highest value open item.**
2. **South Carolina ESTF legislative history.** Secondary sourcing suggests homeschool
   organisations requested their own exclusion from the programme to preserve regulatory
   independence. If primary sources confirm it, that is a Field Note on its own: portable
   funding declined by its intended beneficiaries. Do not publish on the tracker alone.
3. **Federal scholarship tax credit, effective 1 January 2027.** $1,700, routed through
   scholarship organisations rather than family accounts, states opt in. Because SFOs are
   the institutions that built Florida's district channel, this could export the Florida
   model to states with no Florida-style ESA. Nothing on the site covers it yet.
4. **Source-link resolution** for the 14 URLs in Notes 08 and 09. Not yet run.

Six background research memos supporting these notes were produced in the 15 August thread
and live outside the repo. They are internal-facing — they narrate hypothesis revision and
carry "what to check next" sections — and are not publishable without rewriting.

### Scope decision deferred

The Index and Atlas are postsecondary-only. District findings currently live in Field Notes.
If the district corpus keeps growing, decide whether it earns its own section rather than
straining the Field Notes format.

---

## Standing decisions

Things settled once, easy to reopen by accident.

- **Two tier systems, no shared meaning.** Readiness Index tiers code *institutions* by
  what they built. Atlas tiers code *our coverage depth* by country. Never write "Tier N"
  in an Atlas context — use Coded / Shortlisted / Not yet coded.
- **A checked null is a finding; a blank is not.** Cuba, Mexico, Brazil, Uruguay, Costa
  Rica, El Salvador, Panama and Venezuela are *coded* entries recording that money does
  not follow the child. Coding a country is not the same as finding portability in it.
- **Hardcoded numbers in HTML are a safety net, not a second source.** They exist so
  nothing goes blank if a fetch fails. `tools/check.py` verifies they still agree with
  the data — on 25 Aug 2026 the Atlas showed two different numbers for "Not yet coded"
  on the same page, which is what prompted the script.
- **Verify the live site with Chrome tools, never `web_fetch` alone.** `web_fetch`
  returns blank for raw `.json` URLs and strips trailing slashes. It has produced false
  "the site is broken" reports twice.
- **Never hand over a ZIP.** Windows 8.3 extraction once mangled the repo into
  `INDEX~1.HTM`. Edit in the clone. The preflight guards against `~` in filenames.
- **Don't run `git` against this clone from a Claude session.** The working tree is on
  OneDrive, which blocks the sandbox from deleting files git creates. A `git status` on
  25 Aug 2026 left `.git/index.lock` behind and GitHub Desktop refused to commit with
  *"A lock file already exists in the repository."* Read the tree, edit files, run the
  preflight — but leave git itself to GitHub Desktop. If the error appears anyway, delete
  `.git/index.lock` (hidden folder; enable **View → Hidden items**). Always safe when no
  git operation is actually running.
- **One thread edits at a time.** Every thread in this project opens the same clone, and
  nothing isolates them. Two threads editing in parallel silently overwrite each other.
  Finish and commit one piece of work before starting another elsewhere.

---

## Publishing loop

1. Edit files in the clone: `C:\Users\dusti\OneDrive\Documents\GitHub\wmfc-site`
2. Field Notes changed? `python3 tools/build-notes.py`, then add any new `/notes/NN/`
   URL to `sitemap.xml`
3. `python3 tools/check.py` — must exit clean
4. Update this file
5. Dustin: **GitHub Desktop → Commit to main → Push origin.** Vercel redeploys in ~30s.
