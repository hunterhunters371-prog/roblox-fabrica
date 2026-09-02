# -*- coding: utf-8 -*-
"""gen_datos.py - convierte los 11 modelos de animaciones/ en Datos.lua.

El analisis de fase NO compara numeros crudos: delega en cinematica.py, que
reconstruye la posicion real de cada miembro. Ver la cabecera de ese modulo
para el motivo (marcos espejados en R6).

Ademas de los datos reales genera, para cada ciclo de locomocion, una
variante DIDACTICA ROTA con el eje de vaiven izquierdo negado. Sirve para
ponerla al lado del original en el juego y ver la diferencia entre una
marcha que alterna y una que mueve los dos miembros a la vez.
"""

import copy
import glob
import json
import os
import sys

import cinematica as C

AQUI = os.path.dirname(os.path.abspath(__file__))
ANIM = os.path.abspath(os.path.join(AQUI, "..", "animaciones"))
SALIDA = os.path.join(AQUI, "Datos.lua")

TITULOS = {
    "baile_r6": "Baile R6",
    "caminar_chulo_r6": "Caminar chulo R6",
    "caminar_r15": "Caminar epico R15",
    "caminar_r6": "Caminar epico R6",
    "caminar_vida_r15": "Caminar con vida R15",
    "caminar_vida_r6": "Caminar con vida R6",
    "correr_flujo_r6": "Correr con flujo R6",
    "correr_pro_r6": "Correr pro R6",
    "correr_ref_r6": "Correr referencia R6",
    "salto_r6": "Salto explosivo R6",
    "saludar_r6": "Saludar R6",
}


def norm(v):
    """Toda pose queda como 6 numeros: rx, ry, rz, px, py, pz."""
    w = list(v)
    while len(w) < 6:
        w.append(0)
    return [float(x) for x in w[:6]]


def cargar(ruta):
    with open(ruta, encoding="utf-8") as f:
        d = json.load(f)
    kfs = []
    for kf in d["keyframes"]:
        kfs.append({
            "t": float(kf["t"]),
            "poses": {a: norm(v) for a, v in kf["poses"].items()},
        })
    return {
        "rig": d["rig"],
        "nombre": d["nombre"],
        "loop": bool(d.get("loop", True)),
        "prioridad": d.get("prioridad", "accion"),
        "easing": d.get("easing", "suave"),
        "keyframes": kfs,
    }


def num(x):
    if x == int(x):
        return str(int(x))
    return ("%.4f" % x).rstrip("0").rstrip(".")


def lua_txt(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def lua_lista(xs):
    if not xs:
        return "{}"
    return "{" + ", ".join(lua_txt(x) for x in xs) + "}"


def lua_kfs(kfs, ind):
    pad = " " * ind
    out = ["{"]
    for kf in kfs:
        out.append("%s    {t = %s, poses = {" % (pad, num(kf["t"])))
        for art in sorted(kf["poses"]):
            v = kf["poses"][art]
            out.append("%s        [%s] = {%s},"
                       % (pad, lua_txt(art), ", ".join(num(x) for x in v)))
        out.append("%s    }}," % pad)
    out.append("%s}" % pad)
    return "\n".join(out)


def main():
    rutas = sorted(glob.glob(os.path.join(ANIM, "*.json")))
    if len(rutas) != 11:
        print("AVISO: esperaba 11 modelos, encontre %d" % len(rutas))
        for r in rutas:
            print("   " + os.path.basename(r))
        if not rutas:
            return 1

    filas = []
    bloques = []

    for ruta in rutas:
        ident = os.path.basename(ruta)[:-5]
        sp = cargar(ruta)
        rig = sp["rig"]
        kfs = sp["keyframes"]
        dur = kfs[-1]["t"]

        defectos, fases = C.analizar(sp)
        avisos_art = C.estaticas(sp)

        # Un salto o un saludo mueve los dos miembros a la vez a proposito.
        # La regla de contrafase solo aplica a ciclos de locomocion.
        es_ciclo = sp["loop"] and sp["prioridad"] == "movimiento"
        if not es_ciclo:
            defectos = []

        avisos = []
        for a in avisos_art:
            avisos.append(a + " declarada pero nunca cambia de valor")

        # variante rota solo para los ciclos que de verdad alternan
        hay_vaiven = any(v == "contrafase" for _e, _r, v in fases)
        roto = None
        if es_ciclo and hay_vaiven:
            sp2 = copy.deepcopy(sp)
            sp2["keyframes"] = C.variante_opuesta(sp)
            _d2, f2 = C.analizar(sp2)
            if any(v == "EN FASE" for _e, _r, v in f2):
                roto = sp2["keyframes"]

        fase_txt = " ".join(
            "%s=%s" % (e, "n/a" if r is None else "%+.2f" % r)
            for e, r, _v in fases)
        filas.append((ident, rig, len(kfs), dur, "si" if es_ciclo else "-",
                      len(defectos), len(avisos), "si" if roto else "-",
                      fase_txt))

        b = []
        b.append("    {")
        b.append("        id = %s," % lua_txt(ident))
        b.append("        titulo = %s," % lua_txt(TITULOS.get(ident, ident)))
        b.append("        nombre = %s," % lua_txt(sp["nombre"]))
        b.append("        rig = %s," % lua_txt(rig))
        b.append("        loop = %s," % ("true" if sp["loop"] else "false"))
        b.append("        prioridad = %s," % lua_txt(sp["prioridad"]))
        b.append("        easing = %s," % lua_txt(sp["easing"]))
        b.append("        duracion = %s," % num(dur))
        b.append("        ciclo = %s," % ("true" if es_ciclo else "false"))
        b.append("        defectos = %s," % lua_lista(defectos))
        b.append("        avisos = %s," % lua_lista(avisos))
        b.append("        fases = {")
        for e, r, v in fases:
            b.append("            {par = %s, r = %s, veredicto = %s},"
                     % (lua_txt(e),
                        "nil" if r is None else num(round(r, 3)),
                        lua_txt(v)))
        b.append("        },")
        b.append("        keyframes = %s," % lua_kfs(kfs, 8))
        if roto:
            b.append("        roto = %s," % lua_kfs(roto, 8))
        b.append("    },")
        bloques.append("\n".join(b))

    cab = [
        "-- TIPO: ModuleScript",
        "-- RUTA: PlayerGui > Interfaz > Datos",
        "--",
        "-- GENERADO POR gen_datos.py A PARTIR DE animaciones/*.json",
        "-- No editar a mano: se sobrescribe.",
        "--",
        "-- Cada pose son 6 numeros: rx, ry, rz, px, py, pz",
        "-- (grados y studs, tal como los guarda el repositorio).",
        "--",
        "-- El campo 'roto' es una variante DIDACTICA con el eje de vaiven",
        "-- izquierdo negado: NO es un arreglo, es el error a evitar.",
        "",
        "local D = {}",
        "",
        "D.convenciones = {",
        "    R6 = \"En R6 la cadera y el hombro izquierdos llevan el marco "
        "base espejado, asi que un valor IDENTICO en los dos lados produce "
        "movimiento OPUESTO en el mundo. Para que una marcha alterne, los "
        "dos miembros llevan el mismo numero.\",",
        "    R15 = \"En R15 las articulaciones estan alineadas con los ejes, "
        "asi que para alternar hay que poner valores OPUESTOS en cada "
        "lado.\",",
        "}",
        "",
        "D.animaciones = {",
    ]
    texto = "\n".join(cab) + "\n" + "\n".join(bloques) + "\n}\n\nreturn D\n"
    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write(texto)

    print("%-24s %-5s %-4s %-6s %-6s %-4s %-4s %-5s %s"
          % ("modelo", "rig", "kfs", "dur", "ciclo", "def", "avi", "roto",
             "correlacion de fase"))
    print("-" * 108)
    for f in filas:
        print("%-24s %-5s %-4d %-6s %-6s %-4d %-4d %-5s %s"
              % (f[0], f[1], f[2], num(f[3]), f[4], f[5], f[6], f[7], f[8]))
    print("-" * 108)
    print()
    print("defectos reales   : %d" % sum(f[5] for f in filas))
    print("avisos reales     : %d" % sum(f[6] for f in filas))
    print("variantes rotas   : %d" % sum(1 for f in filas if f[7] == "si"))
    print("llaves            : %d abren, %d cierran"
          % (texto.count("{"), texto.count("}")))
    print("salida            : %s  (%d bytes)"
          % (SALIDA, len(texto.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
