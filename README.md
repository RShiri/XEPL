# XEPL — English Premier League match analytics

Multi-source analytics for the **English Premier League**: a standings + results dashboard, an
xG efficiency lab, a per-match "Match Centre" (shot/pass/dribble maps, all-goals reconstruction),
a player leaderboard, and a Poisson **season projection** (title / European / relegation odds).
Cloned from the La Liga (XLALIGA) system; shares the same `xg_core/` model.

**Live dashboard:** `epl_dashboard/index.html` (root `index.html` redirects there).

## How it works
Two data layers:
1. **Schedule spine (token-free):** `epl/build_schedule.py` sweeps FotMob's public feed for the
   Premier League (league 47) → `epl/schedules/SCHEDULE_<season>.json` with every fixture's real
   score + matchday. Drives **standings, results, fixtures and projection** — no browser needed.
2. **Rich per-match layer:** `epl/run_match.py` / `epl/backfill.py` deep-scrape individual games
   (FotMob + WhoScored + Understat) into `epl/matches/<season>/<id>.json`, adding xG, shot/pass/
   dribble maps and player stats. The dashboard degrades gracefully — a match shows its
   result/table contribution immediately, its rich views once deep-scraped.

## Quick start
```bash
pip install -r requirements.txt
py epl/build_schedule.py --season 2025-26     # real results (token-free)
py epl/download_crests.py                      # club badges
py epl_dashboard/build_data.py                 # build the dashboard data
py -m http.server 8778                         # → http://localhost:8778/epl_dashboard/index.html
```
Rich per-match data — the workhorse is the WhoScored crawler (needs Chrome; ~1h/season, resumable):
```bash
py epl/scrape_whoscored.py --season 2025-26     # scrape every match's events
py epl_dashboard/build_match_details.py && py epl_dashboard/build_players.py \
  && py epl_dashboard/build_database.py && py epl_dashboard/build_shots.py \
  && py epl_dashboard/build_data.py
git add -A && git commit -m "refresh data" && git push
```

## European zones (2025/26)
Top **5** → Champions League, 6th → Europa, 7th → Conference, bottom 3 → relegation (England had
a fifth CL place via its UEFA coefficient that season). Encoded in `epl_dashboard/app.js`
`zoneOf()` and the projection Monte-Carlo.

## Layout
`epl/` pipeline · `epl_dashboard/` static site + builders · `epl_png/` published PNGs ·
`team_logos/epl/` crests · `xg_core/` shared xG/xA model.
