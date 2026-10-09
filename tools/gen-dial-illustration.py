# Fokusert illustrasjon av sidehjulet: stripen og dialen i fire steg (status, vri, trykk, hold + vri). 1920x960.
import importlib.util, math, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONTS = r"C:\Windows\Fonts"
spec = importlib.util.spec_from_file_location("gi", os.path.join(HERE, "gen-images.py"))
gi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gi)

W, H = 1920, 960
WHITE, GREY, DIM, CYAN = (255, 255, 255), (159, 179, 200), (127, 141, 160), (38, 184, 168)
PW, GAPX, X0 = 400, 53, 80


def f(px, w="regular"):
    return ImageFont.truetype(os.path.join(FONTS, {"bold": "segoeuib.ttf", "semi": "seguisb.ttf", "regular": "segoeui.ttf"}[w]), px)


def strip(d, x, y, header, header_color, rows):
    """Touch-stripen (200x100) i dobbel størrelse."""
    d.rounded_rectangle((x, y, x + PW, y + 200), radius=18, fill=(0, 0, 0), outline=(58, 62, 70), width=3)
    gi.draw_sync_badge(d, x + 38, y + 30, 22, 0.2)
    d.text((x + 72, y + 2), header, font=f(40, "bold"), fill=header_color)
    d.rectangle((x + 16, y + 58, x + PW - 16, y + 61), fill=CYAN)
    for i, (text, color, size) in enumerate(rows[:3]):
        d.text((x + 16, y + 68 + i * 42), text, font=f(size), fill=color)


def arc_arrow(d, cx, cy, r, a0, a1, color, width=8):
    d.arc((cx - r, cy - r, cx + r, cy + r), start=a0, end=a1, fill=color, width=width)
    a = math.radians(a1)
    tip = (cx + r * math.cos(a), cy + r * math.sin(a))
    tx, ty = -math.sin(a), math.cos(a)
    nx, ny = math.cos(a), math.sin(a)
    s = 22
    base = (tip[0] - tx * s, tip[1] - ty * s)
    d.polygon([(tip[0] + tx * 6, tip[1] + ty * 6), (base[0] + nx * s * 0.7, base[1] + ny * s * 0.7), (base[0] - nx * s * 0.7, base[1] - ny * s * 0.7)], fill=color)


def dial(d, cx, cy, turn=False, press=False):
    r = 92
    if press:
        d.ellipse((cx - r - 16, cy - r - 16, cx + r + 16, cy + r + 16), outline=CYAN, width=6)
    if turn:
        arc_arrow(d, cx, cy, r + 42, 205, 335, CYAN)
    d.ellipse((cx - r, cy - r + 8, cx + r, cy + r + 8), fill=(8, 12, 18))  # skygge
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(27, 34, 48), outline=(78, 84, 94), width=4)
    gi.draw_sync_badge(d, cx, cy, 44, 0.4)


def main():
    img = gi.gradient((W, H), gi.BG_TOP, gi.BG_BOTTOM)
    d = ImageDraw.Draw(img)
    d.text((80, 46), "The page dial", font=f(58, "bold"), fill=WHITE)
    d.text((82, 122), "One dial on Stream Deck + moves every deck. The touch strip always shows where they are.", font=f(30), fill=GREY)

    steps = [
        ("1", "At rest", "Shows the page of every deck.", "ALL: P2", CYAN,
         [("Deck1 - Edit", WHITE, 28), ("Deck2 - Tools", WHITE, 28)], dict()),
        ("2", "Turn", "Pick a page. Nothing moves yet.", "\u2192 P3", CYAN,
         [("Stream", WHITE, 30), ("target: ALL", GREY, 26)], dict(turn=True)),
        ("3", "Press", "All decks go to the page.", "ALL: P3", CYAN,
         [("Deck1 - Stream", WHITE, 28), ("Deck2 - Scenes", WHITE, 28)], dict(press=True)),
        ("4", "Hold and turn", "Choose which deck to move.", "TURN: DECK", CYAN,
         [("target: Deck2", WHITE, 30)], dict(turn=True, press=True)),
    ]
    for i, (num, name, desc, header, hc, rows, gesture) in enumerate(steps):
        x = X0 + i * (PW + GAPX)
        cx = x + PW // 2
        strip(d, x, 240, header, hc, rows)
        dial(d, cx, 610, **gesture)
        d.ellipse((x, 782, x + 44, 826), fill=CYAN)
        tw = d.textlength(num, font=f(26, "bold"))
        d.text((x + 22 - tw / 2, 786), num, font=f(26, "bold"), fill=(16, 21, 28))
        d.text((x + 60, 780), name, font=f(34, "bold"), fill=WHITE)
        d.text((x, 840), desc, font=f(25), fill=GREY)
        if i < len(steps) - 1:
            ax = x + PW + GAPX // 2
            d.line((ax - 12, 340, ax + 10, 340), fill=DIM, width=4)
            d.polygon([(ax + 16, 340), (ax + 4, 331), (ax + 4, 349)], fill=DIM)

    for out in (os.path.join(ROOT, "docs", "examples", "4-page-dial.png"), os.path.join(ROOT, "marketplace", "gallery-4-page-dial.png")):
        img.save(out)
    print("ok")


if __name__ == "__main__":
    main()
