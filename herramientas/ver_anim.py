# -*- coding: utf-8 -*-
"""ver_anim.py  --  vista previa GIF de una animacion de personaje.

Uso:   python ver_anim.py baile.json [salida.gif] [--fps 15] [--ancho 460]

Dibuja un maniqui de bloques (R15 o R6) moviendose segun los keyframes del
JSON. Es una APROXIMACION para revisar el movimiento y los signos de los
ejes sin abrir Studio: el modelo real y la interpolacion exacta del motor
se ven en el Animation Editor.
"""

import argparse
import json
import math
import os
import sys

from PIL import Image, ImageDraw


# -------------------------------------------- rigs (studs, frente hacia +z)
# parte -> (size, centro en reposo, punto de articulacion en reposo, padre)
def rig_r15():
    return {
        "HumanoidRootPart": ((2, 1, 1),        (0, 2, 0),         None,                None),
        "LowerTorso":       ((2, 1, 1),        (0, 2.5, 0),       (0, 2, 0),           "HumanoidRootPart"),
        "UpperTorso":       ((2, 1.4, 1),      (0, 3.7, 0),       (0, 3, 0),           "LowerTorso"),
        "Head":             ((1.2, 1.1, 1.1),  (0, 4.85, 0),      (0, 4.4, 0),         "UpperTorso"),
        "LeftUpperArm":     ((0.9, 1, 0.9),    (-1.45, 3.7, 0),   (-1, 4, 0),          "UpperTorso"),
        "LeftLowerArm":     ((0.85, 1, 0.85),  (-1.45, 2.75, 0),  (-1.45, 3.2, 0),     "LeftUpperArm"),
        "LeftHand":         ((0.85, 0.6, 0.85),(-1.45, 2, 0),     (-1.45, 2.25, 0),    "LeftLowerArm"),
        "RightUpperArm":    ((0.9, 1, 0.9),    (1.45, 3.7, 0),    (1, 4, 0),           "UpperTorso"),
        "RightLowerArm":    ((0.85, 1, 0.85),  (1.45, 2.75, 0),   (1.45, 3.2, 0),      "RightUpperArm"),
        "RightHand":        ((0.85, 0.6, 0.85),(1.45, 2, 0),      (1.45, 2.25, 0),     "RightLowerArm"),
        "LeftUpperLeg":     ((0.9, 1.1, 0.9),  (-0.55, 1.45, 0),  (-0.55, 2, 0),       "LowerTorso"),
        "LeftLowerLeg":     ((0.85, 1, 0.85),  (-0.55, 0.6, 0),   (-0.55, 0.95, 0),    "LeftUpperLeg"),
        "LeftFoot":         ((0.85, 0.4, 1.1), (-0.55, 0.2, 0.1), (-0.55, 0.35, 0),    "LeftLowerLeg"),
        "RightUpperLeg":    ((0.9, 1.1, 0.9),  (0.55, 1.45, 0),   (0.55, 2, 0),        "LowerTorso"),
        "RightLowerLeg":    ((0.85, 1, 0.85),  (0.55, 0.6, 0),    (0.55, 0.95, 0),     "RightUpperLeg"),
        "RightFoot":        ((0.85, 0.4, 1.1), (0.55, 0.2, 0.1),  (0.55, 0.35, 0),     "RightLowerLeg"),
    }


def rig_r6():
    return {
        "HumanoidRootPart": ((2, 2, 1), (0, 2, 0),    None,           None),
        "Torso":            ((2, 2, 1), (0, 3, 0),    (0, 2, 0),      "HumanoidRootPart"),
        "Head":             ((2, 1, 1), (0, 4.5, 0),  (0, 4, 0),      "Torso"),
        "Left Arm":         ((1, 2, 1), (-1.5, 3, 0), (-1, 3.5, 0),   "Torso"),
        "Right Arm":        ((1, 2, 1), (1.5, 3, 0),  (1, 3.5, 0),    "Torso"),
        "Left Leg":         ((1, 2, 1), (-0.5, 1, 0), (-0.5, 2, 0),   "Torso"),
        "Right Leg":        ((1, 2, 1), (0.5, 1, 0),  (0.5, 2, 0),    "Torso"),
    }


RIGS = {"R15": rig_r15, "R6": rig_r6}


def colores(rig):
    amarillo = (245, 205, 48)
    azul, azul2 = (25, 125, 210), (20, 100, 170)
    verde, verde2 = (100, 180, 90), (80, 150, 70)
    if rig == "R6":
        return {"Torso": azul, "Head": amarillo,
                "Left Arm": amarillo, "Right Arm": amarillo,
                "Left Leg": verde, "Right Leg": verde}
    return {"UpperTorso": azul, "LowerTorso": azul2, "Head": amarillo,
            "LeftUpperArm": amarillo, "LeftLowerArm": amarillo,
            "LeftHand": amarillo, "RightUpperArm": amarillo,
            "RightLowerArm": amarillo, "RightHand": amarillo,
            "LeftUpperLeg": verde, "LeftLowerLeg": verde,
            "LeftFoot": verde2, "RightUpperLeg": verde,
            "RightLowerLeg": verde, "RightFoot": verde2}


# -------------------------------------------------------------- matrices
def mult(a, b):
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
        for i in range(3))


def mvec(m, v):
    return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2])


def suma(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def resta(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def rotacion(rx, ry, rz):
    ax, ay, az = math.radians(rx), math.radians(ry), math.radians(rz)
    cx, sx = math.cos(ax), math.sin(ax)
    cy, sy = math.cos(ay), math.sin(ay)
    cz, sz = math.cos(az), math.sin(az)
    mx = ((1, 0, 0), (0, cx, -sx), (0, sx, cx))
    my = ((cy, 0, sy), (0, 1, 0), (-sy, 0, cy))
    mz = ((cz, -sz, 0), (sz, cz, 0), (0, 0, 1))
    return mult(mult(mx, my), mz)


IDENT = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def tr(m):
    """Transpuesta (= inversa para matrices de rotacion)."""
    return tuple(tuple(m[j][i] for j in range(3)) for i in range(3))


# Marcos reales de las articulaciones R6: vienen rotados 90 grados de
# fabrica, por eso sus ejes no coinciden con los del mundo. R15 va directo.
JF_R6 = {
    "Right Arm": (0, 90, 0), "Right Leg": (0, 90, 0),
    "Left Arm": (0, -90, 0), "Left Leg": (0, -90, 0),
}


def marco_joint(rig_nom, parte):
    if rig_nom == "R6" and parte in JF_R6:
        return rotacion(*JF_R6[parte])
    return IDENT

# ---------------------------------------------------------------- camara
AZ, TILT = math.radians(28), math.radians(16)
CA, SA = math.cos(AZ), math.sin(AZ)
CT, ST = math.cos(TILT), math.sin(TILT)
LUZ = (0.35, 0.75, 0.56)


def a_vista(p):
    x, y, z = p
    x2 = x * CA + z * SA
    z2 = -x * SA + z * CA
    y2 = y * CT - z2 * ST
    z3 = y * ST + z2 * CT
    return x2, y2, z3


# ---------------------------------------------------------------- dibujo
SIGNOS = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
          (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
CARAS = [((0, 0, -1), (0, 3, 2, 1)), ((0, 0, 1), (4, 5, 6, 7)),
         ((-1, 0, 0), (0, 4, 7, 3)), ((1, 0, 0), (1, 2, 6, 5)),
         ((0, -1, 0), (0, 1, 5, 4)), ((0, 1, 0), (3, 7, 6, 2))]


def fk(rig, rig_nom, rot, desp=None):
    """Cinematica directa: matriz de rotacion y centro actual por parte."""
    M, C = {}, {}
    desp = desp or {}

    def calc(nombre):
        if nombre in M:
            return
        _size, centro, joint, padre = rig[nombre]
        if padre is None:
            M[nombre] = IDENT
            C[nombre] = centro
            return
        calc(padre)
        Mp, Cp = M[padre], C[padre]
        centro_padre = rig[padre][1]
        Rp = rot.get(nombre, IDENT)
        marco = marco_joint(rig_nom, nombre)
        Rp = mult(mult(marco, Rp), tr(marco))
        # la articulacion viaja con el padre
        Jw = suma(Cp, mvec(Mp, resta(joint, centro_padre)))
        M[nombre] = mult(Mp, Rp)
        # la parte gira alrededor de su articulacion
        C[nombre] = suma(Jw, mvec(M[nombre], resta(centro, joint)))
        # y se desplaza en el marco de la articulacion (rebote vertical)
        pos = desp.get(nombre)
        if pos:
            C[nombre] = suma(C[nombre], mvec(mult(Mp, marco), pos))

    for n in rig:
        calc(n)
    return M, C


def dibuja_frame(rig, rig_nom, cols, rot, W, H, E, desp=None):
    img = Image.new("RGB", (W, H), (240, 242, 246))
    d = ImageDraw.Draw(img)
    suelo = H * 0.80
    d.ellipse([W / 2 - 2.3 * E, suelo - 0.30 * E, W / 2 + 2.3 * E,
               suelo + 0.30 * E], fill=(213, 217, 226))
    M, C = fk(rig, rig_nom, rot, desp)
    caras = []
    for nombre, (size, centro, joint, padre) in rig.items():
        if nombre == "HumanoidRootPart":
            continue
        m, cw = M[nombre], C[nombre]
        hx, hy, hz = size[0] / 2.0, size[1] / 2.0, size[2] / 2.0
        esq = [suma(cw, mvec(m, (hx * gx, hy * gy, hz * gz)))
               for gx, gy, gz in SIGNOS]
        base = cols[nombre]
        for normal, idxs in CARAS:
            nv = a_vista(mvec(m, normal))
            if nv[2] <= 0.001:
                continue
            pts, prof = [], 0.0
            for i in idxs:
                vx, vy, vz = a_vista(esq[i])
                pts.append((W / 2 + vx * E, suelo - vy * E))
                prof += vz
            luz = 0.70 + 0.30 * max(0.0, nv[0] * LUZ[0] + nv[1] * LUZ[1]
                                    + nv[2] * LUZ[2])
            caras.append((prof / 4.0, pts,
                          tuple(min(255, int(c * luz)) for c in base)))
    caras.sort(key=lambda c: c[0])
    for _p, pts, col in caras:
        d.polygon(pts, fill=col)
    return img


# --------------------------------------------------------------- easing
def rebote(f):
    n1, d1 = 7.5625, 2.75
    if f < 1 / d1:
        return n1 * f * f
    if f < 2 / d1:
        f -= 1.5 / d1
        return n1 * f * f + 0.75
    if f < 2.5 / d1:
        f -= 2.25 / d1
        return n1 * f * f + 0.9375
    f -= 2.625 / d1
    return n1 * f * f + 0.984375


def elastica(f):
    if f <= 0 or f >= 1:
        return min(1.0, max(0.0, f))
    return 2 ** (-10 * f) * math.sin((f * 10 - 0.75) * (2 * math.pi / 3)) + 1


def easer(nombre):
    return {"rebote": rebote, "elastica": elastica,
            "instantaneo": lambda f: 0.0 if f < 1 else 1.0,
            "suave": lambda f: f * f * (3 - 2 * f)}.get(nombre,
                                                        lambda f: f)


def pose_en(kfs, t, ez):
    if t <= kfs[0][0]:
        return dict(kfs[0][1])
    if t >= kfs[-1][0]:
        return dict(kfs[-1][1])
    for (ta, pa), (tb, pb) in zip(kfs, kfs[1:]):
        if ta <= t <= tb:
            f = ez((t - ta) / (tb - ta))
            out = {}
            for parte in set(pa) | set(pb):
                va = tuple(pa.get(parte, (0, 0, 0)))
                vb = tuple(pb.get(parte, (0, 0, 0)))
                n = max(len(va), len(vb))
                va = va + (0.0,) * (n - len(va))
                vb = vb + (0.0,) * (n - len(vb))
                out[parte] = tuple(va[i] + (vb[i] - va[i]) * f
                                   for i in range(n))
            return out
    return dict(kfs[-1][1])


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(
        description="vista previa GIF de una animacion (JSON)")
    ap.add_argument("archivo")
    ap.add_argument("salida", nargs="?")
    ap.add_argument("--fps", type=int, default=15)
    ap.add_argument("--ancho", type=int, default=460)
    args = ap.parse_args()

    if not os.path.exists(args.archivo):
        print("no existe el archivo: %s" % args.archivo)
        return 2
    try:
        with open(args.archivo, encoding="utf-8") as fh:
            spec = json.load(fh)
    except json.JSONDecodeError as e:
        print("el JSON no se puede leer: %s" % e)
        return 1

    rig_nom = spec.get("rig", "R15")
    if rig_nom not in RIGS:
        print('rig "%s" no soportado. Rigs validos: R15, R6' % rig_nom)
        return 1
    rig = RIGS[rig_nom]()
    cols = colores(rig_nom)
    ez = easer(spec.get("easing", "suave"))

    kfs = []
    for k in spec.get("keyframes", []):
        if not isinstance(k, dict):
            continue
        try:
            t = float(k.get("t", 0))
        except (TypeError, ValueError):
            continue
        poses = {}
        for p, a in k.get("poses", {}).items():
            if p in rig and isinstance(a, list) and len(a) in (3, 6):
                try:
                    poses[p] = tuple(float(x) for x in a)
                except (TypeError, ValueError):
                    pass
        kfs.append((t, poses))
    kfs.sort(key=lambda k: k[0])
    if len(kfs) < 2:
        print("el JSON necesita al menos 2 keyframes con poses validas")
        return 1

    dur = kfs[-1][0]
    if dur <= 0:
        print("la duracion debe ser mayor que 0")
        return 1
    n = max(2, int(round(dur * args.fps)))
    W = args.ancho
    H = int(W * 1.15)
    E = W / 10.0

    cuadros = []
    for i in range(n):
        t = dur * i / float(n)
        grados = pose_en(kfs, t, ez)
        rot = {p: rotacion(*ang[:3]) for p, ang in grados.items()}
        desp = {p: ang[3:] for p, ang in grados.items() if len(ang) == 6}
        cuadros.append(dibuja_frame(rig, rig_nom, cols, rot, W, H, E, desp))

    salida = args.salida or os.path.splitext(args.archivo)[0] + ".gif"
    cuadros[0].save(salida, save_all=True, append_images=cuadros[1:],
                    duration=int(1000 / args.fps), loop=0, optimize=True)

    print("")
    print("OK  vista previa")
    print("    animacion : %s (%s, %.2fs)" % (spec.get("nombre", "?"),
                                              rig_nom, dur))
    print("    cuadros   : %d a %d fps" % (n, args.fps))
    print("    archivo   : %s" % os.path.abspath(salida))
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
