#!/usr/bin/env python3
"""Generate assets/hero.svg: your ASCII face (left) draws in line by line, then
the 'about me' is typed out like a terminal session (right), and it loops.

    1. python image_to_ascii.py me.jpeg --width 50 --invert > face.txt
    2. edit ABOUT below
    3. python generate_hero_svg.py
    4. commit assets/hero.svg
"""
import random
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).parent

# colour tags: g=green b=blue w=white m=muted y=yellow
ABOUT = [
    [("$ ", "g"), ("g++ about_me.cpp -o about_me && ./about_me", "w")],
    [("[ OK ] ", "g"), ("compiled in 0.42s (0 errors, 0 warnings)", "m")],
    [],
    [("-" * 46, "m")],
    [("name      ", "b"), (": ", "m"), ("Aun Haider Kazmi", "w")],
    [("handle    ", "b"), (": ", "m"), ("@haideraun286-cmyk", "w")],
    [("role      ", "b"), (": ", "m"), ("Software Developer / CS Student at NED", "w")],
    [("location  ", "b"), (": ", "m"), ("Karachi, Pakistan", "w")],
    [("focus     ", "b"), (": ", "m"), ("Web dev | DSA | Problem solving", "w")],
    [("languages ", "b"), (": ", "m"), ("English, Urdu", "w")],
    [("-" * 46, "m")],
    [("status    ", "b"), (": ", "m"), ("building things that matter", "y")],
    [("motto     ", "b"), (": ", "m"), ("while (alive) { learn(); build(); ship(); }", "w")],
    [("-" * 46, "m")],
    [("$ ", "g"), ("echo \"Let's build something together\"", "w")],
]

COL = {"g": "#3fb950", "b": "#79c0ff", "w": "#ffffff", "m": "#8b949e", "y": "#e3b341"}
BG, BAR, FACE_COL = "#000000", "#364a5c", "#7ee787"
TITLE = "about_me.cpp"

FACE_FS, FACE_CW, FACE_LH = 9, 5.4, 10.5
ABOUT_FS, ABOUT_CW, ABOUT_LH = 14, 8.4, 22
PAD, GAP, TOP = 28, 36, 70

# speed (seconds) - lower = faster
FACE_LINE_T = 0.035   # time between face lines appearing
CMD_SPEED = 0.040     # first line (the command) per character
OUT_SPEED = 0.010     # every other line per character
ENTER_PAUSE = 0.30    # pause after the command
LINE_GAP = 0.03
HOLD = 3.0            # pause at the end before looping
SEED = 7


def discrete(tag, attr, times, values, total, extra=""):
    assert times[0] == 0 and all(b >= a for a, b in zip(times, times[1:])), "keyTimes must be sorted"
    kt = ";".join(f"{t / total:.5f}" for t in times)
    return (f'<{tag} attributeName="{attr}" {extra} calcMode="discrete" dur="{total}s" '
            f'repeatCount="indefinite" keyTimes="{kt}" values="{";".join(values)}"/>')


def main():
    rnd = random.Random(SEED)

    def delay(base):
        d = base * rnd.uniform(0.6, 1.5)
        if rnd.random() < 0.04:
            d += rnd.uniform(0.05, 0.12)
        return d

    face_path = HERE / "face.txt"
    face = (face_path.read_text(encoding="utf-8").rstrip("\n").split("\n")
            if face_path.exists() else ["(face.txt missing)"])
    face_w = max(len(l) for l in face) * FACE_CW
    face_h = len(face) * FACE_LH
    about_w = max(sum(len(t) for t, _ in l) for l in ABOUT) * ABOUT_CW
    about_h = len(ABOUT) * ABOUT_LH

    width = int(PAD + face_w + GAP + about_w + PAD)
    height = int(TOP + max(face_h, about_h) + 20)
    face_x, about_x = PAD, PAD + face_w + GAP
    face_y0 = TOP + (max(face_h, about_h) - face_h) / 2
    fy = lambda i: face_y0 + i * FACE_LH
    ay = lambda i: TOP + i * ABOUT_LH

    # ---------------- timeline ----------------
    t = 0.3
    face_clips = {}
    for i, line in enumerate(face):
        if not line.strip():
            continue
        w = len(line) * FACE_CW
        face_clips[i] = [(0.0, 0.0), (t, w * 0.5), (t + 0.03, w)]
        t += FACE_LINE_T
    t += 0.25

    about_clips, cursor = {}, [(0.0, about_x, ay(0))]
    for i, segs in enumerate(ABOUT):
        if not segs:
            continue
        text = "".join(tx for tx, _ in segs)
        n = len(text)
        speed = CMD_SPEED if i == 0 else OUT_SPEED
        cursor.append((t, about_x, ay(i)))
        steps = [(0.0, 0.0)]
        if set(text) == {"-"}:                       # separator lines print instantly
            steps.append((t, n * ABOUT_CW))
            cursor.append((t + 0.0001, about_x + n * ABOUT_CW, ay(i)))
        else:
            for k in range(1, n + 1):
                t += delay(speed)
                steps.append((t, k * ABOUT_CW))
                cursor.append((t, about_x + k * ABOUT_CW, ay(i)))
        about_clips[i] = steps
        t += ENTER_PAUSE if i == 0 else LINE_GAP
    total = round(t + HOLD, 2)

    # ---------------- svg ----------------
    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" rx="10" fill="{BG}"/>',
        f'<path d="M0 10a10 10 0 0 1 10-10h{width - 20}a10 10 0 0 1 10 10v26H0z" fill="{BAR}"/>',
        '<circle cx="22" cy="18" r="6" fill="#e8604c"/><circle cx="42" cy="18" r="6" fill="#9ad08e"/>',
        f'<text x="{width / 2}" y="23" text-anchor="middle" fill="#8b949e" font-family="monospace" font-size="12">{escape(TITLE)}</text>',
        '<defs>',
    ]
    for i, st in face_clips.items():
        s.append(f'<clipPath id="f{i}"><rect x="{face_x}" y="{fy(i) - FACE_LH + 2}" height="{FACE_LH + 2}" width="0">'
                 + discrete("animate", "width", [a for a, _ in st], [f"{w:.1f}" for _, w in st], total)
                 + '</rect></clipPath>')
    for i, st in about_clips.items():
        s.append(f'<clipPath id="a{i}"><rect x="{about_x}" y="{ay(i) - ABOUT_LH + 5}" height="{ABOUT_LH}" width="0">'
                 + discrete("animate", "width", [a for a, _ in st], [f"{w:.1f}" for _, w in st], total)
                 + '</rect></clipPath>')
    s.append('</defs>')

    for i in face_clips:
        line = face[i]
        s.append(f'<text x="{face_x}" y="{fy(i)}" font-family="Courier New, Courier, monospace" font-size="{FACE_FS}" '
                 f'fill="{FACE_COL}" xml:space="preserve" style="white-space:pre" '
                 f'textLength="{len(line) * FACE_CW:.1f}" lengthAdjust="spacing" clip-path="url(#f{i})">{escape(line)}</text>')

    for i, segs in enumerate(ABOUT):
        if not segs:
            continue
        n = sum(len(tx) for tx, _ in segs)
        spans = "".join(f'<tspan fill="{COL[c]}">{escape(tx)}</tspan>' for tx, c in segs)
        s.append(f'<text x="{about_x}" y="{ay(i)}" font-family="Courier New, Courier, monospace" font-size="{ABOUT_FS}" '
                 f'font-weight="bold" xml:space="preserve" style="white-space:pre" '
                 f'textLength="{n * ABOUT_CW:.1f}" lengthAdjust="spacing" clip-path="url(#a{i})">{spans}</text>')

    s.append(
        f'<rect width="{ABOUT_CW:.1f}" height="18" fill="#ffffff" opacity="0.85">'
        + discrete("animate", "x", [a for a, _, _ in cursor], [f"{x:.1f}" for _, x, _ in cursor], total)
        + discrete("animate", "y", [a for a, _, _ in cursor], [f"{yy - 14:.1f}" for _, _, yy in cursor], total)
        + '<animate attributeName="opacity" calcMode="discrete" dur="1.1s" repeatCount="indefinite" '
          'keyTimes="0;0.55" values="0.85;0"/></rect>'
    )
    s.append('</svg>')

    out = HERE / "assets" / "hero.svg"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(s), encoding="utf-8")
    print(f"wrote {out} ({width}x{height}, loop {total}s)")


if __name__ == "__main__":
    main()
