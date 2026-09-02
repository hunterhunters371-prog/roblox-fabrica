# -*- coding: utf-8 -*-
"""cinematica.py - cinematica directa de los rigs R6 y R15, y analisis de
fase medido en el mundo.

Por que existe este modulo
--------------------------
Comparar los numeros crudos de una pose izquierda contra la derecha NO dice
si los miembros alternan. En R6 la cadera y el hombro izquierdos llevan el
marco base espejado (euler(0,-90,0) frente a euler(0,+90,0)), asi que un
valor identico en ambos lados produce movimiento OPUESTO en el mundo. En R15
las articulaciones estan alineadas con los ejes, asi que ahi alternar exige
valores opuestos.

Las dos convenciones son correctas, cada una para su rig. La unica medida
valida es reconstruir la posicion de la punta del miembro y comparar
trayectorias.
"""

import math

import numpy as np

PI = math.pi
I = np.eye(4)


def trans(x, y, z):
    M = np.eye(4)
    M[:3, 3] = (x, y, z)
    return M


def _rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def _ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def euler(a, b, c):
    """Equivale a CFrame.fromEulerAnglesXYZ: Rx * Ry * Rz."""
    M = np.eye(4)
    M[:3, :3] = _rx(a) @ _ry(b) @ _rz(c)
    return M


# --------------------------------------------------------------- definiciones
# (nombre, padre, c0, c1, tamano)   identicas a Rig.lua

R6 = [
    ("HumanoidRootPart", None, None, None, (2, 2, 1)),
    ("Torso", "HumanoidRootPart",
     euler(-PI / 2, 0, PI), euler(-PI / 2, 0, PI), (2, 2, 1)),
    ("Head", "Torso",
     trans(0, 1, 0) @ euler(-PI / 2, 0, PI),
     trans(0, -0.5, 0) @ euler(-PI / 2, 0, PI), (2, 1, 1)),
    ("Right Arm", "Torso",
     trans(1, 0.5, 0) @ euler(0, PI / 2, 0),
     trans(-0.5, 0.5, 0) @ euler(0, PI / 2, 0), (1, 2, 1)),
    ("Left Arm", "Torso",
     trans(-1, 0.5, 0) @ euler(0, -PI / 2, 0),
     trans(0.5, 0.5, 0) @ euler(0, -PI / 2, 0), (1, 2, 1)),
    ("Right Leg", "Torso",
     trans(1, -1, 0) @ euler(0, PI / 2, 0),
     trans(0.5, 1, 0) @ euler(0, PI / 2, 0), (1, 2, 1)),
    ("Left Leg", "Torso",
     trans(-1, -1, 0) @ euler(0, -PI / 2, 0),
     trans(-0.5, 1, 0) @ euler(0, -PI / 2, 0), (1, 2, 1)),
]

R15 = [
    ("HumanoidRootPart", None, None, None, (2, 2, 1)),
    ("LowerTorso", "HumanoidRootPart", I, I, (2, 0.8, 1)),
    ("UpperTorso", "LowerTorso", trans(0, 0.4, 0), trans(0, -0.8, 0),
     (2, 1.6, 1)),
    ("Head", "UpperTorso", trans(0, 0.8, 0), trans(0, -0.6, 0),
     (1.2, 1.2, 1.2)),
    ("RightUpperArm", "UpperTorso", trans(1.45, 0.55, 0), trans(0, 0.6, 0),
     (0.9, 1.2, 0.9)),
    ("RightLowerArm", "RightUpperArm", trans(0, -0.6, 0), trans(0, 0.55, 0),
     (0.8, 1.1, 0.8)),
    ("RightHand", "RightLowerArm", trans(0, -0.55, 0), trans(0, 0.2, 0),
     (0.9, 0.4, 0.9)),
    ("LeftUpperArm", "UpperTorso", trans(-1.45, 0.55, 0), trans(0, 0.6, 0),
     (0.9, 1.2, 0.9)),
    ("LeftLowerArm", "LeftUpperArm", trans(0, -0.6, 0), trans(0, 0.55, 0),
     (0.8, 1.1, 0.8)),
    ("LeftHand", "LeftLowerArm", trans(0, -0.55, 0), trans(0, 0.2, 0),
     (0.9, 0.4, 0.9)),
    ("RightUpperLeg", "LowerTorso", trans(0.5, -0.4, 0), trans(0, 0.7, 0),
     (1, 1.4, 1)),
    ("RightLowerLeg", "RightUpperLeg", trans(0, -0.7, 0), trans(0, 0.65, 0),
     (0.9, 1.3, 0.9)),
    ("RightFoot", "RightLowerLeg", trans(0, -0.65, 0), trans(0, 0.2, 0),
     (1, 0.4, 1.1)),
    ("LeftUpperLeg", "LowerTorso", trans(-0.5, -0.4, 0), trans(0, 0.7, 0),
     (1, 1.4, 1)),
    ("LeftLowerLeg", "LeftUpperLeg", trans(0, -0.7, 0), trans(0, 0.65, 0),
     (0.9, 1.3, 0.9)),
    ("LeftFoot", "LeftLowerLeg", trans(0, -0.65, 0), trans(0, 0.2, 0),
     (1, 0.4, 1.1)),
]

TAM = {}
for _defs in (R6, R15):
    for _n, _p, _a, _b, _t in _defs:
        TAM[_n] = _t

# torso de referencia para medir en local
TRONCO = {"R6": "Torso", "R15": "LowerTorso"}

# pares izquierda/derecha por rig
PARES = {
    "R6": [("piernas", "Left Leg", "Right Leg"),
           ("brazos", "Left Arm", "Right Arm")],
    "R15": [("piernas", "LeftUpperLeg", "RightUpperLeg"),
            ("pantorrillas", "LeftLowerLeg", "RightLowerLeg"),
            ("pies", "LeftFoot", "RightFoot"),
            ("brazos", "LeftUpperArm", "RightUpperArm"),
            ("antebrazos", "LeftLowerArm", "RightLowerArm"),
            ("manos", "LeftHand", "RightHand")],
}

# eje del vaiven adelante/atras, por rig: R6 usa rz, R15 usa rx
EJE_VAIVEN = {"R6": 2, "R15": 0}


def definicion(rig):
    return R15 if rig == "R15" else R6


def poseCF(v):
    if not v:
        return I
    return trans(v[3], v[4], v[5]) @ euler(math.radians(v[0]),
                                            math.radians(v[1]),
                                            math.radians(v[2]))


def fk(defs, poses=None, base=None):
    """mundoHijo = mundoPadre * c0 * pose * c1:Inverse()"""
    mundo = {}
    base = I if base is None else base
    for nombre, padre, c0, c1, tam in defs:
        if padre is None:
            cf = base
        else:
            p = poses.get(nombre) if poses else None
            cf = mundo[padre] @ c0 @ poseCF(p) @ np.linalg.inv(c1)
        mundo[nombre] = cf
    return mundo


def punto(cf, local):
    v = np.array([local[0], local[1], local[2], 1.0])
    return (cf @ v)[:3]


def punta(mundo, art):
    """Extremo distal del miembro, en el mundo."""
    tam = TAM.get(art, (1, 2, 1))
    return punto(mundo[art], (0, -tam[1] / 2.0, 0))


def mas_bajo(defs, mundo):
    lo = 1e9
    for nombre, padre, c0, c1, tam in defs:
        if nombre == "HumanoidRootPart":
            continue
        cf = mundo[nombre]
        hx, hy, hz = tam[0] / 2.0, tam[1] / 2.0, tam[2] / 2.0
        for sx in (-hx, hx):
            for sy in (-hy, hy):
                for sz in (-hz, hz):
                    lo = min(lo, punto(cf, (sx, sy, sz))[1])
    return lo


# ------------------------------------------------------------ analisis fase

def _correlacion(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.std() < 1e-9 or b.std() < 1e-9:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def trayectorias(spec):
    """Para cada par, la coordenada de vaiven de la punta de cada miembro,
    medida en el sistema del torso para quitar el balanceo global."""
    rig = spec["rig"]
    defs = definicion(rig)
    tronco = TRONCO[rig]
    kfs = spec["keyframes"]

    # si el ciclo esta cerrado, el ultimo keyframe repite el primero
    muestras = kfs[:-1] if len(kfs) > 2 and _cerrado(kfs) else kfs

    salida = {}
    for etiqueta, izq, der in PARES.get(rig, []):
        vi, vd = [], []
        ok = True
        for kf in muestras:
            mundo = fk(defs, kf["poses"])
            if izq not in mundo or der not in mundo:
                ok = False
                break
            inv = np.linalg.inv(mundo[tronco])
            pi = punto(inv, punta(mundo, izq))
            pd = punto(inv, punta(mundo, der))
            vi.append(pi[2])
            vd.append(pd[2])
        if ok:
            salida[etiqueta] = (vi, vd)
    return salida


def _cerrado(kfs):
    a, b = kfs[0]["poses"], kfs[-1]["poses"]
    if set(a) != set(b):
        return False
    return all(a[k] == b[k] for k in a)


def analizar(spec):
    """Devuelve (defectos, fases) midiendo el mundo, no los numeros."""
    defectos = []
    fases = []
    for etiqueta, (vi, vd) in trayectorias(spec).items():
        r = _correlacion(vi, vd)
        amp = max(max(vi) - min(vi), max(vd) - min(vd))
        if r is None or amp < 0.15:
            fases.append((etiqueta, r, "sin vaiven apreciable"))
            continue
        if r > 0.5:
            fases.append((etiqueta, r, "EN FASE"))
            defectos.append(etiqueta + " en fase")
        elif r < -0.5:
            fases.append((etiqueta, r, "contrafase"))
        else:
            fases.append((etiqueta, r, "desfase parcial"))
    return defectos, fases


def estaticas(spec):
    kfs = spec["keyframes"]
    arts = set()
    for kf in kfs:
        arts |= set(kf["poses"])
    fuera = []
    for a in sorted(arts):
        vals = [tuple(kf["poses"][a]) for kf in kfs if a in kf["poses"]]
        if len(vals) >= 2 and len(set(vals)) == 1:
            fuera.append(a)
    return fuera


def variante_opuesta(spec):
    """Version DIDACTICA ROTA: niega el eje de vaiven del miembro izquierdo.

    Es el error tipico al portar una animacion de R15 a R6 (o al reves):
    'espejar los numeros'. Sirve para ensenar en pantalla como se ve una
    marcha con los dos miembros en fase.
    """
    rig = spec["rig"]
    eje = EJE_VAIVEN.get(rig, 2)
    izqs = [izq for _e, izq, _d in PARES.get(rig, [])]
    nuevos = []
    for kf in spec["keyframes"]:
        poses = {}
        for art, v in kf["poses"].items():
            w = list(v)
            if art in izqs:
                w[eje] = -w[eje]
            poses[art] = w
        nuevos.append({"t": kf["t"], "poses": poses})
    return nuevos
