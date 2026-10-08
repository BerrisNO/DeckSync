# Lager plugin-ikon, tastebilder, Marketplace-thumbnail og galleribilder for DeckSync med Pillow.
# Kjøres av `npm run images` (python -I tools/gen-images.py). Monokrome SVG-ikoner (kategori/handlinger)
# ligger håndskrevet i imgs/ og lages ikke her.
import math
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMGS = os.path.join(ROOT, "app.decksync.sdPlugin", "imgs")
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
    draw_sync_badge(d, S / 2, S / 2, 36 * k, S / 1024)  # produktikonet (synk-badgen), uten tekst
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


def tile_base(S):
    """Mørk flis med kant, som tastene: #10151C bakgrunn, #232E3D flis, #3A4657 kant."""
    k = S / 144
    img = Image.new("RGB", (S, S), (16, 21, 28))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((6 * k, 6 * k, 138 * k, 138 * k), radius=14 * k, fill=(35, 46, 61), outline=(58, 70, 87), width=int(3 * k))
    return img, d, k


def folder_icon(size):
    """Mappe-tast: mappeglyf i hvit strek øverst, plass til appens tittel nederst."""
    S = 576
    img, d, k = tile_base(S)
    w = int(5 * k)
    x0, y0, x1, y1 = 34 * k, 40 * k, 110 * k, 94 * k
    tab_w, tab_h = 28 * k, 10 * k
    # tab + kropp som én kontur
    d.rounded_rectangle((x0, y0 + tab_h, x1, y1), radius=7 * k, outline=WHITE, width=w)
    d.rounded_rectangle((x0, y0, x0 + tab_w, y0 + tab_h + w * 1.5), radius=5 * k, outline=WHITE, width=w)
    d.rectangle((x0 + w, y0 + tab_h, x0 + tab_w - w, y0 + tab_h + w * 2.2), fill=(35, 46, 61))  # åpner tappen mot kroppen
    return img.resize((size, size), Image.LANCZOS)


def back_icon(size):
    """Tilbake-tast for mapper: pil til venstre i samme strek."""
    S = 576
    img, d, k = tile_base(S)
    w = int(6 * k)
    cx, cy = 72 * k, 66 * k
    d.line((cx - 26 * k, cy, cx + 26 * k, cy), fill=WHITE, width=w)
    d.line((cx - 26 * k, cy, cx - 6 * k, cy - 20 * k), fill=WHITE, width=w)
    d.line((cx - 26 * k, cy, cx - 6 * k, cy + 20 * k), fill=WHITE, width=w)
    d.ellipse((cx - 26 * k - w / 2, cy - w / 2, cx - 26 * k + w / 2, cy + w / 2), fill=WHITE)
    return img.resize((size, size), Image.LANCZOS)


def glyph_tile(size, draw_glyph, color=WHITE):
    """Flis med en liten, tynn strekglyf øverst (ca. 40 px i 144-skala) og plass til tittel nederst."""
    S = 576
    img, d, k = tile_base(S)
    draw_glyph(d, 72 * k, 58 * k, k, color, int(4 * k))
    return img.resize((size, size), Image.LANCZOS)


def g_folder(d, cx, cy, k, c, w):
    x0, y0, x1, y1 = cx - 22 * k, cy - 14 * k, cx + 22 * k, cy + 15 * k
    d.rounded_rectangle((x0, y0 + 7 * k, x1, y1), radius=5 * k, outline=c, width=w)
    d.rounded_rectangle((x0, y0, x0 + 18 * k, y0 + 7 * k + w), radius=4 * k, outline=c, width=w)
    d.rectangle((x0 + w, y0 + 7 * k, x0 + 18 * k - w, y0 + 7 * k + w * 1.6), fill=(35, 46, 61))


def g_back(d, cx, cy, k, c, w):
    d.line((cx - 18 * k, cy, cx + 18 * k, cy), fill=c, width=w)
    d.line((cx - 18 * k, cy, cx - 5 * k, cy - 13 * k), fill=c, width=w)
    d.line((cx - 18 * k, cy, cx - 5 * k, cy + 13 * k), fill=c, width=w)


def g_groups(d, cx, cy, k, c, w):
    s, g = 15 * k, 5 * k
    for dx in (-1, 1):
        for dy in (-1, 1):
            x = cx + dx * (s / 2 + g / 2) - s / 2
            y = cy + dy * (s / 2 + g / 2) - s / 2
            d.rounded_rectangle((x, y, x + s, y + s), radius=3 * k, outline=c, width=w)


def g_presets(d, cx, cy, k, c, w):
    for i, pos in enumerate((-0.6, 0.1, -0.3)):
        x = cx + (i - 1) * 14 * k
        d.line((x, cy - 18 * k, x, cy + 18 * k), fill=c, width=w)
        y = cy + pos * 14 * k
        d.ellipse((x - 5 * k, y - 5 * k, x + 5 * k, y + 5 * k), fill=(35, 46, 61), outline=c, width=w)


def g_light(d, cx, cy, k, c, w):
    r = 13 * k
    d.arc((cx - r, cy - 17 * k, cx + r, cy + 9 * k), start=150, end=390, fill=c, width=w)
    d.line((cx - 7 * k, cy + 4 * k, cx - 7 * k, cy + 13 * k), fill=c, width=w)
    d.line((cx + 7 * k, cy + 4 * k, cx + 7 * k, cy + 13 * k), fill=c, width=w)
    d.line((cx - 7 * k, cy + 13 * k, cx + 7 * k, cy + 13 * k), fill=c, width=w)
    d.line((cx - 5 * k, cy + 19 * k, cx + 5 * k, cy + 19 * k), fill=c, width=w)


def g_sound(d, cx, cy, k, c, w):
    d.polygon([(cx - 18 * k, cy - 7 * k), (cx - 9 * k, cy - 7 * k), (cx + 1 * k, cy - 15 * k), (cx + 1 * k, cy + 15 * k), (cx - 9 * k, cy + 7 * k), (cx - 18 * k, cy + 7 * k)], outline=c, width=w)
    d.arc((cx - 4 * k, cy - 11 * k, cx + 14 * k, cy + 11 * k), start=-45, end=45, fill=c, width=w)
    d.arc((cx - 2 * k, cy - 18 * k, cx + 22 * k, cy + 18 * k), start=-45, end=45, fill=c, width=w)


def g_video(d, cx, cy, k, c, w):
    d.rounded_rectangle((cx - 20 * k, cy - 12 * k, cx + 8 * k, cy + 12 * k), radius=4 * k, outline=c, width=w)
    d.polygon([(cx + 8 * k, cy - 4 * k), (cx + 20 * k, cy - 11 * k), (cx + 20 * k, cy + 11 * k), (cx + 8 * k, cy + 4 * k)], outline=c, width=w)


def g_play(d, cx, cy, k, c, w):
    d.polygon([(cx - 12 * k, cy - 16 * k), (cx + 16 * k, cy), (cx - 12 * k, cy + 16 * k)], outline=c, width=w)


def g_home(d, cx, cy, k, c, w):
    d.line((cx - 20 * k, cy - 1 * k, cx, cy - 17 * k), fill=c, width=w)
    d.line((cx, cy - 17 * k, cx + 20 * k, cy - 1 * k), fill=c, width=w)
    d.rounded_rectangle((cx - 14 * k, cy - 4 * k, cx + 14 * k, cy + 16 * k), radius=2 * k, outline=c, width=w)
    d.rectangle((cx - 4 * k, cy + 5 * k, cx + 4 * k, cy + 16 * k), outline=c, width=w)


def g_star(d, cx, cy, k, c, w):
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        r = 17 * k if i % 2 == 0 else 7.5 * k
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, outline=c, width=w)


def g_gear(d, cx, cy, k, c, w):
    r = 12 * k
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=c, width=w)
    d.ellipse((cx - 4 * k, cy - 4 * k, cx + 4 * k, cy + 4 * k), outline=c, width=w)
    for i in range(8):
        a = math.radians(i * 45)
        d.line((cx + (r + 1 * k) * math.cos(a), cy + (r + 1 * k) * math.sin(a), cx + (r + 7 * k) * math.cos(a), cy + (r + 7 * k) * math.sin(a)), fill=c, width=w + int(k))


def _yoke(d, cx, cy, k, c, w, arm_top, base_y):
    """Base og U-formet yoke, felles for moving heads."""
    d.rounded_rectangle((cx - 19 * k, base_y, cx + 19 * k, base_y + 6 * k), radius=2 * k, outline=c, width=w)
    for s in (-1, 1):
        d.line((cx + s * 19 * k, base_y, cx + s * 19 * k, arm_top), fill=c, width=w)
        d.line((cx + s * 19 * k, arm_top, cx + s * 14 * k, arm_top), fill=c, width=w)


def g_moving_head(d, cx, cy, k, c, w):
    """Moving head med langt beam-hode (à la MegaPointe): base, yoke-armer og et vippet hode med tykk linse i fronten."""
    base_y = cy + 20 * k
    d.rounded_rectangle((cx - 17 * k, base_y, cx + 17 * k, base_y + 6 * k), radius=2 * k, outline=c, width=w)
    for sgn in (-1, 1):
        d.line((cx + sgn * 17 * k, base_y, cx + sgn * 17 * k, cy + 2 * k), fill=c, width=w)
    ang = math.radians(-22)
    hw, hh = 10 * k, 22 * k
    rot = lambda dx, dy: (cx + dx * math.cos(ang) - dy * math.sin(ang), cy - 2 * k + dx * math.sin(ang) + dy * math.cos(ang))
    pts = [rot(-hw, -hh), rot(hw, -hh), rot(hw, hh), rot(-hw, hh)]
    d.polygon(pts, fill=(35, 46, 61), outline=c, width=w)
    d.line((pts[0], pts[1]), fill=c, width=w + int(2 * k))  # linsen
    # pivot-prikker der armene møter hodet
    for sgn in (-1, 1):
        px, py = cx + sgn * 17 * k, cy + 2 * k
        d.ellipse((px - 2.5 * k, py - 2.5 * k, px + 2.5 * k, py + 2.5 * k), fill=c)


def g_beam_head(d, cx, cy, k, c, w):
    """Moving head med rundt LED-ansikt (à la LEDBeam 350), sett forfra: 7 LED-er i sekskant."""
    _yoke(d, cx, cy, k, c, w, arm_top=cy - 2 * k, base_y=cy + 20 * k)
    r = 16 * k
    d.ellipse((cx - r, cy - 4 * k - r, cx + r, cy - 4 * k + r), fill=(35, 46, 61), outline=c, width=w)
    led = 2.8 * k
    pts = [(cx, cy - 4 * k)] + [(cx + 9 * k * math.cos(math.radians(a)), cy - 4 * k + 9 * k * math.sin(math.radians(a))) for a in range(0, 360, 60)]
    for x, y in pts:
        d.ellipse((x - led, y - led, x + led, y + led), fill=c)


def g_par(d, cx, cy, k, c, w):
    """PAR-kanne sett fra siden, vippet opp mot høyre, med bøyle under."""
    ang = math.radians(-25)
    body = ((-20, -11), (18, -16), (18, 16), (-20, 11))
    pts = [(cx + dx * k * math.cos(ang) - dy * k * math.sin(ang), cy - 4 * k + dx * k * math.sin(ang) + dy * k * math.cos(ang)) for dx, dy in body]
    d.polygon(pts, fill=(35, 46, 61), outline=c, width=w)
    d.line((pts[1], pts[2]), fill=c, width=w + int(2 * k))  # frontlinje (bred ende)
    d.arc((cx - 14 * k, cy + 4 * k, cx + 14 * k, cy + 26 * k), start=25, end=155, fill=c, width=w)  # bøyle


def g_vintage_bowl(d, cx, cy, k, c, w):
    """Vintage bowl: åpen skål med glødepære, sett fra siden."""
    d.pieslice((cx - 20 * k, cy - 20 * k, cx + 20 * k, cy + 20 * k), start=0, end=180, fill=(35, 46, 61), outline=c, width=w)
    d.line((cx - 20 * k, cy, cx + 20 * k, cy), fill=c, width=w)
    d.ellipse((cx - 6 * k, cy - 12 * k, cx + 6 * k, cy), fill=(35, 46, 61), outline=c, width=w)
    d.line((cx - 3 * k, cy - 6 * k, cx + 3 * k, cy - 6 * k), fill=c, width=int(w * 0.7))
    d.line((cx, cy - 20 * k, cx, cy - 14 * k), fill=c, width=w)


def g_led_bar(d, cx, cy, k, c, w):
    """LED-bar: liggende stav med en rad LED-er og to små føtter."""
    d.rounded_rectangle((cx - 24 * k, cy - 7 * k, cx + 24 * k, cy + 7 * k), radius=4 * k, outline=c, width=w)
    led = 2.3 * k
    for i in range(6):
        x = cx - 19 * k + i * 7.6 * k
        d.ellipse((x - led, cy - led, x + led, cy + led), fill=c)
    for s in (-1, 1):
        d.line((cx + s * 14 * k, cy + 7 * k, cx + s * 18 * k, cy + 16 * k), fill=c, width=w)


def g_folder_filled(d, cx, cy, k, c, w):
    """Fylt mappe (farge skiller mappene), litt større, med plass til tittel under."""
    x0, y0, x1, y1 = cx - 22 * k, cy - 14 * k, cx + 22 * k, cy + 16 * k
    tab_h = 7 * k
    # flat farge, ingen skygge eller kant: tapp og kropp i samme tone
    d.rounded_rectangle((x0, y0, x0 + 22 * k, y0 + tab_h + 4 * k), radius=4 * k, fill=c)
    d.rounded_rectangle((x0, y0 + tab_h, x1, y1), radius=5 * k, fill=c)


FOLDER_COLORS = [
    ("White", (236, 240, 244)),
    ("Cyan", (38, 184, 168)),
    ("Blue", (66, 133, 244)),
    ("Purple", (156, 102, 230)),
    ("Pink", (236, 82, 150)),
    ("Red", (230, 72, 72)),
    ("Orange", (242, 150, 48)),
    ("Yellow", (240, 200, 60)),
    ("Green", (72, 200, 110)),
    ("Grey", (130, 142, 158)),
]


def colored_tile(size, color, draw_glyph=None):
    """Flis i flat farge (som MA3s appearance-farger), kant i litt lysere tone, hvit (eller mørk) glyf oppå."""
    S = 576
    k = S / 144
    img = Image.new("RGB", (S, S), (16, 21, 28))
    d = ImageDraw.Draw(img)
    edge = tuple(min(255, int(ch * 0.75 + 255 * 0.25)) for ch in color)
    d.rounded_rectangle((6 * k, 6 * k, 138 * k, 138 * k), radius=14 * k, fill=color, outline=edge, width=int(3 * k))
    if draw_glyph:
        lum = (0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]) / 255
        glyph_color = (16, 21, 28) if lum > 0.6 else WHITE
        draw_glyph(d, 72 * k, 58 * k, k, glyph_color, int(4 * k))
    return img.resize((size, size), Image.LANCZOS)


def folder_sheet(out):
    cols = 5
    cell, pad = 144, 24
    rows = (len(FOLDER_COLORS) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cell + pad) + pad, rows * (cell + pad + 28) + pad), (43, 43, 43))
    d = ImageDraw.Draw(sheet)
    f = font("segoeui.ttf", 16)
    for i, (name, color) in enumerate(FOLDER_COLORS):
        x = pad + (i % cols) * (cell + pad)
        y = pad + (i // cols) * (cell + pad + 28)
        sheet.paste(colored_tile(cell, color, g_folder_filled), (x, y))
        tw = d.textlength(name, font=f)
        d.text((x + (cell - tw) / 2, y + cell + 4), name, font=f, fill=(220, 220, 220))
    sheet.save(out)


ICON_SET = [("Folder", g_folder), ("Back", g_back), ("Groups", g_groups), ("Presets", g_presets), ("Light", g_light),
            ("Sound", g_sound), ("Video", g_video), ("Play", g_play), ("Home", g_home), ("Star", g_star), ("Settings", g_gear),
            ("Moving Head", g_moving_head), ("Beam Head", g_beam_head), ("PAR", g_par), ("Vintage Bowl", g_vintage_bowl), ("LED Bar", g_led_bar)]


def icon_sheet(out, cyan=False):
    """Kontaktark: alle ikonene i 144 px ved siden av hverandre, med navn under."""
    cols = 6
    cell, pad = 144, 24
    rows = (len(ICON_SET) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cell + pad) + pad, rows * (cell + pad + 28) + pad), (43, 43, 43))
    d = ImageDraw.Draw(sheet)
    f = font("segoeui.ttf", 16)
    for i, (name, glyph) in enumerate(ICON_SET):
        x = pad + (i % cols) * (cell + pad)
        y = pad + (i // cols) * (cell + pad + 28)
        sheet.paste(glyph_tile(cell, glyph, CYAN if cyan else WHITE), (x, y))
        tw = d.textlength(name, font=f)
        d.text((x + (cell - tw) / 2, y + cell + 4), name, font=f, fill=(220, 220, 220))
    sheet.save(out)


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
    ICONS = os.path.join(ROOT, "icons")
    os.makedirs(ICONS, exist_ok=True)
    tile_base(576)[0].resize((144, 144), Image.LANCZOS).save(os.path.join(ICONS, "DeckSync Tile.png"))  # bare flisen, til egne taster og mapper
    for name, glyph in ICON_SET:
        glyph_tile(144, glyph).save(os.path.join(ICONS, f"DeckSync {name}.png"))
    FOLDERS = os.path.join(ICONS, "folders")
    os.makedirs(FOLDERS, exist_ok=True)
    for name, color in FOLDER_COLORS:
        colored_tile(144, color, g_folder_filled).save(os.path.join(FOLDERS, f"Folder {name}.png"))
        colored_tile(144, color).save(os.path.join(FOLDERS, f"Tile {name}.png"))  # bare farget flis, til andre taster
    folder_sheet(os.path.join(ROOT, "notes", "mock", "folder-sheet.png"))
    icon_sheet(os.path.join(ROOT, "notes", "mock", "icon-sheet.png"))
    icon_sheet(os.path.join(ROOT, "notes", "mock", "icon-sheet-cyan.png"), cyan=True)

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
