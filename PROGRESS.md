# PROGRESS — XEPL

Running log of the Premier League pipeline: every scrape, every platform change, and the lessons
behind both. Newest entries first in each section.

Sister project: **[XLALIGA](https://github.com/RShiri/XLALIGA)** keeps the same journal at its own
`PROGRESS.md`. The two codebases are twins — a lesson learned in one is nearly always true in the
other, so when you add an entry here, consider adding it there too.

## Platform updates & changes

<!-- progress:platform -->
- **2026-09-03** — Ported XLALIGA's `feat/dashboard-beta` work onto XEPL: (1) bug fixes — Player
  Lab event files now keyed `player_lab/<season>/<team>.js` (was already season-nested one level
  differently; restructured to match the per-season split architecture), removed the
  `document.write`/`Date.now()` cache-busting script injection in `index.html`/`match.html`, added
  a CIE76 ΔE team-colour collision guard to `match.js` `teamColours()`, added `epl/render_missing.py`
  to render+publish PNGs for bulk-scraped matches missing one; (2) "Broadcast Kinetic" design skin
  site-wide with `--accent: #a855f7` (Premier League purple, chosen instead of La Liga's lime so
  the two forks don't look identical); (3) per-season data split
  (`build_split.py` → `data/index.js` + `data/<season>.js`, wired as the last rebuild step); (4)
  in-browser PNG export (`match_export.js`, no server needed, works on GitHub Pages).
- **2026-07-07** — Wired the v3 (23-feature) xG + retrained xA into both the dashboard and the
  PNGs; added seasons 2022/23 and 2023/24 (schedule spine + rich WhoScored layer), so four full
  seasons are live (1520 match-centre pages).
- **2026-07-04** — Premier League code extracted out of XLALIGA into this standalone repo.

## Lessons — what worked / what didn't

<!-- progress:lessons -->
- ✅ **Worked** _dashboard-beta port_ — XLALIGA's `feat/dashboard-beta` diff (old La Liga →
  Broadcast Kinetic) applied to XEPL's structurally-near-identical files with `patch --fuzz=5`
  almost hunk-for-hunk (51/52 in `app.js`, 29/30 in `match.js`, 18/19 in `index.html`) since both
  repos share the same BCN/WC2026 fork lineage and file layout. Only the header/branding markup
  and the two big CSS files needed a from-scratch rewrite (too much text differs — "La Liga" vs
  "Premier League", lime vs purple, tab lists — for a text diff to apply cleanly). When porting a
  design/feature branch between sibling forks, try the literal patch first; it's far cheaper than
  reconstructing a diff's intent from prose, and tells you exactly where the forks have actually
  diverged (the hunks that fail) rather than guessing.  (2026-09-03)
- ✅ **Worked** _player_lab_ — before this pass, EPL's `build_player_lab.py` already nested by
  season one level differently (`LL_PLAYERLAB[team][season]`, one file per team covering every
  season) instead of XLALIGA's original team-only bug (`LL_PLAYERLAB[team]`, summed across
  seasons). EPL never had the cross-season stat-bloat bug XLALIGA fixed — but restructuring to
  `player_lab/<season>/<team>.js` still paid off: a team's file now ships one season's events
  instead of all four, so switching teams in Player Lab is a much smaller fetch.  (2026-09-03)

## Scrape log

<!-- progress:scrapes -->
| When | Season | Trigger | Target | Result | Took | Notes |
|---|---|---|---|---|---|---|
| 2026-07-07 | 2022-23 | bulk backfill (historic) | full season · 380 matches | ✅ 380 saved | — | — |
| 2026-07-07 | 2023-24 | bulk backfill (historic) | full season · 380 matches | ✅ 380 saved | — | — |
| 2026-07-04 | 2024-25 | bulk backfill (historic) | full season · 380 matches | ✅ 380 saved | — | — |
| 2026-07-01 | 2025-26 | bulk backfill (historic) | full season · 380 matches | ✅ 380 saved (149 played to date) | — | the default season |
