# -*- coding: utf-8 -*-
"""render_rbxmx.py  --  dibuja CUALQUIER .rbxmx de interfaz como PNG.

Uso:   python render_rbxmx.py archivo.rbxmx [salida.png] [--ancho 1280] [--alto N]

Universal: acepta cualquier .rbxmx con un ScreenGui dentro, venga del
conversor (spec_a_rbxmx.py) o de cualquier otra herramienta. Lo que no sepa
dibujar lo omite y lo reporta al final, pero NUNCA se rompe: siempre sale
un PNG.

Soporta:
  * Frame / TextLabel / TextButton / TextBox / ImageLabel / ImageButton /
    ScrollingFrame
  * UICorner, UIStroke, UIGradient (color + rotacion), UIPadding
  * UIListLayout basico (vertical / horizontal, LayoutOrder, alineaciones)
  * UDim2 escala + offset, AnchorPoint, Rotation, ZIndex, Visible=false
  * ClipsDescendants (y recorte implicito de ScrollingFrame)
  * RichText: <font color>, <font size>, <b>, <i>; texto multilinea con \n
  * TextWrapped, TextScaled, TextTruncate, TextYAlignment completo
  * fuentes Gotham/SourceSans/Arial/etc. aproximadas; mono para Code
  * emojis en color y simbolos via fuentes de repuesto
  * valores por defecto de Roblox cuando el archivo omite propiedades
  * imagenes externas (rbxassetid): caja gris con X (no se descargan)
"""

import argparse
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------ fuentes
CANDIDATAS = {
    "reg": [
        "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
        "/usr/share/fonts/msttcore/arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ],
    "bold": [
        "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf",
        "/usr/share/fonts/msttcore/arialbd.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ],
    "mono": [
        "/usr/share/fonts/liberation-mono/LiberationMono-Regular.ttf",
        "/opt/libreoffice26.2/share/fonts/truetype/DejaVuSansMono.ttf",
        "C:/Windows/Fonts/consola.ttf",
    ],
    "mono_bold": [
        "/usr/share/fonts/liberation-mono/LiberationMono-Bold.ttf",
        "/opt/libreoffice26.2/share/fonts/truetype/DejaVuSansMono-Bold.ttf",
        "C:/Windows/Fonts/consolab.ttf",
    ],
    "sym": [
        "/opt/libreoffice26.2/share/fonts/truetype/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/seguisym.ttf",
    ],
    "sym_bold": [
        "/opt/libreoffice26.2/share/fonts/truetype/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/seguisym.ttf",
    ],
    "emoji": [
        "/usr/share/fonts/google-noto-emoji/NotoColorEmoji.ttf",
        "C:/Windows/Fonts/seguiemj.ttf",
        "/System/Library/Fonts/Apple Color Emoji.ttc",
    ],
}


def resuelve(kind):
    for ruta in CANDIDATAS[kind]:
        if os.path.exists(ruta):
            return ruta
    return None


FONT_REG = resuelve("reg")
FONT_BOLD = resuelve("bold") or FONT_REG
FONT_MONO = resuelve("mono") or FONT_REG
FONT_MONO_BOLD = resuelve("mono_bold") or FONT_MONO
FONT_SYM = resuelve("sym") or FONT_REG
FONT_SYM_BOLD = resuelve("sym_bold") or FONT_BOLD
FONT_EMOJI = resuelve("emoji")

EMOJI_PX = 109
_emoji_base = None
_emoji_cmap = None
_fonts = {}
_cmaps = {}


def cmap(path):
    if path not in _cmaps:
        try:
            from fontTools.ttLib import TTFont
            _cmaps[path] = set(TTFont(path).getBestCmap())
        except Exception:
            _cmaps[path] = set()
    return _cmaps[path]


def emoji_ok():
    global _emoji_base, _emoji_cmap
    if FONT_EMOJI is None:
        return False
    if _emoji_base is None:
        for px in (EMOJI_PX, 128, 136):
            try:
                _emoji_base = ImageFont.truetype(FONT_EMOJI, px)
                break
            except Exception:
                continue
        if _emoji_base is None:
            return False
        _emoji_cmap = cmap(FONT_EMOJI)
    return True


def fuente(kind, px):
    path = {"reg": FONT_REG, "bold": FONT_BOLD, "black": FONT_BOLD,
            "mono": FONT_MONO, "mono_bold": FONT_MONO_BOLD,
            "sym": FONT_SYM, "sym_bold": FONT_SYM_BOLD}[kind]
    key = (path, px)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, px)
    return _fonts[key]


def es_emoji(ch):
    o = ord(ch)
    return o >= 0x1F000 or 0x2600 <= o <= 0x2BFF or o in (0x203C, 0x2049)


def elige_fuente(ch, kind):
    base = {"reg": FONT_REG, "bold": FONT_BOLD, "black": FONT_BOLD,
            "mono": FONT_MONO, "mono_bold": FONT_MONO_BOLD}[kind]
    sym = FONT_SYM if kind in ("reg", "mono") else FONT_SYM_BOLD
    o = ord(ch)
    if es_emoji(ch) and emoji_ok() and o in _emoji_cmap:
        return None, True
    if o in cmap(base):
        return kind, False
    if o in cmap(sym):
        return "sym" if kind in ("reg", "mono") else "sym_bold", False
    if emoji_ok() and o in _emoji_cmap:
        return None, True
    return kind, False


_emoji_cache = {}


def emoji_img(ch, px):
    key = (ch, px)
    if key in _emoji_cache:
        return _emoji_cache[key]
    if not emoji_ok():
        _emoji_cache[key] = None
        return None
    lado = EMOJI_PX + 40
    tmp = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    try:
        d.text((20, 20), ch, font=_emoji_base, embedded_color=True)
    except Exception:
        _emoji_cache[key] = None
        return None
    bbox = tmp.getbbox()
    if not bbox:
        _emoji_cache[key] = None
        return None
    tmp = tmp.crop(bbox)
    esc = px / float(tmp.height)
    tmp = tmp.resize((max(1, int(round(tmp.width * esc))), px),
                     Image.LANCZOS)
    _emoji_cache[key] = tmp
    return tmp


# ------------------------------------------------------------------- parse
class Nodo:
    __slots__ = ("cls", "props", "hijos")

    def __init__(self, cls, props, hijos):
        self.cls = cls
        self.props = props
        self.hijos = hijos


def parse_props(el):
    props = {}
    for p in el:
        tag, name = p.tag, p.get("name")
        if name is None:
            continue
        try:
            if tag in ("string", "ProtectedString"):
                props[name] = p.text or ""
            elif tag in ("int", "int64", "token", "byte"):
                props[name] = int(p.text)
            elif tag in ("float", "double"):
                props[name] = float(p.text)
            elif tag == "bool":
                props[name] = (p.text or "").strip() == "true"
            elif tag == "Color3":
                props[name] = tuple(float(p.findtext(t, "0"))
                                    for t in ("R", "G", "B"))
            elif tag == "ColorSequence":
                nums = [float(t) for t in (p.text or "").split()]
                props[name] = [(nums[i], (nums[i + 1], nums[i + 2],
                                          nums[i + 3]))
                               for i in range(0, len(nums) - 3, 4)]
            elif tag == "NumberSequence":
                nums = [float(t) for t in (p.text or "").split()]
                paso = 3 if len(nums) % 3 == 0 else 2
                props[name] = [(nums[i], nums[i + 1])
                               for i in range(0, len(nums) - 1, paso)]
            elif tag == "UDim2":
                props[name] = tuple(float(p.findtext(t, "0"))
                                    for t in ("XS", "XO", "YS", "YO"))
            elif tag == "UDim":
                props[name] = (float(p.findtext("S", "0")),
                               float(p.findtext("O", "0")))
            elif tag == "Vector2":
                props[name] = (float(p.findtext("X", "0")),
                               float(p.findtext("Y", "0")))
            elif tag == "Content":
                props[name] = p.findtext("url")
        except Exception:
            continue
    return props


def parse_item(el):
    props, hijos = {}, []
    for ch in el:
        if ch.tag == "Properties":
            props = parse_props(ch)
        elif ch.tag == "Item":
            hijos.append(parse_item(ch))
    return Nodo(el.get("class", ""), props, hijos)


# ------------------------------------------------------------- utilidades
SS = 2


def S(v):
    return int(round(v * SS))


def rgb(col):
    return tuple(int(round(c * 255)) for c in col)


def hijo_de(nodo, cls):
    for h in nodo.hijos:
        if h.cls == cls:
            return h
    return None


def radio(nodo, w, h):
    c = hijo_de(nodo, "UICorner")
    if c is None:
        return 0
    s, o = c.props.get("CornerRadius", (0, 0))
    return s * min(w, h) + S(o)


def padding_de(nodo, w, h):
    pad = hijo_de(nodo, "UIPadding")
    if pad is None:
        return 0.0, 0.0, 0.0, 0.0
    pp = pad.props

    def lado(clave, dim):
        s, o = pp.get(clave, (0, 0))
        return s * dim + S(o)

    return (lado("PaddingLeft", w), lado("PaddingRight", w),
            lado("PaddingTop", h), lado("PaddingBottom", h))


def tam(nodo, pw, ph):
    ws, wo, hs, ho = nodo.props.get("Size", (0, 100, 0, 100))
    return ws * pw + S(wo), hs * ph + S(ho)


DIBUJABLES = {"Frame", "TextLabel", "TextButton", "TextBox",
              "ImageLabel", "ImageButton", "ScrollingFrame"}
CON_TEXTO = {"TextLabel", "TextButton", "TextBox"}
MODIFICADORES = {"UICorner", "UIStroke", "UIGradient", "UIPadding",
                 "UIListLayout", "UIGridLayout", "UITableLayout",
                 "UIPageLayout", "UISizeConstraint", "UITextSizeConstraint",
                 "UIAspectRatioConstraint", "UIScale", "LocalScript",
                 "Script", "ModuleScript", "Folder", "Configuration",
                 "StringValue", "NumberValue", "BoolValue", "IntValue",
                 "ObjectValue", "Color3Value", "BrickColorValue"}

# valores por defecto de Roblox cuando el archivo omite la propiedad
SIZE_DEF = (0, 100, 0, 100)
BG_DEF = (0.639, 0.635, 0.647)
FG_DEF = (0.106, 0.106, 0.106)
BORDE_DEF = (0.106, 0.106, 0.106)

_contador = [0]
_omitidas = []
_imagenes = [0]


# ------------------------------------------------------------ texto (v2)
def tipo_fuente(p):
    bold = black = mono = False
    tok = p.get("Font")
    if isinstance(tok, int):
        if tok == 20:
            black = True
        elif tok in (2, 4, 18, 19):
            bold = True
        elif tok == 10:
            mono = True
    ff = str(p.get("FontFace", "") or "").lower()
    if "black" in ff or "heavy" in ff:
        black = True
    elif "bold" in ff or "semibold" in ff or "medium" in ff:
        bold = True
    if "mono" in ff or "code" in ff:
        mono = True
    if black:
        return "black"
    if mono:
        return "mono_bold" if bold else "mono"
    return "bold" if bold else "reg"


def hex2rgb(hx):
    return (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16))


TAG_RE = re.compile(r"<(/?)(font|b|i|u|s|mark|stroke|br|small|big)"
                    r"((?:\s+[^<>]*?))??/?>", re.I | re.S)
ATTR_COLOR = re.compile(r'color\s*=\s*"#?([0-9A-Fa-f]{6})"')
ATTR_SIZE = re.compile(r'size\s*=\s*"(\d+)"')


def trocea_rich(texto, color_def, px_logico):
    """RichText extendido: devuelve lista de dicts {txt,color,bold,mult}.
    Las etiquetas desconocidas se ignoran conservando el texto."""
    runs = []
    estado = {"color": color_def, "bold": False, "mult": 1.0}
    pila = []
    pos = 0
    for m in TAG_RE.finditer(texto):
        if m.start() > pos:
            runs.append({"txt": texto[pos:m.start()], **estado})
        cierre, tag, attrs = m.group(1), m.group(2).lower(), m.group(3) or ""
        if tag == "br":
            runs.append({"txt": "\n", **estado})
        elif cierre:
            if pila:
                estado = pila.pop()
        else:
            pila.append(dict(estado))
            if tag == "font":
                cm = ATTR_COLOR.search(attrs)
                if cm:
                    estado["color"] = hex2rgb(cm.group(1))
                sm = ATTR_SIZE.search(attrs)
                if sm and px_logico:
                    estado["mult"] = max(0.3, min(4.0,
                                         int(sm.group(1)) / px_logico))
            elif tag in ("b", "big"):
                estado["bold"] = True
            elif tag in ("i", "small", "u", "s", "mark", "stroke"):
                pass  # se conserva el texto; el estilo fino no se pinta
        pos = m.end()
    if pos < len(texto):
        runs.append({"txt": texto[pos:], **estado})
    return runs or [{"txt": "", "color": color_def, "bold": False,
                     "mult": 1.0}]


def divide_lineas(runs):
    lineas = [[]]
    for r in runs:
        partes = r["txt"].split("\n")
        for i, parte in enumerate(partes):
            if i > 0:
                lineas.append([])
            if parte:
                lineas[-1].append({"txt": parte, "color": r["color"],
                                   "bold": r["bold"], "mult": r["mult"]})
    return lineas


def atomiza(runs, kind, px):
    atomos = []
    for r in runs:
        rk = kind
        if r["bold"] and kind == "reg":
            rk = "bold"
        elif r["bold"] and kind == "mono":
            rk = "mono_bold"
        apx = max(6, int(round(px * r["mult"])))
        for ch in r["txt"]:
            if ch == "\ufe0f":
                if atomos and atomos[-1][0] == "emoji":
                    a = atomos[-1]
                    atomos[-1] = ("emoji", a[1] + ch, a[2], a[3], a[4])
                continue
            fk, es_em = elige_fuente(ch, rk)
            if es_em:
                atomos.append(("emoji", ch, r["color"], None, apx))
            elif (atomos and atomos[-1][0] == "txt"
                    and atomos[-1][2] == r["color"] and atomos[-1][3] == fk
                    and atomos[-1][4] == apx):
                a = atomos[-1]
                atomos[-1] = ("txt", a[1] + ch, a[2], fk, apx)
            else:
                atomos.append(("txt", ch, r["color"], fk, apx))
    return atomos


def ancho_atomos(atomos):
    total = 0.0
    for tipo, txt, _c, fk, apx in atomos:
        if tipo == "txt":
            total += fuente(fk, apx).getlength(txt)
        else:
            em = emoji_img(txt, apx)
            total += em.width if em else apx * 0.5
    return total


def mide_llano(texto, kind, px):
    return ancho_atomos(atomiza([{"txt": texto, "color": (0, 0, 0),
                                  "bold": kind in ("bold", "black"),
                                  "mult": 1.0}], kind, px))


def envuelve(texto, kind, px, maxw):
    palabras = texto.split(" ")
    lineas, cur = [], ""
    for pal in palabras:
        t = pal if not cur else cur + " " + pal
        if not cur or mide_llano(t, kind, px) <= maxw:
            cur = t
        else:
            lineas.append(cur)
            cur = pal
    if cur:
        lineas.append(cur)
    return lineas or [""]


def elipsiza(texto, kind, px, maxw):
    if mide_llano(texto, kind, px) <= maxw:
        return texto
    while texto and mide_llano(texto + "...", kind, px) > maxw:
        texto = texto[:-1]
    return texto + "..." if texto else ""


def pinta_linea(img, x, top, caja_w, atomos, align, alpha):
    if not atomos:
        return
    px_linea = max(a[4] for a in atomos)
    total = ancho_atomos(atomos)
    if align == 0:
        cx = x
    elif align == 1:
        cx = x + caja_w - total
    else:
        cx = x + (caja_w - total) / 2.0
    d = ImageDraw.Draw(img)
    base = fuente("reg", px_linea)
    asc, desc = base.getmetrics()
    for tipo, txt, color, fk, apx in atomos:
        if tipo == "txt":
            f = fuente(fk, apx)
            sw = max(1, apx // 26) if fk == "black" else 0
            d.text((cx, top), txt, font=f, fill=color + (alpha,),
                   stroke_width=sw, stroke_fill=color + (alpha,))
            cx += f.getlength(txt)
        else:
            img_e = emoji_img(txt, apx)
            if img_e is not None:
                cy = top + (asc + desc) / 2.0
                img.paste(img_e, (int(round(cx)),
                                  int(round(cy - img_e.height / 2.0))),
                          img_e)
                cx += img_e.width
            else:
                cx += apx * 0.5


def dibuja_texto(img, nodo, x, y, w, h):
    p = nodo.props
    texto = p.get("Text", "")
    if not texto:
        return
    pl, pr, pt, pb = padding_de(nodo, w, h)
    x, y = x + pl, y + pt
    w, h = max(4.0, w - pl - pr), max(4.0, h - pt - pb)

    px_logico = p.get("TextSize", 14)
    px = max(6, S(px_logico))
    kind = tipo_fuente(p)
    color = rgb(p.get("TextColor3", FG_DEF))
    alpha = int(round((1 - p.get("TextTransparency", 0)) * 255))
    if alpha <= 0:
        return
    align = p.get("TextXAlignment", 2)      # 0 izq 1 der 2 centro
    valign = p.get("TextYAlignment", 1)     # 0 top 1 centro 2 bottom
    trunca = p.get("TextTruncate", 0) == 1

    if p.get("RichText"):
        runs = trocea_rich(texto, color, px_logico)
    else:
        runs = [{"txt": texto, "color": color, "bold": False, "mult": 1.0}]

    lineas = divide_lineas(runs)

    # envoltura y truncado trabajan sobre el texto llano de cada linea;
    # sin ellos, cada linea conserva sus colores y tamanos (RichText)
    entradas = []
    for lr in lineas:
        llano = "".join(r["txt"] for r in lr)
        if p.get("TextWrapped"):
            for sub in envuelve(llano, kind, px, w):
                entradas.append((None, sub))
        elif trunca:
            entradas.append((None, elipsiza(llano, kind, px, w)))
        else:
            entradas.append((lr, llano))

    planas = [e[1] for e in entradas]

    if p.get("TextScaled"):
        lo, hi, mejor = 6, max(6, int(h)), 6
        while lo <= hi:
            mid = (lo + hi) // 2
            f = fuente(kind, mid)
            a2, d2 = f.getmetrics()
            cabe_h = len(planas) * (a2 + d2) <= h
            cabe_w = all(mide_llano(ln, kind, mid) <= w for ln in planas)
            if cabe_h and cabe_w:
                mejor = mid
                lo = mid + 1
            else:
                hi = mid - 1
        px = mejor

    f = fuente(kind, px)
    asc, desc = f.getmetrics()
    alto_linea = asc + desc
    bloque = len(planas) * alto_linea
    if valign == 0:
        top = y
    elif valign == 2:
        top = y + max(0.0, h - bloque)
    else:
        top = y + max(0.0, (h - bloque) / 2.0)

    for lr, llano in entradas:
        runs_linea = lr or [{"txt": llano, "color": color, "bold": False,
                             "mult": 1.0}]
        atomos = atomiza(runs_linea, kind, px)
        pinta_linea(img, x, top, w, atomos, align, alpha)
        top += alto_linea


# --------------------------------------------------------------- gradiente
def interp(keys, t):
    if not keys:
        return (255, 255, 255)
    keys = sorted(keys)
    if t <= keys[0][0]:
        return rgb(keys[0][1])
    if t >= keys[-1][0]:
        return rgb(keys[-1][1])
    for (t0, c0), (t1, c1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            f = (t - t0) / max(t1 - t0, 1e-9)
            return tuple(int(round(a + (b - a) * f))
                         for a, b in zip(rgb(c0), rgb(c1)))
    return rgb(keys[-1][1])


def capa_gradiente(w, h, grad, alpha):
    keys = grad.props.get("Color")
    if not keys:
        return None
    rot = grad.props.get("Rotation", 0)
    th = math.radians(rot)
    L = max(2, int(abs(w * math.cos(th)) + abs(h * math.sin(th))) + 4)
    strip = Image.new("RGBA", (L, L))
    d = ImageDraw.Draw(strip)
    for i in range(L):
        d.line([(i, 0), (i, L)], fill=interp(keys, i / (L - 1.0)) + (alpha,))
    girada = strip.rotate(-rot, resample=Image.BICUBIC)
    x0 = max(0, (L - int(w)) // 2)
    y0 = max(0, (L - int(h)) // 2)
    return girada.crop((x0, y0, x0 + max(1, int(w)), y0 + max(1, int(h))))


# ----------------------------------------------------------------- dibujo
def pega_rotada(img, capa, x, y, w, h, rot):
    cx, cy = x + w / 2.0, y + h / 2.0
    lado = int(math.ceil(math.hypot(w, h))) + 8
    x0, y0 = int(cx - lado / 2.0), int(cy - lado / 2.0)
    region = capa.crop((x0, y0, x0 + lado, y0 + lado))
    girada = region.rotate(-rot, resample=Image.BICUBIC)
    img.alpha_composite(girada, (x0, y0))


def cuerpo(img, nodo, x, y, w, h):
    p = nodo.props
    d = ImageDraw.Draw(img)
    r = radio(nodo, w, h)
    trans = p.get("BackgroundTransparency", 0)
    if trans < 1:
        alpha = int(round((1 - trans) * 255))
        grad = hijo_de(nodo, "UIGradient")
        grad_img = capa_gradiente(w, h, grad, alpha) \
            if grad is not None else None
        if grad_img is not None:
            if r > 0:
                capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
                capa.paste(grad_img, (int(x), int(y)))
                mascara = Image.new("L", img.size, 0)
                ImageDraw.Draw(mascara).rounded_rectangle(
                    [x, y, x + w, y + h], radius=r, fill=255)
                img.alpha_composite(Image.composite(
                    capa, Image.new("RGBA", img.size, (0, 0, 0, 0)),
                    mascara))
            else:
                img.paste(grad_img, (int(x), int(y)), grad_img)
        else:
            col = rgb(p.get("BackgroundColor3", BG_DEF)) + (alpha,)
            if r > 0:
                d.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=col)
            else:
                d.rectangle([x, y, x + w, y + h], fill=col)

    bsp = p.get("BorderSizePixel", 0)
    if bsp and bsp > 0:
        bc = rgb(p.get("BorderColor3", BORDE_DEF))
        for i in range(min(S(bsp), int(min(w, h) / 2))):
            d.rectangle([x + i, y + i, x + w - 1 - i, y + h - 1 - i],
                        outline=bc)

    st = hijo_de(nodo, "UIStroke")
    if st is not None:
        t = S(st.props.get("Thickness", 1))
        if t > 0:
            col = rgb(st.props.get("Color", (0, 0, 0)))
            mitad = t / 2.0
            d.rounded_rectangle([x - mitad, y - mitad,
                                 x + w + mitad, y + h + mitad],
                                radius=r + mitad, outline=col,
                                width=max(1, int(t)))

    if nodo.cls in ("ImageLabel", "ImageButton") and p.get("Image"):
        _imagenes[0] += 1
        gris = (255, 255, 255, 70)
        d.rectangle([x, y, x + w, y + h], outline=(255, 255, 255, 140),
                    width=max(1, S(1)))
        d.line([x, y, x + w, y + h], fill=gris, width=max(1, S(1)))
        d.line([x + w, y, x, y + h], fill=gris, width=max(1, S(1)))

    if nodo.cls in CON_TEXTO:
        dibuja_texto(img, nodo, x, y, w, h)


def posiciones_lista(nodo, layout, kids, w, h):
    lp = layout.props
    vertical = lp.get("FillDirection", 0) == 1
    gs, go = lp.get("Padding", (0, 0))
    gap = gs * (h if vertical else w) + S(go)
    pl, pr, pt, pb = padding_de(nodo, w, h)
    ha = lp.get("HorizontalAlignment", 0)
    va = lp.get("VerticalAlignment", 0)
    orden = sorted(kids, key=lambda c: c.props.get("LayoutOrder", 0))
    pos = {}
    cursor = pt if vertical else pl
    for c in orden:
        cw, chh = tam(c, w, h)
        if vertical:
            if ha == 1:
                cx = pl + max(0.0, (w - pl - pr - cw) / 2.0)
            elif ha == 2:
                cx = w - pr - cw
            else:
                cx = pl
            pos[id(c)] = (cx, cursor)
            cursor += chh + gap
        else:
            if va == 1:
                cy = pt + max(0.0, (h - pt - pb - chh) / 2.0)
            elif va == 2:
                cy = h - pb - chh
            else:
                cy = pt
            pos[id(c)] = (cursor, cy)
            cursor += cw + gap
    return pos


def hijos(img, nodo, x, y, w, h):
    kids, saltados = [], []
    for c in nodo.hijos:
        if c.cls in DIBUJABLES:
            kids.append(c)
        elif c.cls not in MODIFICADORES:
            saltados.append(c)
    for c in saltados:
        _omitidas.append((c.props.get("Name", "?"), c.cls,
                          "clase sin soporte visual"))
    kids.sort(key=lambda c: c.props.get("ZIndex", 1))

    layout = hijo_de(nodo, "UIListLayout")
    overrides = posiciones_lista(nodo, layout, kids, w, h) \
        if layout is not None else {}

    def pos_abs(c):
        ov = overrides.get(id(c))
        return (x + ov[0], y + ov[1]) if ov else None

    clips = nodo.props.get("ClipsDescendants") is True \
        or nodo.cls == "ScrollingFrame"
    if clips:
        capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
        for c in kids:
            dibuja(capa, c, x, y, w, h, pos_abs(c))
        mascara = Image.new("L", img.size, 0)
        ImageDraw.Draw(mascara).rounded_rectangle(
            [x, y, x + w, y + h], radius=radio(nodo, w, h), fill=255)
        img.alpha_composite(Image.composite(
            capa, Image.new("RGBA", img.size, (0, 0, 0, 0)), mascara))
    else:
        for c in kids:
            dibuja(img, c, x, y, w, h, pos_abs(c))


def dibuja(img, nodo, ox, oy, pw, ph, forzar_pos=None):
    p = nodo.props
    if p.get("Visible") is False:
        return
    xs, xo, ys, yo = p.get("Position", (0, 0, 0, 0))
    w, h = tam(nodo, pw, ph)
    x = ox + xs * pw + S(xo)
    y = oy + ys * ph + S(yo)
    if forzar_pos is not None:
        x, y = forzar_pos
    ax, ay = p.get("AnchorPoint", (0, 0))
    x -= ax * w
    y -= ay * h
    _contador[0] += 1
    rot = p.get("Rotation", 0)
    try:
        if rot:
            capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
            cuerpo(capa, nodo, x, y, w, h