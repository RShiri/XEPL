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
  `matches_detail/*.js` carry the full rich xG/shot/player layer. `epl/schedules/SCHEDULE_2026-27.json`
  is an empty placeholder awaiting FotMob's 2026/27 fixture release.
- **To add or refresh a season** — run on a machine with network + Chrome (the scrapers need
  FotMob/WhoScored, which are firewalled in some CI/cloud environments). Swap the `--season` value
  (e.g. `2026-27` once fixtures drop):
  ```bash
  py epl/build_schedule.py --season 2026-27            # FotMob 47 → standings/results spine
  py epl/download_crests.py                             # crests → team_logos/epl/
  py epl/scrape_whoscored.py --season 2026-27           # ~1h, Chrome (rich xG/shot/player layer)
  py epl_dashboard/build_match_details.py && py epl_dashboard/build_players.py \
    && py epl_dashboard/build_database.py && py epl_dashboard/build_shots.py \
    && py epl_dashboard/build_player_lab.py && py epl_dashboard/build_data.py
  git add -A && git commit -m "EPL 2026/27 data" && git push
  ```

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

## Scraper button + PROGRESS.md
- `py server.py` serves the dashboard **and** a loopback control API (`/api/*`) on **port 8779**
  (XLALIGA uses 8778, so both can run at once): http://localhost:8779/epl_dashboard/index.html.
  While it runs, a **⚡ Scraper** button appears in the dashboard header — locally and on the live
  site (the API sends the CORS + Private-Network headers Chrome needs for an https page calling
  loopback). It runs the same commands as the CLI (refresh fixtures · scrape everything not yet
  scraped · scrape specific WhoScored ids · scrape one FotMob id · rebuild · commit + push),
  streams their output into the panel, and journals the outcome. **The panel is one button** — *⚡ Update
  everything*: it picks the season (the one with unscraped played matches, else the newest),
  refreshes the fixture list, scrapes what's missing, rebuilds and pushes; the refresh is an
  optional step so a FotMob outage doesn't block the scrape. Season/action pickers, id and limit
  fields and a **Commit & push** button live behind **Advanced ▾**. Pushing always uses the local
  clone's own remote, never `git_ops`' `XWORLDCUPTWIT_REPO`. The browser never sends a
  command — it picks an action name and `server.py` builds the argv (`server.ACTIONS`).
  Front-end: `epl_dashboard/control.js`, which injects nothing when no server answers, so the
  public site is untouched. Optional shared secret: `EPL_CONTROL_TOKEN`.
- **`PROGRESS.md`** is the running journal: every scrape is appended automatically (from
  `run_match.py`, `scrape_whoscored.py`, `scrape_resilient.py`, `backfill.py` and the button),
  plus platform changes and what worked / what didn't. Append with
  `py epl/progress_log.py {scrape|platform|lesson|show}` or the panel's note box. XLALIGA keeps
  the same journal — lessons usually transfer between the two.
