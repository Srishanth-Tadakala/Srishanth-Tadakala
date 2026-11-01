"""Fetch REAL GitHub telemetry for the profile command center.

Sources (all public):
  * REST  /users/{login}, /users/{login}/repos, /repos/{login}/{repo}/languages
  * HTML  https://github.com/users/{login}/contributions  (public contribution calendar)

Writes data/telemetry.json. If any request fails, the previous snapshot is kept untouched
so the README never shows fabricated or zeroed-out numbers.

Usage: python scripts/fetch_telemetry.py      (set GITHUB_TOKEN to raise API rate limits)
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE = json.load(open(os.path.join(ROOT, "data", "profile.json"), encoding="utf-8"))
LOGIN = PROFILE["identity"]["login"]
OUT = os.path.join(ROOT, "data", "telemetry.json")
TOKEN = os.environ.get("GITHUB_TOKEN")


def _get(url, accept="application/vnd.github+json"):
    headers = {"User-Agent": f"{LOGIN}-profile-telemetry", "Accept": accept}
    if TOKEN and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return r.read().decode("utf-8")


def contributions():
    html = _get(f"https://github.com/users/{LOGIN}/contributions", accept="text/html")
    cells = re.findall(r'<td[^>]*?data-date="([\d-]+)"[^>]*?id="([^"]+)"[^>]*?data-level="(\d)"', html)
    tips = dict(re.findall(r'<tool-tip[^>]*?for="([^"]+)"[^>]*>([^<]+)</tool-tip>', html))
    days = []
    for date, cid, level in cells:
        tip = tips.get(cid, "")
        m = re.match(r"\s*([\d,]+)\s+contribution", tip)
        days.append({"date": date, "level": int(level), "count": int(m.group(1).replace(",", "")) if m else 0})
    days.sort(key=lambda d: d["date"])
    if len(days) < 300:
        raise RuntimeError(f"contribution calendar parse failed ({len(days)} cells)")
    return days


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    # current streak: allow today to be empty (day not finished yet)
    current = 0
    seq = list(reversed(days))
    if seq and seq[0]["count"] == 0:
        seq = seq[1:]
    for d in seq:
        if d["count"] > 0:
            current += 1
        else:
            break
    return current, longest


def main():
    try:
        user = json.loads(_get(f"https://api.github.com/users/{LOGIN}"))
        repos = json.loads(_get(f"https://api.github.com/users/{LOGIN}/repos?per_page=100&type=owner"))
        langs, repo_meta = {}, {}
        for r in repos:
            repo_meta[r["name"]] = {
                "stars": r["stargazers_count"], "forks": r["forks_count"], "language": r["language"],
                "pushed_at": r["pushed_at"], "description": r["description"], "fork": r["fork"],
            }
            if r["fork"] or r["name"] == LOGIN:
                continue  # profile repo holds this generator, not project work
            for k, v in json.loads(_get(r["languages_url"])).items():
                langs[k] = langs.get(k, 0) + v
        days = contributions()
        cur, longest = streaks(days)
    except Exception as exc:  # keep last good snapshot
        print(f"[telemetry] fetch failed: {exc!r} -> keeping previous snapshot", file=sys.stderr)
        return 0 if os.path.exists(OUT) else 1

    data = {
        "synced_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "public_repos": user["public_repos"],
        "followers": user["followers"],
        "stars": sum(m["stars"] for n, m in repo_meta.items() if not m["fork"]),
        "project_repos": sum(1 for n, m in repo_meta.items() if not m["fork"] and n != LOGIN),
        "languages": dict(sorted(langs.items(), key=lambda kv: -kv[1])),
        "repos": repo_meta,
        "contributions_last_year": sum(d["count"] for d in days),
        "active_days": sum(1 for d in days if d["count"] > 0),
        "best_day": max(days, key=lambda d: d["count"]),
        "current_streak": cur,
        "longest_streak": longest,
        "calendar": days,
    }
    json.dump(data, open(OUT, "w", encoding="utf-8"), indent=1)
    print(f"[telemetry] ok: {data['contributions_last_year']} contributions, {data['active_days']} active days, "
          f"streak {cur}/{longest}, repos {data['public_repos']}, stars {data['stars']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

