#!/usr/bin/env python3
"""Build assets/stats.svg, assets/streak.svg and assets/languages.svg from the
GitHub API, so the README doesn't depend on rate-limited public card services.

Runs in GitHub Actions (see .github/workflows/profile-assets.yml), which passes
GITHUB_TOKEN and GH_LOGIN. Locally:  GITHUB_TOKEN=... GH_LOGIN=Harishram4106 python3 scripts/build_stats.py
"""
import datetime as dt
import json
import os
import urllib.request
from xml.sax.saxutils import escape

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
LIME, GREEN, DIM, TEXT, MUTED = "#d2ff4d", "#7dff8a", "#2f7a3a", "#e6edf3", "#9fc9a3"
MONO = "'JetBrains Mono','SFMono-Regular',Menlo,Consolas,'Liberation Mono','Courier New',monospace"

PROFILE_QUERY = """query($login: String!, $cursor: String) {
  user(login: $login) {
    name createdAt
    followers { totalCount }
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
    contributionsCollection {
      totalCommitContributions totalPullRequestContributions totalIssueContributions
      totalRepositoriesWithContributedCommits
      contributionCalendar { totalContributions }
    }
  }
}"""

CAL_QUERY = """query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}"""


def gql(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
        "Content-Type": "application/json", "User-Agent": "profile-stats"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GitHub API error: {data['errors']}")
    return data["data"]["user"]


def fetch_profile(login):
    user, repos, cursor = None, [], None
    while True:
        u = gql(PROFILE_QUERY, {"login": login, "cursor": cursor})
        user = user or u
        page = u["repositories"]
        repos += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    return user, repos


def fetch_days(login, created_at):
    """Every day's contribution count since the account was created."""
    start = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    now = dt.datetime.now(dt.timezone.utc)
    days = {}
    frm = start
    while frm < now:
        to = min(frm + dt.timedelta(days=365), now)
        u = gql(CAL_QUERY, {"login": login, "from": frm.isoformat(), "to": to.isoformat()})
        for w in u["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[dt.date.fromisoformat(d["date"])] = d["contributionCount"]
        frm = to
    return dict(sorted(days.items()))


def streaks(days):
    dates = list(days)
    today = dates[-1]
    longest = (0, None, None)
    run, run_start = 0, None
    for d in dates:
        if days[d] > 0:
            run_start = d if run == 0 else run_start
            run += 1
            if run > longest[0]:
                longest = (run, run_start, d)
        else:
            run = 0
    # the current streak survives a quiet "today": count back from yesterday then
    end = today if days[today] > 0 else today - dt.timedelta(days=1)
    cur, d = 0, end
    while d in days and days[d] > 0:
        cur += 1
        d -= dt.timedelta(days=1)
    cur_range = (d + dt.timedelta(days=1), end) if cur else (None, None)
    return cur, cur_range, longest


def frame(w, h, title, inner):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>
  .t {{ font-family: {MONO}; fill: {TEXT}; }}
  .h {{ font-size: 17px; font-weight: 800; fill: {LIME}; }}
  .k {{ font-size: 14px; fill: {MUTED}; }}
  .v {{ font-size: 14px; font-weight: 700; fill: {TEXT}; }}
  .big {{ font-size: 30px; font-weight: 800; fill: {TEXT}; }}
  .lbl {{ font-size: 13px; font-weight: 700; fill: {LIME}; }}
  .sub {{ font-size: 11px; fill: {MUTED}; }}
  .fade {{ opacity: 0; animation: fade .6s ease-out forwards; }}
  @keyframes fade {{ to {{ opacity: 1; }} }}
  @media (prefers-reduced-motion: reduce) {{ .fade {{ animation: none; opacity: 1; }} }}
</style>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="10" fill="#060b07" stroke="{DIM}" stroke-width="1.5"/>
{inner}
</svg>
'''


def fmt_range(a, b):
    if not a:
        return "no active streak"
    f = lambda d: d.strftime("%b %-d")
    return f(a) if a == b else f"{f(a)} – {f(b)}"


def stats_svg(user, repos):
    c = user["contributionsCollection"]
    rows = [
        ("Contributions (last year)", c["contributionCalendar"]["totalContributions"]),
        ("Commits (last year)", c["totalCommitContributions"]),
        ("Pull requests", c["totalPullRequestContributions"]),
        ("Issues", c["totalIssueContributions"]),
        ("Public repos", user["repositories"]["totalCount"]),
        ("Stars earned", sum(r["stargazerCount"] for r in repos)),
        ("Followers", user["followers"]["totalCount"]),
    ]
    inner = [f'<text x="24" y="38" class="t h">&gt; {escape((user["name"] or "").split()[0] or "my")} --stats</text>']
    for i, (k, v) in enumerate(rows):
        y = 72 + i * 25
        inner.append(f'<g class="fade" style="animation-delay:{0.1 * i:.1f}s">'
                     f'<rect x="24" y="{y - 11}" width="6" height="12" fill="{GREEN}"/>'
                     f'<text x="40" y="{y}" class="t k">{k}</text>'
                     f'<text x="456" y="{y}" text-anchor="end" class="t v">{v:,}</text></g>')
    return frame(480, 248, "GitHub stats", "\n".join(inner))


def streak_svg(days):
    total = sum(days.values())
    cur, cur_range, (lng, l_from, l_to) = streaks(days)
    first = next(iter(days)).strftime("%b %-d, %Y")
    cols = [
        (f"{total:,}", "Contributions", f"{first} – present"),
        (f"{cur}", "Current streak", fmt_range(*cur_range)),
        (f"{lng}", "Longest streak", fmt_range(l_from, l_to)),
    ]
    inner = [f'<text x="24" y="38" class="t h">&gt; streak --watch</text>']
    for i, (big, lbl, sub) in enumerate(cols):
        cx = 90 + i * 150
        if i == 1:
            inner.append(f'<circle cx="{cx}" cy="118" r="42" fill="none" stroke="{LIME}" stroke-width="5"/>')
        if i:
            inner.append(f'<line x1="{cx - 75}" y1="70" x2="{cx - 75}" y2="210" stroke="{DIM}"/>')
        inner.append(f'<g class="fade" style="animation-delay:{0.15 * i:.2f}s">'
                     f'<text x="{cx}" y="129" text-anchor="middle" class="t big">{big}</text>'
                     f'<text x="{cx}" y="188" text-anchor="middle" class="t lbl">{lbl}</text>'
                     f'<text x="{cx}" y="208" text-anchor="middle" class="t sub">{sub}</text></g>')
    return frame(480, 248, "Contribution streak", "\n".join(inner))


def languages_svg(repos, top=8):
    sizes, colors = {}, {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            sizes[n] = sizes.get(n, 0) + e["size"]
            colors[n] = e["node"]["color"] or GREEN
    ranked = sorted(sizes.items(), key=lambda kv: -kv[1])[:top]
    total = sum(v for _, v in ranked) or 1
    w = 980
    inner = [f'<text x="24" y="38" class="t h">&gt; ls --languages --sort=size</text>']
    x, bar_w = 24, w - 48
    for n, v in ranked:
        seg = bar_w * v / total
        inner.append(f'<rect x="{x:.1f}" y="56" width="{max(seg, 1):.1f}" height="10" fill="{colors[n]}"/>')
        x += seg
    inner.append(f'<rect x="24" y="56" width="{bar_w}" height="10" rx="5" fill="none" stroke="#060b07" stroke-width="2"/>')
    for i, (n, v) in enumerate(ranked):
        col, row = i % 4, i // 4
        lx, ly = 24 + col * 236, 98 + row * 28
        inner.append(f'<g class="fade" style="animation-delay:{0.08 * i:.2f}s">'
                     f'<circle cx="{lx + 6}" cy="{ly - 5}" r="6" fill="{colors[n]}"/>'
                     f'<text x="{lx + 20}" y="{ly}" class="t k" style="fill:{TEXT}">{escape(n)}</text>'
                     f'<text x="{lx + 216}" y="{ly}" text-anchor="end" class="t k">{100 * v / total:.1f}%</text></g>')
    h = 98 + ((len(ranked) + 3) // 4) * 28
    return frame(w, h, "Most used languages", "\n".join(inner))


def main():
    login = os.environ.get("GH_LOGIN", "Harishram4106")
    if not os.environ.get("GITHUB_TOKEN"):
        raise SystemExit("Set GITHUB_TOKEN (any token that can read public data).")
    user, repos = fetch_profile(login)
    days = fetch_days(login, user["createdAt"])
    os.makedirs(ASSETS, exist_ok=True)
    for name, svg in (("stats.svg", stats_svg(user, repos)), ("streak.svg", streak_svg(days)),
                      ("languages.svg", languages_svg(repos))):
        with open(os.path.join(ASSETS, name), "w") as f:
            f.write(svg)
        print(f"wrote assets/{name}")


if __name__ == "__main__":
    main()
