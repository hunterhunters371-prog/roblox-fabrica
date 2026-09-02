# -*- coding: utf-8 -*-
"""gen_rbxmx.py - ensambla el juego en un solo archivo .rbxmx.

Arbol que produce:

    Folder  BancoDeAnimaciones
        Script       Servidor
        ScreenGui    Interfaz          (plantilla inerte en Workspace)
            LocalScript  Cliente
            ModuleScript Datos
            ModuleScript Rig

Antes de escribir nada revisa el Luau: no hay interprete en este entorno,
asi que se comprueba el balance de bloques (function/if/do frente a end,
repeat frente a until) y el de parentesis, corchetes y llaves, ignorando
comentarios y cadenas.
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "BancoDeAnimaciones.rbxmx")

CAB = (
    '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" '
    'version="4">'
)


# ------------------------------------------------------------ revision lua

def despojar(src):
    """Quita comentarios y cadenas para poder contar palabras clave."""
    out = []
    i = 0
    n = len(src)
    while i < n:
        c = src[i]

        # comentario largo  --[[ ]]  o  --[==[ ]==]
        if src.startswith("--", i):
            m = re.match(r"--\[(=*)\[", src[i:])
            if m:
                cierre = "]" + m.group(1) + "]"
                fin = src.find(cierre, i + m.end())
                i = n if fin < 0 else fin + len(cierre)
                continue
            fin = src.find("\n", i)
            if fin < 0:
                break
            out.append("\n")
            i = fin + 1
            continue

        # cadena larga  [[ ]]
        m = re.match(r"\[(=*)\[", src[i:])
        if m:
            cierre = "]" + m.group(1) + "]"
            fin = src.find(cierre, i + m.end())
            i = n if fin < 0 else fin + len(cierre)
            out.append('""')
            continue

        # cadena corta
        if c in "\"'":
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == c:
                    j += 1
                    break
                if src[j] == "\n":
                    break
                j += 1
            out.append('""')
            i = j
            continue

        out.append(c)
        i += 1
    return "".join(out)


def contar(texto, palabra):
    return len(re.findall(r"\b" + palabra + r"\b", texto))


def revisar_lua(nombre, src):
    """Devuelve (lista_de_problemas, tabla_de_conteos)."""
    limpio = despojar(src)
    problemas = []

    # OJO: \bif\b no casa dentro de 'elseif' porque la 'e' anterior ya
    # es caracter de palabra. Descontar los elseif era un fallo de este
    # verificador, no del Luau: daba 5 'end' de mas en Cliente.lua.
    n_if = contar(limpio, "if")
    n_func = contar(limpio, "function")
    n_do = contar(limpio, "do")
    n_end = contar(limpio, "end")
    n_rep = contar(limpio, "repeat")
    n_until = contar(limpio, "until")

    # for/while siempre llevan su propio 'do', asi que contando 'do' ya
    # quedan cubiertos y no hace falta sumarlos aparte.
    esperado = n_func + n_if + n_do
    if n_end != esperado:
        problemas.append(
            "bloques descompensados: %d 'end' frente a %d esperados "
            "(function %d + if %d + do %d)"
            % (n_end, esperado, n_func, n_if, n_do))
    if n_rep != n_until:
        problemas.append("repeat %d frente a until %d" % (n_rep, n_until))

    for abre, cierra, etiqueta in (("(", ")", "parentesis"),
                                   ("[", "]", "corchetes"),
                                   ("{", "}", "llaves")):
        a, b = limpio.count(abre), limpio.count(cierra)
        if a != b:
            problemas.append("%s descompensados: %d abren, %d cierran"
                             % (etiqueta, a, b))

    # APIs obsoletas segun el propio checklist del repositorio
    obsoletas = ["BodyVelocity", "BodyPosition", "BodyGyro",
                 "BodyAngularVelocity", "SetPrimaryPartCFrame",
                 "FindPartOnRay", "FindPartsInRegion3", "LoadAnimation"]
    for api in obsoletas:
        if re.search(r"\b" + api + r"\b", limpio):
            problemas.append("API obsoleta: " + api)
    for viejo in ("wait", "spawn", "delay"):
        if re.search(r"(?<![.:%s])\b" % "\\w" + viejo + r"\s*\(", limpio):
            problemas.append("usa %s() en vez de task.%s()" % (viejo, viejo))

    # WaitForChild sin timeout
    for m in re.finditer(r"WaitForChild\(([^)]*)\)", limpio):
        if "," not in m.group(1):
            problemas.append("WaitForChild sin timeout: " + m.group(0)[:48])

    conteos = {
        "lineas": src.count("\n") + 1,
        "bytes": len(src.encode("utf-8")),
        "function": n_func,
        "if": n_if,
        "do": n_do,
        "end": n_end,
    }
    return problemas, conteos


# ------------------------------------------------------------------- xml

def esc(t):
    return (t.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


class Arbol(object):
    def __init__(self):
        self.lineas = []
        self.n = 0

    def ref(self):
        r = "RBX%d" % self.n
        self.n += 1
        return r

    def abrir(self, clase, props, ind):
        pad = " " * ind
        self.lineas.append('%s<Item class="%s" referent="%s">'
                           % (pad, clase, self.ref()))
        self.lineas.append("%s  <Properties>" % pad)
        for tipo, nombre, valor in props:
            self.lineas.append('%s    <%s name="%s">%s</%s>'
                               % (pad, tipo, nombre, valor, tipo))
        self.lineas.append("%s  </Properties>" % pad)

    def cerrar(self, ind):
        self.lineas.append("%s</Item>" % (" " * ind))


def main():
    fuentes = {}
    for nombre in ("Servidor", "Cliente", "Datos", "Rig"):
        ruta = os.path.join(AQUI, nombre + ".lua")
        if not os.path.exists(ruta):
            print("FALTA %s" % ruta)
            return 1
        fuentes[nombre] = open(ruta, encoding="utf-8").read()

    print("=== REVISION DEL LUAU ===")
    print("%-10s %-7s %-8s %-9s %-5s %-5s %-5s %s"
          % ("archivo", "lineas", "bytes", "function", "if", "do", "end",
             "veredicto"))
    print("-" * 74)
    fallos = 0
    detalles = []
    for nombre in ("Servidor", "Rig", "Datos", "Cliente"):
        probs, c = revisar_lua(nombre, fuentes[nombre])
        estado = "OK" if not probs else "%d PROBLEMAS" % len(probs)
        if probs:
            fallos += 1
            detalles.append((nombre, probs))
        print("%-10s %-7d %-8d %-9d %-5d %-5d %-5d %s"
              % (nombre, c["lineas"], c["bytes"], c["function"],
                 c["if"], c["do"], c["end"], estado))
    print("-" * 74)
    for nombre, probs in detalles:
        print()
        print("  %s" % nombre)
        for p in probs:
            print("     - %s" % p)
    if fallos:
        print()
        print("No se genera el .rbxmx con problemas pendientes.")
        return 1
    print("los 4 fuentes pasan la revision estructural")
    print()

    a = Arbol()
    a.lineas.append('<?xml version="1.0" encoding="utf-8"?>')
    a.lineas.append(CAB)
    a.lineas.append('  <Meta name="ExplicitAutoJoints">true</Meta>')

    a.abrir("Folder", [
        ("string", "Name", "BancoDeAnimaciones"),
    ], 2)

    a.abrir("Script", [
        ("string", "Name", "Servidor"),
        ("ProtectedString", "Source", esc(fuentes["Servidor"])),
        ("bool", "Disabled", "false"),
    ], 4)
    a.cerrar(4)

    a.abrir("ScreenGui", [
        ("string", "Name", "Interfaz"),
        ("bool", "Enabled", "true"),
        ("bool", "ResetOnSpawn", "false"),
        ("bool", "IgnoreGuiInset", "true"),
        ("token", "ZIndexBehavior", "1"),
    ], 4)

    a.abrir("LocalScript", [
        ("string", "Name", "Cliente"),
        ("ProtectedString", "Source", esc(fuentes["Cliente"])),
        ("bool", "Disabled", "false"),
    ], 6)
    a.cerrar(6)

    for mod in ("Datos", "Rig"):
        a.abrir("ModuleScript", [
            ("string", "Name", mod),
            ("ProtectedString", "Source", esc(fuentes[mod])),
        ], 6)
        a.cerrar(6)

    a.cerrar(4)
    a.cerrar(2)
    a.lineas.append("</roblox>")

    texto = "\n".join(a.lineas) + "\n"
    open(SALIDA, "w", encoding="utf-8").write(texto)

    # ------------------------------------------------------- auditoria xml
    print("=== AUDITORIA DEL .RBXMX ===")
    try:
        raiz = ET.parse(SALIDA).getroot()
    except ET.ParseError as e:
        print("XML MAL FORMADO: %s" % e)
        return 1
    print("xml bien formado           si")

    items = list(raiz.iter("Item"))
    clases = {}
    for it in items:
        clases[it.get("class")] = clases.get(it.get("class"), 0) + 1
    refs = [it.get("referent") for it in items]
    print("instancias                 %d" % len(items))
    print("referentes duplicados      %d" % (len(refs) - len(set(refs))))
    for cl in sorted(clases):
        print("  %-22s %d" % (cl, clases[cl]))

    # el Source debe volver a salir identico al original
    ok_src = 0
    for it in items:
        pr = it.find("Properties")
        if pr is None:
            continue
        nom = None
        src = None
        for hijo in pr:
            if hijo.get("name") == "Name":
                nom = hijo.text
            if hijo.get("name") == "Source":
                src = hijo.text
        if nom in fuentes and src is not None:
            if src == fuentes[nom]:
                ok_src += 1
            else:
                print("  DIFIERE el Source de %s" % nom)
    print("fuentes que vuelven iguales %d de 4" % ok_src)

    crudo = open(SALIDA, encoding="utf-8").read()
    print("doble escapado (&amp;amp;)  %s"
          % ("si" if "&amp;amp;" in crudo else "no"))
    print("tamano                     %d bytes" % len(crudo.encode("utf-8")))
    print("archivo                    %s" % SALIDA)
    return 0 if ok_src == 4 else 1


if __name__ == "__main__":
    sys.exit(main())
