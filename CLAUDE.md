# CLAUDE.md — XEPL project guide (read this first)

**English Premier League match analytics.** Two outputs from one scraped dataset: an interactive
**web dashboard** (`epl_dashboard/`, static site) and a per-match **PNG infographic**
(`epl/renderer.py`). Cloned from the La Liga (XLALIGA) system; `xg_core/` is the shared model.

- **Live site:** root `index.html` redirects to `epl_dashboard/`. (Enable GitHub Pages on `main`.)
- This repo is self-contained: `epl/` pipeline, `epl_dashboard/` site, `xg_core/` model,
  `team_logos/epl/` crests, `epl_png/` published PNGs.

## CURRENT STATE
- **Populated — four seasons complete.** `2022-23`, `2023-24`, `2024-25` and `2025-26` are fully
  scraped (**380/380** matches each, 1,520 total): schedule spines in `epl/schedules/`, raw scrapes
  in `epl/matches/<season>/`, and the shipped `epl_dashboard/{data.js,players.js,shots.js}` +
  `matches_detail/*.js` carry the full rich xG/shot/player layer. The scraper pipeline
  (`build_schedule.py`, `scraper.py`) was brought up to date for 2026/27 (ported from XLALIGA's own
  26/27 readiness work: the FotMob endpoint migration, matchday reconstruction, incremental sweeps
  — see the gotchas below), but every FotMob/ESPN endpoint is blocked from this sandboxed session's
  network, so `--full` still needs to be run once on a machine with real network access to actually
  pull the season in. **`epl/schedules/SCHEDULE_2026-27.json` currently holds 3 HAND-ADDED
  placeholder records** (matchweek 1: Arsenal 3-0 Coventry City, Hull City 2-0 Manchester United,
  Newcastle United 2-2 Liverpool — real results, found via web research since FotMob itself isn't
  reachable from here) as a preview that the promoted-club pipeline works end to end. Each has a
  negative `fotmob_id` and `"_placeholder": true`. No manual cleanup needed before the first real
  `--full` sweep — `merge_matches`/`_drop_superseded_placeholders` auto-drop a placeholder the
  moment a real (positive-id) record shows up for the same (home, away, date), so they can't
  double-count a match in the standings; any placeholder for a fixture the sweep hasn't reached
  yet is left alone. `epl/team_colors.py` already has real kit colours for the three promoted clubs
  (Coventry City, Hull City, Ipswich Town, replacing relegated Burnley/West Ham United/Wolverhampton
  Wanderers) so nothing needs fixing there once the real schedule lands.
- **To add or refresh a season** — run on a machine with network + Chrome (the scrapers need
  FotMob/WhoScored, which are firewalled in some CI/cloud environments, this one included — see
  the FotMob endpoint gotcha below). Swap the `--season` value (e.g. `2026-27`):
  ```bash
  py epl/build_schedule.py --season 2026-27 --full     # FotMob 47 → standings/results spine (whole season)
  py epl/download_crests.py                             # crests → team_logos/epl/
  py epl/scrape_whoscored.py --season 2026-27           # ~1h, Chrome (rich xG/shot/player layer)
  py epl/render_missing.py --season 2026-27              # PNGs for matches scraped in bulk, publish to epl_png/
  py epl_dashboard/build_match_details.py && py epl_dashboard/build_players.py \
    && py epl_dashboard/build_database.py && py epl_dashboard/build_shots.py \
    && py epl_dashboard/build_player_lab.py && py epl_dashboard/build_data.py \
    && py epl_dashboard/build_split.py
  git add -A && git commit -m "EPL 2026/27 data" && git push
  ```
  Or just `py epl_dashboard/build_site.py`, which runs the same eight builders (render_missing
  first, build_split last) in one call. **`build_split.py` must be the LAST step of every
  rebuild** — see the per-season bundles gotcha below; skipping it (or running it out of order)
  leaves the live site on the previous build even though `data.js`/`players.js`/`shots.js` look
  freshly generated on disk. For a routine refresh once a season is underway,
  `py epl/build_schedule.py --season 2026-27` (no `--full`) sweeps only what's new — a handful of
  requests instead of 300+ — or run `py epl/weekly_update.py` for schedule refresh + scrape +
  push in one command (see the automation gotcha below).

## Config
FotMob league **47** (`EPL_FOTMOB_LEAGUE_ID`); WhoScored
`Regions/252/Tournaments/2/England-Premier-League` (`EPL_WHOSCORED_URLS`); Understat slug `EPL`;
crests `team_logos/epl/`; PNGs `epl_png/` (`EPL_PNG_SUBDIR`); raw scrapes `epl/matches/`
(`EPL_MATCH_DIR` for rebuilds in a clean clone).

## European zones (season-aware)
UCL cut is **top 5** for 2024/25 & 2025/26 (England's coefficient-earned 5th place), **top 4** for
earlier seasons; then Europa, Conference play-off, bottom 3 relegation. Lives in
`epl_dashboard/app.js` `zoneOf()`/`uclSpots()` AND the projection Monte-Carlo — edit both if you
change it.

## Design system — "Broadcast Kinetic"
The dashboard skin (`epl_dashboard/styles.css`, `match.css`) is a live-sport broadcast-graphics
identity: carbon ground, ONE signal accent colour (`--accent: #a855f7`, "Premier League purple" —
picked instead of La Liga's lime so the two forks don't look identical), chamfered plates
(`clip-path: var(--plate-cut)`), slanted tabs/buttons/chips (`--slant`/`--slant-sm`), condensed
italic display type (Barlow Condensed/Barlow), and hatched diagonal-stripe comparison bars
(`--hatch-accent`) instead of flat fills. `--brand-red: #ff2a4d` is the only other semantic colour
(negative/relegation) and is shared with La Liga on purpose — it's sport-neutral. No
`border-radius` anywhere in this skin. Ported from `XLALIGA`'s `feat/dashboard-beta` branch —
re-derive the accent per fork rather than copying another sport's colour blindly.

## Gotchas
- **Team-matcher must NOT strip "united"/"city"** — `epl/scrape_whoscored._key` keeps them so the
  two Manchester clubs never collide (the analogue of La Liga's "don't strip real" rule).
- **xG/xA come from `xg_core/`** (shared, league-agnostic; EPL passed as the league key, falls
  back to the `_global` shift until an EPL corpus is trained).
- **Raw match JSONs are gitignored** (`epl/matches/20*/*.json`, ~2 MB each). The dashboard ships
  the derived `epl_dashboard/matches_detail/*.js` instead.
- **players.js fields are `g`/`a`/`xg`/`mp`** (not `goals`/`assists`); `app.js` reads those.
- **Scores come from WhoScored, not the FotMob schedule** — FotMob's historical/mid-season feed
  reports `0-0` for some games (17 in 2022-23, 9 in 2023-24, 1 in 2024-25) and null for unplayed
  fixtures. `build_data` prefers the rich WhoScored score whenever a match has scraped events (it
  matches the event-derived score for every match, every season); the schedule is only the fallback.
- **The site loads per-season bundles, not the monolithic files.** `index.html`/`match.html` load
  `epl_dashboard/data/index.js` (`window.LL_INDEX`: season list + a content-hash `v` cache-buster +
  `teamColors`) statically; `app.js`/`match.js` fetch `data/<season>.js` on demand
  (`loadSeason()`/`loadSeasonData()`) instead of the old monolithic `data.js`/`players.js`/
  `shots.js` (those three still get written by their builders and stay in git — `build_split.py`
  slices them into `data/`). **`build_split.py` must run LAST**, after `build_data.py` — it reads
  `data.js` off disk. Forgetting it (or running it before `build_data.py`) means the site silently
  keeps serving the previous build's `data/*.js` bundles.
- **Player Lab event files are keyed by SEASON, not just team** —
  `player_lab/<season>/<team-slug>.js` (`window.LL_PLAYERLAB[season][team]`), rebuilt from scratch
  every run by `build_player_lab.py` so a stale team-only file never lingers. `app.js`'s
  `plLoadTeam()`/`plEvents()` read `[season][team]`; a naive `[team]`-only key would sum a
  player's shot/pass maps across every scraped season instead of the one on screen.
- **Match Centre team-colour collision guard** — `match.js` `teamColours()` measures the CIE76 ΔE
  between the home/away primaries (from `epl/team_colors.py` via `LL_INDEX.teamColors`); two clubs
  whose primaries are near-identical (e.g. Liverpool vs Nottingham Forest, both red) fall back the
  away side to its secondary kit colour, then to a neutral. Every downstream mark (shot map, pass
  network, stat bars) reads `D.home.color`/`D.away.color` **after** this runs, so add new
  colour-coded marks after `boot()` sets them, not before.
- **In-browser PNG export** (`match_export.js`, `window.LL_EXPORT.render/download`) draws the match
  board straight to a `<canvas>` in the Broadcast Kinetic skin and downloads it client-side — no
  server, works on the deployed GitHub Pages site. It's the "Download image" button next to the
  pipeline-rendered "Pipeline PNG" link in the Match Centre header; the pipeline PNG is still
  needed for anything that posts a pre-rendered image (e.g. social automation), so both stay.
- **`epl/render_missing.py`** renders PNGs from raw match JSONs for matches scraped in bulk
  (`scrape_whoscored.py` only saves JSON, no image) and publishes them to `epl_png/` — a PNG that
  only exists in the git-ignored `epl/output/` 404s on GitHub Pages. It's the first step of every
  rebuild (`build_site.py`, `renderer._refresh_web_dashboard_db`); `build_data.py`'s `_find_png()`
  also self-heals by copying an `epl/output/`-only PNG into `epl_png/` the next time it runs.
- **FotMob's fixture feed moved twice** — `api.fotmob.com/matches?date=` (the original token-free
  XML feed) went LIVE-ONLY in 2026: root `<live>/<exmatches>`, `?date` is ignored, so it rarely has
  anything for a past or future date any more. `build_schedule.py` and `scraper.fotmob_fetch_wc_matches`
  now try `www.fotmob.com/api/data/leagues?id=47&season=` (whole season, one request, carries the
  round number) and `www.fotmob.com/api/data/matches?date=` (site API, every league that day)
  first, falling back to the legacy XML endpoint only if those come back empty. Every one of these
  is blocked from this sandboxed session's network policy (403 via the proxy) — the openfootball
  static mirror (`raw.githubusercontent.com/openfootball/football.json`) is reachable here but its
  future-season files can be placeholder/template data, not confirmed fixtures — don't trust it for
  real team names. Run the scrapers on a machine with real network access.
- **"Premier League" is not a unique league name on FotMob** — at least a dozen countries (Russia,
  Egypt, Wales, Canada, Kazakhstan, Ukraine, Belarus, Azerbaijan, …) run a division literally named
  "Premier League". `_is_epl`/`_is_our_league` (`build_schedule.py`, `scraper.py`) always accept an
  exact FotMob league id match, but gate the *name* fallback on the England country code (`ccode`)
  — matching by name alone would occasionally pull in a foreign league's fixtures on a day-sweep.
- **Matchday isn't always in FotMob's feed.** `build_schedule.py`'s `_fill_missing_rounds` tries,
  in order: the round field the payload already carries; the fixture order; kickoff order; then
  earliest-fit packing (each fixture in date order drops into the earliest round with a free slot
  and neither team in it — robust to postponed/rearranged games, unlike a naive "new round when a
  team recurs" split, which fragments the season). If nothing validates, matchday is left empty
  rather than published wrong.
- **`build_schedule.py` is incremental by default** — with a schedule already on disk it sweeps
  from a few days before the last finished match to a fortnight ahead and merges in
  (`sweep_window`/`merge_matches`); `--full` forces the whole season window (needed once, when a
  season is brand new). `--debug-day YYYY-MM-DD` dumps what a date's feed actually contains and
  `--probe-endpoints YYYY-MM-DD` tries every known fixture source — reach for these before assuming
  "no matches" means the season hasn't started.
- **`EPL_SKIP_DASHBOARD_REFRESH=1`** skips `renderer._refresh_web_dashboard_db()` entirely —
  `backfill.py` sets it for the whole batch and rebuilds once at the end instead, because the
  per-match refresh re-reads every season and rewrites every derived file (fourteen full rebuilds
  racing a live Chrome, for a fourteen-match batch, is how you crash the machine).
- **A WhoScored failure used to be invisible and permanent** — the match still saved (FotMob shots
  only, no event stream), so a plain "already scraped" check counted it done and no later run
  would ever fill in the maps/lineups/pass network. `backfill.py` now classifies each match
  none/partial/full (`_scrape_state`) and `--redo-partial` retries only the partials.
- **`PROGRESS.md` is an append-only journal, not hand-maintained prose** — `epl/progress_log.py`
  (`log_scrape`/`log_platform`/`log_lesson`) is called automatically from `run_match.py`,
  `scrape_whoscored.py` and `backfill.py`, so every scrape — scheduled task, bulk backfill, or a
  manual run — leaves a row in the Scrape log table whether it succeeded or not. Write the Platform
  and Lessons sections by hand or with `py epl/progress_log.py platform "..."` /
  `... lesson --worked/--failed "..."`. `epl/check_data.py --season <season> [--detail]` reports
  what each scraped match's raw JSON actually contains (sources, event count, xG, player count) —
  reach for it before assuming a thin dashboard page means a scrape bug rather than a partial scrape.
- **Two ways to automate scraping on a Windows machine**: `epl/register_tasks.ps1` registers one
  Scheduled Task per fixture that runs `run_match.py --fotmob-id <id>` directly (needs `GIT_TOKEN`
  in `.env` for `git_ops.py`'s auto-push). `epl/register_fixture_tasks.ps1` is the newer,
  token-free alternative: one Scheduled Task per fixture that instead runs
  `epl/weekly_update.py --season <season>` at kick-off+3h, which re-sweeps the whole season
  (fixtures refresh + `backfill.py` for anything newly finished) and pushes with plain `git push`
  against the local clone's own already-authenticated remote — no token needed. Both can coexist;
  `weekly_update.py` is also runnable on its own fixed weekly schedule via
  `epl/register_weekly_task.ps1` as a safety net that catches whatever a missed per-fixture run did.
