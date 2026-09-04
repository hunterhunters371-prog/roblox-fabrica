"""Pruebas locales: Lua 5.4 para logica pura, NO sustituye Roblox Studio."""
from pathlib import Path
import ctypes
import ctypes.util
import hashlib
import json
import xml.etree.ElementTree as ET

AQUI = Path(__file__).resolve().parent
biblioteca = ctypes.util.find_library("lua-5.4") or ctypes.util.find_library("lua5.4")
if not biblioteca:
    raise SystemExit("Falta la biblioteca Lua 5.4. Las pruebas no se han ejecutado.")
lua = ctypes.CDLL(biblioteca)
lua.luaL_newstate.restype = ctypes.c_void_p
lua.luaL_openlibs.argtypes = [ctypes.c_void_p]
lua.luaL_loadbufferx.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p]
lua.luaL_loadbufferx.restype = ctypes.c_int
lua.lua_pcallk.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_longlong, ctypes.c_void_p]
lua.lua_pcallk.restype = ctypes.c_int
lua.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_size_t)]
lua.lua_tolstring.restype = ctypes.c_char_p
lua.lua_close.argtypes = [ctypes.c_void_p]


def comprobar(texto, nombre, ejecutar=False):
    estado = lua.luaL_newstate()
    lua.luaL_openlibs(estado)
    try:
        datos = texto.encode("utf-8")
        codigo = lua.luaL_loadbufferx(estado, datos, len(datos), nombre.encode(), None)
        if not codigo and ejecutar:
            codigo = lua.lua_pcallk(estado, 0, 0, 0, 0, None)
        if codigo:
            raise AssertionError(nombre + ": " + lua.lua_tolstring(estado, -1, None).decode())
    finally:
        lua.lua_close(estado)


fuentes = {p.stem: p.read_text() for p in (AQUI / "generado").glob("*.lua")}
assert set(fuentes) == {"Servidor", "Cliente", "Config", "Turnos"}
for nombre, texto in fuentes.items():
    comprobar(texto, nombre)
    assert texto.isascii(), nombre + " contiene caracteres no ASCII"
    print("SINTAXIS LUA 5.4 + ASCII: " + nombre, flush=True)

modulo = (AQUI / "Turnos.lua").read_text()
pruebas = (AQUI / "Turnos.spec.lua").read_text()
comprobar("local T = (function()\n" + modulo + "\nend)()\n" + pruebas, "contratos", True)

# Ejecutar las funciones reales de entrega y recogida con servicios simulados.
# No simula Touched, replicacion, fisica ni renderizado.
servidor = fuentes["Servidor"]
inicio = servidor.index("local function cercaDe(")
fin = servidor.index("\ntable.insert(conexiones, almacen.Touched", inicio)
funciones = servidor[inicio:fin]
preparar = r'''
local Turnos = T
local ahora = 5
local workspace = { GetServerTimeNow = function() return ahora end }
local vector = {}
vector.__sub = function(a,b) return { Magnitude = math.abs(a.valor-b.valor) } end
local function pos(n) return setmetatable({valor=n},vector) end
local salud = { Health = 100 }
local raiz = { Position = pos(0) }
local personaje = {
    FindFirstChild = function() return raiz end,
    FindFirstChildOfClass = function() return salud end,
}
local jugador = { Character = personaje }
local ronda = { activa = true, finaliza = 90, ritmo = 1, id = 1 }
local Config = { CAJAS_MAXIMAS = 3, ENFRIAMIENTO_TOQUE = 0.3,
    PUNTOS_POR_CAJA = 60, BONUS_LOTE = 45, BONUS_COMBO = 0.25,
    COMBO_MAXIMO = 6, SEGUNDOS_COMBO = 12 }
local almacen = { Position = pos(0) }
local puntos = { { Position = pos(0) } }
local s, p
local function reiniciar()
    ahora = 5
    raiz.Position = pos(0)
    salud.Health = 100
    ronda.activa = true
    s = { cajas = 3, ultimoToque = 0, comboVence = 0, combo = 0,
        puntos = 0, entregas = 0, turno = T.nuevo() }
    T.iniciar(s.turno, 1)
    p = { id = 1, pad = 1, vence = 10, urgente = false, valor = 1 }
end
local function estadoDe() return s end
local function pedidoDePad() return 1, p end
local function quitarCajas() end
local function dibujarCajas() end
local function aplicarMovimiento() end
local function quitarPedido() p = nil end
local function nuevoPedido() end
local function avisar() end
local Jugadores = { GetPlayers = function() return {} end }
'''
casos = r'''
local total = 0
local function caso(nombre, cambia, cajasFinales, puntosFinales, avance)
    reiniciar()
    cambia()
    entregar(jugador, personaje, 1)
    assert(s.cajas == cajasFinales, nombre .. " cajas")
    assert(s.puntos == puntosFinales, nombre .. " puntos")
    assert(s.turno.cajas == avance, nombre .. " contrato")
    total = total + 1
    print("OK servidor: " .. nombre)
end
caso("entrega valida", function() end, 0, 270, 3)
caso("vencida en el instante exacto", function() ahora = 10 end, 3, 0, 0)
caso("ronda terminada en el instante exacto", function() ahora = 90 end, 3, 0, 0)
caso("jugador demasiado lejos", function() raiz.Position = pos(23) end, 3, 0, 0)
caso("jugador muerto", function() salud.Health = 0 end, 3, 0, 0)
caso("sin carga", function() s.cajas = 0 end, 0, 0, 0)
caso("sin ronda activa", function() ronda.activa = false end, 3, 0, 0)
caso("entrega ya registrada", function() T.registrar(s.turno, 1, 1, 3, 1, false) end, 3, 0, 3)
caso("enfriamiento de toque", function() s.ultimoToque = 4.9 end, 3, 0, 0)
reiniciar()
s.cajas = 0
recoger(jugador, personaje)
assert(s.cajas == 1)
recoger(jugador, personaje)
assert(s.cajas == 1)
total = total + 1
print("OK servidor: recogida con antirrebote")
print("PRUEBAS DE INTEGRACION SIMULADA: " .. total)
'''
comprobar("local T = (function()\n" + modulo + "\nend)()\n" + preparar + funciones + casos, "entregas", True)

raiz = ET.parse(AQUI / "generado/EntregaFinalV4-Experimental.rbxmx").getroot()
recuperadas = {}
for item in raiz.iter("Item"):
    src = item.find("Properties/ProtectedString[@name='Source']")
    if src is not None:
        recuperadas[item.find("Properties/string[@name='Name']").text] = src.text
assert recuperadas == fuentes
manifiesto = json.loads((AQUI / "generado/SHA256.json").read_text())
for nombre, firma in manifiesto.items():
    assert hashlib.sha256((AQUI / "generado" / nombre).read_bytes()).hexdigest() == firma
print("XML: 4 fuentes identicas; SHA256: todas las firmas correctas")
print("PENDIENTE: compilador Luau, Play Solo, dos clientes, R6/R15, HUD y guardado en Roblox.")
