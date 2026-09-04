-- TIPO: ModuleScript
-- RUTA: Workspace > EntregaFinalV4 > Turnos
-- Solo el servidor crea y modifica estos estados. No contiene APIs de Roblox.

local Turnos = {}

Turnos.OPCIONES = {
    carga = { nombre = "CARGA", descripcion = "Entrega cajas. Mas carga, menos velocidad.", unidad = "cajas", metas = { 3, 9, 18 } },
    ruta = { nombre = "RUTA", descripcion = "Visita destinos distintos. Repetir no avanza.", unidad = "destinos", metas = { 2, 4, 6 } },
    express = { nombre = "EXPRESS", descripcion = "Completa pedidos urgentes antes de vencer.", unidad = "urgentes", metas = { 1, 3, 5 } },
}

local medallas = { "BRONCE", "PLATA", "ORO" }
local premios = { 30, 70, 120 }
local rangos = {
    { meta = 0, nombre = "APRENDIZ" },
    { meta = 120, nombre = "REPARTIDOR" },
    { meta = 360, nombre = "ESPECIALISTA" },
    { meta = 720, nombre = "LEYENDA" },
}

local function entero(valor, minimo, maximo)
    return type(valor) == "number" and valor == valor and valor >= minimo
        and valor <= maximo and valor == math.floor(valor)
end

function Turnos.nuevo()
    return {
        eleccion = "carga", idRonda = 0, activa = false,
        cajas = 0, destinos = 0, urgentes = 0,
        visitados = {}, entregasVistas = {}, reputacion = 0, ultimo = nil,
    }
end

function Turnos.elegir(estado, clave)
    if estado.activa or type(clave) ~= "string" or not Turnos.OPCIONES[clave] then
        return false
    end
    if estado.eleccion ~= clave then
        estado.cajas = 0
        estado.destinos = 0
        estado.urgentes = 0
        estado.visitados = {}
    end
    estado.eleccion = clave
    return true
end

function Turnos.iniciar(estado, idRonda)
    if not entero(idRonda, 1, 1000000000) or idRonda <= estado.idRonda then
        return false
    end
    estado.idRonda = idRonda
    estado.activa = true
    estado.cajas = 0
    estado.destinos = 0
    estado.urgentes = 0
    estado.visitados = {}
    estado.entregasVistas = {}
    return true
end

-- Id de ronda y de entrega impiden premios repetidos o de una ronda anterior.
function Turnos.registrar(estado, idRonda, idEntrega, cajas, pad, urgente)
    if not estado.activa or idRonda ~= estado.idRonda then
        return false
    end
    if not entero(idEntrega, 1, 1000000000) or estado.entregasVistas[idEntrega] then
        return false
    end
    if not entero(cajas, 1, 3) or not entero(pad, 1, 8) or type(urgente) ~= "boolean" then
        return false
    end
    estado.entregasVistas[idEntrega] = true
    estado.cajas = estado.cajas + cajas
    if not estado.visitados[pad] then
        estado.visitados[pad] = true
        estado.destinos = estado.destinos + 1
    end
    if urgente then
        estado.urgentes = estado.urgentes + 1
    end
    return true
end

function Turnos.valor(estado)
    if estado.eleccion == "ruta" then
        return estado.destinos
    elseif estado.eleccion == "express" then
        return estado.urgentes
    end
    return estado.cajas
end

function Turnos.nivel(estado)
    local valor = Turnos.valor(estado)
    local nivel = 0
    for indice, meta in ipairs(Turnos.OPCIONES[estado.eleccion].metas) do
        if valor >= meta then
            nivel = indice
        end
    end
    return nivel
end

function Turnos.rango(reputacion)
    local nombre = rangos[1].nombre
    local siguiente = nil
    for _, rango in ipairs(rangos) do
        if reputacion >= rango.meta then
            nombre = rango.nombre
        elseif not siguiente then
            siguiente = rango.meta
        end
    end
    return nombre, siguiente
end

function Turnos.resumen(estado)
    local opcion = Turnos.OPCIONES[estado.eleccion]
    local nivel = Turnos.nivel(estado)
    local rango, siguiente = Turnos.rango(estado.reputacion)
    return {
        eleccion = estado.eleccion,
        idRonda = estado.idRonda,
        nombre = opcion.nombre,
        descripcion = opcion.descripcion,
        unidad = opcion.unidad,
        valor = Turnos.valor(estado),
        meta = opcion.metas[3],
        siguienteMeta = opcion.metas[math.min(3, nivel + 1)],
        nivel = nivel,
        medalla = medallas[nivel] or "EN CAMINO",
        reputacion = estado.reputacion,
        rango = rango,
        siguienteRango = siguiente,
        ultimo = estado.ultimo,
    }
end

function Turnos.cerrar(estado, idRonda)
    if not estado.activa or idRonda ~= estado.idRonda then
        return false, 0
    end
    -- Cerrar antes de conceder: dos llamadas no pueden duplicar la recompensa.
    estado.activa = false
    local nivel = Turnos.nivel(estado)
    local premio = (premios[nivel] or 0) + math.min(30, estado.cajas * 2)
    estado.reputacion = estado.reputacion + premio
    estado.ultimo = {
        idRonda = idRonda, contrato = Turnos.OPCIONES[estado.eleccion].nombre,
        medalla = medallas[nivel] or "SIN MEDALLA", premio = premio,
        valor = Turnos.valor(estado), nivel = nivel,
    }
    return true, premio
end

return Turnos
