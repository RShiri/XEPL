# PROGRESS — XEPL

Running log of the Premier League pipeline: every scrape, every platform change, and the lessons
behind both. Newest entries first in each section.

Sister project: **[XLALIGA](https://github.com/RShiri/XLALIGA)** keeps the same journal at its own
`PROGRESS.md`. The two codebases are twins — a lesson learned in one is nearly always true in the
other, so when you add an entry here, consider adding it there too.

## Platform updates & changes

<!-- progress:platform -->
- **2026-09-03** — build_schedule.py now auto-heals hand-added placeholder schedule records: merge_matches calls a new _drop_superseded_placeholders, which drops a _placeholder:true record (negative fotmob_id) the moment a real (positive-id) record appears for the same (home, away, date) — no more relying on someone remembering to delete the 3 preview matches before the first real --full sweep.
- **2026-09-03** — Added 3 hand-verified 2026/27 matchweek-1 results to SCHEDULE_2026-27.json as a preview (Arsenal 3-0 Coventry City, Hull City 2-0 Manchester United, Newcastle United 2-2 Liverpool) plus real kit colours for the 3 promoted clubs (Coventry City, Hull City, Ipswich Town) in team_colors.py, since FotMob itself is unreachable from this sandbox but web search corroborated the results/promotions/relegations across multiple independent sources (premierleague.com, ESPN gameIds, specific scorers). The 3 schedule records use negative fotmob_id + "_placeholder": true and MUST be deleted before the first real --full sweep (see CLAUDE.md) to avoid double-counting once real positive-id records arrive.
- **2026-09-03** — Ported XLALIGA's 26/27 scraper readiness work: build_schedule.py migrated off the retired live-only FotMob XML feed to the site API (season view + day-sweep JSON, legacy XML kept as last-resort fallback), three-tier matchday reconstruction (payload round -> kickoff order -> earliest-fit packing), incremental sweeps (--full for a fresh season), --debug-day/--probe-endpoints diagnostics; scraper.py got the same endpoint migration for the live-watch day fetch, an undetected-chromedriver circuit breaker (stop retrying after the first failure), and an Understat empty-twice circuit breaker; scrape_whoscored.py isolates a fresh --user-data-dir per Chrome launch (orphaned profiles were causing connection-refused failures) and now defaults --season to the newest schedule on disk; backfill.py classifies each match none/partial/full and adds --redo-partial, plus EPL_SKIP_DASHBOARD_REFRESH so a batch rebuilds once at the end instead of once per match; git_ops.py now pushes shots.js/player_lab/ and the new data/ per-season bundles, and fixed a bug where the raw-match-JSON push glob never matched the actual matches/<season>/<id>.json path; added epl/progress_log.py (this journal, called automatically from run_match.py/scrape_whoscored.py/backfill.py), epl/check_data.py, epl/weekly_update.py + epl/register_fixture_tasks.ps1/register_weekly_task.ps1 for token-free Scheduled Task automation. Also fixed a latent bug found while porting: XLALIGA's own renderer.py has the build_split.py call sitting outside the builder-loop tuple (dead code, never runs) -- EPL's version puts it correctly last inside the loop.
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
- ❌ **Didn't work** _data-sources_ — The 'openfootball placeholder data' lesson logged earlier today was wrong: WebSearch (unlike direct HTTP fetches, which the sandbox's egress proxy blocks for fotmob.com/espn.com/premierleague.com/wikipedia.org) reaches real, current sources and confirmed Coventry City / Hull City / Ipswich Town ARE genuinely 2026/27's three promoted clubs (replacing Burnley/West Ham/Wolves) -- the openfootball mirror I distrusted was actually right. Lesson: distrust a single unverified source, but WebSearch triangulated across 3+ independent queries is strong enough evidence to act on, even for facts past a training cutoff; don't tar every reachable data source with the same 'sandbox = untrustworthy' brush.  (2026-09-03)
- ❌ **Didn't work** _data-sources_ — openfootball's football.json mirror (raw.githubusercontent.com, reachable from this sandbox when FotMob/ESPN are blocked) returned a 2026-27 EPL fixture list with Coventry City / Hull City / Ipswich Town in it and Burnley / West Ham / Wolves missing -- three Championship-tier names replacing three established Premier League clubs, all at once. Treated as unreliable placeholder data rather than confirmed promotions; did not add any of it to team_colors.py.  (2026-09-03)
- ✅ **Worked** _scraper-port_ — Reading both sides fully before porting a scraper fix paid off: EPL's build_schedule.py/scrape_whoscored.py had already diverged from La Liga's with their own independent fixes (England ccode gating against foreign 'Premier League' leagues, id-based team-name canonicalisation, abandoned/replay dedup, extra Chrome stability flags) that a blind patch or wholesale file copy would have silently deleted. Read the current file in full before assuming a sibling fork's diff still applies cleanly.  (2026-09-03)
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
