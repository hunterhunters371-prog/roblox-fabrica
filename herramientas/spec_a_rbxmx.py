# -*- coding: utf-8 -*-
"""spec_a_rbxmx.py  --  convierte un JSON simple en un .rbxmx valido.

Uso:   python spec_a_rbxmx.py pase.json

La IA solo escribe el JSON. Este programa se encarga de lo que la IA siempre
rompe:
  * redondea todo offset a entero          (UDim.Offset es int32)
  * escapa el texto exactamente una vez    (nada de doble escapado)
  * los colores salen de una paleta cerrada
  * comprueba que cada texto cabe en su caja
  * calcula las posiciones, asi que no puede haber solapes

Si el JSON tiene fallos, los lista en un formato que puedes copiar y pegar
de vuelta a la IA para que corrija.
"""

import json
import os
import sys

# ------------------------------------------------------------------ paleta
NAVY, NAVY_DARK = (29, 43, 79), (16, 26, 51)
CREAM, WHITE = (255, 246, 229), (255, 255, 255)
MUTED = (107, 120, 153)
CYAN, CYAN_DARK = (34, 195, 230), (18, 138, 166)
GOLD, GOLD_DARK = (255, 194, 46), (217, 154, 0)
GREEN, GREEN_DARK = (62, 196, 109), (42, 158, 82)
TRACK, TRACK_DARK = (217, 219, 230), (182, 185, 199)

# nombre -> (fondo, color del texto encima)
PALETA = {
    "azul":    ((77, 163, 255), WHITE),
    "cian":    ((34, 195, 230), WHITE),
    "dorado":  ((255, 194, 46), NAVY),
    "morado":  ((169, 123, 255), WHITE),
    "naranja": ((255, 146, 54), WHITE),
    "rojo":    ((255, 107, 107), WHITE),
    "rosa":    ((255, 126, 199), WHITE),
    "verde":   ((62, 196, 109), WHITE),
}
COLORES = ", ".join(sorted(PALETA))

GOTHAM, GOTHAM_BOLD, GOTHAM_BLACK = 17, 19, 20
X_LEFT, X_RIGHT, X_CENTER = 0, 1, 2
Y_CENTER = 1
ANCHO_CHAR = 0.55          # ancho medio de un caracter respecto al TextSize


# -------------------------------------------------------------- validacion
ERRORES = []


def err(msg):
    ERRORES.append(msg)


def pide(d, clave, tipo, donde):
    if clave not in d:
        err('%s falta la clave "%s".' % (donde, clave))
        return None
    v = d[clave]
    if not isinstance(v, tipo):
        nombre = {str: "texto", int: "numero entero",
                  bool: "true o false", list: "lista"}.get(tipo, str(tipo))
        err('%s.%s debe ser %s, no %r.' % (donde, clave, nombre, v))
        return None
    return v


def sin_markup(texto, donde):
    for mal in ("<", ">", "&"):
        if mal in texto:
            err('%s contiene "%s". No escribas etiquetas ni HTML en los '
                "textos; el conversor pone los colores por ti." % (donde, mal))
            return


def cabe(texto, ancho_px, text_size, donde):
    limite = int(ancho_px / (text_size * ANCHO_CHAR))
    if len(texto) > limite:
        err("%s tiene %d caracteres y solo caben %d. Acortalo."
            % (donde, len(texto), limite))


# ------------------------------------------------------------------- XML
REF = [0]


def nref():
    r = "RBX%d" % REF[0]
    REF[0] += 1
    return r


def esc(s):
    """Escapa UNA sola vez."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def f6(v):
    return ("%.6f" % float(v)).rstrip("0").rstrip(".") or "0"


def ent(v):
    """UDim.Offset es int32: un decimal aqui se convierte en 0."""
    return int(round(float(v)))


def prop_xml(name, val):
    if isinstance(val, tuple) and len(val) == 2 and isinstance(val[0], str):
        kind, v = val
        if kind == "token":
            return '<token name="%s">%d</token>' % (name, v)
        if kind == "color":
            r, g, b = v
            return ('<Color3 name="%s"><R>%s</R><G>%s</G><B>%s</B></Color3>'
                    % (name, f6(r / 255.0), f6(g / 255.0), f6(b / 255.0)))
        if kind == "udim2":
            xs, xo, ys, yo = v
            return ('<UDim2 name="%s"><XS>%s</XS><XO>%d</XO>'
                    '<YS>%s</YS><YO>%d</YO></UDim2>'
                    % (name, f6(xs), ent(xo), f6(ys), ent(yo)))
        if kind == "udim":
            s, o = v
            return ('<UDim name="%s"><S>%s</S><O>%d</O></UDim>'
                    % (name, f6(s), ent(o)))
        if kind == "vector2":
            x, y = v
            return ('<Vector2 name="%s"><X>%s</X><Y>%s</Y></Vector2>'
                    % (name, f6(x), f6(y)))
        if kind == "protected":
            return ('<ProtectedString name="%s"><![CDATA[%s]]'
                    + '></ProtectedString>') % (name, v)
        if kind == "float":
            return '<float name="%s">%s</float>' % (name, f6(v))
        raise ValueError(kind)
    if isinstance(val, bool):
        return '<bool name="%s">%s</bool>' % (name, "true" if val else "false")
    if isinstance(val, int):
        return '<int name="%s">%d</int>' % (name, val)
    if isinstance(val, float):
        return '<float name="%s">%s</float>' % (name, f6(val))
    return '<string name="%s">%s</string>' % (name, esc(val))


def render(node, depth=1):
    pad = "  " * depth
    out = ['%s<Item class="%s" referent="%s">' % (pad, node["class"], nref())]
    out.append("%s  <Properties>" % pad)
    for k in sorted(node.get("props", {})):
        out.append("%s    %s" % (pad, prop_xml(k, node["props"][k])))
    out.append("%s  </Properties>" % pad)
    for c in node.get("children", []):
        out.append(render(c, depth + 1))
    out.append("%s</Item>" % pad)
    return "\n".join(out)


def count(n):
    return 1 + sum(count(c) for c in n.get("children", []))


def corner(r):
    return {"class": "UICorner",
            "props": {"Name": "UICorner", "CornerRadius": ("udim", r)}}


def stroke(t=3, c=NAVY):
    return {"class": "UIStroke", "props": {
        "Name": "UIStroke", "Thickness": ("float", t),
        "Color": ("color", c), "ApplyStrokeMode": ("token", 1)}}


def frame(name, x, y, w, h, color, z, radius=None, thick=None,
          sc=NAVY, clips=False, children=None, anchor=None, visible=None,
          transparent=False):
    props = {
        "Name": name,
        "Position": ("udim2", (0, x, 0, y)),
        "Size": ("udim2", (0, w, 0, h)),
        "BackgroundColor3": ("color", color),
        "BackgroundTransparency": ("float", 1 if transparent else 0),
        "BorderSizePixel": 0,
        "ZIndex": z,
    }
    if clips:
        props["ClipsDescendants"] = True
    if anchor:
        props["AnchorPoint"] = ("vector2", anchor)
    if visible is not None:
        props["Visible"] = visible
    kids = list(children or [])
    if radius is not None:
        kids.insert(0, corner(radius))
    if thick is not None:
        kids.insert(0, stroke(thick, sc))
    return {"class": "Frame", "props": props, "children": kids}


def label(name, x, y, w, h, text, size, color, z, font=GOTHAM_BOLD,
          xa=X_CENTER, rich=False, wrapped=False):
    return {"class": "TextLabel", "props": {
        "Name": name,
        "Position": ("udim2", (0, x, 0, y)),
        "Size": ("udim2", (0, w, 0, h)),
        "BackgroundTransparency": ("float", 1),
        "BorderSizePixel": 0,
        "Text": text,
        "TextSize": ("float", size),
        "TextColor3": ("color", color),
        "Font": ("token", font),
        "TextXAlignment": ("token", xa),
        "TextYAlignment": ("token", Y_CENTER),
        "RichText": rich,
        "TextWrapped": wrapped,
        "ZIndex": z,
    }}


def button(name, x, y, w, h, text, size, bg, fg, z, radius=12, thick=3,
           visible=None):
    props = {
        "Name": name,
        "Position": ("udim2", (0, x, 0, y)),
        "Size": ("udim2", (0, w, 0, h)),
        "BackgroundColor3": ("color", bg),
        "BackgroundTransparency": ("float", 0),
        "BorderSizePixel": 0,
        "Text": text,
        "TextSize": ("float", size),
        "TextColor3": ("color", fg),
        "Font": ("token", GOTHAM_BOLD),
        "TextXAlignment": ("token", X_CENTER),
        "TextYAlignment": ("token", Y_CENTER),
        "AutoButtonColor": False,
        "ZIndex": z,
    }
    if visible is not None:
        props["Visible"] = visible
    return {"class": "TextButton", "props": props,
            "children": [stroke(thick, NAVY), corner((0, radius))]}


Z_BG, Z_SH, Z_FACE, Z_ISH, Z_IN, Z_TX, Z_TAG = 0, 10, 11, 12, 13, 14, 16
R_PANEL, R_BTN, R_PILL = (0, 18), (0, 12), (0.5, 0)
CONTENT_W = 1064
GAP = 16
CARD_H = 288
DOT = 38


def miles(n):
    return "{:,}".format(int(n))


# ------------------------------------------------------------------ carga
def main():
    if len(sys.argv) < 2:
        print("uso: python spec_a_rbxmx.py pase.json")
        return 2

    ruta = sys.argv[1]
    if not os.path.exists(ruta):
        print("no existe el archivo: %s" % ruta)
        return 2

    try:
        with open(ruta, encoding="utf-8") as fh:
            spec = json.load(fh)
    except json.JSONDecodeError as e:
        print("\nEL JSON NO ES VALIDO\n")
        print("  linea %d, columna %d: %s" % (e.lineno, e.colno, e.msg))
        print("\nPega este mensaje a la IA para que corrija el JSON.\n")
        return 1

    if not isinstance(spec, dict):
        print("el JSON debe ser un objeto { ... }")
        return 1

    # --- cabecera
    temporada = pide(spec, "temporada", str, "raiz") or ""
    titulo = pide(spec, "titulo", str, "raiz") or ""
    subtitulo = pide(spec, "subtitulo", str, "raiz") or ""
    tiempo = pide(spec, "tiempo", str, "raiz") or ""
    resaltado = spec.get("resaltado", "")
    t_todos = spec.get("textoAbrirTodos", "Abrir todos")
    t_prem = spec.get("textoPremium", "Mejorar")

    for nom, val in (("temporada", temporada), ("titulo", titulo),
                     ("subtitulo", subtitulo), ("tiempo", tiempo),
                     ("textoAbrirTodos", t_todos), ("textoPremium", t_prem)):
        if isinstance(val, str):
            sin_markup(val, "raiz.%s" % nom)

    cabe(temporada, 190, 12, "raiz.temporada")
    cabe(titulo, 630, 38, "raiz.titulo")
    cabe(subtitulo, 630, 14, "raiz.subtitulo")
    cabe(tiempo, 150, 24, "raiz.tiempo")

    if resaltado and resaltado not in titulo:
        err('raiz.resaltado = "%s" no aparece dentro de raiz.titulo = "%s".'
            % (resaltado, titulo))

    # --- numeros
    niveles = pide(spec, "niveles", int, "raiz")
    nivel = pide(spec, "nivel", int, "raiz")
    xp = pide(spec, "xp", int, "raiz")
    por_nivel = pide(spec, "xpPorNivel", int, "raiz")
    premio = spec.get("xpPorPremio", 100)
    premio_p = spec.get("xpPorPremioPremium", 150)

    if isinstance(niveles, int) and not (2 <= niveles <= 20):
        err("raiz.niveles = %d. Debe estar entre 2 y 20." % niveles)
        niveles = None
    if isinstance(nivel, int) and isinstance(niveles, int) \
            and not (1 <= nivel <= niveles):
        err("raiz.nivel = %d. Debe estar entre 1 y raiz.niveles (%d)."
            % (nivel, niveles))
    if isinstance(por_nivel, int) and por_nivel < 1:
        err("raiz.xpPorNivel = %d. Debe ser 1 o mas." % por_nivel)
    if isinstance(xp, int) and isinstance(por_nivel, int) \
            and not (0 <= xp < por_nivel):
        err("raiz.xp = %d. Debe estar entre 0 y xpPorNivel - 1 (%d)."
            % (xp, por_nivel - 1))

    # --- pistas
    def revisar_pista(clave):
        lista = pide(spec, clave, list, "raiz")
        if lista is None:
            return []
        if not (1 <= len(lista) <= 6):
            err("raiz.%s tiene %d premios. Debe tener entre 1 y 6."
                % (clave, len(lista)))
            return []
        return lista

    gratis = revisar_pista("gratis")
    prem = revisar_pista("premium")

    def ancho_carta(n):
        if n <= 0:
            return 200
        return (CONTENT_W - GAP * (n - 1)) // n

    def revisar_cartas(lista, clave):
        cw = ancho_carta(len(lista))
        interior = cw - 24
        for i, c in enumerate(lista):
            donde = "raiz.%s[%d]" % (clave, i)
            if not isinstance(c, dict):
                err("%s debe ser un objeto { ... }." % donde)
                continue
            for k in ("etiqueta", "color", "icono", "titulo", "desc"):
                v = pide(c, k, str, donde)
                if isinstance(v, str):
                    sin_markup(v, "%s.%s" % (donde, k))
            col = c.get("color")
            if isinstance(col, str) and col not in PALETA:
                err('%s.color = "%s" no existe.\n     Colores validos: %s'
                    % (donde, col, COLORES))
            if isinstance(c.get("etiqueta"), str):
                cabe(c["etiqueta"], interior - 20, 10, "%s.etiqueta" % donde)
            if isinstance(c.get("titulo"), str):
                cabe(c["titulo"], interior, 15, "%s.titulo" % donde)
            if isinstance(c.get("desc"), str):
                # se envuelve en 2 lineas
                cabe(c["desc"], interior * 2, 11, "%s.desc" % donde)
            bonus = c.get("bonus", "")
            if not isinstance(bonus, str):
                err("%s.bonus debe ser texto." % donde)
            elif bonus:
                sin_markup(bonus, "%s.bonus" % donde)
                cabe(bonus, interior - 26, 14, "%s.bonus" % donde)
            nuevo = c.get("nuevo", False)
            if not isinstance(nuevo, bool):
                err("%s.nuevo debe ser true o false." % donde)

    revisar_cartas(gratis, "gratis")
    revisar_cartas(prem, "premium")

    if ERRORES:
        print("\n" + "=" * 66)
        print("ERRORES EN EL JSON  (%d)" % len(ERRORES))
        print("=" * 66 + "\n")
        for i, m in enumerate(ERRORES, 1):
            print("  %d. %s" % (i, m))
        print("\nCopia esta lista y pegala a la IA para que corrija el JSON.")
        print("No se genero ningun .rbxmx.\n")
        return 1

    # ================================================================ build
    body = []

    def add_panel(name, x, y, w, h, face, inner):
        body.append(frame("PanelShadow", x, y + 6, w, h, NAVY, Z_SH,
                          radius=R_PANEL))
        body.append(frame(name, x, y, w, h, face, Z_FACE, radius=R_PANEL,
                          thick=3, children=inner))

    # ---- cabecera
    tw = max(120, int(len(temporada) * 7.2 + 24))
    if resaltado:
        titulo_xml = titulo.replace(
            resaltado, '<font color="#128aa6">%s</font>' % resaltado, 1)
        rico = True
    else:
        titulo_xml, rico = titulo, False

    hero = [
        frame("Shadow", 24, 24, tw, 26, GOLD_DARK, Z_ISH, radius=R_PILL),
        frame("Badge", 24, 20, tw, 26, GOLD, Z_IN, radius=R_PILL, thick=3,
              children=[label("T", 0, 0, tw, 26, temporada, 12, NAVY, Z_TX)]),
        label("Title", 24, 52, 640, 44, titulo_xml, 38, NAVY, Z_TX,
              font=GOTHAM_BLACK, xa=X_LEFT, rich=rico),
        label("Sub", 24, 98, 640, 18, subtitulo, 14, MUTED, Z_TX,
              font=GOTHAM, xa=X_LEFT),
        frame("Shadow", 880, 35, 160, 70, NAVY, Z_ISH, radius=(0, 14)),
        frame("Timer", 880, 30, 160, 70, WHITE, Z_IN, radius=(0, 14), thick=3,
              children=[label("L", 0, 10, 160, 14, "TERMINA EN", 10, MUTED,
                              Z_TX),
                        label("V", 0, 28, 160, 30, tiempo, 24, NAVY, Z_TX)]),
    ]
    add_panel("HeroPanel", 0, 0, CONTENT_W, 130, CREAM, hero)

    # ---- progreso
    xp_txt = ('<font color="#128aa6">%s</font> / %s XP'
              % (miles(xp), miles(por_nivel)))
    progress = [
        frame("Shadow", 22, 22, 110, 30, CYAN_DARK, Z_ISH, radius=R_PILL),
        frame("LevelPill", 77, 33, 110, 30, CYAN, Z_IN, radius=R_PILL,
              thick=3, anchor=(0.5, 0.5),
              children=[label("T", 0, 0, 110, 30, "NIVEL %d" % nivel, 14,
                              WHITE, Z_TX)]),
        label("XpLabel", 742, 22, 300, 22, xp_txt, 15, NAVY, Z_TX,
              xa=X_RIGHT, rich=True),
        frame("BarTrack", 22, 58, 1020, 22, TRACK, Z_IN, radius=R_PILL,
              thick=3, clips=True, children=[
                  {"class": "Frame", "props": {
                      "Name": "BarFill",
                      "Position": ("udim2", (0, 0, 0, 0)),
                      "Size": ("udim2", (xp / float(por_nivel), 0, 1, 0)),
                      "BackgroundColor3": ("color", CYAN),
                      "BackgroundTransparency": ("float", 0),
                      "BorderSizePixel": 0, "ZIndex": Z_TX,
                  }, "children": [corner(R_PILL)]}]),
        label("FootLabel", 22, 88, 600, 16,
              "Faltan %s XP para el nivel %d"
              % (miles(por_nivel - xp), nivel + 1),
              12, MUTED, Z_TX, xa=X_LEFT),
    ]
    add_panel("ProgressPanel", 0, 152, CONTENT_W, 120, WHITE, progress)

    # ---- camino de niveles (separacion ENTERA por construccion)
    span = (1020 - DOT) // (niveles - 1)
    path = [label("Title", 22, 18, 400, 16,
                  "TU CAMINO \u00b7 %d NIVELES" % niveles, 13, NAVY, Z_TX,
                  xa=X_LEFT)]
    dot_y = 50
    for i in range(niveles - 1):
        lx = 22 + i * span + DOT
        path.append(frame("Link%d" % (i + 1), lx, dot_y + 16,
                          max(1, span - DOT), 5,
                          CYAN if (i + 1) < nivel else TRACK, Z_IN))
    for i in range(niveles):
        dx, n = 22 + i * span, i + 1
        if n < nivel:
            face, txt, tc, sh = CYAN, "\u2713", WHITE, NAVY
        elif n == nivel:
            face, txt, tc, sh = GOLD, str(n), NAVY, GOLD_DARK
        else:
            face, txt, tc, sh = WHITE, str(n), MUTED, NAVY
        path.append(frame("DotShadow%d" % n, dx, dot_y + 3, DOT, DOT, sh,
                          Z_ISH, radius=R_PILL))
        path.append(frame("TierDot%d" % n, dx, dot_y, DOT, DOT, face, Z_IN,
                          radius=R_PILL, thick=3,
                          children=[label("T", 0, 0, DOT, DOT, txt, 13, tc,
                                          Z_TX)]))
    add_panel("PathPanel", 0, 294, CONTENT_W, 112, CREAM, path)

    # ---- tarjetas
    def build_card(idx, c, base_y, pista, cw):
        lvl = idx + 1
        x = idx * (cw + GAP)
        locked = pista == "P"
        face = CREAM if locked else WHITE
        cbg, cfg = PALETA[c["color"]]
        interior = cw - 24
        inner = [label("Lvl", 12, 12, 90, 14, "NIVEL %d" % lvl, 11, MUTED,
                       Z_TX, xa=X_LEFT)]

        chip = c["etiqueta"]
        chw = min(interior, max(50, int(len(chip) * 6.6 + 18)))
        inner.append(frame("Chip", cw - 12 - chw, 10, chw, 18, cbg, Z_IN,
                           radius=R_PILL, thick=2,
                           children=[label("T", 0, 0, chw, 18, chip, 10, cfg,
                                           Z_TX)]))

        if c.get("nuevo"):
            inner.append(frame("TagNew", cw - 36, 42, 48, 16,
                               (255, 126, 199), Z_TAG, radius=R_PILL,
                               thick=2, anchor=(0.5, 0.5),
                               children=[label("T", 0, 0, 48, 16, "NUEVO", 9,
                                               WHITE, Z_TAG + 1)]))

        inner.append(frame("IconRing", cw // 2, 72, 72, 72, cbg, Z_IN,
                           radius=R_PILL, thick=3, anchor=(0.5, 0.5),
                           children=[label("Emoji", 0, 0, 72, 72,
                                           c["icono"], 34, WHITE, Z_TX)]))

        inner.append(label("Title", 12, 118, interior, 20, c["titulo"], 15,
                           NAVY, Z_TX))
        inner.append(label("Desc", 12, 142, interior, 30, c["desc"], 11,
                           MUTED, Z_TX, font=GOTHAM, wrapped=True))

        bonus = c.get("bonus", "")
        if bonus:
            bw = min(interior, max(70, int(len(bonus) * 9 + 26)))
            inner.append(frame("Mult", cw // 2, 190, bw, 24,
                               WHITE if locked else CREAM, Z_IN,
                               radius=R_PILL, thick=2, anchor=(0.5, 0.5),
                               children=[label("T", 0, 0, bw, 24, bonus, 14,
                                               NAVY, Z_TX)]))

        if locked:
            inner.append(frame("BtnShadow", 12, 244, interior, 34, TRACK_DARK,
                               Z_ISH, radius=R_BTN))
            inner.append(button("CardBtn", 12, 240, interior, 34,
                                "\U0001F512 PREMIUM", 12, TRACK, MUTED, Z_IN))
        else:
            inner.append(frame("BtnShadow", 12, 244, interior, 34, GREEN_DARK,
                               Z_ISH, radius=R_BTN))
            inner.append(button("CardBtn", 12, 240, interior, 34, "ABRIR",
                                12, GREEN, WHITE, Z_IN))

        return [
            frame("CardShadow", x, base_y + 6, cw, CARD_H, NAVY, Z_SH,
                  radius=R_PANEL),
            frame("Card%s%d" % (pista, lvl), x, base_y, cw, CARD_H, face,
                  Z_FACE, radius=R_PANEL, thick=3, clips=True,
                  children=inner),
        ]

    def add_head(y, titulo_pista, bname, btext, bbg, bfg, bsh):
        bw = max(150, int(len(btext) * 9 + 40))
        body.append(label("TrackName", 0, y + 8, 500, 28, titulo_pista, 20,
                          CREAM, Z_TX, xa=X_LEFT))
        bx = CONTENT_W - bw
        body.append(frame("Shadow", bx, y + 5, bw, 42, bsh, Z_SH,
                          radius=(0, 14)))
        body.append(button(bname, bx, y, bw, 42, btext, 14, bbg, bfg, Z_FACE,
                           radius=14))

    y_gratis_head, y_gratis = 432, 490
    add_head(y_gratis_head, "\U0001F4E6 Pista Gratis", "OpenAllBtn", t_todos,
             GREEN, WHITE, GREEN_DARK)
    cw_g = ancho_carta(len(gratis))
    for i, c in enumerate(gratis):
        body.extend(build_card(i, c, y_gratis, "F", cw_g))

    y_prem_head = y_gratis + CARD_H + 30
    y_prem = y_prem_head + 58
    add_head(y_prem_head, "\u2B50 Pista Premium", "UpgradeBtn", t_prem,
             GOLD, NAVY, GOLD_DARK)
    cw_p = ancho_carta(len(prem))
    for i, c in enumerate(prem):
        body.extend(build_card(i, c, y_prem, "P", cw_p))

    y_rule = y_prem + CARD_H + 30
    body.append(frame("Rule", 0, y_rule, CONTENT_W, 3, NAVY, Z_FACE))
    body.append(label("FootText", 0, y_rule + 14, CONTENT_W, 20,
                      "Pulsa ABRIR para reclamar \u00b7 pasa el cursor por "
                      "las tarjetas", 12, MUTED, Z_TX, font=GOTHAM))

    content_h = y_rule + 40
    canvas_h = content_h + 40

    # ---- Luau: la configuracion sale del JSON, la logica es fija
    cfg = ("local CFG = {\n"
           "\tnivel = %d,\n\txp = %d,\n\tporNivel = %d,\n"
           "\tniveles = %d,\n\tpremio = %d,\n\tpremioPremium = %d,\n"
           "\tnGratis = %d,\n\tnPremium = %d,\n}\n"
           % (nivel, xp, por_nivel, niveles, premio, premio_p,
              len(gratis), len(prem)))

    lua = cfg + LOGICA
    assert "]" + "]" not in lua, "el Luau rompe el bloque CDATA"

    screen = {"class": "ScreenGui", "props": {
        "Name": "PaseDeBatalla",
        "ResetOnSpawn": False,
        "IgnoreGuiInset": True,
        "ZIndexBehavior": ("token", 1),
        "Enabled": True,
    }, "children": [
        {"class": "Frame", "props": {
            "Name": "Backdrop",
            "Position": ("udim2", (0, 0, 0, 0)),
            "Size": ("udim2", (1, 0, 1, 0)),
            "BackgroundColor3": ("color", NAVY_DARK),
            "BackgroundTransparency": ("float", 0),
            "BorderSizePixel": 0, "ZIndex": Z_BG,
        }},
        {"class": "ScrollingFrame", "props": {
            "Name": "Scroll",
            "Position": ("udim2", (0, 0, 0, 0)),
            "Size": ("udim2", (1, 0, 1, 0)),
            "BackgroundTransparency": ("float", 1),
            "BorderSizePixel": 0,
            "CanvasSize": ("udim2", (0, 0, 0, canvas_h)),
            "ScrollBarThickness": 8,
            "ScrollBarImageColor3": ("color", CYAN),
            "ScrollingDirection": ("token", 2),
            "ZIndex": 1,
        }, "children": [
            {"class": "Frame", "props": {
                "Name": "Content",
                "Position": ("udim2", (0.5, -(CONTENT_W // 2), 0, 28)),
                "Size": ("udim2", (0, CONTENT_W, 0, content_h)),
                "BackgroundTransparency": ("float", 1),
                "BorderSizePixel": 0, "ZIndex": 1,
            }, "children": body},
        ]},
        frame("CloseShadow", 0, 0, 46, 46, NAVY, 29, radius=R_PILL,
              anchor=(1, 0)),
        button("CloseBtn", 0, 0, 46, 46, "\u2715", 20, WHITE, NAVY, 30,
               radius=23),
        frame("ReopenShadow", 0, 0, 260, 48, GOLD_DARK, 29, radius=(0, 16),
              visible=False, anchor=(0.5, 0.5)),
        button("ReopenBtn", 0, 0, 260, 48, "ABRIR PASE DE BATALLA", 14,
               GOLD, NAVY, 30, radius=16, visible=False),
        {"class": "LocalScript", "props": {
            "Name": "PaseFuncional",
            "Source": ("protected", lua),
        }},
    ]}

    for kid in screen["children"]:
        n = kid.get("props", {}).get("Name")
        if n == "CloseShadow":
            kid["props"]["Position"] = ("udim2", (1, -22, 0, 27))
        elif n == "CloseBtn":
            kid["props"]["AnchorPoint"] = ("vector2", (1, 0))
            kid["props"]["Position"] = ("udim2", (1, -22, 0, 22))
        elif n == "ReopenShadow":
            kid["props"]["Position"] = ("udim2", (0.5, 0, 1, -75))
        elif n == "ReopenBtn":
            kid["props"]["AnchorPoint"] = ("vector2", (0.5, 0.5))
            kid["props"]["Position"] = ("udim2", (0.5, 0, 1, -80))

    total = count(screen)
    xml = ('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" '
           'version="4">\n' + render(screen) + "\n</roblox>\n")

    salida = os.path.splitext(os.path.abspath(ruta))[0] + ".rbxmx"
    with open(salida, "w", encoding="utf-8") as fh:
        fh.write(xml)

    print("")
    print("OK  el JSON es valido")
    print("    instancias : %d" % total)
    print("    tamano     : %d bytes" % len(xml.encode("utf-8")))
    print("    premios    : %d gratis + %d premium" % (len(gratis), len(prem)))
    print("    archivo    : %s" % salida)
    print("")
    print("Siguiente paso:")
    print("    python roblox_lint.py %s" % os.path.basename(salida))
    print("")
    return 0


# ============================================================ logica Luau
LOGICA = r"""
-- Pase de Batalla - logica fija. Lo unico que cambia es CFG, arriba.

local TweenService = game:GetService("TweenService")

local gui = script.Parent
local scroll = gui:WaitForChild("Scroll")
local contenido = scroll:WaitForChild("Content")
local progreso = contenido:WaitForChild("ProgressPanel")
local camino = contenido:WaitForChild("PathPanel")

local levelPill = progreso:WaitForChild("LevelPill")
local xpLabel = progreso:WaitForChild("XpLabel")
local footLabel = progreso:WaitForChild("FootLabel")
local barFill = progreso:WaitForChild("BarTrack"):WaitForChild("BarFill")

local openAllBtn = contenido:WaitForChild("OpenAllBtn")
local upgradeBtn = contenido:WaitForChild("UpgradeBtn")
local backdrop = gui:WaitForChild("Backdrop")
local closeBtn = gui:WaitForChild("CloseBtn")
local closeShadow = gui:WaitForChild("CloseShadow")
local reopenBtn = gui:WaitForChild("ReopenBtn")
local reopenShadow = gui:WaitForChild("ReopenShadow")

local COL = {
	navy = Color3.fromRGB(29, 43, 79),
	cream = Color3.fromRGB(255, 246, 229),
	white = Color3.fromRGB(255, 255, 255),
	muted = Color3.fromRGB(107, 120, 153),
	cyan = Color3.fromRGB(34, 195, 230),
	cyanDark = Color3.fromRGB(18, 138, 166),
	gold = Color3.fromRGB(255, 194, 46),
	goldDark = Color3.fromRGB(217, 154, 0),
	green = Color3.fromRGB(62, 196, 109),
	greenDark = Color3.fromRGB(42, 158, 82),
	track = Color3.fromRGB(217, 219, 230),
	trackDark = Color3.fromRGB(182, 185, 199),
}

local SUBE = TweenInfo.new(0.15, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
local BAJA = TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local PULSA = TweenInfo.new(0.08, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local CRECE = TweenInfo.new(0.12, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
local VUELVE = TweenInfo.new(0.18, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)

local estado = {
	nivel = CFG.nivel,
	xp = CFG.xp,
	porNivel = CFG.porNivel,
	premium = false,
	reclamados = {},
}

local function fmt(n)
	local s = tostring(math.floor(n))
	local r = s:reverse()
	local g = r:gsub("(%d%d%d)", "%1,")
	local out = g:reverse()
	if out:sub(1, 1) == "," then
		out = out:sub(2)
	end
	return out
end

-- UDim2 no admite multiplicacion por un numero: hay que escalar componente
-- a componente, y el Offset debe quedar entero.
local function escalar(u, k)
	return UDim2.new(
		u.X.Scale * k, math.round(u.X.Offset * k),
		u.Y.Scale * k, math.round(u.Y.Offset * k)
	)
end

local tamBase = {}

local function pop(obj, k)
	if tamBase[obj] == nil then
		tamBase[obj] = obj.Size
	end
	local base = tamBase[obj]
	obj.Size = base
	local crece = TweenService:Create(obj, CRECE, { Size = escalar(base, k) })
	crece.Completed:Connect(function()
		TweenService:Create(obj, VUELVE, { Size = base }):Play()
	end)
	crece:Play()
end

local function toast(msg)
	local marco = Instance.new("Frame")
	marco.Name = "Toast"
	marco.AnchorPoint = Vector2.new(0.5, 0)
	marco.Position = UDim2.new(0.5, 0, 0, -70)
	marco.Size = UDim2.new(0, 380, 0, 48)
	marco.BackgroundColor3 = COL.gold
	marco.BorderSizePixel = 0
	marco.ZIndex = 60
	marco.Parent = gui

	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(0, 14)
	esquina.Parent = marco

	local borde = Instance.new("UIStroke")
	borde.Thickness = 3
	borde.Color = COL.navy
	borde.Parent = marco

	local txt = Instance.new("TextLabel")
	txt.Size = UDim2.new(1, 0, 1, 0)
	txt.BackgroundTransparency = 1
	txt.Text = msg
	txt.TextSize = 16
	txt.Font = Enum.Font.GothamBold
	txt.TextColor3 = COL.navy
	txt.ZIndex = 61
	txt.Parent = marco

	TweenService:Create(marco, SUBE, { Position = UDim2.new(0.5, 0, 0, 26) }):Play()

	task.delay(1.9, function()
		local salir = TweenService:Create(
			marco,
			TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
			{ Position = UDim2.new(0.5, 0, 0, -70) }
		)
		salir.Completed:Connect(function()
			marco:Destroy()
		end)
		salir:Play()
	end)
end

-- El +XP se cuelga del ScreenGui, no de la tarjeta: la tarjeta recorta a sus
-- hijos y el numero quedaria cortado.
local function flotarXp(card, cantidad)
	local t = Instance.new("TextLabel")
	t.Name = "FloatXp"
	t.AnchorPoint = Vector2.new(0.5, 0.5)
	t.Size = UDim2.new(0, 140, 0, 32)
	t.BackgroundTransparency = 1
	t.Text = "+" .. cantidad .. " XP"
	t.TextSize = 22
	t.Font = Enum.Font.GothamBlack
	t.TextColor3 = COL.cyanDark
	t.ZIndex = 50

	local ap = card.AbsolutePosition
	local az = card.AbsoluteSize
	local cx = math.round(ap.X + az.X / 2)
	local cy = math.round(ap.Y + 110)
	t.Position = UDim2.new(0, cx, 0, cy)
	t.Parent = gui

	TweenService:Create(
		t,
		TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
		{ Position = UDim2.new(0, cx, 0, cy - 70) }
	):Play()

	local fade = TweenService:Create(
		t,
		TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
		{ TextTransparency = 1 }
	)
	fade.Completed:Connect(function()
		t:Destroy()
	end)
	fade:Play()
end

-- Confeti al reclamar: cuadraditos que salen volando del centro de la tarjeta.
local CONFETI = { COL.cyan, COL.gold, COL.green, COL.cream }

local function confeti(card)
	local ap = card.AbsolutePosition
	local az = card.AbsoluteSize
	local cx = math.round(ap.X + az.X / 2)
	local cy = math.round(ap.Y + az.Y / 2)
	for i = 1, 14 do
		local p = Instance.new("Frame")
		p.Size = UDim2.new(0, 8, 0, 8)
		p.AnchorPoint = Vector2.new(0.5, 0.5)
		p.Position = UDim2.new(0, cx, 0, cy)
		p.BackgroundColor3 = CONFETI[(i % #CONFETI) + 1]
		p.BorderSizePixel = 0
		p.Rotation = math.random(0, 180)
		p.ZIndex = 55
		p.Parent = gui

		local ang = math.rad(math.random(0, 360))
		local dist = 70 + math.random(0, 90)
		local dx = math.round(math.cos(ang) * dist)
		local dy = math.round(math.sin(ang) * dist) - 50
		local tw = TweenService:Create(
			p,
			TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
			{
				Position = UDim2.new(0, cx + dx, 0, cy + dy),
				Rotation = p.Rotation + math.random(-180, 180),
				BackgroundTransparency = 1,
			}
		)
		tw.Completed:Connect(function()
			p:Destroy()
		end)
		tw:Play()
	end
end

-- Entrada del contenido: sube suave al abrir el pase.
local posContenido = contenido.Position

local function animarEntrada()
	contenido.Position = posContenido + UDim2.new(0, 0, 0, 34)
	TweenService:Create(
		contenido,
		TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
		{ Position = posContenido }
	):Play()
end

local function refrescarProgreso()
	local frac = math.clamp(estado.xp / estado.porNivel, 0, 1)
	levelPill.T.Text = "NIVEL " .. estado.nivel
	xpLabel.Text = string.format(
		'<font color="#128aa6">%s</font> / %s XP',
		fmt(estado.xp), fmt(estado.porNivel)
	)
	footLabel.Text = "Faltan " .. fmt(estado.porNivel - estado.xp)
		.. " XP para el nivel " .. (estado.nivel + 1)
	TweenService:Create(
		barFill,
		TweenInfo.new(0.6, Enum.EasingStyle.Quart, Enum.EasingDirection.Out),
		{ Size = UDim2.new(frac, 0, 1, 0) }
	):Play()
end

local function refrescarCamino()
	for i = 1, CFG.niveles do
		local dot = camino:FindFirstChild("TierDot" .. i)
		local sombra = camino:FindFirstChild("DotShadow" .. i)
		if dot then
			local et = dot:FindFirstChild("T")
			if i < estado.nivel then
				dot.BackgroundColor3 = COL.cyan
				if et then
					et.Text = "\u{2713}"
					et.TextColor3 = COL.white
				end
				if sombra then
					sombra.BackgroundColor3 = COL.navy
				end
			elseif i == estado.nivel then
				dot.BackgroundColor3 = COL.gold
				if et then
					et.Text = tostring(i)
					et.TextColor3 = COL.navy
				end
				if sombra then
					sombra.BackgroundColor3 = COL.goldDark
				end
			else
				dot.BackgroundColor3 = COL.white
				if et then
					et.Text = tostring(i)
					et.TextColor3 = COL.muted
				end
				if sombra then
					sombra.BackgroundColor3 = COL.navy
				end
			end
		end
		if i < CFG.niveles then
			local lk = camino:FindFirstChild("Link" .. i)
			if lk then
				if i < estado.nivel then
					lk.BackgroundColor3 = COL.cyan
				else
					lk.BackgroundColor3 = COL.track
				end
			end
		end
	end
end

local function sumarXp(n)
	estado.xp = estado.xp + n
	while estado.xp >= estado.porNivel and estado.nivel < CFG.niveles do
		estado.xp = estado.xp - estado.porNivel
		estado.nivel = estado.nivel + 1
		pop(levelPill, 1.22)
		refrescarCamino()
		toast("\u{A1}Subiste al nivel " .. estado.nivel .. "!")
	end
	if estado.nivel >= CFG.niveles then
		estado.xp = math.min(estado.xp, estado.porNivel)
	end
	refrescarProgreso()
end

local function abrirCarta(card)
	local clave = card.Name
	if estado.reclamados[clave] then
		toast("Ya reclamaste este premio")
		return
	end

	local pista = clave:sub(5, 5)
	local nivelCarta = tonumber(clave:sub(6)) or 1

	if pista == "P" and not estado.premium then
		toast("Necesitas el pase Premium")
		return
	end
	if nivelCarta > estado.nivel then
		toast("Llega al nivel " .. nivelCarta .. " para abrirlo")
		return
	end

	estado.reclamados[clave] = true

	local aro = card:FindFirstChild("IconRing")
	if aro then
		pop(aro, 1.18)
		local emo = aro:FindFirstChild("Emoji")
		if emo then
			emo.Rotation = 0
			TweenService:Create(
				emo,
				TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
				{ Rotation = 360 }
			):Play()
			task.delay(0.55, function()
				emo.Rotation = 0
			end)
		end
	end
	pop(card, 1.05)
	confeti(card)

	local btn = card:FindFirstChild("CardBtn")
	if btn then
		btn.Text = "RECLAMADO"
		btn.BackgroundColor3 = COL.track
		btn.TextColor3 = COL.muted
	end

	local bs = card:FindFirstChild("BtnShadow")
	if bs then
		bs.BackgroundColor3 = COL.trackDark
	end

	local mult = card:FindFirstChild("Mult")
	if mult then
		local et = mult:FindFirstChild("T")
		if pista == "P" then
			mult.BackgroundColor3 = COL.gold
			if et then
				et.TextColor3 = COL.navy
			end
		else
			mult.BackgroundColor3 = COL.cyan
			if et then
				et.TextColor3 = COL.white
			end
		end
		pop(mult, 1.15)
	end

	local premio = CFG.premio
	if pista == "P" then
		premio = CFG.premioPremium
	end
	flotarXp(card, premio)
	sumarXp(premio)
end

local function abrirTodos()
	task.spawn(function()
		local alguno = false
		for i = 1, CFG.nGratis do
			local card = contenido:FindFirstChild("CardF" .. i)
			if card and not estado.reclamados[card.Name] then
				alguno = true
				abrirCarta(card)
				task.wait(0.3)
			end
		end
		if not alguno then
			toast("No queda nada por abrir en la pista gratis")
		end
	end)
end

local function activarPremium()
	if estado.premium then
		toast("Ya tienes el pase Premium")
		return
	end
	estado.premium = true
	upgradeBtn.Text = "PREMIUM ACTIVO"
	upgradeBtn.BackgroundColor3 = COL.goldDark
	upgradeBtn.TextColor3 = COL.cream
	for i = 1, CFG.nPremium do
		local card = contenido:FindFirstChild("CardP" .. i)
		if card and not estado.reclamados[card.Name] then
			local btn = card:FindFirstChild("CardBtn")
			local bs = card:FindFirstChild("BtnShadow")
			if btn then
				btn.Text = "ABRIR"
				btn.BackgroundColor3 = COL.green
				btn.TextColor3 = COL.white
			end
			if bs then
				bs.BackgroundColor3 = COL.greenDark
			end
		end
	end
	toast("\u{A1}Pista Premium desbloqueada!")
end

local function hoverGrupo(fuente, piezas, alEntrar, alSalir)
	local reposo = {}
	local activos = {}
	for i, p in ipairs(piezas) do
		reposo[i] = p.obj.Position
	end
	local dentro = 0

	local function ir(arriba)
		for i, p in ipairs(piezas) do
			local tw = activos[i]
			if tw then
				tw:Cancel()
			end
			local destino = reposo[i]
			local info = BAJA
			if arriba then
				destino = reposo[i] - UDim2.new(0, 0, 0, p.px)
				info = SUBE
			end
			activos[i] = TweenService:Create(p.obj, info, { Position = destino })
			activos[i]:Play()
		end
	end

	-- Un boton hijo dispara el MouseLeave del padre. Sin este contador la
	-- tarjeta se caeria justo al acercar el cursor a ABRIR.
	local function entra()
		dentro = dentro + 1
		if dentro == 1 then
			ir(true)
			if alEntrar then
				alEntrar()
			end
		end
	end

	local function sale()
		dentro = dentro - 1
		if dentro <= 0 then
			dentro = 0
			ir(false)
			if alSalir then
				alSalir()
			end
		end
	end

	fuente.MouseEnter:Connect(entra)
	fuente.MouseLeave:Connect(sale)
	for _, hijo in ipairs(fuente:GetDescendants()) do
		if hijo:IsA("GuiButton") then
			hijo.MouseEnter:Connect(entra)
			hijo.MouseLeave:Connect(sale)
		end
	end
end

local function press(btn, pixeles)
	local reposo = btn.Position
	local abajo = reposo + UDim2.new(0, 0, 0, pixeles)
	local activo = nil
	local function ir(destino)
		if activo then
			activo:Cancel()
		end
		activo = TweenService:Create(btn, PULSA, { Position = destino })
		activo:Play()
	end
	btn.MouseButton1Down:Connect(function()
		ir(abajo)
	end)
	btn.MouseButton1Up:Connect(function()
		ir(reposo)
	end)
	btn.MouseLeave:Connect(function()
		ir(reposo)
	end)
end

for _, obj in ipairs(gui:GetDescendants()) do
	if obj:IsA("Frame") and obj.Name:match("^Card[FP]%d$") then
		local piezas = { { obj = obj, px = 6 } }
		local aro = obj:FindFirstChild("IconRing")
		if aro then
			table.insert(piezas, { obj = aro, px = 3 })
		end
		local borde = obj:FindFirstChild("UIStroke")
		local emo = aro and aro:FindFirstChild("Emoji")
		hoverGrupo(obj, piezas, function()
			if borde then
				TweenService:Create(borde, SUBE, { Thickness = 5 }):Play()
			end
			if emo then
				TweenService:Create(emo, SUBE, { Rotation = 10 }):Play()
			end
		end, function()
			if borde then
				TweenService:Create(borde, BAJA, { Thickness = 3 }):Play()
			end
			if emo then
				TweenService:Create(emo, BAJA, { Rotation = 0 }):Play()
			end
		end)

		local btn = obj:FindFirstChild("CardBtn")
		if btn then
			local carta = obj
			btn.MouseButton1Click:Connect(function()
				abrirCarta(carta)
			end)
		end

	elseif obj:IsA("Frame") and obj.Name:match("^TierDot%d+$") then
		hoverGrupo(obj, { { obj = obj, px = 4 } })
	end
end

for _, obj in ipairs(gui:GetDescendants()) do
	if obj:IsA("GuiButton") then
		press(obj, 3)
	end
end

openAllBtn.MouseButton1Click:Connect(abrirTodos)
upgradeBtn.MouseButton1Click:Connect(activarPremium)

closeBtn.MouseButton1Click:Connect(function()
	backdrop.Visible = false
	scroll.Visible = false
	closeBtn.Visible = false
	closeShadow.Visible = false
	reopenBtn.Visible = true
	reopenShadow.Visible = true
	pop(reopenBtn, 1.12)
end)

reopenBtn.MouseButton1Click:Connect(function()
	backdrop.Visible = true
	scroll.Visible = true
	closeBtn.Visible = true
	closeShadow.Visible = true
	reopenBtn.Visible = false
	reopenShadow.Visible = false
	animarEntrada()
end)

-- La etiqueta NUEVO rebota en bucle: repeticion infinita nativa.
for _, tag in ipairs(gui:GetDescendants()) do
	if tag:IsA("Frame") and tag.Name == "TagNew" then
		local reposo = tag.Position
		TweenService:Create(
			tag,
			TweenInfo.new(0.6, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true),
			{ Position = reposo - UDim2.new(0, 0, 0, 2) }
		):Play()
	end
end

refrescarCamino()
animarEntrada()
local objetivo = math.clamp(estado.xp / estado.porNivel, 0, 1)
barFill.Size = UDim2.new(0, 0, 1, 0)
TweenService:Create(
	barFill,
	TweenInfo.new(1, Enum.EasingStyle.Quart, Enum.EasingDirection.Out, 0, false, 0.3),
	{ Size = UDim2.new(objetivo, 0, 1, 0) }
):Play()
"""


if __name__ == "__main__":
    sys.exit(main())
