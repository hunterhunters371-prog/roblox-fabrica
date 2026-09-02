# -*- coding: utf-8 -*-
"""gen_rbxmx.py - empaqueta juego3 en un solo archivo .rbxmx

Arbol que produce:

    Folder  EntregaFinal
        Script       Servidor
        ScreenGui    Interfaz          (plantilla inerte dentro de Workspace)
            LocalScript  Cliente
            ModuleScript Config

Uso:
    python juego3/gen_rbxmx.py

Esta version esta ejecutada, no solo escrita: la salida verificada es
"3 de 3 fuentes verificadas byte a byte".
"""

import os
import re
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "EntregaFinal.rbxmx")

FUENTES = ("Servidor", "Cliente", "Config")

TIPO_ESPERADO = {
    "Servidor": "Script",
    "Cliente": "LocalScript",
    "Config": "ModuleScript",
}

ARBOL = {
    "clase": "Folder",
    "nombre": "EntregaFinal",
    "props": [],
    "hijos": [
        {
            "clase": "Script",
            "nombre": "Servidor",
            "fuente": "Servidor",
            "props": [],
            "hijos": [],
        },
        {
            "clase": "ScreenGui",
            "nombre": "Interfaz",
            "props": [
                ("bool", "Enabled", "true"),
                ("bool", "ResetOnSpawn", "false"),
                ("bool", "IgnoreGuiInset", "true"),
                ("token", "ZIndexBehavior", "1"),
            ],
            "hijos": [
                {
                    "clase": "LocalScript",
                    "nombre": "Cliente",
                    "fuente": "Cliente",
                    "props": [],
                    "hijos": [],
                },
                {
                    "clase": "ModuleScript",
                    "nombre": "Config",
                    "fuente": "Config",
                    "props": [],
                    "hijos": [],
                },
            ],
        },
    ],
}

CAB = (
    '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" '
    'version="4">'
)

OBSOLETAS = (
    ("BodyVelocity", "usa LinearVelocity"),
    ("BodyPosition", "usa AlignPosition"),
    ("BodyGyro", "usa AlignOrientation"),
    ("BodyAngularVelocity", "usa AngularVelocity"),
    ("SetPrimaryPartCFrame", "usa Model:PivotTo"),
    ("GetPrimaryPartCFrame", "usa Model:GetPivot"),
    ("FindPartOnRay", "usa workspace:Raycast"),
    ("FindPartsInRegion3", "usa workspace:GetPartBoundsInBox"),
    ("TeleportPartyAsync", "usa TeleportService:TeleportAsync"),
)


def despojar(src):
    """Devuelve el Luau sin comentarios ni contenido de cadenas.

    Las cadenas se sustituyen por dos comillas para no perder la posicion.
    A diferencia de juego2, aqui el acento grave cuenta como comilla: las
    cadenas interpoladas de Luau se abren y cierran con el, y si no se
    consumen, las palabras clave que llevan dentro descuadran el recuento.
    """
    salida = []
    i = 0
    n = len(src)
    while i < n:
        resto = src[i:]
        largo = re.match(r"--\[(=*)\[", resto)
        if largo:
            cierre = "]" + largo.group(1) + "]"
            fin = src.find(cierre, i)
            if fin == -1:
                break
            i = fin + len(cierre)
            continue
        if resto.startswith("--"):
            fin = src.find("\n", i)
            if fin == -1:
                break
            i = fin
            continue
        cadena = re.match(r"\[(=*)\[", resto)
        if cadena:
            cierre = "]" + cadena.group(1) + "]"
            fin = src.find(cierre, i)
            if fin == -1:
                break
            salida.append('""')
            i = fin + len(cierre)
            continue
        c = src[i]
        if c == '"' or c == "'" or c == "`":
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == c:
                    j += 1
                    break
                # una cadena normal no cruza el salto de linea; una
                # interpolada con acento grave si puede hacerlo
                if src[j] == "\n" and c != "`":
                    break
                j += 1
            salida.append('""')
            i = j
            continue
        salida.append(c)
        i += 1
    return "".join(salida)


def contar(texto, palabra):
    return len(re.findall(r"\b" + palabra + r"\b", texto))


def argumentos_de(texto, apertura):
    """Texto entre el parentesis de apertura y su cierre equilibrado.

    juego2 usaba WaitForChild\\(([^)]*)\\) y esa clase para en el primer
    cierre, asi que WaitForChild(tostring(i), 5) se leia como "tostring(i"
    y avisaba de falta de tiempo maximo donde si lo habia.
    """
    nivel = 0
    for i in range(apertura, len(texto)):
        c = texto[i]
        if c == "(":
            nivel += 1
        elif c == ")":
            nivel -= 1
            if nivel == 0:
                return texto[apertura + 1:i]
    return None


def hay_coma_de_primer_nivel(args):
    nivel = 0
    for c in args:
        if c in "([{":
            nivel += 1
        elif c in ")]}":
            nivel -= 1
        elif c == "," and nivel == 0:
            return True
    return False


def esc(valor):
    """Escapa lo que entra al XML. Se aplica tambien a los Name: un nombre
    con & o < generaba XML mal formado y el fallo salia tarde y disfrazado.
    """
    texto = str(valor)
    texto = texto.replace("&", "&amp;")
    texto = texto.replace("<", "&lt;")
    texto = texto.replace(">", "&gt;")
    return texto


def revisar_cabecera(nombre, src):
    """AGENTS.md exige dos lineas de cabecera y ninguna herramienta lo mira."""
    lineas = src.splitlines()
    problemas = []
    if len(lineas) < 2:
        return ["el archivo es demasiado corto para llevar cabecera"]
    if not lineas[0].startswith("-- TIPO:"):
        problemas.append("la linea 1 no es la cabecera '-- TIPO: ...'")
    elif TIPO_ESPERADO[nombre] not in lineas[0]:
        problemas.append(
            "la cabecera dice '%s' pero el arbol lo monta como %s"
            % (lineas[0].strip(), TIPO_ESPERADO[nombre])
        )
    if not lineas[1].startswith("-- RUTA:"):
        problemas.append("la linea 2 no es la cabecera '-- RUTA: ...'")
    return problemas


def revisar_lua(nombre, src):
    problemas = list(revisar_cabecera(nombre, src))
    limpio = despojar(src)

    for viejo, arreglo in OBSOLETAS:
        if re.search(r"\b" + viejo + r"\b", limpio):
            problemas.append("API retirada: %s (%s)" % (viejo, arreglo))

    # solo se marca LoadAnimation cuando cuelga de un Humanoid: la lista
    # negra de juego2 rechazaba tambien Animator:LoadAnimation, que es el
    # sustituto que obliga PROMPT-3
    if re.search(r"[Hh]umanoid[e]?\s*:\s*LoadAnimation", limpio):
        problemas.append(
            "API retirada: Humanoid:LoadAnimation (usa Animator:LoadAnimation)"
        )
    if re.search(r"\.\s*Chatted\b", limpio):
        problemas.append("API retirada: Player.Chatted (usa TextChatService)")
    if re.search(r"\.\s*(Velocity|RotVelocity)\b", limpio):
        problemas.append(
            "propiedad retirada: part.Velocity (usa AssemblyLinearVelocity)"
        )
    for viejo in ("wait", "spawn", "delay"):
        if re.search(r"(?<![.:\w])" + viejo + r"\s*\(", limpio):
            problemas.append("%s() global: usa task.%s()" % (viejo, viejo))

    for m in re.finditer(r"WaitForChild\s*\(", limpio):
        args = argumentos_de(limpio, m.end() - 1)
        if args is None:
            problemas.append("WaitForChild con el parentesis sin cerrar")
        elif not hay_coma_de_primer_nivel(args):
            problemas.append(
                "WaitForChild sin tiempo maximo: WaitForChild(%s)"
                % args.strip()[:48]
            )

    for m in re.finditer(r"CFrame\.(?:Angles|fromEulerAnglesXYZ)\s*\(", limpio):
        args = argumentos_de(limpio, m.end() - 1)
        if args is not None and "math.rad" not in args:
            problemas.append(
                "CFrame con angulos sin math.rad: (%s)" % args.strip()[:48]
            )

    n_func = contar(limpio, "function")
    # \bif\b no casa dentro de "elseif": antes de la i hay una e, que es
    # caracter de palabra, asi que no hay frontera. Por eso los elseif no se
    # cuentan y no hay que restarlos; restarlos deja el recuento corto y da
    # un falso "bloques descuadrados" por cada elseif del archivo.
    n_if = contar(limpio, "if")
    n_do = contar(limpio, "do")
    n_end = contar(limpio, "end")
    esperado = n_func + n_if + n_do
    if esperado != n_end:
        problemas.append(
            "bloques descuadrados: function %d + if %d + do %d = %d, end %d"
            % (n_func, n_if, n_do, esperado, n_end)
        )
    if contar(limpio, "repeat") != contar(limpio, "until"):
        problemas.append("repeat y until no coinciden")

    for abre, cierra, etiqueta in (("(", ")", "parentesis"),
                                   ("[", "]", "corchetes"),
                                   ("{", "}", "llaves")):
        if limpio.count(abre) != limpio.count(cierra):
            problemas.append(
                "%s descuadrados: %d abren y %d cierran"
                % (etiqueta, limpio.count(abre), limpio.count(cierra))
            )

    return problemas


def escribir_nodo(nodo, fuentes, lineas, contador, nivel):
    sangria = "  " * nivel
    ref = contador[0]
    contador[0] += 1
    lineas.append(
        '%s<Item class="%s" referent="RBX%d">' % (sangria, esc(nodo["clase"]), ref)
    )
    lineas.append("%s  <Properties>" % sangria)
    lineas.append(
        '%s    <string name="Name">%s</string>' % (sangria, esc(nodo["nombre"]))
    )
    clave = nodo.get("fuente")
    if clave:
        lineas.append(
            '%s    <ProtectedString name="Source">%s</ProtectedString>'
            % (sangria, esc(fuentes[clave]))
        )
    for tipo, propiedad, valor in nodo.get("props", []):
        lineas.append(
            "%s    <%s name=\"%s\">%s</%s>"
            % (sangria, tipo, esc(propiedad), esc(valor), tipo)
        )
    lineas.append("%s  </Properties>" % sangria)
    for hijo in nodo.get("hijos", []):
        escribir_nodo(hijo, fuentes, lineas, contador, nivel + 1)
    lineas.append("%s</Item>" % sangria)


def construir(fuentes):
    lineas = [
        '<?xml version="1.0" encoding="utf-8"?>',
        CAB,
        '  <Meta name="ExplicitAutoJoints">true</Meta>',
    ]
    escribir_nodo(ARBOL, fuentes, lineas, [0], 1)
    lineas.append("</roblox>")
    return "\n".join(lineas) + "\n"


def auditar(ruta, fuentes):
    """Relee el archivo escrito: XML valido, referentes unicos y cada fuente
    igual byte a byte que la que entro.
    """
    problemas = []
    try:
        raiz = ET.parse(ruta).getroot()
    except ET.ParseError as error:
        return ["el XML no se puede releer: %s" % error], {}

    referentes = [item.get("referent") for item in raiz.iter("Item")]
    if len(referentes) != len(set(referentes)):
        problemas.append("hay referentes repetidos")

    halladas = {}
    for item in raiz.iter("Item"):
        props = item.find("Properties")
        if props is None:
            continue
        nombre = None
        for nodo in props.findall("string"):
            if nodo.get("name") == "Name":
                nombre = nodo.text or ""
        for nodo in props.findall("ProtectedString"):
            if nodo.get("name") != "Source":
                continue
            texto = nodo.text or ""
            halladas[nombre] = texto
            if "&amp;" in texto or "&lt;" in texto or "&gt;" in texto:
                problemas.append("doble escapado en la fuente de %s" % nombre)

    for clave in FUENTES:
        if clave not in halladas:
            problemas.append("falta la fuente de %s dentro del XML" % clave)
        elif halladas[clave] != fuentes[clave]:
            problemas.append(
                "la fuente de %s no vuelve igual que salio" % clave
            )
    return problemas, halladas


def main():
    fuentes = {}
    for clave in FUENTES:
        ruta = os.path.join(AQUI, clave + ".lua")
        if not os.path.exists(ruta):
            print("FALTA %s" % ruta)
            return 1
        with open(ruta, encoding="utf-8") as archivo:
            fuentes[clave] = archivo.read()

    print("revision estatica de Luau")
    fallos = 0
    for clave in FUENTES:
        problemas = revisar_lua(clave, fuentes[clave])
        if problemas:
            fallos += len(problemas)
            print("  %s: %d avisos" % (clave, len(problemas)))
            for problema in problemas:
                print("    - %s" % problema)
        else:
            lineas = fuentes[clave].count("\n") + 1
            print("  %s: limpio (%d lineas)" % (clave, lineas))

    if fallos:
        print("no escribo el .rbxmx con avisos pendientes")
        return 1

    with open(SALIDA, "w", encoding="utf-8", newline="\n") as archivo:
        archivo.write(construir(fuentes))
    print("escrito %s" % SALIDA)

    print("auditoria del XML")
    problemas, halladas = auditar(SALIDA, fuentes)
    for problema in problemas:
        print("  - %s" % problema)
    if problemas:
        return 1
    print("  XML valido, %d de %d fuentes verificadas byte a byte"
          % (len(halladas), len(FUENTES)))
    print("listo: arrastra EntregaFinal.rbxmx a Workspace en Studio")
    # el 4 fijo de juego2 se queda corto o largo en cuanto cambia la lista
    return 0 if len(halladas) == len(FUENTES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
