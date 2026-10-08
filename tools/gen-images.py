# Lager plugin-ikon, tastebilder, Marketplace-thumbnail og galleribilder for DeckSync med Pillow.
# Kjøres av `npm run images` (python -I tools/gen-images.py). Monokrome SVG-ikoner (kategori/handlinger)
# ligger håndskrevet i imgs/ og lages ikke her.
import math
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMGS = os.path.join(ROOT, "no.berland.decksync.sdPlugin", "imgs")
MARKET = os.path.join(ROOT, "marketplace")
FONTS = r"C:\Windows\Fonts"

BG_TOP, BG_BOTTOM = (24, 50, 77), (11, 22, 35)
DECK, DECK_EDGE = (42, 72, 104), (111, 168, 220)
KEY, KEY_LIT = (207, 227, 247), (45, 212, 191)
CYAN, WHITE = (38, 184, 168), (255, 255, 255)
CYAN_DEEP = (31, 160, 147)


def gradient(size, top, bottom):
    w, h = size
    g = Image.linear_gradient("L").resize((w, h))
    return Image.composite(Image.new("RGB", size, bottom), Image.new("RGB", size, top), g)


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return m


def draw_deck(d, box, cols, rows, lit, scale):
    """Et deck: avrundet rektangel med tastenett. `lit` = sett av (col,row) som lyser."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=40 * scale, fill=DECK, outline=DECK_EDGE, width=int(6 * scale))
    pad = 44 * scale
    gap = 22 * scale
    kw = ((x1 - x0) - 2 * pad - (cols - 1) * gap) / cols
    kh = ((y1 - y0) - 2 * pad - (rows - 1) * gap) / rows
    for r in range(rows):
        for c in range(cols):
            kx = x0 + pad + c * (kw + gap)
            ky = y0 + pad + r * (kh + gap)
            d.rounded_rectangle((kx, ky, kx + kw, ky + kh), radius=14 * scale, fill=KEY_LIT if (c, r) in lit else KEY)


def _arrowhead(d, cx, cy, ir, angle_deg, size, fill):
    """Pilhode med spissen på sirkelen (radius ir) ved vinkel angle_deg, pekende med klokka."""
    a = math.radians(angle_deg)
    tip = (cx + ir * math.cos(a), cy + ir * math.sin(a))
    # tangentretning (med klokka i PIL-koordinater) og normal
    tx, ty = -math.sin(a), math.cos(a)
    nx, ny = math.cos(a), math.sin(a)
    base = (tip[0] - tx * size, tip[1] - ty * size)
    p1 = (base[0] + nx * size * 0.75, base[1] + ny * size * 0.75)
    p2 = (base[0] - nx * size * 0.75, base[1] - ny * size * 0.75)
    d.polygon([tip, p1, p2], fill=fill)


def draw_sync_badge(d, cx, cy, r, scale):
    """Rund cyan-plate med to buede piler (synk-symbol). Myk: tynnere piler, dempet hvit, svak skygge."""
    d.ellipse((cx - r * 1.02, cy - r * 0.96 + r * 0.05, cx + r * 1.02, cy + r * 1.06), fill=(14, 30, 46))  # svak skygge
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=CYAN)
    d.ellipse((cx - r * 0.86, cy - r * 0.86, cx + r * 0.86, cy + r * 0.86), fill=CYAN_DEEP)
    w = max(2, int(r * 0.13))
    ir = r * 0.52
    soft = (236, 250, 247)
    # to buer med klokka, hver avsluttet med et pilhode
    d.arc((cx - ir, cy - ir, cx + ir, cy + ir), start=200, end=325, fill=soft, width=w)
    d.arc((cx - ir, cy - ir, cx + ir, cy + ir), start=20, end=145, fill=soft, width=w)
    _arrowhead(d, cx, cy, ir, 334, r * 0.24, soft)
    _arrowhead(d, cx, cy, ir, 154, r * 0.24, soft)


def dial_key_image(size):
    """Bildet i dial-sirkelen i appen: appens egen knott-glyf (ring med viser), hvit på mørk flate, uten tekst."""
    S = 576
    k = S / 144
    img = Image.new("RGB", (S, S), (27, 34, 48))
    d = ImageDraw.Draw(img)
    cx, cy, r = S / 2, S / 2, 30 * k
    w = int(5 * k)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=WHITE, width=w)
    # viseren peker mot klokka ett, som på appens dial-ikon
    a = math.radians(-55)
    d.line((cx, cy, cx + r * 0.78 * math.cos(a), cy + r * 0.78 * math.sin(a)), fill=WHITE, width=w)
    d.ellipse((cx - w * 0.9, cy - w * 0.9, cx + w * 0.9, cy + w * 0.9), fill=WHITE)
    return img.resize((size, size), Image.LANCZOS)


def badge_only(size):
    """Bare synk-platen på gjennomsiktig bakgrunn, til dial-layouten."""
    S = 448
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_sync_badge(d, S / 2, S / 2, S * 0.42, S / 1024)
    return img.resize((size, size), Image.LANCZOS)


def plugin_icon(size):
    """Plugin-ikonet: to deck side om side med synk-plate i midten. Tegnes i 1024 og skaleres ned."""
    S = 1024
    scale = 1.0
    img = gradient((S, S), BG_TOP, BG_BOTTOM)
    d = ImageDraw.Draw(img)
    draw_deck(d, (80, 318, 470, 706), 3, 2, {(2, 0)}, scale)
    draw_deck(d, (554, 318, 944, 706), 3, 2, {(0, 0)}, scale)
    draw_sync_badge(d, 512, 512, 150, scale)
    img.putalpha(rounded_mask((S, S), 200))
    return img.resize((size, size), Image.LANCZOS)


def key_image(size):
    """Statisk tastebilde i samme stil som MA3Deck-tastene: mørk bakgrunn, avrundet flis med kant, liten badge øverst."""
    S = 576  # = 144 * 4
    k = S / 144
    img = Image.new("RGB", (S, S), (16, 21, 28))  # #10151C
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((6 * k, 6 * k, 138 * k, 138 * k), radius=14 * k, fill=(35, 46, 61), outline=(58, 70, 87), width=int(3 * k))  # #232E3D / #3A4657
    draw_sync_badge(d, S / 2, 52 * k, 20 * k, S / 1024)
    return img.resize((size, size), Image.LANCZOS)


def font(name, px):
    return ImageFont.truetype(os.path.join(FONTS, name), px)


def wrap(d, text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def slide(title, lines, out, icon_px=400, show_decks=None):
    """1920×960 Marketplace-bilde: venstre kolonne = ikon + deck-illustrasjon, høyre kolonne = tekst."""
    W, H = 1920, 960
    img = gradient((W, H), BG_TOP, BG_BOTTOM)
    d = ImageDraw.Draw(img)
    col_w = 620
    icon = plugin_icon(icon_px)
    img.paste(icon, (120 + (col_w - icon_px) // 2, 130), icon)
    if show_decks:
        a, b = show_decks  # sidetall som vises på de to deckene
        bw, bh, gap = 250, 130, 110
        dx0 = 120 + (col_w - (2 * bw + gap)) // 2
        dy = 640
        f = font("segoeuib.ttf", 50)
        for dx, page in ((dx0, a), (dx0 + bw + gap, b)):
            d.rounded_rectangle((dx, dy, dx + bw, dy + bh), radius=20, fill=DECK, outline=DECK_EDGE, width=4)
            label = f"Page {page}"
            tw = d.textlength(label, font=f)
            d.text((dx + (bw - tw) / 2, dy + 34), label, font=f, fill=KEY_LIT)
        draw_sync_badge(d, dx0 + bw + gap / 2, dy + bh / 2, 42, 0.3)
    x = 120 + col_w + 100
    d.text((x, 150), "DeckSync", font=font("segoeuib.ttf", 150), fill=WHITE)
    y = 350
    sub = font("seguisb.ttf", 58)
    for ln in wrap(d, title, sub, W - x - 100):
        d.text((x, y), ln, font=sub, fill=CYAN)
        y += 72
    y += 24
    body = font("segoeui.ttf", 44)
    for para in lines:
        for ln in wrap(d, para, body, W - x - 100):
            d.text((x, y), ln, font=body, fill=(220, 230, 240))
            y += 58
        y += 20
    img.save(out)


def main():
    os.makedirs(IMGS, exist_ok=True)
    os.makedirs(MARKET, exist_ok=True)
    plugin_icon(256).save(os.path.join(IMGS, "plugin.png"))
    plugin_icon(512).save(os.path.join(IMGS, "plugin@2x.png"))
    key_image(72).save(os.path.join(IMGS, "key.png"))
    key_image(144).save(os.path.join(IMGS, "key@2x.png"))
    dial_key_image(72).save(os.path.join(IMGS, "dial-key.png"))
    dial_key_image(144).save(os.path.join(IMGS, "dial-key@2x.png"))
    badge_only(56).save(os.path.join(IMGS, "badge.png"))
    badge_only(112).save(os.path.join(IMGS, "badge@2x.png"))
    plugin_icon(1024).save(os.path.join(MARKET, "app-icon-1024.png"))

    slide(
        "Keep every Stream Deck on the same page",
        ["Turn a page on one deck and the others follow. Works across Stream Deck, Stream Deck +, XL, Mini and Neo.",
         "Or send each deck to its own page with a single key or a dial."],
        os.path.join(MARKET, "thumbnail-1920x960.png"), show_decks=(3, 3),
    )
    slide(
        "Page markers on every page",
        ["DeckSync installs a profile per device with a page marker on every page.",
         "When a page appears on one deck, the other decks jump to the same page. No loops, no lag."],
        os.path.join(MARKET, "gallery-1-markers.png"), show_decks=(2, 2),
    )
    slide(
        "Page dial on Stream Deck +",
        ["Turn the dial to pick a page. Press it to choose the target: ALL decks or a single one.",
         "Give each deck its own name, so the dial reads \"Page 4 → Lights\"."],
        os.path.join(MARKET, "gallery-2-dial.png"), show_decks=(4, 1),
    )
    slide(
        "Go to page: one key, different pages",
        ["Set a page per deck on a key, dial or touch tap. Empty means that deck stays put.",
         "Example: key 1 sends the 15-key deck to page 2 while Stream Deck + stays on page 1."],
        os.path.join(MARKET, "gallery-3-goto.png"), show_decks=(2, 1),
    )
    print("bilder skrevet til", IMGS, "og", MARKET)


if __name__ == "__main__":
    main()
