# PROGRESS — XEPL

Running log of the Premier League pipeline: every scrape, every platform change, and the
lessons behind both. Newest entries first in each section.

Rows under **Scrape log** are appended **automatically** by `epl/progress_log.py`, which is
called from `run_match.py`, `scrape_whoscored.py`, `scrape_resilient.py`, `backfill.py` and the
dashboard's **Scraper** button — every scrape lands here whether it was a scheduled task, a bulk
backfill, or a click. Write the Platform and Lessons sections by hand, from the dashboard's
Scraper panel ("Log a note"), or with:

```
py epl/progress_log.py platform "what changed"
py epl/progress_log.py lesson --worked "what to keep doing"
py epl/progress_log.py lesson --failed "what not to repeat"
py epl/progress_log.py show --limit 20
```

Sister project: **[XLALIGA](https://github.com/RShiri/XLALIGA)** keeps the same journal at its own
`PROGRESS.md`. The two codebases are twins — a lesson learned in one is nearly always true in
the other, so when you add an entry here, consider adding it there too.

## Platform updates & changes

<!-- progress:platform -->
- **2026-08-24** — 26/27 readiness sweep: scraper.fotmob_fetch_wc_matches migrated off the retired live-only endpoint to /api/data/matches (legacy XML only if the new one returns nothing); defaultSeason now follows the newest PLAYED season instead of being pinned to 2025-26; backfill/scrape_whoscored --season defaults to the newest schedule on disk; git_ops finally pushes shots.js + player_lab/ and finds the raw JSON under matches/<season>/; build_schedule warns about clubs with no colour or crest.
- **2026-08-24** — FotMob moved the fixture feed: api.fotmob.com/matches?date= is now LIVE-ONLY (root <live>/<exmatches>, ?date ignored). The spine now uses www.fotmob.com/api/data/leagues?id=47&season=2026%2F2027 (whole season in one request, with round numbers), with /api/data/matches?date= as the per-day fallback and the old XML as a last resort.
- **2026-08-23** — build_schedule is now incremental by default: it sweeps from a few days before the last finished match to a fortnight ahead and merges into the existing schedule (--full for the whole season). It also parses the feed as XML or JSON, and says why a sweep found nothing instead of silently reporting 0.
- **2026-08-22** — Scraper panel collapsed to a single '⚡ Update everything' button — picks the season, refreshes fixtures, scrapes what's missing, rebuilds and publishes in one click; the season/action/id/limit controls moved behind an Advanced toggle.
- **2026-08-22** — Scraper panel: added a Commit & push button, made publish-when-done the default, and folded the fixture refresh into the scrape action (optional step — a FotMob outage no longer blocks the scrape). All pushes now go through the local clone's remote instead of git_ops.
- **2026-08-22** — Added this journal (`PROGRESS.md` + `epl/progress_log.py`) and a
  **Scraper button** in the dashboard, served by the new local control server `server.py`
  (`py server.py` → http://localhost:8779/epl_dashboard/index.html — port **8779** so it can run
  alongside XLALIGA's 8778). The button runs the same scrape/rebuild commands as the CLI and
  writes its result here automatically.
- **2026-07-30** — Match page: calibrated in-play win-probability chart.
- **2026-07-04** — Repo split out of XLALIGA into standalone **RShiri/XEPL**: `epl/` pipeline,
  `epl_dashboard/` site, `xg_core/` shared model, `team_logos/epl/`, `epl_png/`.
- **(seasons)** — 2022/23, 2023/24, 2024/25 and 2025/26 fully scraped: 380/380 each, 1,520
  match-centre pages. `epl/schedules/SCHEDULE_2026-27.json` is an empty placeholder awaiting
  FotMob's 2026/27 fixture release.

## Lessons — what worked / what didn't

<!-- progress:lessons -->
- ❌ **Didn't work** — Skipping the per-match dashboard refresh in batches silently dropped the Match Centre pages: matches_detail/<id>.js was ONLY written by the per-match path, and the end-of-batch rebuild ran the other five builders but not that one. The batch rebuild now runs build_match_details.main() too.  (2026-08-24)
- ✅ **Worked** — Two cheap wins on scrape time and stability: remember that undetected-chromedriver is broken after the FIRST failure (it was retried at every browser launch — 3x per match), and stop launching a browser for Understat after it returns nothing twice. Roughly halves the browser launches per match.  (2026-08-24)
- ❌ **Didn't work** — backfill rebuilt the ENTIRE dashboard after every match (renderer's refresh hook re-reads every season and rewrites every derived file). For a 14-match batch that is 14 full rebuilds racing a live Chrome. Batches now set EPL_SKIP_DASHBOARD_REFRESH=1 and rebuild once at the end.  (2026-08-24)
- ❌ **Didn't work** — FotMob's season payload carries NO round field — confirmed with --dump-sample: each match has only id, home, away, status, pageUrl and an empty tournament.stage. Matchday has to be reconstructed; don't go looking for the field again.  (2026-08-24)
- ✅ **Worked** — Matchday inference now tries the payload order AND kickoff order, validating each by 'no team twice in a round'. FotMob's season view is date-ordered, not round-ordered, so the first attempt fails and the second succeeds — and if both fail it leaves matchday empty instead of publishing a wrong table.  (2026-08-24)
- ❌ **Didn't work** — A WhoScored failure used to be invisible and permanent: the match still saved (FotMob shots only, no event stream), so _already_scraped counted it done and no later run would ever fill in the maps/lineups. backfill now classifies each match none/partial/full and --redo-partial retries only the partials.  (2026-08-24)
- ✅ **Worked** — Probing candidate endpoints from the user's own machine (--probe-endpoints) found the replacement in one shot: /api/matches 404s but /api/data/matches works, and /api/data/leagues returns the entire season. When a source dies, enumerate doors rather than guessing one.  (2026-08-24)
- ❌ **Didn't work** — A sweep printing '0 matches so far' told us nothing: ET.fromstring failures were swallowed by 'except Exception: continue', so a FotMob format change looked identical to 'no fixtures yet'. Failure counters + a verdict line now distinguish blocked / format-changed / no-such-league / not-published.  (2026-08-23)
- ❌ **Didn't work** _deploy_ — `git_ops.push_match_update` copies `data.js`, `players.js`,
  `matches_detail/` and `database/` but **not** `shots.js` or `player_lab/`, so auto-pushed
  matches leave the live Team Lab and Player Lab stale even though the renderer regenerates
  them locally.  (2026-08-22)
- ❌ **Didn't work** _seasons_ — `defaultSeason` is pinned to `"2025-26"` in
  `epl_dashboard/build_data.py`, and `build_database.py` exports only that default season.
  A new season goes live in the switcher but the site still lands on the old one.  (2026-08-22)
- ❌ **Didn't work** _team matching_ — stripping "united"/"city" in `epl/scrape_whoscored._key`
  collapses the two Manchester clubs into each other. Keep both words (the analogue of La Liga's
  "don't strip real" rule) and verify the mapping is collision-free before a bulk re-scrape.  (2026-08-22)
- ✅ **Worked** _data integrity_ — FotMob's feed reports some real results as `0-0`
  (17 in 2022/23, 9 in 2023/24, 1 in 2024/25) and null for unplayed fixtures. Preferring the
  scraped WhoScored score whenever a match has events fixed the standings; it matches the
  event-derived score for every match, every season.  (2026-08-22)
- ✅ **Worked** _scraping_ — `scrape_resilient.py` (restartable sweep with an `_ids.txt` cache)
  is what got four seasons in; the plain sweep loses its place when the browser dies.  (2026-08-22)
- ❌ **Didn't work** _environment_ — the scrapers need FotMob/WhoScored **and** Chrome; both are
  firewalled in most CI/cloud environments, so scraping only ever works on the home PC.  (2026-08-22)
- ❌ **Didn't work** _European zones_ — the UCL cut (top 5 for 2024/25 & 2025/26, top 4 earlier)
  lives in **two** places: `epl_dashboard/app.js` `zoneOf()`/`uclSpots()` *and* the projection
  Monte-Carlo. Changing one leaves the table and the projection disagreeing.  (2026-08-22)
- ❌ **Didn't work** _front-end_ — `players.js` fields are `g`/`a`/`xg`/`mp`, not
  `goals`/`assists`; reading the long names shows 0 for every player.  (2026-08-22)
- ✅ **Worked** _models_ — sharing `xg_core/` with XLALIGA/XWORLDCUPTWIT keeps xG identical
  across projects; EPL currently falls back to the `_global` shift until an EPL corpus is
  trained.  (2026-08-22)
- ✅ **Worked** _repo size_ — keeping raw match JSONs gitignored (~2 MB each) and shipping only
  the derived `matches_detail/*.js` keeps the repo clonable.  (2026-08-22)

## Scrape log

<!-- progress:scrapes -->
| When | Season | Trigger | Target | Result | Took | Notes |
|---|---|---|---|---|---|---|
| 2026-07 | 2022-23 | bulk backfill (historic) | full season · 380 matches | ✅ 380 saved | — | Archived-season WhoScored path |
| 2026-07 | 2023-24 | bulk backfill (historic) | full season · 380 matches | ✅ 380 saved | — | Archived-season WhoScored path |
| 2026-07 | 2024-25 | bulk backfill (historic) | full season · 380 matches | ✅ 380 saved | — | Archived-season WhoScored path |
| 2026-07 | 2025-26 | bulk backfill (historic) | full season · 380 matches | ✅ 380 saved | — | The default season |
