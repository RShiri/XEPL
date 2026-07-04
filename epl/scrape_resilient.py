#!/usr/bin/env python3
"""Resilient WhoScored scrape driver for the XEPL pipeline.

WhoScored is intermittently flaky (502 gateway pages; page loads that hang until Selenium's
120s client timeout and raise). The stock ``scrape_whoscored.py`` has no per-request guards, so
a single hung ``driver.get`` crashes the whole run. This wrapper reuses that module's harvesting,
matching and save logic but adds: a Chrome page-load timeout (fail fast, keep partial HTML),
try/except around every navigation, automatic driver recreation on a dead session, and a
per-match retry budget so one bad match can't stall the season. Resumable via ``already_done``.

Usage:
    py epl/scrape_resilient.py --season 2025-26 --url <archived-season-url> [--max-back 46] [--limit N]
"""
from __future__ import annotations
import os, re, sys, time, argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PAGE_TIMEOUT = int(os.environ.get("EPL_PAGE_TIMEOUT", "45"))
# matchCentreData is server-rendered into the initial HTML, so it's present within a few seconds;
# 5s first try (with a longer retry) is plenty and ~halves the stock 9s wait. Override if flaky.
MATCH_WAIT = int(os.environ.get("EPL_MATCH_WAIT", "5"))


def _now():
    return time.strftime("%H:%M:%S")


def new_driver():
    from epl.scrape_whoscored import make_driver
    d = make_driver()
    try:
        d.set_page_load_timeout(PAGE_TIMEOUT)
    except Exception:
        pass
    return d


def safe_get(d, url, wait):
    """Navigate; swallow timeouts/webdriver errors (partial page_source is still usable).
    Returns (driver, ok) — driver may be a fresh instance if the session died."""
    from selenium.common.exceptions import TimeoutException, WebDriverException, InvalidSessionIdException
    try:
        d.get(url)
        time.sleep(wait)
        return d, True
    except (TimeoutException,):
        time.sleep(1)
        return d, True  # timed out mid-load, but whatever rendered is readable
    except (InvalidSessionIdException,):
        try: d.quit()
        except Exception: pass
        print(f"  {_now()} session died, recreating driver", flush=True)
        return new_driver(), False
    except WebDriverException as e:
        msg = str(e)[:120]
        if any(k in msg.lower() for k in ("invalid session", "session deleted", "disconnected", "not reachable")):
            try: d.quit()
            except Exception: pass
            print(f"  {_now()} driver unhealthy ({msg}); recreating", flush=True)
            return new_driver(), False
        time.sleep(1)
        return d, True


def harvest(d, base, max_back, want=None):
    from selenium.webdriver.common.by import By
    from epl.scrape_whoscored import _cal_label
    ids, seen = [], set()
    got = False
    for attempt in range(1, 9):
        d, _ = safe_get(d, base, 9)
        if re.search(r"/[Mm]atches/(\d+)/", d.page_source):
            got = True
            break
        print(f"  {_now()} fixtures load attempt {attempt}: no ids yet", flush=True)
    if not got:
        print(f"  {_now()} fixtures page never yielded ids on {base}", flush=True)
        return ids
    empty_streak = 0
    for step in range(max_back + 1):
        page_ids = list(dict.fromkeys(re.findall(r"/[Mm]atches/(\d+)/", d.page_source)))
        new = [i for i in page_ids if i not in seen]
        for i in new:
            seen.add(i); ids.append(i)
        print(f"  {_now()} week {step} ({_cal_label(d)}): +{len(new)} ids (total {len(ids)})", flush=True)
        empty_streak = empty_streak + 1 if not new else 0
        if empty_streak >= 8:
            print(f"  {_now()} 8 empty weeks — reached season edge, stopping harvest.", flush=True)
            break
        if want and len(ids) >= want:
            break
        clicked = False
        for sel in ["#dayChangeBtn-prev", "button.Calendar-module_dayChangeBtn__sEvC8",
                    "[id='dayChangeBtn-prev']", "a.previous"]:
            try:
                for e in d.find_elements(By.CSS_SELECTOR, sel):
                    if e.is_displayed():
                        d.execute_script("arguments[0].click();", e); clicked = True; break
                if clicked: break
            except Exception:
                continue
        if not clicked:
            print(f"  {_now()} previous-week control not found; stopping pagination.", flush=True)
            break
        time.sleep(5)
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", required=True)
    ap.add_argument("--url", help="archived-season fixtures URL (sets EPL_WHOSCORED_URLS)")
    ap.add_argument("--max-back", type=int, default=46)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--ids", help="comma-separated ids, skip harvest")
    args = ap.parse_args()

    if args.url:
        os.environ["EPL_WHOSCORED_URLS"] = args.url
    # import AFTER setting env so EPL_WS_BASES picks up the season URL
    from epl.scrape_whoscored import (extract_mcd, save_match, load_schedule, already_done,
                                      _exact_match, _teams_match, EPL_WS_BASES)

    schedule = load_schedule(args.season)
    print(f"{_now()} Season {args.season}: {len(schedule)} fixtures; base={EPL_WS_BASES[0]}", flush=True)
    d = new_driver()
    saved = skipped = unmatched = failed = 0
    try:
        if args.ids:
            ids = [x.strip() for x in args.ids.split(",") if x.strip()]
        else:
            print(f"{_now()} Harvesting match ids…", flush=True)
            ids = harvest(d, EPL_WS_BASES[0], args.max_back)
        print(f"{_now()} {len(ids)} candidate ids. Scraping…", flush=True)
        # persist harvested ids for reuse/debugging
        try:
            (_REPO / "epl" / "matches" / args.season).mkdir(parents=True, exist_ok=True)
            (_REPO / "epl" / "matches" / args.season / "_ids.txt").write_text(",".join(ids))
        except Exception:
            pass

        for n, wsid in enumerate(ids, 1):
            mcd = None
            for attempt in range(2):  # played matches load in 1-2 tries; upcoming never do
                d, _ = safe_get(d, f"https://www.whoscored.com/Matches/{wsid}/Live", MATCH_WAIT + 4 * attempt)
                mcd = extract_mcd(d.page_source)
                if mcd and mcd.get("events"):
                    break
                mcd = None
            if not mcd:
                failed += 1
                if n % 10 == 0 or failed % 10 == 0:
                    print(f"  {_now()} [{n}/{len(ids)}] {wsid}: no data (fail #{failed})", flush=True)
                continue
            wh = (mcd.get("home") or {}).get("name", "")
            wa = (mcd.get("away") or {}).get("name", "")
            fixture = (next((f for f in schedule if _exact_match(wh, wa, f["home"], f["away"])), None)
                       or next((f for f in schedule if _teams_match(wh, wa, f["home"], f["away"])), None))
            if not fixture:
                unmatched += 1
                print(f"  {_now()} [{n}/{len(ids)}] {wsid}: {wh} vs {wa} — not in schedule", flush=True)
                continue
            if already_done(args.season, fixture["fotmob_id"]):
                skipped += 1
                continue
            try:
                out = save_match(mcd, fixture, args.season)
            except Exception as e:
                failed += 1
                print(f"  {_now()} [{n}/{len(ids)}] {wsid}: save error {str(e)[:80]}", flush=True)
                continue
            saved += 1
            print(f"  {_now()} [{n}/{len(ids)}] {wsid}: {wh} "
                  f"{(mcd.get('home') or {}).get('scores',{}).get('fulltime')}-"
                  f"{(mcd.get('away') or {}).get('scores',{}).get('fulltime')} {wa} "
                  f"-> {out.name} MD{fixture.get('matchday')} [saved {saved}]", flush=True)
            if args.limit and saved >= args.limit:
                break
    finally:
        try: d.quit()
        except Exception: pass
    print(f"\n{_now()} Done: {saved} saved, {skipped} already had data, {unmatched} unmatched, {failed} failed.", flush=True)


if __name__ == "__main__":
    main()
