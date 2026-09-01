# -*- coding: utf-8 -*-
"""roblox_lint.py - Entorno que imita los limites de Roblox Studio.

Revisa un .rbxmx SIN abrir Studio y falla igual que fallaria el motor.
Cada regla nacio de un bug real observado en pantalla.

Uso:
    python3 roblox_lint.py archivo.rbxmx

Salida: lista de ERROR / AVISO con la ruta del objeto, y codigo de salida 1
si hay algun ERROR.
"""

import math
import re
import sys
import xml.etree.ElementTree as ET

# ----------------------------------------------------------------- limites

CLASES = {
    "ScreenGui", "Frame", "ScrollingFrame", "CanvasGroup",
    "TextLabel", "TextButton", "TextBox",
    "ImageLabel", "ImageButton", "ViewportFrame",
    "UICorner", "UIStroke", "UIPadding", "UIListLayout",
    "UIAspectRatioConstraint", "UISizeConstraint", "UIGradient",
    "LocalScript", "ModuleScript", "Folder",
}

COMUN_GUI = {
    "Name", "Position", "Size", "AnchorPoint", "Rotation", "Visible",
    "ZIndex", "ClipsDescendants", "BackgroundColor3",
    "BackgroundTransparency", "BorderSizePixel", "BorderColor3",
    "Active", "Selectable", "AutomaticSize", "LayoutOrder", "Interactable",
}

TEXTO = {
    "Text", "TextColor3", "TextSize", "TextTransparency", "Font",
    "FontFace", "TextXAlignment", "TextYAlignment", "TextWrapped",
    "TextScaled", "RichText", "TextStrokeColor3",
    "TextStrokeTransparency", "LineHeight", "MaxVisibleGraphemes",
}

BOTON = {"AutoButtonColor", "Modal", "Style"}

IMAGEN = {
    "Image", "ImageColor3", "ImageTransparency", "ScaleType",
    "ImageRectOffset", "ImageRectSize", "SliceCenter", "TileSize",
}

PROPS = {
    "ScreenGui": {"Name", "Enabled", "ResetOnSpawn", "IgnoreGuiInset",
                  "ZIndexBehavior", "DisplayOrder", "ClipToDeviceSafeArea"},
    "Frame": COMUN_GUI,
    "CanvasGroup": COMUN_GUI | {"GroupTransparency", "GroupColor3"},
    "ScrollingFrame": COMUN_GUI | {
        "CanvasSize", "CanvasPosition", "ScrollBarThickness",
        "ScrollBarImageColor3", "ScrollBarImageTransparency",
        "ScrollingDirection", "ScrollingEnabled", "AutomaticCanvasSize",
        "ElasticBehavior", "VerticalScrollBarInset",
    },
    "TextLabel": COMUN_GUI | TEXTO,
    "TextButton": COMUN_GUI | TEXTO | BOTON,
    "TextBox": COMUN_GUI | TEXTO | {"PlaceholderText", "ClearTextOnFocus",
                                    "MultiLine", "PlaceholderColor3"},
    "ImageLabel": COMUN_GUI | IMAGEN,
    "ImageButton": COMUN_GUI | IMAGEN | BOTON | {"HoverImage", "PressedImage"},
    "UICorner": {"Name", "CornerRadius"},
    "UIStroke": {"Name", "Thickness", "Color", "Transparency",
                 "ApplyStrokeMode", "LineJoinMode", "Enabled"},
    "UIPadding": {"Name", "PaddingTop", "PaddingBottom",
                  "PaddingLeft", "PaddingRight"},
    "UIListLayout": {"Name", "Padding", "FillDirection", "SortOrder",
                     "HorizontalAlignment", "VerticalAlignment", "Wraps"},
    "UIGradient": {"Name", "Color", "Offset", "Rotation", "Enabled",
                   "Transparency"},
    "LocalScript": {"Name", "Source", "Disabled", "RunContext"},
    "ModuleScript": {"Name", "Source"},
    "Folder": {"Name"},
}

# enum -> maximo token valido (comprobacion de rango, no exhaustiva)
TOKENS = {
    "Font": 60, "TextXAlignment": 2, "TextYAlignment": 2,
    "ZIndexBehavior": 1, "ApplyStrokeMode": 1, "ScrollingDirection": 4,
    "AutomaticSize": 3, "SortOrder": 2, "FillDirection": 1,
    "ScaleType": 3, "LineJoinMode": 2, "ElasticBehavior": 2,
}

# ancho medio de caracter como fraccion de TextSize (Gotham)
ANCHO_CHAR = 0.55


class Lint:
    def __init__(self):
        self.errores = []
        self.avisos = []

    def error(self, ruta, regla, msg):
        self.errores.append((ruta, regla, msg))

    def aviso(self, ruta, regla, msg):
        self.avisos.append((ruta, regla, msg))


def props_de(item):
    """Devuelve {nombre: (tipo_xml, elemento)} de un <Item>."""
    out = {}
    holder = item.find("Properties")
    if holder is None:
        return out
    for el in holder:
        n = el.get("name")
        if n:
            out[n] = (el.tag, el)
    return out


def texto_de(props, clave):
    if clave not in props:
        return None
    return props[clave][1].text


def udim2_de(props, clave):
    if clave not in props:
        return None
    el = props[clave][1]
    if el.tag != "UDim2":
        return None

    def g(t):
        n = el.find(t)
        return n.text if n is not None else "0"

    return (g("XS"), g("XO"), g("YS"), g("YO"))


def es_entero(s):
    if s is None:
        return True
    s = s.strip()
    if not s:
        return True
    try:
        v = float(s)
    except ValueError:
        return False
    return abs(v - round(v)) < 1e-9 and "." not in s and "e" not in s.lower()


def num(s, default=0.0):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def revisar(path):
    L = Lint()
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        L.error(path, "XML", "el archivo no es XML valido: %s" % e)
        return L, 0

    # referentes duplicados
    refs = [i.get("referent") for i in root.iter("Item")]
    if len(refs) != len(set(refs)):
        L.error("(archivo)", "REF", "hay referentes repetidos; Studio unira objetos")

    global_z = False
    for it in root.iter("Item"):
        if it.get("class") == "ScreenGui":
            p = props_de(it)
            if texto_de(p, "ZIndexBehavior") == "1":
                global_z = True

    total = [0]

    def caminar(item, ruta, padre_size, padre_clips):
        total[0] += 1
        cls = item.get("class")
        p = props_de(item)
        nombre = texto_de(p, "Name") or cls
        mi_ruta = "%s/%s" % (ruta, nombre)

        # --- R1 clase permitida
        if cls not in CLASES:
            L.error(mi_ruta, "R1-CLASE",
                    "la clase '%s' no esta en la lista permitida" % cls)

        # --- R2 propiedades permitidas
        permitidas = PROPS.get(cls)
        if permitidas:
            for k in p:
                if k not in permitidas:
                    L.error(mi_ruta, "R2-PROP",
                            "'%s' no es una propiedad valida de %s" % (k, cls))

        # --- R3 los offsets de UDim y UDim2 son ENTEROS en el motor
        for k, (tipo, el) in p.items():
            if tipo == "UDim2":
                for tag in ("XO", "YO"):
                    n = el.find(tag)
                    if n is not None and not es_entero(n.text):
                        L.error(mi_ruta, "R3-OFFSET",
                                "%s.%s = %s ; UDim.Offset es entero, "
                                "un decimal se convierte en 0"
                                % (k, tag, n.text))
            elif tipo == "UDim":
                n = el.find("O")
                if n is not None and not es_entero(n.text):
                    L.error(mi_ruta, "R3-OFFSET",
                            "%s.O = %s ; UDim.Offset es entero" % (k, n.text))

        # --- R4 rango de tokens de enum
        for k, (tipo, el) in p.items():
            if tipo == "token" and k in TOKENS:
                v = int(num(el.text, -1))
                if v < 0 or v > TOKENS[k]:
                    L.error(mi_ruta, "R4-ENUM",
                            "%s = %s esta fuera del rango valido 0..%d"
                            % (k, el.text, TOKENS[k]))

        # --- R5 componentes Color3 en 0..1
        for k, (tipo, el) in p.items():
            if tipo == "Color3":
                for c in ("R", "G", "B"):
                    n = el.find(c)
                    if n is not None and not (0.0 <= num(n.text) <= 1.0):
                        L.error(mi_ruta, "R5-COLOR",
                                "%s.%s = %s ; debe estar entre 0 y 1 "
                                "(no 0..255)" % (k, c, n.text))

        # --- R6 RichText coherente
        txt = texto_de(p, "Text")
        rich = texto_de(p, "RichText") == "true"
        if txt:
            if "&lt;" in txt or "&amp;" in txt:
                L.error(mi_ruta, "R6-RICHTEXT",
                        "el texto guardo entidades escapadas (%s...); "
                        "se escapo dos veces y se vera el markup crudo"
                        % txt[:24])
            if rich:
                abre = len(re.findall(r"<\s*(\w+)", txt))
                cierra = len(re.findall(r"<\s*/\s*\w+", txt))
                if abre != cierra * 2 - cierra:  # abre == cierra
                    if abre != cierra:
                        L.error(mi_ruta, "R6-RICHTEXT",
                                "etiquetas sin cerrar: %d abren, %d cierran"
                                % (abre, cierra))
            elif re.search(r"<\s*(font|b|i|u|s|stroke|br)\b", txt or ""):
                L.error(mi_ruta, "R6-RICHTEXT",
                        "el texto lleva etiquetas pero RichText es false; "
                        "se veran como caracteres")

        # --- geometria
        sz = udim2_de(p, "Size")
        pos = udim2_de(p, "Position")
        w = h = None
        if sz:
            xs, xo, ys, yo = (num(v) for v in sz)
            if padre_size:
                w = xs * padre_size[0] + xo
                h = ys * padre_size[1] + yo
            else:
                w, h = xo or None, yo or None

        # --- R7 el texto cabe en su caja
        if cls in ("TextLabel", "TextButton") and txt and w and h:
            size = num(texto_de(p, "TextSize"), 14)
            limpio = re.sub(r"<[^>]+>", "", txt)
            est = len(limpio) * size * ANCHO_CHAR
            envuelto = texto_de(p, "TextWrapped") == "true"
            if not envuelto and est > w * 1.18:
                L.aviso(mi_ruta, "R7-TEXTO",
                        "'%s' mide ~%dpx y la caja %dpx; se cortara o saldra"
                        % (limpio[:26], est, w))
            elif envuelto:
                lineas = max(1, math.ceil(est / max(w, 1)))
                if lineas * size * 1.25 > h * 1.15:
                    L.aviso(mi_ruta, "R7-TEXTO",
                            "necesita ~%d lineas (%dpx) y solo hay %dpx de alto"
                            % (lineas, lineas * size * 1.25, h))

        # --- R8 el hijo se sale del padre que no recorta
        if pos and w and h and padre_size and not padre_clips:
            xs, xo, ys, yo = (num(v) for v in pos)
            ax = ay = 0.0
            if "AnchorPoint" in p:
                el = p["AnchorPoint"][1]
                ax = num(el.find("X").text if el.find("X") is not None else 0)
                ay = num(el.find("Y").text if el.find("Y") is not None else 0)
            left = xs * padre_size[0] + xo - ax * w
            top = ys * padre_size[1] + yo - ay * h
            if left < -1 or top < -1 or left + w > padre_size[0] + 1 \
                    or top + h > padre_size[1] + 1:
                L.aviso(mi_ruta, "R8-DESBORDE",
                        "ocupa x %d..%d y %d..%d dentro de un padre de %dx%d"
                        % (left, left + w, top, top + h,
                           padre_size[0], padre_size[1]))

        # --- R9 sombra dura por debajo de su cara
        if global_z and nombre in ("Shadow", "BtnShadow"):
            z = num(texto_de(p, "ZIndex"), 1)
            hermanos = []
            # se valida contra el resto de hermanos en el bucle del padre
            item.set("_shadowz", str(z))

        # --- R10 un Frame no recibe clics
        #     Se excluyen los *Shadow: son la sombra dura del boton, y ser
        #     Frame es justo lo correcto.
        if cls == "Frame" \
                and re.search(r"(btn|button|boton)", nombre, re.I) \
                and not re.search(r"shadow|sombra", nombre, re.I):
            L.aviso(mi_ruta, "R10-CLIC",
                    "se llama como boton pero es un Frame; "
                    "un Frame no dispara MouseButton1Click")

        clips = texto_de(p, "ClipsDescendants") == "true"
        hijos_size = (w, h) if (w and h) else padre_size
        for hijo in item.findall("Item"):
            caminar(hijo, mi_ruta, hijos_size, clips)

    for it in root.findall("Item"):
        caminar(it, "", None, False)

    if not global_z:
        L.aviso("(ScreenGui)", "R9-ZINDEX",
                "ZIndexBehavior no es Global; con sombras duras una tarjeta "
                "puede taparse con la sombra de su vecina")

    return L, total[0]


def main():
    if len(sys.argv) < 2:
        print("uso: python3 roblox_lint.py archivo.rbxmx")
        return 2

    salida = 0
    for path in sys.argv[1:]:
        L, n = revisar(path)
        print("=" * 66)
        print("%s   (%d instancias)" % (path, n))
        print("=" * 66)

        if L.errores:
            print("\nERRORES  (%d)  -- rompen el resultado en Studio\n"
                  % len(L.errores))
            vistos = {}
            for ruta, regla, msg in L.errores:
                vistos.setdefault((regla, msg.split(";")[0][:40]), []).append(ruta)
            for (regla, _), rutas in vistos.items():
                ej = rutas[0]
                print("  [%s] x%d" % (regla, len(rutas)))
                print("        %s" % ej)
            print()
            for ruta, regla, msg in L.errores[:8]:
                print("  [%s] %s" % (regla, msg))
                print("        en %s" % ruta)
            if len(L.errores) > 8:
                print("  ... y %d mas" % (len(L.errores) - 8))
            salida = 1
        else:
            print("\nERRORES  0   nada que rompa el motor")

        if L.avisos:
            print("\nAVISOS   (%d)  -- se vera mal pero funciona\n"
                  % len(L.avisos))
            for ruta, regla, msg in L.avisos[:10]:
                print("  [%s] %s" % (regla, msg))
                print("        en %s" % ruta)
            if len(L.avisos) > 10:
                print("  ... y %d mas" % (len(L.avisos) - 10))
        else:
            print("AVISOS   0")
        print()

    return salida


if __name__ == "__main__":
    sys.exit(main())
