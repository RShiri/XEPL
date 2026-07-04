# CLAUDE.md — XEPL project guide (read this first)

**English Premier League match analytics.** Two outputs from one scraped dataset: an interactive
**web dashboard** (`epl_dashboard/`, static site) and a per-match **PNG infographic**
(`epl/renderer.py`). Cloned from the La Liga (XLALIGA) system; `xg_core/` is the shared model.

- **Live site:** root `index.html` redirects to `epl_dashboard/`. (Enable GitHub Pages on `main`.)
- This repo is self-contained: `epl/` pipeline, `epl_dashboard/` site, `xg_core/` model,
  `team_logos/epl/` crests, `epl_png/` published PNGs.

## CURRENT STATE
- **Pipeline-ready, EMPTY.** `epl/schedules/SCHEDULE_2025-26.json` is an empty placeholder and the
  shipped `epl_dashboard/{data.js,players.js,shots.js}` are valid-but-empty. Fill it on a machine
  with network + Chrome (the scrapers need FotMob/WhoScored, which are firewalled in some CI/cloud
  environments):
  ```bash
  py epl/build_schedule.py --season 2025-26            # FotMob 47 → standings/results spine
  py epl/download_crests.py                             # crests → team_logos/epl/
  py epl/scrape_whoscored.py --season 2025-26           # ~1h, Chrome (rich xG/shot/player layer)
  py epl_dashboard/build_match_details.py && py epl_dashboard/build_players.py \
    && py epl_dashboard/build_database.py && py epl_dashboard/build_shots.py \
    && py epl_dashboard/build_data.py
  git add -A && git commit -m "EPL 2025/26 data" && git push
  ```

## Config
FotMob league **47** (`EPL_FOTMOB_LEAGUE_ID`); WhoScored
`Regions/252/Tournaments/2/England-Premier-League` (`EPL_WHOSCORED_URLS`); Understat slug `EPL`;
crests `team_logos/epl/`; PNGs `epl_png/` (`EPL_PNG_SUBDIR`); raw scrapes `epl/matches/`
(`EPL_MATCH_DIR` for rebuilds in a clean clone).

## European zones (2025/26-accurate)
Top **5** → Champions League, 6th → Europa, 7th → Conference, bottom 3 → relegation. Lives in
`epl_dashboard/app.js` `zoneOf()` AND the projection Monte-Carlo — edit both if you change it.

## Gotchas
- **Team-matcher must NOT strip "united"/"city"** — `epl/scrape_whoscored._key` keeps them so the
  two Manchester clubs never collide (the analogue of La Liga's "don't strip real" rule).
- **xG/xA come from `xg_core/`** (shared, league-agnostic; EPL passed as the league key, falls
  back to the `_global` shift until an EPL corpus is trained).
- **Raw match JSONs are gitignored** (`epl/matches/20*/*.json`, ~2 MB each). The dashboard ships
  the derived `epl_dashboard/matches_detail/*.js` instead.
- **players.js fields are `g`/`a`/`xg`/`mp`** (not `goals`/`assists`); `app.js` reads those.
