# -*- coding: utf-8 -*-
"""spec_anim.py  --  convierte un JSON simple en una animacion .rbxmx
(KeyframeSequence) lista para importar en Roblox Studio.

Uso:   python spec_anim.py baile.json

Misma filosofia que spec_a_rbxmx.py: la IA solo escribe tiempos y angulos;
este programa valida todo y escribe el XML de Roblox, que es donde la IA
siempre se equivoca:
  * solo articulaciones que existen en el rig elegido (R15 o R6)
  * tiempos en orden creciente, angulos acotados
  * easing y prioridad de listas cerradas
  * el arbol de poses se genera completo y con la jerarquia correcta

Si el JSON tiene fallos, los lista para copiarlos de vuelta a la IA.
"""

import json
import math
import os
import sys

# ------------------------------------------------------ arboles de poses
# Jerarquia de partes del rig (los nombres deben coincidir con las partes).
# La raiz (HumanoidRootPart) existe en el arbol pero no se anima.
R15 = {
    "HumanoidRootPart": {
        "LowerTorso": {
            "LeftUpperLeg": {"LeftLowerLeg": {"LeftFoot": {}}},
            "RightUpperLeg": {"RightLowerLeg": {"RightFoot": {}}},
            "UpperTorso": {
                "Head": {},
                "LeftUpperArm": {"LeftLowerArm": {"LeftHand": {}}},
                "RightUpperArm": {"RightLowerArm": {"RightHand": {}}},
            },
        }
    }
}

R6 = {
    "HumanoidRootPart": {
        "Torso": {
            "Head": {},
            "Left Arm": {},
            "Right Arm": {},
            "Left Leg": {},
            "Right Leg": {},
        }
    }
}

RIGS = {"R15": R15, "R6": R6}
RAIZ = "HumanoidRootPart"


def articulaciones(arbol, acc=None):
    if acc is None:
        acc = []
    for nombre, hijos in arbol.items():
        acc.append(nombre)
        articulaciones(hijos, acc)
    return acc


# nombre -> (EasingStyle token, EasingDirection token)
EASINGS = {
    "suave": (0, 2),        # Linear / InOut
    "lineal": (0, 1),       # Linear / Out
    "rebote": (4, 1),       # Bounce / Out
    "elastica": (2, 1),     # Elastic / Out
    "instantaneo": (1, 1),  # Constant / Out
}
LISTA_EASINGS = ", ".join(sorted(EASINGS))

PRIORIDADES = {"core": 0, "idle": 1, "movimiento": 2, "accion": 3}
LISTA_PRIORIDADES = ", ".join(sorted(PRIORIDADES))

MAX_KEYFRAMES = 40
MAX_DURACION = 30.0
MAX_ANGULO = 180.0
MAX_DESPLAZAMIENTO = 2.5   # studs; >1 = deformacion estilizada a proposito


# -------------------------------------------------------------- validacion
ERRORES = []


def err(msg):
    ERRORES.append(msg)


def pide(d, clave, tipo, donde):
    if clave not in d:
        err('%s falta la clave "%s".' % (donde, clave))
        return None
    v = d[clave]
    if not isinstance(v, tipo) or (tipo is int and isinstance(v, bool)):
        nombre = {str: "texto", int: "numero entero", float: "numero",
                  bool: "true o false", list: "lista", dict: "objeto"}.get(
                      tipo, str(tipo))
        err('%s.%s debe ser %s, no %r.' % (donde, clave, nombre, v))
        return None
    return v


def sin_markup(texto, donde):
    for mal in ("<", ">", "&"):
        if mal in texto:
            err('%s contiene "%s". No escribas etiquetas ni HTML en los '
                "textos." % (donde, mal))
            return


# ------------------------------------------------------------------- math
def rotacion_matriz(rx, ry, rz):
    """Euler XYZ en grados -> matriz 3x3 (filas)."""
    ax, ay, az = math.radians(rx), math.radians(ry), math.radians(rz)
    cx, sx = math.cos(ax), math.sin(ax)
    cy, sy = math.cos(ay), math.sin(ay)
    cz, sz = math.cos(az), math.sin(az)
    filas_x = ((1, 0, 0), (0, cx, -sx), (0, sx, cx))
    filas_y = ((cy, 0, sy), (0, 1, 0), (-sy, 0, cy))
    filas_z = ((cz, -sz, 0), (sz, cz, 0), (0, 0, 1))

    def mult(a, b):
        return tuple(
            tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
            for i in range(3))

    return mult(mult(filas_x, filas_y), filas_z)


# ------------------------------------------------------------------- XML
REF = [0]


def nref():
    r = "RBX%d" % REF[0]
    REF[0] += 1
    return r


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def f6(v):
    return ("%.6f" % float(v)).rstrip("0").rstrip(".") or "0"


def pose_xml(nombre, hijos, rotaciones, easing, depth):
    """Una pose por parte, anidadas segun el arbol del rig."""
    pad = "  " * depth
    vals = rotaciones.get(nombre, (0.0, 0.0, 0.0))
    rx, ry, rz = vals[:3]
    px, py, pz = tuple(vals[3:]) if len(vals) == 6 else (0.0, 0.0, 0.0)
    m = rotacion_matriz(rx, ry, rz)
    es_tok, ed_tok = easing
    out = ['%s<Item class="Pose" referent="%s">' % (pad, nref())]
    out.append('%s  <Properties>' % pad)
    out.append('%s    <string name="Name">%s</string>' % (pad, esc(nombre)))
    cf = ['%s    <CoordinateFrame name="CFrame">' % pad,
          '%s      <X>%s</X><Y>%s</Y><Z>%s</Z>'
          % (pad, f6(px), f6(py), f6(pz))]
    for i, fila in enumerate(m):
        for j, val in enumerate(fila):
            cf.append('%s      <R%d%d>%s</R%d%d>' % (pad, i, j, f6(val), i, j))
    cf.append('%s    </CoordinateFrame>' % pad)
    out.append("".join(cf))
    out.append('%s    <token name="EasingStyle">%d</token>' % (pad, es_tok))
    out.append('%s    <token name="EasingDirection">%d</token>' % (pad, ed_tok))
    out.append('%s    <float name="Weight">1</float>' % pad)
    out.append('%s  </Properties>' % pad)
    for hijo, nietos in hijos.items():
        out.append(pose_xml(hijo, nietos, rotaciones, easing, depth + 1))
    out.append('%s</Item>' % pad)
    return "\n".join(out)


def keyframe_xml(t, poses, arbol, easing, depth=1):
    pad = "  " * depth
    raiz = next(iter(arbol))
    out = ['%s<Item class="Keyframe" referent="%s">' % (pad, nref())]
    out.append('%s  <Properties>' % pad)
    out.append('%s    <float name="Time">%s</float>' % (pad, f6(t)))
    out.append('%s  </Properties>' % pad)
    out.append(pose_xml(raiz, arbol[raiz], poses, easing, depth + 1))
    out.append('%s</Item>' % pad)
    return "\n".join(out)


# ------------------------------------------------------------------ carga
def main():
    if len(sys.argv) < 2:
        print("uso: python spec_anim.py baile.json")
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

    # --- campos de raiz
    rig = pide(spec, "rig", str, "raiz") or ""
    nombre = pide(spec, "nombre", str, "raiz") or ""
    loop = spec.get("loop", True)
    prioridad = spec.get("prioridad", "accion")
    easing_nom = spec.get("easing", "suave")

    sin_markup(nombre, "raiz.nombre")
    if len(nombre) > 40:
        err("raiz.nombre tiene %d caracteres y solo caben 40."
            % len(nombre))

    if rig not in RIGS:
        err('raiz.rig = "%s" no existe. Rigs validos: R15, R6' % rig)
    if not isinstance(loop, bool):
        err("raiz.loop debe ser true o false.")
    if prioridad not in PRIORIDADES:
        err('raiz.prioridad = "%s" no existe.\n     Prioridades validas: %s'
            % (prioridad, LISTA_PRIORIDADES))
    if easing_nom not in EASINGS:
        err('raiz.easing = "%s" no existe.\n     Easings validos: %s'
            % (easing_nom, LISTA_EASINGS))

    arbol = RIGS.get(rig, R15)
    partes = articulaciones(arbol)
    animables = [p for p in partes if p != RAIZ]

    # --- keyframes
    kfs = pide(spec, "keyframes", list, "raiz") or []
    if kfs and not (2 <= len(kfs) <= MAX_KEYFRAMES):
        err("raiz.keyframes tiene %d. Debe tener entre 2 y %d."
            % (len(kfs), MAX_KEYFRAMES))
        kfs = []

    t_anterior = -1.0
    se_mueve_algo = False
    for i, k in enumerate(kfs):
        donde = "raiz.keyframes[%d]" % i
        if not isinstance(k, dict):
            err("%s debe ser un objeto { ... }." % donde)
            continue
        t = k.get("t")
        if not isinstance(t, (int, float)) or isinstance(t, bool):
            err('%s.t debe ser numero (segundos), no %r.' % (donde, t))
            continue
        if t < 0:
            err("%s.t = %s. No puede ser negativo." % (donde, t))
        elif t <= t_anterior:
            err("%s.t = %s. Los tiempos deben ir en orden creciente "
                "(el anterior era %s)." % (donde, t, t_anterior))
        t_anterior = t

        poses = k.get("poses")
        if not isinstance(poses, dict):
            err('%s falta la clave "poses" (un objeto articulacion -> '
                "[x, y, z])." % donde)
            continue
        if not poses:
            err("%s.poses esta vacio. Al menos una articulacion debe "
                "moverse." % donde)
        for parte, ang in poses.items():
            dp = "%s.poses.%s" % (donde, parte)
            if parte == RAIZ:
                err("%s: no se anima la raiz (HumanoidRootPart). "
                    "Anima las demas articulaciones." % dp)
                continue
            if parte not in partes:
                err('%s no existe en el rig %s.\n     Articulaciones '
                    "validas: %s" % (dp, rig, ", ".join(animables)))
                continue
            if (not isinstance(ang, list) or len(ang) not in (3, 6)
                    or any(not isinstance(a, (int, float))
                           or isinstance(a, bool) for a in ang)):
                err("%s debe ser [x, y, z] en grados, o [x, y, z, px, py, "
                    "pz] con desplazamiento en studs. No %r." % (dp, ang))
                continue
            for a in ang[:3]:
                if abs(a) > MAX_ANGULO:
                    err("%s tiene %s grados. Maximo +/-%d."
                        % (dp, a, int(MAX_ANGULO)))
                    break
            for a in ang[3:]:
                if abs(a) > MAX_DESPLAZAMIENTO:
                    err("%s desplaza %s studs. Maximo +/-%.1f."
                        % (dp, a, MAX_DESPLAZAMIENTO))
                    break
            if any(a != 0 for a in ang):
                se_mueve_algo = True

    if kfs and t_anterior > MAX_DURACION:
        err("la animacion dura %ss. Maximo %ss." % (t_anterior,
                                                    int(MAX_DURACION)))
    if kfs and not se_mueve_algo:
        err("ninguna articulacion se mueve: todas las poses son [0, 0, 0].")

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
    easing = EASINGS[easing_nom]
    cuerpo = []
    for k in kfs:
        cuerpo.append(keyframe_xml(k["t"], k["poses"], arbol, easing))

    xml = ('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" '
           'version="4">\n'
           '<Item class="KeyframeSequence" referent="%s">\n'
           '  <Properties>\n'
           '    <string name="Name">%s</string>\n'
           '    <bool name="Loop">%s</bool>\n'
           '    <token name="Priority">%d</token>\n'
           '    <float name="AuthoredHipHeight">0</float>\n'
           '  </Properties>\n'
           '%s\n'
           '</Item>\n'
           '</roblox>\n'
           % (nref(), esc(nombre), "true" if loop else "false",
              PRIORIDADES[prioridad], "\n".join(cuerpo)))

    salida = os.path.splitext(os.path.abspath(ruta))[0] + ".rbxmx"
    with open(salida, "w", encoding="utf-8") as fh:
        fh.write(xml)

    movidas = sorted({p for k in kfs for p, a in k["poses"].items()
                      if any(x != 0 for x in a)})
    print("")
    print("OK  el JSON es valido")
    print("    animacion   : %s (%s)" % (nombre, rig))
    print("    keyframes   : %d, duracion %.2fs" % (len(kfs), t_anterior))
    print("    articulac.  : %d en movimiento" % len(movidas))
    print("    archivo     : %s" % salida)
    print("")
    print("En Studio: abre un Dummy (%s), Animation Editor, y arrastra el" % rig)
    print(".rbxmx a su carpeta AnimSaves (o Insert from File ahi mismo).")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
