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

Es la version corregida del generador de juego2. Cada cambio esta explicado
en HALLAZGOS.md:

    1. WaitForChild se localiza contando parentesis, no con [^)]*
    2. LoadAnimation solo se marca cuando cuelga de un Humanoid
    3. la lista de fuentes y el arbol son datos, no numeros escritos a mano
    4. todo valor que entra en el XML pasa por esc(), tambien los Name
    5. despojar() entiende las cadenas con acento grave de Luau
    6. se exige la cabecera TIPO / RUTA que pide AGENTS.md
    7. se avisa de CFrame.Angles sin math.rad

No hay interprete de Luau aqui: todo lo que hace este archivo es revision
estatica. Ver la seccion Limites del README.
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

# El arbol es un dato. Anadir un cuarto script es tocar FUENTES, TIPO_ESPERADO
# y esta estructura; no hay ningun numero suelto que haya que recordar.
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


# ---------------------------------------------------------------- utilidades


def despojar(src):
    """Devuelve el codigo sin comentarios y con las cadenas vaciadas.

    Entiende cadenas cortas con " y ', cadenas largas [[ ]] y [=[ ]=], los
    comentarios -- y --[[ ]], y tambien las cadenas con acento grave de Luau
    (las interpoladas). El generador de juego2 no conocia las ultimas: una
    palabra clave escrita dentro de una de ellas descuadraba el recuento de
    bloques sin motivo aparente.
    """
    salida = []
    i = 0
    n = len(src)
    while i < n:
        resto = src[i:]
        # comentario largo
        largo = re.match(r"--\[(=*)\[", resto)
        if largo:
            cierre = "]" + largo.group(1) + "]"
            fin = src.find(cierre, i)
            if fin == -1:
                break
            i = fin + len(cierre)
            continue
        # comentario de linea
        if resto.startswith("--"):
            fin = src.find("\n", i)
            if fin == -1:
                break
            i = fin
            continue
        # cadena larga
        cadena = re.match(r"\[(=*)\[", resto)
        if cadena:
            cierre = "]" + cadena.group(1) + "]"
            fin = src.find(cierre, i)
            if fin == -1:
                break
            salida.append('""')
            i = fin + len(cierre)
            continue
        # cadena corta o interpolada
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
    """Texto entre parentesis equilibrados. apertura apunta al '('.

    Devuelve None si el parentesis no llega a cerrarse.
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
    """Escapa un valor para meterlo en texto XML.

    Se aplica a todo lo que entra: fuentes, nombres, valores de propiedad y
    nombres de propiedad. El orden importa: primero &, luego < y >.
    """
    texto = str(valor)
    texto = texto.replace("&", "&amp;")
    texto = texto.replace("<", "&lt;")
    texto = texto.replace(">", "&gt;")
    return texto


# ------------------------------------------------------------ revision lua


def revisar_cabecera(nombre, src):
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

    # APIs retiradas
    for viejo, arreglo in OBSOLETAS:
        if re.search(r"\b" + viejo + r"\b", limpio):
            problemas.append("API retirada: %s (%s)" % (viejo, arreglo))

    # Animator:LoadAnimation es la forma correcta; la que hay que cazar es la
    # del Humanoid. La lista negra de juego2 marcaba las dos y por eso
    # rechazaba codigo que cumple la regla 4 de PROMPT-3.
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

    # WaitForChild sin tiempo maximo. Se leen los argumentos contando
    # parentesis, asi WaitForChild(tostring(i), 5) no da un falso positivo.
    for m in re.finditer(r"WaitForChild\s*\(", limpio):
        args = argumentos_de(limpio, m.end() - 1)
        if args is None:
            problemas.append("WaitForChild con el parentesis sin cerrar")
        elif not hay_coma_de_primer_nivel(args):
            problemas.append(
                "WaitForChild sin tiempo maximo: WaitForChild(%s)"
                % args.strip()[:48]
            )

    # Angulos en CFrame. Roblox espera radianes; escribir grados es el error
    # mas comun del catalogo.
    for m in re.finditer(r"CFrame\.(?:Angles|fromEulerAnglesXYZ)\s*\(", limpio):
        args = argumentos_de(limpio, m.end() - 1)
        if args is not None and "math.rad" not in args:
            problemas.append(
                "CFrame con angulos sin math.rad: (%s)" % args.strip()[:48]
            )

    # Recuento de bloques. Es una heuristica: cuenta las palabras que abren
    # bloque y las compara con los end. elseif no abre bloque nuevo y por eso
    # se descuenta de los if; repeat cierra con until y va aparte.
    n_func = contar(limpio, "function")
    n_if = contar(limpio, "if") - contar(limpio, "elseif")
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

    # Simbolos por parejas
    for abre, cierra, etiqueta in (("(", ")", "parentesis"),
                                   ("[", "]", "corchetes"),
                                   ("{", "}", "llaves")):
        if limpio.count(abre) != limpio.count(cierra):
            problemas.append(
                "%s descuadrados: %d abren y %d cierran"
                % (etiqueta, limpio.count(abre), limpio.count(cierra))
            )

    return problemas


# ---------------------------------------------------------------- escritura


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


# ----------------------------------------------------------------- auditoria


def auditar(ruta, fuentes):
    """Relee el archivo escrito y comprueba que dice lo que se le pidio."""
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
            # Si quedara doble escapado, el parser devolveria el literal.
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


# ---------------------------------------------------------------------- main


def main():
    fuentes = {}
    for clave in FUENTES:
        ruta = os.path.join(AQUI, clave + ".lua")
        if not os.path.exists(ruta):
            print("FALTA %s" % ruta)
            return 1
        # Modo texto a proposito: los saltos \r\n se normalizan a \n aqui, y
        # asi la comparacion de la auditoria no falla por el final de linea.
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
