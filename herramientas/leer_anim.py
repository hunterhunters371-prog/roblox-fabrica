# -*- coding: utf-8 -*-
"""leer_anim.py -- extrae una animacion (KeyframeSequence) de un .rbxm
BINARIO y muestra sus valores reales: tiempos, angulos y DESPLAZAMIENTOS.

Uso: python leer_anim.py "dummy animacion de caminar.rbxm"

Decodificacion correcta del formato binario de Roblox:
  - i32/referentes: carriles de byte + zigzag + (referentes) acumulado
  - f32: carriles de byte + bit de signo rotado a la derecha
  - CFrame: primero POR CADA instancia un byte de tipo de rotacion
    (y 9 floats crudos si es 0x00), y DESPUES las posiciones como
    tres arreglos entrelazados X, Y, Z
"""

import math
import struct
import sys
from collections import Counter

try:
    import lz4.block
except ImportError:
    lz4 = None


# ------------------------------------------------------- lectura de bajo nivel
def rd_u32(b, o):
    return struct.unpack_from("<I", b, o)[0], o + 4


def rd_str(b, o):
    n, o = rd_u32(b, o)
    return b[o:o + n].decode("utf-8", "replace"), o + n


def lanes_u32(b, o, n):
    """n enteros sin signo: 4 carriles de byte, big-endian por elemento."""
    out = []
    for i in range(n):
        v = ((b[o + i] << 24) | (b[o + n + i] << 16) |
             (b[o + 2 * n + i] << 8) | b[o + 3 * n + i])
        out.append(v)
    return out, o + 4 * n


def zigzag(v):
    """Deshace el zigzag: los negativos van en los impares."""
    return (v >> 1) ^ (-(v & 1))


def inter_i32(b, o, n):
    crudos, o = lanes_u32(b, o, n)
    return [zigzag(v) for v in crudos], o


def inter_f32(b, o, n):
    """El bit de signo viaja al final; hay que rotarlo de vuelta."""
    crudos, o = lanes_u32(b, o, n)
    out = []
    for v in crudos:
        bits = ((v >> 1) | ((v & 1) << 31)) & 0xFFFFFFFF
        out.append(struct.unpack(">f", struct.pack(">I", bits))[0])
    return out, o


def acumula(vals):
    acc, out = 0, []
    for v in vals:
        acc += v
        out.append(acc)
    return out


# matrices de rotacion predefinidas (los tipos != 0x00)
def rot_predef(idx):
    """Los 24 giros de 90 grados. Se generan por construccion."""
    ejes = [(1, 0, 0), (0, 1, 0), (0, 0, 1),
            (-1, 0, 0), (0, -1, 0), (0, 0, -1)]

    def cruz(a, b):
        return (a[1] * b[2] - a[2] * b[1],
                a[2] * b[0] - a[0] * b[2],
                a[0] * b[1] - a[1] * b[0])

    tabla = []
    for ejeX in ejes:
        for ejeY in ejes:
            if abs(ejeX[0] * ejeY[0] + ejeX[1] * ejeY[1] +
                   ejeX[2] * ejeY[2]) > 0.5:
                continue
            ejeZ = cruz(ejeX, ejeY)
            tabla.append((ejeX, ejeY, ejeZ))
    i = idx - 2  # el 0x02 es el primero de la tabla
    if 0 <= i < len(tabla):
        x, y, z = tabla[i]
        return ((x[0], y[0], z[0]), (x[1], y[1], z[1]), (x[2], y[2], z[2]))
    return ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def euler(m):
    """De matriz a angulos XYZ en grados (mismo orden que el conversor)."""
    sy = max(-1.0, min(1.0, m[0][2]))
    y = math.asin(sy)
    if abs(sy) < 0.9999:
        x = math.atan2(-m[1][2], m[2][2])
        z = math.atan2(-m[0][1], m[0][0])
    else:
        x = math.atan2(m[2][1], m[1][1])
        z = 0.0
    return tuple(round(math.degrees(a), 1) for a in (x, y, z))


# ---------------------------------------------------------------- el archivo
CLASES, INSTS, PADRES, AVISOS = {}, {}, [], []
T_STR, T_BOOL, T_I32, T_F32 = 0x01, 0x02, 0x03, 0x04
T_CFRAME, T_ENUM, T_REF = 0x10, 0x12, 0x13


def parse_inst(b):
    cid, o = rd_u32(b, 0)
    nombre, o = rd_str(b, o)
    marcador = b[o]
    o += 1
    if marcador:
        n, o = rd_u32(b, o)
        o += n
    count, o = rd_u32(b, o)
    ids, o = inter_i32(b, o, count)
    CLASES[cid] = nombre
    for i in acumula(ids):
        INSTS[i] = {"cls": nombre, "name": "?", "props": {}}


def parse_prop(b):
    cid, o = rd_u32(b, 0)
    prop, o = rd_str(b, o)
    tipo = b[o]
    o += 1
    ids = [i for i, d in INSTS.items() if d["cls"] == CLASES.get(cid)]
    n = len(ids)
    if n == 0:
        return
    try:
        if tipo == T_STR:
            vals = []
            for _ in range(n):
                s, o = rd_str(b, o)
                vals.append(s)
        elif tipo == T_BOOL:
            vals = [b[o + i] != 0 for i in range(n)]
        elif tipo == T_I32:
            vals, o = inter_i32(b, o, n)
        elif tipo == T_F32:
            vals, o = inter_f32(b, o, n)
        elif tipo == T_ENUM:
            vals, o = lanes_u32(b, o, n)
        elif tipo == T_REF:
            vals, o = inter_i32(b, o, n)
            vals = acumula(vals)
        elif tipo == T_CFRAME:
            # 1) rotaciones, una por instancia
            mats = []
            for _ in range(n):
                rt = b[o]
                o += 1
                if rt == 0x00:
                    f = struct.unpack_from("<9f", b, o)
                    o += 36
                    mats.append(((f[0], f[1], f[2]),
                                 (f[3], f[4], f[5]),
                                 (f[6], f[7], f[8])))
                else:
                    mats.append(rot_predef(rt))
            # 2) posiciones entrelazadas
            xs, o = inter_f32(b, o, n)
            ys, o = inter_f32(b, o, n)
            zs, o = inter_f32(b, o, n)
            vals = [{"pos": (xs[i], ys[i], zs[i]), "rot": mats[i]}
                    for i in range(n)]
        else:
            return
    except Exception as e:
        AVISOS.append("%s (tipo 0x%02X): %s" % (prop, tipo, str(e)[:50]))
        return
    for i, v in zip(ids, vals):
        INSTS[i]["props"][prop] = v
        if prop == "Name":
            INSTS[i]["name"] = v


def parse_prnt(b):
    o = 1
    count, o = rd_u32(b, o)
    hijos, o = inter_i32(b, o, count)
    padres, o = inter_i32(b, o, count)
    PADRES.extend(zip(acumula(hijos), acumula(padres)))


def cargar(ruta):
    d = open(ruta, "rb").read()
    if not d.startswith(b"<roblox!"):
        raise SystemExit("no es un .rbxm binario")
    o = 32
    while o < len(d):
        nombre = d[o:o + 4].decode("ascii", "replace")
        if nombre.startswith("END"):
            break
        clen, ulen = struct.unpack_from("<II", d, o + 4)
        o += 16
        carga = d[o:o + clen]
        o += clen
        plano = carga
        if lz4 is not None and clen and ulen:
            try:
                cand = lz4.block.decompress(carga, uncompressed_size=ulen)
                if len(cand) == ulen:
                    plano = cand
            except Exception:
                pass
        try:
            if nombre == "INST":
                parse_inst(plano)
            elif nombre == "PROP":
                parse_prop(plano)
            elif nombre == "PRNT":
                parse_prnt(plano)
        except Exception as e:
            AVISOS.append("chunk %s: %s" % (nombre, str(e)[:50]))


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else "dummy_caminar.rbxm"
    cargar(ruta)

    hijos_de = {}
    for h, p in PADRES:
        hijos_de.setdefault(p, []).append(h)

    print("\n=== %s ===" % ruta)
    print("instancias: %d" % len(INSTS))
    print("clases:", dict(Counter(x["cls"] for x in INSTS.values())))

    # -------------------------------------------------- la secuencia
    seqs = [i for i, d in INSTS.items() if d["cls"] == "KeyframeSequence"]
    if not seqs:
        print("no hay KeyframeSequence en el archivo")
        return 1
    sid = seqs[0]
    sec = INSTS[sid]
    print("\n--- animacion ---")
    print("nombre    :", sec["name"])
    print("loop      :", sec["props"].get("Loop"))
    print("prioridad :", sec["props"].get("Priority"))

    # keyframes con su tiempo
    kfs = []
    for k in hijos_de.get(sid, []):
        if INSTS[k]["cls"] != "Keyframe":
            continue
        t = INSTS[k]["props"].get("Time", 0.0)
        kfs.append((t, k))
    kfs.sort(key=lambda x: x[0])
    print("keyframes : %d" % len(kfs))
    if kfs:
        print("duracion  : %.2fs" % kfs[-1][0])

    # poses: recorrido en profundidad desde cada keyframe
    def poses_de(nodo, acc):
        for h in hijos_de.get(nodo, []):
            if INSTS[h]["cls"] == "Pose":
                cf = INSTS[h]["props"].get("CFrame")
                if cf:
                    acc[INSTS[h]["name"]] = cf
                poses_de(h, acc)
        return acc

    datos = []
    for t, k in kfs:
        datos.append((t, poses_de(k, {})))

    # ------------------------------------------- rangos por articulacion
    print("\n--- RANGOS por articulacion (grados | studs) ---")
    partes = sorted({p for _, ps in datos for p in ps})
    resumen = {}
    for p in partes:
        angs = [euler(ps[p]["rot"]) for _, ps in datos if p in ps]
        poss = [ps[p]["pos"] for _, ps in datos if p in ps]
        if not angs:
            continue
        rot_min = tuple(round(min(a[i] for a in angs), 1) for i in range(3))
        rot_max = tuple(round(max(a[i] for a in angs), 1) for i in range(3))
        pos_min = tuple(round(min(v[i] for v in poss), 2) for i in range(3))
        pos_max = tuple(round(max(v[i] for v in poss), 2) for i in range(3))
        resumen[p] = (rot_min, rot_max, pos_min, pos_max)
        desp = max(abs(v) for v in pos_min + pos_max)
        print("\n%s   (%d poses)" % (p, len(angs)))
        print("   rot  min %s   max %s" % (rot_min, rot_max))
        print("   pos  min %s   max %s   |desplazamiento max| = %.2f studs"
              % (pos_min, pos_max, desp))

    # ------------------------------------------------ muestra temporal
    print("\n--- MUESTRA (8 momentos del ciclo) ---")
    paso = max(1, len(datos) // 8)
    for t, ps in datos[::paso]:
        print("\nt = %.3fs" % t)
        for p in sorted(ps):
            e = euler(ps[p]["rot"])
            q = tuple(round(v, 2) for v in ps[p]["pos"])
            marca = "  <-- DESPLAZADO" if max(abs(v) for v in q) > 0.3 else ""
            print("   %-18s rot %-22s pos %s%s"
                  % (p, e, q, marca))

    if AVISOS:
        print("\n--- avisos ---")
        for a in AVISOS[:10]:
            print("  " + a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
