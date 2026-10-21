#!/usr/bin/env python3
"""Build assets/heatmap.svg: a terminal-style GitHub contributions heatmap.

Runs in GitHub Actions (see .github/workflows/profile-assets.yml), which passes
GITHUB_TOKEN and GH_LOGIN. Locally:  GITHUB_TOKEN=... GH_LOGIN=Harishram4106 python3 scripts/build_heatmap.py
With --placeholder it writes an empty "awaiting first sync" card instead.
"""
import datetime as dt
import json
import os
import sys
import urllib.request

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "heatmap.svg")

W, H = 1200, 330
CELL, GAP = 15, 3.8
GX, GY = 112, 126                       # grid origin
GREEN = "#7dff8a"
GREEN_DIM = "#2f7a3a"
LEVEL_FILL = {                           # GitHub's contribution quartiles
    "NONE": "#0f2a14", "FIRST_QUARTILE": "#1f6b2c", "SECOND_QUARTILE": "#36a548",
    "THIRD_QUARTILE": "#5ad66b", "FOURTH_QUARTILE": "#9cff9f",
}
MONO = "'JetBrains Mono','SFMono-Regular',Menlo,Consolas,'Liberation Mono','Courier New',monospace"

QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel weekday } }
      }
    }
  }
}"""


def fetch(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-heatmap"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GitHub API error: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["totalContributions"], cal["weeks"]


def build(total, weeks):
    cells, months = [], []
    last_month = None
    for wi, week in enumerate(weeks):
        x = GX + wi * (CELL + GAP)
        first = dt.date.fromisoformat(week["contributionDays"][0]["date"])
        if first.month != last_month:
            months.append((x, first.strftime("%b")))
            last_month = first.month
        for day in week["contributionDays"]:
            d = dt.date.fromisoformat(day["date"])
            y = GY + day["weekday"] * (CELL + GAP)
            fill = LEVEL_FILL[day["contributionLevel"]]
            n = day["contributionCount"]
            delay = 0.012 * wi
            cells.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="4" fill="{fill}" '
                f'style="animation-delay:{delay:.2f}s"><title>{n} contribution{"s" if n != 1 else ""} on {d:%b %d, %Y}</title></rect>')
    # drop month labels that would collide
    spaced, last_x = [], -999
    for x, m in months:
        if x - last_x >= 40:
            spaced.append((x, m))
            last_x = x
    month_svg = "".join(f'<text x="{x:.0f}" y="{GY - 14}" class="t lbl">{m}</text>' for x, m in spaced)
    day_svg = "".join(
        f'<text x="{GX - 14}" y="{GY + i * (CELL + GAP) + 13}" text-anchor="end" class="t lbl">{name}</text>'
        for i, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")))
    title = f"{total:,} contributions in the last year" if total is not None else "contribution stream booting…"
    return wrap(title, month_svg + day_svg + "".join(cells),
                "&gt; github activity heatmap // contribution stream online" if total is not None
                else "&gt; awaiting first sync // run the profile-assets workflow")


def placeholder():
    cells = []
    for wi in range(53):
        for wd in range(7):
            x, y = GX + wi * (CELL + GAP), GY + wd * (CELL + GAP)
            cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="4" fill="#0f2a14" '
                         f'style="animation-delay:{0.012 * wi:.2f}s"/>')
    return build_frame_only("".join(cells))


def build_frame_only(inner):
    return wrap("contribution stream booting…", inner, "&gt; awaiting first sync // run the profile-assets workflow")


def wrap(title, inner, footer):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{title}">
<title>{title}</title>
<style>
  .t {{ font-family: {MONO}; fill: #d7ffd9; }}
  .h {{ font-size: 30px; font-weight: 800; }}
  .lbl {{ font-size: 15px; fill: #9fc9a3; }}
  .pill {{ font-size: 15px; fill: #c8f5cb; }}
  .foot {{ font-size: 14px; fill: {GREEN}; fill-opacity: .85; }}
  rect[style] {{ opacity: 0; animation: pop .5s ease-out forwards; }}
  @keyframes pop {{ to {{ opacity: 1; }} }}
  @media (prefers-reduced-motion: reduce) {{ rect[style] {{ animation: none; opacity: 1; }} }}
</style>
<rect width="{W}" height="{H}" fill="#040704"/>
<rect x="14" y="14" width="{W - 28}" height="{H - 28}" rx="22" fill="#060b07" stroke="{GREEN_DIM}" stroke-width="2"/>
<rect x="28" y="28" width="{W - 56}" height="{H - 70}" rx="16" fill="none" stroke="{GREEN_DIM}" stroke-opacity=".55"/>
<text x="60" y="80" class="t h">{title}</text>
<rect x="{W - 230}" y="46" width="180" height="44" rx="8" fill="#08120a" stroke="{GREEN_DIM}"/>
<text x="{W - 208}" y="74" class="t pill">Past year</text>
<path d="M{W - 82} 64 l12 0 l-6 8 z" fill="#c8f5cb"/>
{inner}
<text x="60" y="{H - 22}" class="t foot">{footer}</text>
</svg>
'''


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    if "--placeholder" in sys.argv:
        svg = placeholder()
    else:
        token, login = os.environ.get("GITHUB_TOKEN"), os.environ.get("GH_LOGIN", "Harishram4106")
        if not token:
            raise SystemExit("Set GITHUB_TOKEN (any token that can read public data).")
        total, weeks = fetch(login, token)
        svg = build(total, weeks)
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {os.path.normpath(OUT)}")


if __name__ == "__main__":
    main()
