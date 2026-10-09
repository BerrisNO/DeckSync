# Illustrasjoner av to deck (Stream Deck + og 15 taster) som viser hvordan DeckSync virker.
# Bruker tastene fra gen-demo-keys.py og glyfene fra gen-images.py. 1920x960, til Marketplace/README.
import importlib.util, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONTS = r"C:\Windows\Fonts"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


demo = load("demo", "gen-demo-keys.py")
gi = load("gi", "gen-images.py")
KEYS = demo.KEYS

W, H = 1920, 960
KEY, GAP, PAD = 132, 22, 40
WHITE, GREY, DIM, CYAN, LIT = (255, 255, 255), (159, 179, 200), (127, 141, 160), (38, 184, 168), (53, 208, 127)
BODY, BODY_EDGE = (22, 23, 26), (60, 62, 68)


def f(px, w="regular"):
    return ImageFont.truetype(os.path.join(FONTS, {"bold": "segoeuib.ttf", "semi": "seguisb.ttf", "regular": "segoeui.ttf"}[w]), px)


def marker(page, name, glyph, lit):
    """Sidemarkøren: p-nummer, synk-firkant, sideikon og navn."""
    S, k = 576, 4
    img, d, _ = gi.tile_base(S)
    d.text((16 * k, 15 * k), f"Page {page}", font=f(16 * k, "semi"), fill=(200, 208, 218))
    d.rounded_rectangle((113 * k, 14 * k, 130 * k, 31 * k), radius=3 * k, fill=LIT if lit else (14, 19, 25), outline=LIT if lit else (58, 70, 87), width=6)
    glyph(d, 72 * k, 66 * k, k * 1.25, WHITE, int(4.5 * k))
    fo = f(19 * k, "bold")
    tw = d.textlength(name, font=fo)
    d.text(((S - tw) / 2, 104 * k), name, font=fo, fill=(174, 185, 199))
    return img.resize((KEY, KEY), Image.LANCZOS)


def empty_key():
    return gi.tile_base(576)[0].resize((KEY, KEY), Image.LANCZOS)


def k(name):
    return KEYS[name].resize((KEY, KEY), Image.LANCZOS)


def body(img, x, y, w, h):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x, y + 8, x + w, y + h + 8), radius=34, fill=(8, 12, 18))  # skygge
    d.rounded_rectangle((x, y, x + w, y + h), radius=34, fill=BODY, outline=BODY_EDGE, width=3)


def grid(img, x, y, keys, cols):
    for i, key in enumerate(keys):
        img.paste(key, (x + PAD + (i % cols) * (KEY + GAP), y + PAD + (i // cols) * (KEY + GAP)))


def strip(img, x, y, w, lines, header, header_color, segs):
    """Touch-stripen: tre enkle segmenter og DeckSync-segmentet helt til høyre."""
    d = ImageDraw.Draw(img)
    h = 110
    d.rounded_rectangle((x, y, x + w, y + h), radius=12, fill=(0, 0, 0), outline=(50, 52, 58), width=2)
    seg = w / 4
    for i, (label, val) in enumerate(segs):
        sx = x + i * seg + 14
        d.text((sx, y + 12), label, font=f(15, "semi"), fill=WHITE)
        d.ellipse((sx, y + 46, sx + 34, y + 80), outline=(242, 163, 58), width=4)
        d.line((sx + 17, y + 63, sx + 27, y + 53), fill=(242, 163, 58), width=4)
        if val is not None:
            d.text((sx + 92, y + 40), f"{val} %", font=f(18, "semi"), fill=WHITE)
            d.rounded_rectangle((sx + 46, y + 72, sx + 132, y + 79), radius=3, fill=(60, 60, 60))
            d.rounded_rectangle((sx + 46, y + 72, sx + 46 + 86 * val / 100, y + 79), radius=3, fill=WHITE)
    sx = x + 3 * seg + 10
    gi.draw_sync_badge(d, sx + 13, y + 20, 12, 0.1)
    d.text((sx + 32, y + 5), header, font=f(22, "bold"), fill=header_color)
    d.rectangle((sx, y + 36, x + w - 12, y + 38), fill=CYAN)
    for i, (text, color) in enumerate(lines[:3]):
        d.text((sx, y + 42 + i * 21), text, font=f(15), fill=color)


def dials(img, x, y, w, active):
    d = ImageDraw.Draw(img)
    seg = w / 4
    for i in range(4):
        cx, cy, r = x + seg * i + seg / 2, y + 50, 44
        if i == 3 and active:
            d.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), outline=CYAN, width=4)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(27, 34, 48), outline=(70, 74, 82), width=3)
        if i == 3:
            gi.draw_sync_badge(d, cx, cy, 22, 0.2)


def scene(out, title, subtitle, plus, sd15, strip_args, dial_active=False, caption=("Stream Deck +", "Stream Deck")):
    img = gi.gradient((W, H), gi.BG_TOP, gi.BG_BOTTOM)
    d = ImageDraw.Draw(img)
    d.text((80, 46), title, font=f(58, "bold"), fill=WHITE)
    d.text((82, 122), subtitle, font=f(30), fill=GREY)

    pw = 4 * KEY + 3 * GAP + 2 * PAD
    ph = PAD + 2 * KEY + GAP + 24 + 110 + 24 + 100 + PAD
    sw = 5 * KEY + 4 * GAP + 2 * PAD
    sh = 3 * KEY + 2 * GAP + 2 * PAD
    total = pw + 120 + sw
    px, top = (W - total) // 2, 220
    sx, sy = px + pw + 120, top + (ph - sh) // 2

    body(img, px, top, pw, ph)
    grid(img, px, top, plus, 4)
    inner = pw - 2 * PAD
    strip(img, px + PAD, top + PAD + 2 * KEY + GAP + 24, inner, *strip_args)
    dials(img, px + PAD, top + PAD + 2 * KEY + GAP + 24 + 110 + 24, inner, dial_active)

    body(img, sx, sy, sw, sh)
    grid(img, sx, sy, sd15, 5)

    gi.draw_sync_badge(d, px + pw + 60, top + ph // 2, 34, 0.3)
    for cx, text in ((px + pw // 2, caption[0]), (sx + sw // 2, caption[1])):
        fo = f(24, "semi")
        tw = d.textlength(text, font=fo)
        d.text((cx - tw / 2, top + ph + 34), text, font=fo, fill=DIM)
    img.save(out)


def main():
    out = os.path.join(ROOT, "docs", "examples")
    os.makedirs(out, exist_ok=True)
    E = empty_key()
    segs = [("Dimmer", 98), ("Pan", 42), ("Tilt", 61)]

    prog_plus = lambda lit: [k("prog-clear"), k("prog-store"), k("prog-align"), marker(3, "MA3 Prog", gi.g_presets, lit),
                             k("feat-dimmer"), k("feat-position"), k("feat-gobo"), k("feat-color")]
    prog_15 = [k("grp-spots"), k("grp-beams"), k("grp-wash"), k("grp-par"), marker(3, "MA3 Prog", gi.g_presets, True),
               k("pre-warm"), k("pre-cool"), k("pre-red"), k("pre-blue"), k("grp-all"),
               k("pre-center"), k("pre-stage-l"), k("pre-stage-r"), k("pre-audience"), k("prog-highlt")]
    home_15 = [k("pb-go"), k("pb-pause"), k("pb-goback"), k("pb-flash"), marker(1, "Home", gi.g_home, False),
               k("cue-1"), k("cue-2"), k("cue-3"), k("cue-4"), k("cue-5"),
               k("snd-mic1"), k("snd-mic2"), k("snd-track"), k("snd-mute"), k("pb-blackout")]

    scene(os.path.join(out, "1-follow.png"), "Every deck on the same page",
          "Turn a page on one Stream Deck and the others follow.",
          prog_plus(True), prog_15,
          ([("Deck1 - MA3 Prog", WHITE), ("Deck2 - MA3 Prog", WHITE)], "ALL: P3", CYAN, segs))

    scene(os.path.join(out, "2-split.png"), "Or send each deck its own way",
          "A Go to page key or the dial moves one deck. The strip shows where every deck is.",
          prog_plus(False), home_15,
          ([("Deck1: P3 MA3 Prog", WHITE), ("Deck2: P1 Home", WHITE)], "PAGES", GREY, segs))

    scene(os.path.join(out, "3-dial.png"), "One dial for every page",
          "Turn to pick a page, press to go there. Hold and turn to choose which deck.",
          prog_plus(True), prog_15,
          ([("Playback", WHITE), ("target: ALL", GREY)], "\u2192 P4", CYAN, segs), dial_active=True)
    print("ok", out)


if __name__ == "__main__":
    main()
