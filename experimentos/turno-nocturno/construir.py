"""Genera una copia experimental desde el paquete V3; nunca modifica el original."""
from pathlib import Path
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET

AQUI = Path(__file__).resolve().parent
BASE_SHA256 = "bc7b1cfbfb010a16346a2b99c18c69446bf65ae5a5940ea9769f3c1b1cf57e77"


def construir(base, salida):
    datos = base.read_bytes()
    if hashlib.sha256(datos).hexdigest() != BASE_SHA256:
        raise ValueError("La base no es la V3 esperada. No aplicar sobre cambios nuevos de Studio.")
    if salida.resolve() == base.parent.resolve():
        raise ValueError("Usar otra carpeta de salida para conservar la base.")
    raiz = ET.fromstring(datos)
    carpeta = raiz.find("Item")
    if carpeta is None:
        raise ValueError("Falta el contenedor del juego")
    fuentes = {}
    nodos = {}
    for item in raiz.iter("Item"):
        nombre = item.find("Properties/string[@name='Name']")
        fuente = item.find("Properties/ProtectedString[@name='Source']")
        if nombre is not None and fuente is not None:
            fuentes[nombre.text] = fuente.text or ""
            nodos[nombre.text] = fuente
    if set(fuentes) != {"Servidor", "Cliente", "Config"}:
        raise ValueError("Se esperaba la base de tres scripts, sin reemplazos desconocidos")
    cambios = []

    def cambiar(nombre, antes, despues):
        if fuentes[nombre].count(antes) != 1:
            raise ValueError("Ancla no unica en " + nombre + ": " + antes[:70])
        fuentes[nombre] = fuentes[nombre].replace(antes, despues, 1)
        cambios.append({"archivo": nombre, "antes": antes, "despues": despues})

    cambiar("Config", "Workspace > EntregaFinalV3", "Workspace > EntregaFinalV4")
    cambiar("Config", 'Config.LEMA = "TRES PEDIDOS. UNA ESPALDA. NOVENTA SEGUNDOS."',
            'Config.LEMA = "TURNO NOCTURNO. TU CONTRATO, TU RUTA."')
    cambiar("Config", "Config.SEGUNDOS_DESCANSO = 12", "Config.SEGUNDOS_DESCANSO = 20")
    cambiar("Config", 'Config.CLAVE_DATASTORE = "EntregaFinalV3_1"',
            'Config.CLAVE_DATASTORE = "EntregaFinalV4_Experimental_1"')
    cambiar("Config", "    empezar = true,", "    empezar = true,\n    contrato_carga = true,\n    contrato_ruta = true,\n    contrato_express = true,")

    cambiar("Servidor", "Workspace > EntregaFinalV3", "Workspace > EntregaFinalV4")
    cambiar("Servidor", "local carpeta = script.Parent", '''local carpeta = script.Parent
for _, otra in ipairs(workspace:GetChildren()) do
    if otra ~= carpeta and otra.Name:match("^EntregaFinal") then
        local servidor = otra:FindFirstChild("Servidor")
        if servidor and servidor:IsA("Script") and servidor.Enabled then
            warn("Turno Nocturno: mueve la version anterior a ServerStorage antes de probar.")
            return
        end
    end
end
local moduloTurnos = carpeta:WaitForChild("Turnos", 10)
if not moduloTurnos then
    warn("Turno Nocturno: falta el modulo Turnos")
    return
end
local Turnos = require(moduloTurnos)''')
    cambiar("Servidor", "    viejosRemotos:Destroy()", '''    warn("Turno Nocturno: ya hay otra version activa; no reemplazo sus remotos.")
    return''')
    cambiar("Servidor", "local pedidos = {}\nlocal ronda = {", "local pedidos = {}\nlocal secuenciaPedido = 0\nlocal ronda = {\n    id = 0,")
    cambiar("Servidor", 'if objeto:IsA("SpawnLocation") then', 'if objeto:IsA("SpawnLocation") and objeto.Enabled then')
    cambiar("Servidor", 'almacenDatos:SetAsync("mejor_" .. jugador.UserId, valor)', '''almacenDatos:UpdateAsync("mejor_" .. jugador.UserId, function(anterior)
            return math.max(type(anterior) == "number" and anterior or 0, valor)
        end)''')
    cambiar("Servidor", "            propias = {},", "            propias = {},\n            turno = Turnos.nuevo(),")
    cambiar("Servidor", "local function listaPedidos()", "local function listaPedidos(estado)")
    cambiar("Servidor", "            posicion = puntos[pedido.pad].Position,", "            posicion = puntos[pedido.pad].Position,\n            indice = pedido.pad,\n            nuevoDestino = not estado.turno.visitados[pedido.pad],")
    cambiar("Servidor", "        pedidos = listaPedidos(),", "        pedidos = listaPedidos(estado),\n        turno = Turnos.resumen(estado.turno),")
    cambiar("Servidor", "    local urgente = math.random() < Config.PROBABILIDAD_URGENTE", '''    local hayUrgente = false
    for _, activo in ipairs(pedidos) do
        if activo.urgente and activo.vence > ahora then
            hayUrgente = true
        end
    end
    local urgente = not hayUrgente or math.random() < Config.PROBABILIDAD_URGENTE
    secuenciaPedido = secuenciaPedido + 1''')
    cambiar("Servidor", "    local pedido = {\n        pad = indice,", "    local pedido = {\n        id = secuenciaPedido,\n        pad = indice,")
    cambiar("Servidor", "local function recoger(jugador, personaje)", '''local function cercaDe(personaje, parte)
    local raizViva = personaje and personaje:FindFirstChild("HumanoidRootPart")
    local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
    return raizViva and humanoide and humanoide.Health > 0
        and (raizViva.Position - parte.Position).Magnitude <= 22
end

local function recoger(jugador, personaje)''')
    cambiar("Servidor", '''local function recoger(jugador, personaje)
    local estado = estadoDe(jugador)
    local ahora = workspace:GetServerTimeNow()
    if not ronda.activa then''', '''local function recoger(jugador, personaje)
    local estado = estadoDe(jugador)
    local ahora = workspace:GetServerTimeNow()
    if not ronda.activa or ahora >= ronda.finaliza or not cercaDe(personaje, almacen) then''')
    cambiar("Servidor", '''local function entregar(jugador, personaje, indice)
    local estado = estadoDe(jugador)
    local ahora = workspace:GetServerTimeNow()
    if not ronda.activa then''', '''local function entregar(jugador, personaje, indice)
    local estado = estadoDe(jugador)
    local ahora = workspace:GetServerTimeNow()
    if not ronda.activa or ahora >= ronda.finaliza or not cercaDe(personaje, puntos[indice]) then''')
    cambiar("Servidor", '''    if not pedido then
        return
    end
    estado.ultimoToque = ahora''', '''    if not pedido or pedido.vence <= ahora then
        return
    end
    if not Turnos.registrar(estado.turno, ronda.id, pedido.id, estado.cajas, indice, pedido.urgente) then
        return
    end
    estado.ultimoToque = ahora''')
    cambiar("Servidor", "local function terminarRonda()\n    ronda.activa = false", '''local function terminarRonda()
    if not ronda.activa then
        return
    end
    ronda.activa = false''')
    cambiar("Servidor", '''        local estado = estadoDe(jugador)
        quitarCajas(jugador.Character)''', '''        local estado = estadoDe(jugador)
        Turnos.cerrar(estado.turno, ronda.id)
        estado.deslizando = false
        estado.deslizaHasta = 0
        quitarCajas(jugador.Character)''')
    cambiar("Servidor", "            guardarMejor(jugador, estado.mejor)", "            task.spawn(guardarMejor, jugador, estado.mejor)")
    cambiar("Servidor", '''local function empezarRonda()
    local ahora = workspace:GetServerTimeNow()''', '''local function empezarRonda()
    local ahora = workspace:GetServerTimeNow()
    ronda.id = ronda.id + 1''')
    cambiar("Servidor", '''        estado.puntos = 0
        estado.combo = 0''', '''        Turnos.iniciar(estado.turno, ronda.id)
        estado.deslizando = false
        estado.deslizaHasta = 0
        estado.deslizaLibre = 0
        estado.ultimaPos = nil
        estado.puntos = 0
        estado.combo = 0''')
    cambiar("Servidor", '''    if accion == "empezar" then
        if ronda.activa then
            return
        end
        empezarRonda()''', '''    if accion:sub(1, 9) == "contrato_" then
        if ronda.activa then
            return
        end
        if Turnos.elegir(estado.turno, accion:sub(10)) then
            avisar(jugador, "CONTRATO: " .. Turnos.OPCIONES[estado.turno.eleccion].nombre, nil)
        end
    elseif accion == "empezar" then
        if ronda.activa then
            return
        end
        if ahora < ronda.finaliza - Config.SEGUNDOS_DESCANSO + 8 then
            avisar(jugador, "PRIMERO ELIGE CONTRATO: 1 CARGA / 2 RUTA / 3 EXPRESS", nil)
            return
        end
        empezarRonda()''')
    cambiar("Servidor", '''local function entra(jugador)
    local estado = estadoDe(jugador)''', '''local function entra(jugador)
    local estado = estadoDe(jugador)
    if ronda.activa then
        Turnos.iniciar(estado.turno, ronda.id)
    end''')
    cambiar("Servidor", "    estado.mejor = cargarMejor(jugador)", "    estado.mejor = cargarMejor(jugador)\n    if not jugador.Parent then\n        return\n    end")

    cambiar("Cliente", "-- ------------------------------------------------- brujula y panel de abajo", '''-- El contrato ocupa el panel existente: no se anade otra capa sobre el mapa.
local guiContrato = { botones = {}, nivel = 0, ronda = 0 }
do
    panelTabla.Size = UDim2.new(0, 270, 0, 330)
    panelTabla:FindFirstChild("Titulo").Text = "TU CONTRATO"
    guiContrato.nombre = etiqueta("Contrato", UDim2.new(1, -28, 0, 25), UDim2.new(0, 14, 0, 36), "CARGA", Enum.Font.GothamBlack, 20, ORO, panelTabla)
    guiContrato.detalle = etiqueta("DetalleContrato", UDim2.new(1, -28, 0, 40), UDim2.new(0, 14, 0, 64), "Elige durante el descanso", Enum.Font.Gotham, 14, BLANCO, panelTabla)
    guiContrato.detalle.TextWrapped = true
    for k, clave in ipairs({ "carga", "ruta", "express" }) do
        local boton = nuevo("TextButton", {
            Name = "Elegir_" .. clave, Size = UDim2.new(0, 76, 0, 38),
            Position = UDim2.new(0, 14 + (k - 1) * 82, 0, 110),
            BackgroundColor3 = FONDO, TextColor3 = BLANCO,
            Font = Enum.Font.GothamBold, TextSize = 12,
            Text = string.upper(clave), ZIndex = 9, BorderSizePixel = 0,
        }, panelTabla)
        esquina(boton, 8)
        borde(boton, NEON, 1, 0.4)
        guiContrato.botones[clave] = boton
    end
    local fondo = nuevo("Frame", { Size = UDim2.new(1, -28, 0, 8), Position = UDim2.new(0, 14, 0, 158), BackgroundColor3 = GRIS, BorderSizePixel = 0, ZIndex = 8 }, panelTabla)
    guiContrato.barra = nuevo("Frame", { Size = UDim2.new(0, 0, 1, 0), BackgroundColor3 = ORO, BorderSizePixel = 0, ZIndex = 9 }, fondo)
    guiContrato.estado = etiqueta("Medalla", UDim2.new(1, -28, 0, 22), UDim2.new(0, 14, 0, 174), "0/18 cajas", Enum.Font.GothamBold, 13, BLANCO, panelTabla)
    etiqueta("Ranking", UDim2.new(1, -28, 0, 20), UDim2.new(0, 14, 0, 202), "RANKING DEL TURNO", Enum.Font.GothamBold, 12, GRIS, panelTabla)
    for k, fila in ipairs(filasTabla) do
        fila.marco.Position = UDim2.new(0, 14, 0, 226 + (k - 1) * 32)
        fila.marco.Visible = k <= 3
    end
end

-- ------------------------------------------------- brujula y panel de abajo''')
    cambiar("Cliente", "local function elegirObjetivo(estado, posicion)", '''local function elegirObjetivo(estado, posicion)
    if not estado.activa then
        return estado.almacen, "ELIGE CONTRATO Y PULSA E", NEON
    end''')
    cambiar("Cliente", "        local nota = pedido.valor / distancia", '''        local nota = pedido.valor / distancia
        local contrato = estado.turno and estado.turno.eleccion
        if contrato == "ruta" and pedido.nuevoDestino then
            nota = nota * 3
        elseif contrato == "express" and pedido.urgente then
            nota = nota * 3
        end''')
    cambiar("Cliente", '    return mejor.posicion, "ENTREGA EN EL PUNTO VERDE", VERDE', '''    if estado.turno and estado.turno.eleccion == "ruta" and mejor.nuevoDestino then
        return mejor.posicion, "NUEVO DESTINO: P" .. tostring(mejor.indice), VERDE
    end
    return mejor.posicion, "ENTREGA EN EL PUNTO VERDE", VERDE''')
    cambiar("Cliente", "local function mostrarResultados(estado)", '''local function actualizarContrato(estado)
    local contrato = estado.turno
    if not contrato then
        return
    end
    guiContrato.nombre.Text = contrato.nombre .. " / " .. contrato.rango
    guiContrato.nombre.TextScaled = true
    guiContrato.detalle.Text = contrato.descripcion
    guiContrato.estado.Text = tostring(contrato.valor) .. "/" .. tostring(contrato.meta) .. " " .. contrato.unidad .. " | " .. contrato.medalla
    guiContrato.barra.Size = UDim2.new(math.clamp(contrato.valor / contrato.meta, 0, 1), 0, 1, 0)
    for clave, boton in pairs(guiContrato.botones) do
        boton.Active = not estado.activa
        boton.AutoButtonColor = not estado.activa
        boton.BackgroundColor3 = clave == contrato.eleccion and ORO or FONDO
        boton.TextColor3 = clave == contrato.eleccion and NEGRO or BLANCO
    end
    if guiContrato.ronda ~= contrato.idRonda then
        guiContrato.nivel = 0
        guiContrato.ronda = contrato.idRonda
    end
    if estado.activa and contrato.nivel > guiContrato.nivel then
        banner("CONTRATO: " .. contrato.medalla, ORO)
        golpe(guiContrato.estado, 1.2)
    end
    guiContrato.nivel = contrato.nivel
end

local function mostrarResultados(estado)''')
    cambiar("Cliente", '    cuerpoFinal.Text = table.concat(lineasTexto, "\\n")', '''    local turno = estado.turno
    if turno and turno.ultimo then
        local cierre = turno.ultimo
        tituloFinal.Text = cierre.medalla .. " / " .. cierre.contrato
        table.insert(lineasTexto, "")
        table.insert(lineasTexto, "+" .. tostring(cierre.premio) .. " REP  |  " .. turno.rango)
        table.insert(lineasTexto, "Reputacion de esta sesion: " .. tostring(turno.reputacion))
        table.insert(lineasTexto, "Proximo turno: prueba otro contrato (1 / 2 / 3).")
    end
    panelFinal.Size = UDim2.new(0, 500, 0, 360)
    tituloFinal.TextScaled = true
    cuerpoFinal.Text = table.concat(lineasTexto, "\\n")''')
    cambiar("Cliente", "    ultimo = estado\n    mostrarMensaje", "    ultimo = estado\n    actualizarContrato(estado)\n    mostrarMensaje")
    cambiar("Cliente", "        if puesto then", "        if puesto and k <= 3 then")
    cambiar("Cliente", '''local textosTarjeta = {
    "E  EMPIEZA LA RONDA",
    "SHIFT  CORRE Y GASTA AIRE",
    "C  DESLIZADA: RAFAGA CORTA",
    "Q  SUELTA LA CARGA",
}''', '''local textosTarjeta = {
    "CARGA EN EL ALMACEN DORADO",
    "ENTREGA EN LAS PUERTAS ACTIVAS",
    "SHIFT CORRE / C DESLIZA / Q SUELTA",
    "1 CARGA / 2 RUTA / 3 EXPRESS",
}''')
    cambiar("Cliente", "-- --------------------------------------------------------------- entradas", '''-- --------------------------------------------------------------- entradas
for clave, boton in pairs(guiContrato.botones) do
    table.insert(conexiones, boton.Activated:Connect(function()
        if ultimo and not ultimo.activa then
            pedir("contrato_" .. clave, 0.3)
        end
    end))
end''')
    cambiar("Cliente", '''    if objeto.KeyCode == Enum.KeyCode.E then
        pedir("empezar", 0.6)''', '''    if objeto.KeyCode == Enum.KeyCode.One then
        pedir("contrato_carga", 0.3)
    elseif objeto.KeyCode == Enum.KeyCode.Two then
        pedir("contrato_ruta", 0.3)
    elseif objeto.KeyCode == Enum.KeyCode.Three then
        pedir("contrato_express", 0.3)
    elseif objeto.KeyCode == Enum.KeyCode.E and not introFondo.Visible then
        pedir("empezar", 0.6)''')
    cambiar("Cliente", '''table.insert(conexiones, botonEmpezar.MouseButton1Click:Connect(function()
    pedir("empezar", 0.6)
end))''', '''table.insert(conexiones, botonEmpezar.MouseButton1Click:Connect(function()
    if not introFondo.Visible then
        pedir("empezar", 0.6)
    end
end))''')

    carpeta.find("Properties/string[@name='Name']").text = "EntregaFinalV4"
    for nombre, texto in fuentes.items():
        nodos[nombre].text = texto
    modulo = ET.SubElement(carpeta, "Item", {"class": "ModuleScript", "referent": "RBXTurnosV4"})
    propiedades = ET.SubElement(modulo, "Properties")
    ET.SubElement(propiedades, "string", {"name": "Name"}).text = "Turnos"
    fuentes["Turnos"] = (AQUI / "Turnos.lua").read_text(encoding="utf-8")
    ET.SubElement(propiedades, "ProtectedString", {"name": "Source"}).text = fuentes["Turnos"]
    salida.mkdir(parents=True, exist_ok=True)
    for nombre, texto in fuentes.items():
        (salida / (nombre + ".lua")).write_text(texto, encoding="utf-8")
    destino = salida / "EntregaFinalV4-Experimental.rbxmx"
    ET.indent(raiz, space="  ")
    ET.ElementTree(raiz).write(destino, encoding="utf-8", xml_declaration=True)
    extraido = {}
    for item in ET.parse(destino).getroot().iter("Item"):
        src = item.find("Properties/ProtectedString[@name='Source']")
        if src is not None:
            nombre = item.find("Properties/string[@name='Name']").text
            extraido[nombre] = src.text or ""
    assert extraido == fuentes, "El XML cambio una fuente al escribirla"
    manifiesto = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in salida.iterdir() if p.suffix in {".lua", ".rbxmx"}}
    (salida / "SHA256.json").write_text(json.dumps(manifiesto, indent=2) + "\n")
    (salida / "cambios.json").write_text(json.dumps(cambios, indent=2) + "\n")
    print(f"Generado {destino.name}: {len(fuentes)} fuentes recuperadas sin cambios, {len(cambios)} ediciones controladas.")
    return destino


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("--salida", type=Path, default=AQUI / "generado")
    args = parser.parse_args()
    construir(args.base, args.salida)
