# Illustrasjoner for deck uten dial (Page step) og Virtual Stream Deck som fjernkontroll. 1920x960.
import importlib.util, os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location("il", os.path.join(HERE, "gen-illustrations.py"))
il = importlib.util.module_from_spec(spec)
spec.loader.exec_module(il)
gi, f, k, KEY, GAP, PAD = il.gi, il.f, il.k, il.KEY, il.GAP, il.PAD
W, H = il.W, il.H
WHITE, GREY, DIM, CYAN, LIT = il.WHITE, il.GREY, il.DIM, il.CYAN, il.LIT


def tile(text, number="", note="", glyph=None, lit=None, big=False):
    """Flis som pluginen tegner: nummer, valgfri synk-firkant, ikon, navn (grått under ikon), notat."""
    S, q = 576, 4
    img, d, _ = gi.tile_base(S)
    if number:
        d.text((16 * q, 15 * q), number, font=f(16 * q, "semi"), fill=(200, 208, 218))
    if lit is not None:
        d.rounded_rectangle((113 * q, 14 * q, 130 * q, 31 * q), radius=3 * q, fill=LIT if lit else (14, 19, 25), outline=LIT if lit else (58, 70, 87), width=6)
    if glyph:
        glyph(d, 72 * q, 58 * q, q * 1.1, WHITE, int(4.5 * q))
        fo = f(18 * q, "bold")
        tw = d.textlength(text, font=fo)
        d.text(((S - tw) / 2, 84 * q), text, font=fo, fill=(174, 185, 199))
    else:
        fo = f((34 if big else 24) * q, "bold")
        tw = d.textlength(text, font=fo)
        d.text(((S - tw) / 2, (52 if big else 56) * q), text, font=fo, fill=WHITE)
    if note:
        fo = f(15 * q, "semi")
        tw = d.textlength(note, font=fo)
        d.text(((S - tw) / 2, 114 * q), note, font=fo, fill=(150, 160, 174))
    return img.resize((KEY, KEY), Image.LANCZOS)


def step(page, name, glyph, prev=False):
    return tile(name, f"p{page}", "‹ prev" if prev else "next ›", glyph)


def device(img, x, y, cols, rows, keys):
    w = cols * KEY + (cols - 1) * GAP + 2 * PAD
    h = rows * KEY + (rows - 1) * GAP + 2 * PAD
    il.body(img, x, y, w, h)
    il.grid(img, x, y, keys, cols)
    return w, h


def caption(d, cx, y, text):
    fo = f(24, "semi")
    tw = d.textlength(text, font=fo)
    d.text((cx - tw / 2, y), text, font=fo, fill=DIM)


def header(title, subtitle):
    img = gi.gradient((W, H), gi.BG_TOP, gi.BG_BOTTOM)
    d = ImageDraw.Draw(img)
    d.text((80, 46), title, font=f(58, "bold"), fill=WHITE)
    d.text((82, 122), subtitle, font=f(30), fill=GREY)
    return img, d


def no_dial(out):
    img, d = header("No dial? No problem", "Page step keys go to the next or previous page, and show where they lead.")
    E = il.empty_key()
    sd15 = [k("grp-spots"), k("grp-beams"), k("grp-wash"), k("grp-par"), il.marker(3, "MA3 Prog", gi.g_presets, True),
            k("pre-warm"), k("pre-cool"), k("pre-red"), k("pre-blue"), k("grp-all"),
            step(2, "Groups", gi.g_groups, prev=True), k("pre-center"), k("pre-stage-l"), k("pre-stage-r"), step(4, "Playback", gi.g_play)]
    mini = [k("prog-clear"), k("prog-store"), il.marker(3, "MA3 Prog", gi.g_presets, True),
            step(2, "Groups", gi.g_groups, prev=True), k("prog-highlt"), step(4, "Playback", gi.g_play)]
    w1 = 5 * KEY + 4 * GAP + 2 * PAD
    w2 = 3 * KEY + 2 * GAP + 2 * PAD
    h1 = 3 * KEY + 2 * GAP + 2 * PAD
    h2 = 2 * KEY + GAP + 2 * PAD
    x1 = (W - (w1 + 140 + w2)) // 2
    y1 = 250
    x2, y2 = x1 + w1 + 140, y1 + (h1 - h2) // 2
    device(img, x1, y1, 5, 3, sd15)
    device(img, x2, y2, 3, 2, mini)
    gi.draw_sync_badge(d, x1 + w1 + 70, y1 + h1 // 2, 34, 0.3)
    caption(d, x1 + w1 // 2, y1 + h1 + 34, "Stream Deck")
    caption(d, x2 + w2 // 2, y1 + h1 + 34, "Stream Deck Mini")
    img.save(out)


def virtual(out):
    img, d = header("Virtual Stream Deck as a remote", "Put DeckSync keys on a virtual deck on your screen and save keys on the real ones.")
    # vindu på skjermen
    vk = [step(2, "Groups", gi.g_groups, prev=True), tile("MA3 Prog", "p3", "Deck1", gi.g_presets, lit=True), step(4, "Playback", gi.g_play),
          tile("Home", "p1", "go to", gi.g_home), tile("Playback", "p4", "go to", gi.g_play), tile("ALL", note="target", big=True)]
    vw = 3 * KEY + 2 * GAP + 2 * PAD
    vh = 2 * KEY + GAP + 2 * PAD
    x1, y1 = 150, 300
    d.rounded_rectangle((x1 - 6, y1 - 50 + 8, x1 + vw + 6, y1 + vh + 14), radius=18, fill=(8, 12, 18))
    d.rounded_rectangle((x1 - 6, y1 - 50, x1 + vw + 6, y1 + vh + 6), radius=18, fill=(34, 36, 42), outline=(78, 82, 92), width=2)
    d.text((x1 + 14, y1 - 40), "Virtual Stream Deck", font=f(22, "semi"), fill=(200, 205, 214))
    for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse((x1 + vw - 78 + i * 26, y1 - 34, x1 + vw - 62 + i * 26, y1 - 18), fill=c)
    il.grid(img, x1, y1, vk, 3)
    caption(d, x1 + vw // 2, y1 + vh + 40, "On your screen")

    # fysisk deck til høyre
    sd15 = [k("grp-spots"), k("grp-beams"), k("grp-wash"), k("grp-par"), il.marker(3, "MA3 Prog", gi.g_presets, True),
            k("pre-warm"), k("pre-cool"), k("pre-red"), k("pre-blue"), k("grp-all"),
            k("pre-center"), k("pre-stage-l"), k("pre-stage-r"), k("pre-audience"), k("prog-highlt")]
    w2 = 5 * KEY + 4 * GAP + 2 * PAD
    h2 = 3 * KEY + 2 * GAP + 2 * PAD
    x2 = W - 150 - w2
    y2 = y1 + (vh - h2) // 2 - 10
    device(img, x2, y2, 5, 3, sd15)
    caption(d, x2 + w2 // 2, y2 + h2 + 34, "Your Stream Decks follow")

    # pil fra virtuelt til fysisk
    ax0, ax1, ay = x1 + vw + 30, x2 - 30, y1 + vh // 2
    d.line((ax0, ay, ax1 - 20, ay), fill=CYAN, width=8)
    d.polygon([(ax1, ay), (ax1 - 30, ay - 20), (ax1 - 30, ay + 20)], fill=CYAN)
    img.save(out)


def main():
    for name, fn in (("5-no-dial.png", no_dial), ("6-virtual-remote.png", virtual)):
        fn(os.path.join(ROOT, "docs", "examples", name))
        fn(os.path.join(ROOT, "marketplace", "gallery-" + name))
    print("ok")


if __name__ == "__main__":
    main()
