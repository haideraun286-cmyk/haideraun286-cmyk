#!/usr/bin/env python3
"""Generate assets/skills-typing.svg: a terminal that types a command and then
types out your skills character by character, scrolls when the window is full,
and loops forever. GitHub plays SMIL animations inside <img>, so it just works.

    1. set USER, COMMAND and SKILLS below
    2. python generate_typing_svg.py
    3. commit assets/skills-typing.svg
"""
import json
import random
import re
from pathlib import Path
from xml.sax.saxutils import escape

# ----------------------------- your content -----------------------------
USER = "aunhaider"            # shows as the prompt:  /yourname $
COMMAND = "cat skills.json"  # the command typed first

SKILLS = {
    "type": "hard skills",
    "categories": [
        {"name": "Languages", "items": ["JavaScript", "Python", "C", "C++", "C#"]},
        {"name": "Frameworks", "items": ["React", "Node.js","Django"]},
        {"name": "Databases", "items": ["MongoDB", "MySQL", "PostgreSQL"]},
        {"name": "Tools", "items": ["Git", "Docker", "Linux", "VS Code"]},
    ],
}

# ------------------------------ look & feel ------------------------------
SYNTAX_COLORS = False   # False = plain white like a real terminal, True = coloured JSON
FONT_SIZE, CW, LH = 16, 9.6, 28   # font size, char width (monospace 0.6em), line height
PAD_X, BAR_H, PAD_TOP = 28, 0, 10
VISIBLE_LINES = 10                # window shows this many lines before it scrolls
MIN_WIDTH = 760

CMD_SPEED = 0.045       # seconds per typed command character (avg)
CODE_SPEED = 0.10      # seconds per typed code character (avg) - lower = faster
ENTER_PAUSE = 0.30      # pause after pressing "enter"
LINE_GAP = 0.03
HOLD = 2.5              # pause at the end before looping
SEED = 7                # change for a different "typing rhythm"

BG = "#000000"
WHITE, PROMPT_C = "#ffffff", "#e0a3ff"
C_KEY, C_STR = "#79c0ff", "#a5d6ff"


def json_lines():
    """Pretty-print JSON, keeping each 'items' list on a single line."""
    text = json.dumps(SKILLS, indent=4)
    text = re.sub(
        r"\[\s+((?:\"[^\"]*\",?\s*)+)\]",
        lambda m: "[" + ", ".join(re.findall(r"\"[^\"]*\"", m.group(1))) + "]",
        text,
    )
    return text.split("\n")


def colorize(line):
    if not SYNTAX_COLORS:
        return [(line, WHITE)]
    out, pos = [], 0
    for m in re.finditer(r"\"[^\"]*\"", line):
        out.append((line[pos:m.start()], WHITE))
        out.append((m.group(0), C_KEY if line[m.end():m.end() + 1] == ":" else C_STR))
        pos = m.end()
    out.append((line[pos:], WHITE))
    return out


def discrete(tag, attr, times, values, total, extra=""):
    assert times[0] == 0 and all(b >= a for a, b in zip(times, times[1:])), "keyTimes must be sorted"
    kt = ";".join(f"{t / total:.5f}" for t in times)
    return (f'<{tag} attributeName="{attr}" {extra} calcMode="discrete" dur="{total}s" '
            f'repeatCount="indefinite" keyTimes="{kt}" values="{";".join(values)}"/>')


def main():
    rnd = random.Random(SEED)

    def delay(base):
        d = base * rnd.uniform(0.6, 1.5)
        if rnd.random() < 0.04:               # the odd hesitation
            d += rnd.uniform(0.05, 0.12)
        return d

    code = json_lines()
    prompt = f"/{USER} $ "
    n_lines = len(code) + 2                    # command line + code + final prompt
    y = lambda i: BAR_H + PAD_TOP + (i + 1) * LH - 8   # baseline of line i

    width = int(max(MIN_WIDTH, max(len(l) for l in code) * CW + 2 * PAD_X))
    height = BAR_H + PAD_TOP + VISIBLE_LINES * LH + 8

    cursor = [(0.0, PAD_X + len(prompt) * CW, y(0))]   # (time, x, y)
    scroll = [(0.0, 0)]                                 # (time, offset px)
    clips = {}                                          # line index -> [(time, width)]
    t = 0.6

    # 1) typed command
    xcmd = PAD_X + len(prompt) * CW
    steps = [(0.0, 0.0)]
    for k in range(1, len(COMMAND) + 1):
        t += delay(CMD_SPEED)
        steps.append((t, k * CW))
        cursor.append((t, xcmd + k * CW, y(0)))
    clips[0] = steps
    t += ENTER_PAUSE

    # 2) typed code
    cur_off = 0
    for idx, line in enumerate(code, start=1):
        t += LINE_GAP
        indent = len(line) - len(line.lstrip(" "))
        off = max(0, (idx + 1 - VISIBLE_LINES) * LH)
        if off != cur_off:
            scroll.append((t, -off))
            cur_off = off
        cursor.append((t, PAD_X + indent * CW, y(idx)))
        steps = [(0.0, 0.0), (t, indent * CW)]          # indentation appears instantly
        for k in range(indent + 1, len(line) + 1):
            t += delay(CODE_SPEED)
            steps.append((t, k * CW))
            cursor.append((t, PAD_X + k * CW, y(idx)))
        clips[idx] = steps

    # 3) fresh prompt waiting for the next command
    last = n_lines - 1
    t += 0.5
    off = max(0, (last + 1 - VISIBLE_LINES) * LH)
    if off != cur_off:
        scroll.append((t, -off))
    clips[last] = [(0.0, 0.0), (t, len(prompt) * CW)]
    cursor.append((t, PAD_X + len(prompt) * CW, y(last)))
    total = round(t + HOLD, 2)

    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" rx="10" fill="{BG}"/>',
        '<defs>',
        f'<clipPath id="view"><rect x="0" y="{BAR_H}" width="{width}" height="{height - BAR_H}"/></clipPath>',
    ]
    for i, st in clips.items():
        times = [a for a, _ in st]
        vals = [f"{w:.1f}" for _, w in st]
        s.append(
            f'<clipPath id="c{i}"><rect x="{PAD_X}" y="{y(i) - 20}" height="{LH}" width="0">'
            f'{discrete("animate", "width", times, vals, total)}</rect></clipPath>'
        )
    s.append('</defs>')

    s.append('<g clip-path="url(#view)"><g>')
    s.append(discrete("animateTransform", "transform", [a for a, _ in scroll],
                      [f"0 {o}" for _, o in scroll], total, 'type="translate"'))

    font = (f'font-family="Courier New, Courier, monospace" font-size="{FONT_SIZE}" '
            f'font-weight="bold" xml:space="preserve" style="white-space:pre"')

    def text(x, yy, segs, clip=None):
        n = sum(len(tx) for tx, _ in segs)
        spans = "".join(f'<tspan fill="{c}">{escape(tx)}</tspan>' for tx, c in segs)
        cp = f' clip-path="url(#{clip})"' if clip else ""
        return (f'<text x="{x}" y="{yy}" {font} textLength="{n * CW:.1f}" '
                f'lengthAdjust="spacing"{cp}>{spans}</text>')

    # prompt on the first line is always visible; the command after it is typed
    prompt_segs = [(f"/{USER}", PROMPT_C), (" $ ", WHITE)]
    s.append(text(PAD_X, y(0), prompt_segs))
    s.append(text(xcmd, y(0), [(COMMAND, WHITE)], "c0"))
    for idx, line in enumerate(code, start=1):
        s.append(text(PAD_X, y(idx), colorize(line), f"c{idx}"))
    s.append(text(PAD_X, y(last), prompt_segs, f"c{last}"))

    # block cursor follows the typing head and blinks
    s.append(
        f'<rect width="{CW:.1f}" height="20" fill="#ffffff" opacity="0.85">'
        + discrete("animate", "x", [a for a, _, _ in cursor], [f"{x:.1f}" for _, x, _ in cursor], total)
        + discrete("animate", "y", [a for a, _, _ in cursor], [f"{yy - 16}" for _, _, yy in cursor], total)
        + '<animate attributeName="opacity" calcMode="discrete" dur="1.1s" repeatCount="indefinite" '
          'keyTimes="0;0.55" values="0.85;0"/></rect>'
    )
    s.append('</g></g></svg>')

    out = Path(__file__).parent / "assets" / "skills-typing.svg"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(s), encoding="utf-8")
    print(f"wrote {out} ({width}x{height}, {len(code)} code lines, loop {total}s)")


if __name__ == "__main__":
    main()