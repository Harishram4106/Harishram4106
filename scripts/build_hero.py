#!/usr/bin/env python3
"""Build assets/hero.svg: the terminal hero card with a dot-matrix portrait.

Usage:
    python3 scripts/build_hero.py                      # placeholder silhouette
    python3 scripts/build_hero.py path/to/cutout.png   # your photo as dot-matrix

For a clean portrait, remove the photo's background first so it's a PNG with
transparency, e.g.  pip install rembg pillow && rembg i photo.jpg cutout.png
Needs Pillow only when a photo is given.
"""
import math
import os
import sys

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "hero.svg")

NAME_1 = "HARISHRAM"
NAME_2 = "BALAMURUGAN"
GREETING = "&gt; hello, world"
TAGLINE = "AI/ML Engineer | Full-Stack Developer | LLM &amp; RAG Builder"
CHIPS = ["Python", "FastAPI", "RAG", "Agentic AI", "Flutter"]
FOOTLINE = "shipping &#8594; durable agents, RAG systems, local-first AI"

W, H = 1200, 460
GREEN = "#7dff8a"
GREEN_DIM = "#2f7a3a"
MONO = "'JetBrains Mono','SFMono-Regular',Menlo,Consolas,'Liberation Mono','Courier New',monospace"

# portrait panel
PX, PY, PW, PH = 760, 50, 390, 360
GRID_W, GRID_H = 116, 98         # dots across / down
STEP = 3.1                        # px between dot centres


def dot_path(dots, r):
    """One <path> drawing many circles of radius r (two arcs per dot)."""
    d = []
    for x, y in dots:
        d.append(f"M{x - r:.1f} {y:.1f}a{r} {r} 0 1 0 {2 * r} 0a{r} {r} 0 1 0 {-2 * r} 0")
    return "".join(d)


def levels_from_photo(path):
    """Dots for a photo. A PNG with a transparent background (a cut-out) works
    best; otherwise the backdrop is guessed from the top corners."""
    from PIL import Image, ImageOps, ImageFilter
    img = ImageOps.exif_transpose(Image.open(path))
    alpha = img.getchannel("A") if img.mode in ("RGBA", "LA") else None
    gray = img.convert("L")
    target = GRID_W / GRID_H
    if alpha is not None:
        # frame head and shoulders: start just above the hair, width ~0.95x the person
        left, top, right, bottom = alpha.point(lambda a: 255 if a > 128 else 0).getbbox()
        cw = int((right - left) * 0.95)
        ch = int(cw / target)
        cx = (left + right) // 2
        box = (cx - cw // 2, max(0, top - int(ch * 0.06)), cx + cw // 2, max(0, top - int(ch * 0.06)) + ch)
    else:
        w, h = gray.size
        if w / h > target:
            nw = int(h * target)
            box = ((w - nw) // 2, 0, (w - nw) // 2 + nw, h)
        else:
            box = (0, 0, w, int(w / target))
    gray = gray.crop(box).filter(ImageFilter.UnsharpMask(radius=8, percent=220, threshold=2)).resize((GRID_W, GRID_H), Image.LANCZOS)
    g = gray.load()
    if alpha is not None:
        a = alpha.crop(box).resize((GRID_W, GRID_H), Image.LANCZOS).load()
        inside = [(x, y) for y in range(GRID_H) for x in range(GRID_W) if a[x, y] > 110]
    else:
        corners = [g[x, y] for x in range(4) for y in range(4)] + \
                  [g[GRID_W - 1 - x, y] for x in range(4) for y in range(4)]
        bg = sum(corners) / len(corners)
        inside = [(x, y) for y in range(GRID_H) for x in range(GRID_W) if abs(g[x, y] - bg) >= 18]
    # rank-normalise brightness inside the subject so dark skin, hair and
    # suits still spread across all four dot sizes
    ranked = sorted(inside, key=lambda p: g[p])
    n = max(1, len(ranked) - 1)
    return {p: (i / n) ** 1.3 for i, p in enumerate(ranked)}


def levels_placeholder():
    """A head-and-shoulders silhouette, shaded from the left."""
    out = {}
    cx, head_cy, head_r = GRID_W / 2, GRID_H * 0.36, GRID_W * 0.2
    for y in range(GRID_H):
        for x in range(GRID_W):
            hx, hy = (x - cx) / head_r, (y - head_cy) / (head_r * 1.18)
            head = hx * hx + hy * hy <= 1
            neck = abs(x - cx) < head_r * 0.42 and head_cy < y < GRID_H * 0.66
            sy = y - GRID_H * 0.64
            shoulders = sy > 0 and abs(x - cx) < head_r * 1.1 + sy * 1.05
            if head or neck or shoulders:
                shade = 0.35 + 0.65 * (1 - x / GRID_W)
                if head:
                    shade += 0.15 * math.cos(hx * 1.4)
                out[(x, y)] = max(0.0, min(1.0, shade))
    return out


def portrait_svg(levels):
    buckets = {b: [] for b in range(6)}
    ox = PX + (PW - GRID_W * STEP) / 2 + STEP / 2
    oy = PY + 26
    for (x, y), v in levels.items():
        b = min(5, int(v * 6))
        buckets[b].append((ox + x * STEP, oy + y * STEP))
    radii = {0: 0.35, 1: 0.55, 2: 0.75, 3: 0.95, 4: 1.15, 5: 1.4}
    alpha = {0: 0.35, 1: 0.5, 2: 0.65, 3: 0.8, 4: 0.92, 5: 1.0}
    parts = []
    for b in range(6):
        if buckets[b]:
            parts.append(f'<path d="{dot_path(buckets[b], radii[b])}" fill="{GREEN}" fill-opacity="{alpha[b]}"/>')
    return "\n".join(parts)


def chips_svg(x0, y0):
    parts, x = [], x0
    for c in CHIPS:
        w = 24 + len(c) * 10.2
        parts.append(
            f'<g class="chip"><rect x="{x:.0f}" y="{y0}" width="{w:.0f}" height="34" rx="4" fill="none" '
            f'stroke="{GREEN}" stroke-width="2"/><text x="{x + w / 2:.0f}" y="{y0 + 23}" text-anchor="middle" '
            f'class="t chipt">{c}</text></g>')
        x += w + 12
    return "\n".join(parts)


def build(levels):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Harishram Balamurugan, AI/ML Engineer and Full-Stack Developer">
<title>Harishram Balamurugan</title>
<defs>
  <pattern id="dots" width="3" height="3" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1.15" fill="#fff"/></pattern>
  <mask id="matrix" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="url(#dots)"/></mask>
  <filter id="glow" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <radialGradient id="haze" cx="0.62" cy="0.55" r="0.55"><stop offset="0" stop-color="#103a1a" stop-opacity=".55"/><stop offset="1" stop-color="#050805" stop-opacity="0"/></radialGradient>
  <linearGradient id="scan" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{GREEN}" stop-opacity="0"/><stop offset=".5" stop-color="{GREEN}" stop-opacity=".18"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></linearGradient>
  <clipPath id="panel"><rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="10"/></clipPath>
  <clipPath id="reveal"><rect x="{PX}" y="{PY}" width="{PW}" height="0"><animate attributeName="height" from="0" to="{PH}" dur="2.4s" begin="0.3s" fill="freeze"/></rect></clipPath>
  <clipPath id="type1"><rect x="40" y="150" width="0" height="80"><animate attributeName="width" from="0" to="700" dur="1.1s" begin="0.2s" fill="freeze" calcMode="discrete" values="0;72;114;156;198;240;282;324;366;408;700" keyTimes="0;.1;.2;.3;.4;.5;.6;.7;.8;.9;1"/></rect></clipPath>
  <clipPath id="type2"><rect x="40" y="222" width="0" height="80"><animate attributeName="width" from="0" to="700" dur="1.3s" begin="1.3s" fill="freeze" calcMode="discrete" values="0;72;114;156;198;240;282;324;366;408;450;492;700" keyTimes="0;.083;.166;.25;.333;.416;.5;.583;.666;.75;.833;.916;1"/></rect></clipPath>
</defs>
<style>
  .t {{ font-family: {MONO}; fill: {GREEN}; }}
  .name {{ font-size: 70px; font-weight: 800; letter-spacing: 1px; }}
  .small {{ font-size: 15px; font-weight: 700; letter-spacing: 3px; }}
  .greet {{ font-size: 22px; font-weight: 700; }}
  .tag {{ font-size: 19px; font-weight: 700; }}
  .chipt {{ font-size: 16px; font-weight: 700; }}
  .foot {{ font-size: 16px; font-weight: 700; fill-opacity: .8; }}
  .cap {{ font-size: 14px; fill-opacity: .9; }}
  .blink {{ animation: blink 1s steps(1) infinite; }}
  .fade {{ opacity: 0; animation: fade .6s ease-out forwards; }}
  .scanline {{ animation: sweep 5s linear infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  @keyframes fade {{ to {{ opacity: 1; }} }}
  @keyframes sweep {{ from {{ transform: translateY(-120px); }} to {{ transform: translateY({H}px); }} }}
  @media (prefers-reduced-motion: reduce) {{ .blink, .scanline {{ animation: none; }} .fade {{ animation: none; opacity: 1; }} }}
</style>

<rect width="{W}" height="{H}" fill="#040704"/>
<rect x="14" y="14" width="{W - 28}" height="{H - 28}" rx="22" fill="#060b07" stroke="{GREEN_DIM}" stroke-width="2"/>
<rect x="28" y="28" width="{W - 56}" height="{H - 56}" rx="16" fill="none" stroke="{GREEN_DIM}" stroke-opacity=".55"/>
<rect x="28" y="28" width="{W - 56}" height="{H - 56}" rx="16" fill="url(#haze)"/>

<g mask="url(#matrix)" filter="url(#glow)">
  <text x="60" y="82" class="t small">SYSTEM ONLINE // PROFILE.EXE</text>
  <text x="60" y="138" class="t greet">{GREETING}</text>
  <g clip-path="url(#type1)"><text x="56" y="210" class="t name">{NAME_1}</text></g>
  <g clip-path="url(#type2)"><text x="56" y="284" class="t name">{NAME_2}<tspan class="blink">_</tspan></text></g>
  <g class="fade" style="animation-delay:2.6s"><text x="60" y="330" class="t tag">{TAGLINE}</text></g>
</g>

<g class="fade" style="animation-delay:2.9s" filter="url(#glow)">
{chips_svg(60, 352)}
</g>

<g class="fade" style="animation-delay:3.2s">
  <rect x="60" y="406" width="6" height="18" fill="{GREEN}"/>
  <text x="76" y="421" class="t foot">{FOOTLINE}</text>
</g>

<line x1="{PX - 50}" y1="{PY + 30}" x2="{PX}" y2="{PY + 30}" stroke="{GREEN_DIM}"/>
<line x1="{PX - 50}" y1="{PY + PH - 30}" x2="{PX}" y2="{PY + PH - 30}" stroke="{GREEN_DIM}"/>
<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="10" fill="#020402" stroke="{GREEN_DIM}" stroke-width="1.5"/>
<g clip-path="url(#panel)">
  <g clip-path="url(#reveal)" filter="url(#glow)">
{portrait_svg(levels)}
  </g>
  <rect class="scanline" x="{PX}" y="0" width="{PW}" height="90" fill="url(#scan)"/>
</g>
<text x="{PX + PW - 22}" y="{PY + 30}" text-anchor="end" class="t small fade" style="animation-delay:2.7s;font-size:13px">COMPLETE</text>
<text x="{PX + 18}" y="{PY + PH - 14}" class="t cap">&gt; portrait.svg loaded // terminal profile</text>
</svg>
'''


def main():
    levels = levels_from_photo(sys.argv[1]) if len(sys.argv) > 1 else levels_placeholder()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(build(levels))
    print(f"wrote {os.path.normpath(OUT)} ({len(levels)} dots)")


if __name__ == "__main__":
    main()
