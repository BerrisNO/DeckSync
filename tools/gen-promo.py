# Universelle reklameillustrasjoner: redigering, strømming, musikk og kontor i stedet for lysprogrammering.
# Skriver over docs/examples/1-3,5,6 og marketplace/gallery-*. Generiske ikoner, ingen varemerker.
import importlib.util, math, os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


il = load("il", "gen-illustrations.py")
i2 = load("i2", "gen-illustrations-2.py")
gi, f, KEY = il.gi, il.f, il.KEY
WHITE, GREY, CYAN = il.WHITE, il.GREY, il.CYAN
TILE = (35, 46, 61)
ORANGE, RED, GREEN, DARK = (242, 163, 58), (214, 64, 64), (53, 208, 127), (16, 21, 28)


# ---- generiske glyfer: (d, cx, cy, k, farge, strek) ----
def g_brush(d, cx, cy, k, c, w):
    d.line((cx + 16 * k, cy - 18 * k, cx - 4 * k, cy + 2 * k), fill=c, width=w + int(2 * k))
    d.ellipse((cx - 18 * k, cy + 2 * k, cx - 2 * k, cy + 18 * k), fill=c)


def g_crop(d, cx, cy, k, c, w):
    d.line((cx - 12 * k, cy - 20 * k, cx - 12 * k, cy + 12 * k), fill=c, width=w)
    d.line((cx - 12 * k, cy + 12 * k, cx + 20 * k, cy + 12 * k), fill=c, width=w)
    d.line((cx - 20 * k, cy - 12 * k, cx + 12 * k, cy - 12 * k), fill=c, width=w)
    d.line((cx + 12 * k, cy - 12 * k, cx + 12 * k, cy + 20 * k), fill=c, width=w)


def g_layers(d, cx, cy, k, c, w):
    for dy in (8, 0, -8):
        y = cy + dy * k
        d.polygon([(cx, y - 9 * k), (cx + 20 * k, y), (cx, y + 9 * k), (cx - 20 * k, y)], fill=TILE, outline=c, width=w)


def _arc_arrow(d, cx, cy, r, a0, a1, c, w, head_at_start):
    d.arc((cx - r, cy - r, cx + r, cy + r), start=a0, end=a1, fill=c, width=w)
    a = math.radians(a0 if head_at_start else a1)
    sgn = -1 if head_at_start else 1
    tip = (cx + r * math.cos(a), cy + r * math.sin(a))
    tx, ty = -math.sin(a) * sgn, math.cos(a) * sgn
    nx, ny = math.cos(a), math.sin(a)
    s = r * 0.55
    base = (tip[0] - tx * s * 0.2, tip[1] - ty * s * 0.2)
    d.polygon([(tip[0] + tx * s * 0.75, tip[1] + ty * s * 0.75), (base[0] + nx * s * 0.6, base[1] + ny * s * 0.6), (base[0] - nx * s * 0.6, base[1] - ny * s * 0.6)], fill=c)


def g_undo(d, cx, cy, k, c, w):
    _arc_arrow(d, cx, cy + 2 * k, 15 * k, 200, 60, c, w, True)


def g_redo(d, cx, cy, k, c, w):
    _arc_arrow(d, cx, cy + 2 * k, 15 * k, 120, 340, c, w, False)


def g_text(d, cx, cy, k, c, w):
    d.line((cx - 15 * k, cy - 16 * k, cx + 15 * k, cy - 16 * k), fill=c, width=w + int(k))
    d.line((cx, cy - 16 * k, cx, cy + 17 * k), fill=c, width=w + int(k))


def g_zoom(d, cx, cy, k, c, w):
    d.ellipse((cx - 18 * k, cy - 18 * k, cx + 8 * k, cy + 8 * k), outline=c, width=w)
    d.line((cx + 5 * k, cy + 5 * k, cx + 18 * k, cy + 18 * k), fill=c, width=w + int(k))


def g_export(d, cx, cy, k, c, w):
    d.line((cx - 16 * k, cy + 2 * k, cx - 16 * k, cy + 16 * k), fill=c, width=w)
    d.line((cx - 16 * k, cy + 16 * k, cx + 16 * k, cy + 16 * k), fill=c, width=w)
    d.line((cx + 16 * k, cy + 16 * k, cx + 16 * k, cy + 2 * k), fill=c, width=w)
    d.line((cx, cy + 6 * k, cx, cy - 18 * k), fill=c, width=w)
    d.line((cx, cy - 18 * k, cx - 9 * k, cy - 9 * k), fill=c, width=w)
    d.line((cx, cy - 18 * k, cx + 9 * k, cy - 9 * k), fill=c, width=w)


def g_save(d, cx, cy, k, c, w):
    d.rounded_rectangle((cx - 17 * k, cy - 17 * k, cx + 17 * k, cy + 17 * k), radius=4 * k, outline=c, width=w)
    d.rectangle((cx - 9 * k, cy - 17 * k, cx + 7 * k, cy - 6 * k), outline=c, width=w)
    d.rectangle((cx - 9 * k, cy + 3 * k, cx + 9 * k, cy + 17 * k), outline=c, width=w)


def g_mic(d, cx, cy, k, c, w):
    d.rounded_rectangle((cx - 7 * k, cy - 20 * k, cx + 7 * k, cy + 4 * k), radius=7 * k, outline=c, width=w)
    d.arc((cx - 14 * k, cy - 12 * k, cx + 14 * k, cy + 12 * k), start=0, end=180, fill=c, width=w)
    d.line((cx, cy + 12 * k, cx, cy + 20 * k), fill=c, width=w)
    d.line((cx - 8 * k, cy + 20 * k, cx + 8 * k, cy + 20 * k), fill=c, width=w)


def g_rec(d, cx, cy, k, c, w):
    d.ellipse((cx - 17 * k, cy - 17 * k, cx + 17 * k, cy + 17 * k), outline=c, width=w)
    d.ellipse((cx - 9 * k, cy - 9 * k, cx + 9 * k, cy + 9 * k), fill=c)


def g_chat(d, cx, cy, k, c, w):
    d.rounded_rectangle((cx - 19 * k, cy - 16 * k, cx + 19 * k, cy + 9 * k), radius=6 * k, outline=c, width=w)
    d.polygon([(cx - 9 * k, cy + 8 * k), (cx - 9 * k, cy + 19 * k), (cx + 2 * k, cy + 8 * k)], fill=c)


def g_screen(d, cx, cy, k, c, w):
    d.rounded_rectangle((cx - 20 * k, cy - 16 * k, cx + 20 * k, cy + 9 * k), radius=3 * k, outline=c, width=w)
    d.line((cx, cy + 9 * k, cx, cy + 17 * k), fill=c, width=w)
    d.line((cx - 10 * k, cy + 17 * k, cx + 10 * k, cy + 17 * k), fill=c, width=w)


def g_note(d, cx, cy, k, c, w):
    d.ellipse((cx - 14 * k, cy + 6 * k, cx - 2 * k, cy + 17 * k), fill=c)
    d.line((cx - 3 * k, cy + 11 * k, cx - 3 * k, cy - 18 * k), fill=c, width=w)
    d.line((cx - 3 * k, cy - 18 * k, cx + 13 * k, cy - 12 * k), fill=c, width=w + int(k))


def g_next(d, cx, cy, k, c, w):
    d.polygon([(cx - 14 * k, cy - 14 * k), (cx + 6 * k, cy), (cx - 14 * k, cy + 14 * k)], outline=c, width=w)
    d.line((cx + 13 * k, cy - 14 * k, cx + 13 * k, cy + 14 * k), fill=c, width=w + int(k))


def g_timer(d, cx, cy, k, c, w):
    d.ellipse((cx - 16 * k, cy - 13 * k, cx + 16 * k, cy + 19 * k), outline=c, width=w)
    d.line((cx, cy + 3 * k, cx, cy - 7 * k), fill=c, width=w)
    d.line((cx - 5 * k, cy - 19 * k, cx + 5 * k, cy - 19 * k), fill=c, width=w)


def g_mail(d, cx, cy, k, c, w):
    d.rounded_rectangle((cx - 20 * k, cy - 13 * k, cx + 20 * k, cy + 14 * k), radius=3 * k, outline=c, width=w)
    d.line((cx - 19 * k, cy - 11 * k, cx, cy + 3 * k), fill=c, width=w)
    d.line((cx, cy + 3 * k, cx + 19 * k, cy - 11 * k), fill=c, width=w)


def g_calendar(d, cx, cy, k, c, w):
    d.rounded_rectangle((cx - 17 * k, cy - 14 * k, cx + 17 * k, cy + 17 * k), radius=3 * k, outline=c, width=w)
    d.line((cx - 17 * k, cy - 4 * k, cx + 17 * k, cy - 4 * k), fill=c, width=w)
    for dx in (-8, 8):
        d.line((cx + dx * k, cy - 19 * k, cx + dx * k, cy - 11 * k), fill=c, width=w)


def ukey(label, glyph, fill=None):
    """Vanlig tast: ikon og navn. fill gir farget flis (aktiv/advarsel)."""
    S, q = 576, 4
    img, d, _ = gi.tile_base(S)
    fg = WHITE
    if fill:
        edge = tuple(min(255, int(ch * 0.8 + 51)) for ch in fill)
        d.rounded_rectangle((6 * q, 6 * q, 138 * q, 138 * q), radius=14 * q, fill=fill, outline=edge, width=3 * q)
        fg = DARK if (0.299 * fill[0] + 0.587 * fill[1] + 0.114 * fill[2]) > 150 else WHITE
    if fill:  # glyfer med TILE-fyll (lag) trenger flisfargen
        global TILE
        old, TILE = TILE, fill
        glyph(d, 72 * q, 54 * q, q * 1.15, fg, int(4.5 * q))
        TILE = old
    else:
        glyph(d, 72 * q, 54 * q, q * 1.15, fg, int(4.5 * q))
    fo = f(19 * q, "bold")
    tw = d.textlength(label, font=fo)
    d.text(((S - tw) / 2, 92 * q), label, font=fo, fill=fg)
    return img.resize((KEY, KEY), Image.LANCZOS)


U = {
    "undo": ukey("Undo", g_undo), "redo": ukey("Redo", g_redo), "save": ukey("Save", g_save), "export": ukey("Export", g_export),
    "brush": ukey("Brush", g_brush, ORANGE), "crop": ukey("Crop", g_crop), "layers": ukey("Layers", g_layers), "text": ukey("Text", g_text),
    "zoom": ukey("Zoom", g_zoom), "assets": ukey("Assets", gi.g_folder), "preview": ukey("Preview", gi.g_play),
    "mic": ukey("Mic", g_mic), "cam": ukey("Camera", gi.g_video), "live": ukey("Go Live", g_rec, RED), "rec": ukey("Record", g_rec),
    "chat": ukey("Chat", g_chat), "scene1": ukey("Scene 1", g_screen), "scene2": ukey("Scene 2", g_screen), "volume": ukey("Volume", gi.g_sound),
    "music": ukey("Music", g_note), "play": ukey("Play", gi.g_play, GREEN), "next": ukey("Next", g_next), "timer": ukey("Timer", g_timer),
    "mail": ukey("Mail", g_mail), "calendar": ukey("Calendar", g_calendar), "fav": ukey("Favorites", gi.g_star), "settings": ukey("Settings", gi.g_gear),
    "lights": ukey("Lights", gi.g_light),
}
PAGES = {1: ("Home", gi.g_home), 2: ("Edit", g_brush), 3: ("Stream", g_rec), 4: ("Music", g_note)}
mk = lambda p, lit=True: il.marker(p, PAGES[p][0], PAGES[p][1], lit)
stp = lambda p, prev=False: i2.step(p, PAGES[p][0], PAGES[p][1], prev)

EDIT_PLUS = lambda lit=True: [U["undo"], U["redo"], U["save"], mk(2, lit), U["brush"], U["crop"], U["layers"], U["text"]]
EDIT_15 = lambda: [U["zoom"], U["crop"], U["layers"], U["text"], mk(2), U["undo"], U["redo"], U["save"], U["export"], U["assets"],
                   U["preview"], U["rec"], U["mic"], U["volume"], U["fav"]]
HOME_15 = lambda: [U["mail"], U["calendar"], U["chat"], U["music"], mk(1, False), U["scene1"], U["assets"], U["timer"], U["volume"], U["mic"],
                   U["play"], U["next"], U["fav"], U["settings"], U["lights"]]
SEGS = [("Brush size", 40), ("Opacity", 80), ("Zoom", 100)]


def both(name, fn):
    for folder, prefix in (("docs/examples", ""), ("marketplace", "gallery-")):
        fn(os.path.join(ROOT, folder, prefix + name))


def no_dial(out):
    img, d = i2.header("No dial? No problem", "Page step keys go to the next or previous page, and show where they lead.")
    sd15 = EDIT_15()
    sd15[10], sd15[14] = stp(1, True), stp(3)
    mini = [U["undo"], U["save"], mk(2), stp(1, True), U["brush"], stp(3)]
    KEYW, GAP, PAD = il.KEY, il.GAP, il.PAD
    w1, w2 = 5 * KEYW + 4 * GAP + 2 * PAD, 3 * KEYW + 2 * GAP + 2 * PAD
    h1, h2 = 3 * KEYW + 2 * GAP + 2 * PAD, 2 * KEYW + GAP + 2 * PAD
    x1, y1 = (il.W - (w1 + 140 + w2)) // 2, 250
    x2, y2 = x1 + w1 + 140, y1 + (h1 - h2) // 2
    i2.device(img, x1, y1, 5, 3, sd15)
    i2.device(img, x2, y2, 3, 2, mini)
    gi.draw_sync_badge(d, x1 + w1 + 70, y1 + h1 // 2, 34, 0.3)
    i2.caption(d, x1 + w1 // 2, y1 + h1 + 34, "Stream Deck")
    i2.caption(d, x2 + w2 // 2, y1 + h1 + 34, "Stream Deck Mini")
    img.save(out)


def virtual(out):
    img, d = i2.header("Virtual Stream Deck as a remote", "Put DeckSync keys on a virtual deck on your screen and save keys on the real ones.")
    KEYW, GAP, PAD = il.KEY, il.GAP, il.PAD
    vk = [stp(1, True), i2.tile("Edit", "Page 2", "Deck1", g_brush, lit=True), stp(3),
          i2.tile("Home", "Page 1", "go to", gi.g_home), i2.tile("Music", "Page 4", "go to", g_note), i2.tile("ALL", note="target", big=True)]
    vw, vh = 3 * KEYW + 2 * GAP + 2 * PAD, 2 * KEYW + GAP + 2 * PAD
    x1, y1 = 150, 300
    d.rounded_rectangle((x1 - 6, y1 - 42, x1 + vw + 6, y1 + vh + 14), radius=18, fill=(8, 12, 18))
    d.rounded_rectangle((x1 - 6, y1 - 50, x1 + vw + 6, y1 + vh + 6), radius=18, fill=(34, 36, 42), outline=(78, 82, 92), width=2)
    d.text((x1 + 14, y1 - 40), "Virtual Stream Deck", font=f(22, "semi"), fill=(200, 205, 214))
    for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse((x1 + vw - 78 + i * 26, y1 - 34, x1 + vw - 62 + i * 26, y1 - 18), fill=c)
    il.grid(img, x1, y1, vk, 3)
    i2.caption(d, x1 + vw // 2, y1 + vh + 40, "On your screen")
    w2, h2 = 5 * KEYW + 4 * GAP + 2 * PAD, 3 * KEYW + 2 * GAP + 2 * PAD
    x2, y2 = il.W - 150 - w2, y1 + (vh - h2) // 2 - 10
    i2.device(img, x2, y2, 5, 3, EDIT_15())
    i2.caption(d, x2 + w2 // 2, y2 + h2 + 34, "Your Stream Decks follow")
    ax0, ax1, ay = x1 + vw + 30, x2 - 30, y1 + vh // 2
    d.line((ax0, ay, ax1 - 20, ay), fill=CYAN, width=8)
    d.polygon([(ax1, ay), (ax1 - 30, ay - 20), (ax1 - 30, ay + 20)], fill=CYAN)
    img.save(out)


def main():
    both("1-follow.png", lambda o: il.scene(o, "Every deck on the same page", "Turn a page on one Stream Deck and the others follow.",
                                            EDIT_PLUS(), EDIT_15(), ([("Deck1 - Edit", WHITE), ("Deck2 - Edit", WHITE)], "ALL: Page 2", CYAN, SEGS)))
    both("2-split.png", lambda o: il.scene(o, "Or send each deck its own way", "A Go to page key or the dial moves one deck. The strip shows where every deck is.",
                                           EDIT_PLUS(False), HOME_15(), ([("Deck1: Page 2 Edit", WHITE), ("Deck2: Page 1 Home", WHITE)], "PAGES", GREY, SEGS)))
    both("3-dial.png", lambda o: il.scene(o, "One dial for every page", "Turn to pick a page, press to go there. Hold and turn to choose which deck.",
                                          EDIT_PLUS(), EDIT_15(), ([("Stream", WHITE), ("target: ALL", GREY)], "→ Page 3", CYAN, SEGS), dial_active=True))
    both("5-no-dial.png", no_dial)
    both("6-virtual-remote.png", virtual)
    print("ok")


if __name__ == "__main__":
    main()
