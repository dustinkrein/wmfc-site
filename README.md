# When Money Follows the Child (WMFC)

Independent, nonpartisan research tracking how postsecondary institutions respond as K-12 education funding becomes portable.

Static site. No build step, no framework, no dependencies. Plain HTML, one CSS file, one JS file, one JSON dataset.

---

## Getting online — do these in order

### 1. Put this folder on GitHub

Create a new **private** repository named `wmfc-site` on github.com (private for now; you can flip it public later).

Then, in a terminal, from inside this folder:

```bash
git init
git add .
git commit -m "Initial site: The Record brand system, 2026 baseline"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/wmfc-site.git
git push -u origin main
```

If you'd rather avoid the terminal: on GitHub, create the repo, click **uploading an existing file**, and drag this entire folder in. That works fine.

### 2. Deploy on Vercel

1. Go to vercel.com → **Add New… → Project**
2. **Import** the `wmfc-site` repository
3. Framework preset: **Other**. Leave build command and output directory **empty** — this is a static site.
4. Click **Deploy**

You'll get a live URL like `wmfc-site.vercel.app` in about 20 seconds.

### 3. Point your domain at it

In Vercel: **Project → Settings → Domains → Add**, enter your domain.

Vercel will show you what to add at your registrar. Typically:

| Type | Name | Value |
|---|---|---|
| A | `@` | `76.76.21.21` |
| CNAME | `www` | `cname.vercel-dns.com` |

**Use the exact values Vercel shows you** — they occasionally change. In GoDaddy: *My Products → Domain → DNS → Manage Zones*. Delete any conflicting parking records GoDaddy added by default.

DNS usually propagates in 10–30 minutes. HTTPS is automatic.

### 4. Wire up the email form

The signup form on the homepage has a placeholder: `FORM_ACTION_URL` in `index.html`.

Pick one (all have free tiers):

- **Buttondown** — buttondown.email — best fit. Real newsletter tool, free to 100 subscribers, gives you a form action URL and handles unsubscribes. Recommended.
- **Formspree** — formspree.io — simplest. Free to 50 submissions/month, emails you each signup. Good if you just want to collect addresses for now.
- **ConvertKit / Kit** — free to 10,000 subscribers, heavier but scales furthest.

Replace `FORM_ACTION_URL` with the action URL they give you, commit, push. Vercel redeploys automatically.

### 5. Set your contact address

In `about/index.html`, replace `hello@[YOUR-DOMAIN]` with your real address.

---

## How we work together on this

**The dataset is the source of truth.** `data/scan-2026.json` holds every coded institution, hypothesis, gap and context figure. The research page reads that file at load time.

That means: **updating the research is editing one JSON file.** I produce the updated JSON in our conversation, you replace the file, commit, push — Vercel redeploys in seconds. No page edits, no HTML, no rebuilding.

Adding a new institution looks like this:

```json
{
  "name": "Example State University",
  "state": "Ohio",
  "tier": "Tier 2",
  "checked": "2026-08-03",
  "evidence": "What was found, and what it means. HTML allowed for <b>emphasis</b>.",
  "source": "https://example.edu/program-page"
}
```

`tier` must be one of: `Tier 1`, `Tier 2`, `Tier 3`, `Tier 0`. The labels and colors come from the `categories` block at the top of the file — change them once there and every page updates.

---

## File map

```
/
├── index.html              Homepage
├── research/index.html     The Readiness Index (reads data/scan-2026.json)
├── method/index.html       Method, limits, corrections log
├── about/index.html        Mission, vision, independence, contact
├── data/
│   └── scan-2026.json      ← THE DATASET. Edit this to update research.
├── assets/
│   ├── wmfc.css            The Record brand system — all styling
│   ├── wmfc.js             Motion + expandable rows
│   └── favicon.svg         WMFC monogram
├── vercel.json             Clean URLs, security headers
└── README.md               This file
```

---

## Brand system — "The Record"

Do not override these in page files. Edit `assets/wmfc.css`.

**Color — one anchor.** Oxblood `#6E1F2C` is the only color. It marks the italic F, the 5px page rule, card top-borders, data fills, key numerals and links. Nothing else. Secondary data series use rule gray `#C9C9C3`. No green, no gold, no second accent. No red-and-blue together, ever.

**Type.** Georgia serif for what we say (headlines, numbers, product names). System sans for how we work (body, UI, labels). Numerals are always tabular.

**Geometry.** Zero rounded corners. The 5px oxblood rule runs across the top of every page and above the footer — the signature. Cards carry top-borders, never shadows.

**Motion.** Data animates; decoration never does. Bars sweep left-to-right — the direction of *following* — once, on first view. Key numerals count up once. **The zero holds still**: when the finding is an absence, its bar never fills. `prefers-reduced-motion` is respected.

**Legibility floor (binding).** No meaning-bearing text under 13px. No gray lighter than `#6E6E76` on white. Tiny all-caps is for eyebrows and column heads only.

**Voice.** "Institutions are responding" / "declining to engage" — both are coded observations. Never "falling behind" or "failing to adapt." Never "nothing exists" — always "nothing found." Cite peer organizations generously and by name. Corrections run on the front page, never as silent edits.

**Imagery.** No stock photography. No classrooms, no children. Data, documents, institutions.

---

## Local preview

The research page fetches JSON, and browsers block that over `file://`. To preview locally:

```bash
npx serve
```

Then open the localhost URL it prints. The homepage, method and about pages work fine opened directly.

---

## Notes

- Nothing here locks you in. Static HTML on GitHub — portable to any host, any time.
- The site prints cleanly. The brand system is document-native by design, so what a member sees on screen is what a dean prints.
- Every published number links to its source. Keep it that way; it is the whole basis of the thing.

