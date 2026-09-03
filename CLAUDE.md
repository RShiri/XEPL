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
  freshly generated on disk.

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
