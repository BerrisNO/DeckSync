# Lager "falske" tastebilder med innbakt tekst til skjermbilder (Marketplace, README).
# Samme flis-stil som DeckSync/MA3Deck-tastene. Skrives til notes/mock/screenshot-keys/ (lokalt).
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "notes", "mock", "screenshot-keys")
FONTS = r"C:\Windows\Fonts"
S = 576
K = S / 144
WHITE, DARK = (255, 255, 255), (16, 21, 28)
TILE, EDGE, BG = (35, 46, 61), (58, 70, 87), (16, 21, 28)
ACTIVE, LIT, RED, CYAN, GREY = (242, 163, 58), (53, 208, 127), (214, 64, 64), (38, 184, 168), (159, 179, 200)


def font(px, weight="bold"):
    name = {"bold": "segoeuib.ttf", "semi": "seguisb.ttf", "regular": "segoeui.ttf"}[weight]
    return ImageFont.truetype(os.path.join(FONTS, name), int(px * K))


def fit(d, text, max_w, sizes, max_lines=2):
    words = text.split()
    for size in sizes:
        f = font(size)
        lines, cur = [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if d.textlength(t, font=f) <= max_w:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        if len(lines) <= max_lines and all(d.textlength(l, font=f) <= max_w for l in lines):
            return f, lines
    f = font(sizes[-1])
    return f, lines[:max_lines]


def key(text, number="", note="", fill=TILE, text_color=WHITE, lit=False, square=True):
    img = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(img)
    edge = EDGE if fill == TILE else tuple(min(255, int(c * 0.8 + 255 * 0.2)) for c in fill)
    d.rounded_rectangle((6 * K, 6 * K, 138 * K, 138 * K), radius=14 * K, fill=fill, outline=edge, width=int(3 * K))
    has_number = number != ""
    top = 34 if has_number else 12
    bottom = 112 if note else 132
    sizes = [27, 24, 21, 18, 16] if has_number or note else [36, 31, 27, 23, 20]
    f, lines = fit(d, text, 120 * K, sizes)
    line_h = f.size * 1.12
    y = (top + bottom) / 2 * K - (len(lines) * line_h) / 2 + (2 * K if has_number else 0)
    for line in lines:
        tw = d.textlength(line, font=f)
        d.text(((S - tw) / 2, y), line, font=f, fill=text_color)
        y += line_h
    small = font(16, "semi")
    if has_number:
        d.text((16 * K, 17 * K), number, font=small, fill=text_color + (190,) if False else text_color)
        if square:
            sq = (113 * K, 14 * K, 130 * K, 31 * K)
            d.rounded_rectangle(sq, radius=3 * K, fill=LIT if lit else (14, 19, 25), outline=LIT if lit else EDGE, width=int(1.5 * K))
    if note:
        tw = d.textlength(note, font=small)
        d.text(((S - tw) / 2, 118 * K), note, font=small, fill=text_color)
    return img.resize((144, 144), Image.LANCZOS)


KEYS = {
    # programmering (MA3-stil)
    "prog-clear": key("CLEAR", "1"),
    "prog-store": key("STORE", "2"),
    "prog-update": key("UPDATE", "3"),
    "prog-align": key("ALIGN", "4"),
    "prog-highlt": key("HIGHLT", "5"),
    "prog-blind": key("BLIND", "6"),
    "feat-dimmer": key("Dimmer", fill=ACTIVE, text_color=DARK),
    "feat-position": key("Position", text_color=GREY),
    "feat-gobo": key("Gobo", text_color=GREY),
    "feat-color": key("Color", text_color=GREY),
    "feat-beam": key("Beam", text_color=GREY),
    "feat-fx": key("FX", text_color=GREY),
    # avvikling
    "pb-go": key("GO", fill=LIT, text_color=DARK),
    "pb-pause": key("PAUSE"),
    "pb-goback": key("GO-"),
    "pb-blackout": key("BLACK OUT", fill=RED),
    "cue-1": key("Intro", "1.1", "Cue", lit=True),
    "cue-2": key("Verse", "1.2", "Cue"),
    "cue-3": key("Chorus", "1.3", "Cue"),
    "cue-4": key("Bridge", "1.4", "Cue"),
    "cue-5": key("Finale", "1.5", "Cue"),
    "pb-flash": key("FLASH", note="Hold"),
    # grupper
    "grp-spots": key("Spots", "1", "Group", lit=True),
    "grp-beams": key("Beams", "2", "Group"),
    "grp-wash": key("Wash", "3", "Group"),
    "grp-par": key("PAR", "4", "Group"),
    "grp-bowls": key("Bowls", "5", "Group"),
    "grp-ledbar": key("LED Bars", "6", "Group"),
    "grp-all": key("ALL", "7", "Group"),
    # presets
    "pre-warm": key("Warm", "4.1", "Color"),
    "pre-cool": key("Cool", "4.2", "Color"),
    "pre-red": key("Red", "4.3", "Color"),
    "pre-blue": key("Blue", "4.4", "Color"),
    "pre-center": key("Center", "2.1", "Pos"),
    "pre-stage-l": key("Stage L", "2.2", "Pos"),
    "pre-stage-r": key("Stage R", "2.3", "Pos"),
    "pre-audience": key("Audience", "2.4", "Pos"),
    # lyd
    "snd-mute": key("MUTE", fill=RED),
    "snd-mic1": key("Mic 1", "1", "Ch", lit=True),
    "snd-mic2": key("Mic 2", "2", "Ch"),
    "snd-track": key("Track", "3", "Ch"),
    "snd-talk": key("TALK BACK"),
    "snd-tone": key("1 kHz", note="Test"),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, img in KEYS.items():
        img.save(os.path.join(OUT, f"{name}.png"))
    # kontaktark
    cols, cell, pad = 8, 144, 16
    names = list(KEYS)
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cell + pad) + pad, rows * (cell + pad) + pad), (43, 43, 43))
    for i, name in enumerate(names):
        sheet.paste(KEYS[name], (pad + (i % cols) * (cell + pad), pad + (i // cols) * (cell + pad)))
    sheet.save(os.path.join(ROOT, "notes", "mock", "screenshot-keys.png"))
    print(len(KEYS), "taster skrevet til", OUT)


if __name__ == "__main__":
    main()
