-- TIPO: Script
-- RUTA: Workspace > EntregaFinal > Servidor
--
-- Bucle de entregas de 60 segundos. El servidor decide todo lo que da
-- puntos; el cliente solo recibe estado y dibuja.
-- Fichas del catalogo usadas: 08.11 rondas, 08.12 cuenta atras por instante
-- de fin, 06.18 validacion de remotes, 07.09 deteccion de toques.

local Jugadores = game:GetService("Players")
local Compartido = game:GetService("ReplicatedStorage")
local ServicioDatos = game:GetService("DataStoreService")

local carpeta = script.Parent

local plantilla = carpeta:WaitForChild("Interfaz", 10)
if not plantilla then
    warn("EntregaFinal: no aparece la ScreenGui Interfaz; no arranco")
    return
end

local moduloConfig = plantilla:WaitForChild("Config", 10)
if not moduloConfig then
    warn("EntregaFinal: no aparece el ModuleScript Config; no arranco")
    return
end

local Config = require(moduloConfig)

-- Insertar el archivo dos veces dejaria una carpeta de remotos huerfana y
-- el cliente se conectaria a la que ya no dispara nadie.
local viejosRemotos = Compartido:FindFirstChild("EntregaFinalRemotos")
if viejosRemotos then
    viejosRemotos:Destroy()
end

local remotos = Instance.new("Folder")
remotos.Name = "EntregaFinalRemotos"

local eventoEstado = Instance.new("RemoteEvent")
eventoEstado.Name = "Estado"
eventoEstado.Parent = remotos

local eventoAcciones = Instance.new("RemoteEvent")
eventoAcciones.Name = "Acciones"
eventoAcciones.Parent = remotos

remotos.Parent = Compartido

local conexiones = {}
local estados = {}
local ronda = {
    activa = false,
    finaliza = 0,
    destino = 0,
    entregas = 0,
}

-- ------------------------------------------------------------------ arena

local viejaArena = carpeta:FindFirstChild("Arena")
if viejaArena then
    viejaArena:Destroy()
end

local arena = Instance.new("Folder")
arena.Name = "Arena"
arena.Parent = carpeta

local function nuevaParte(nombre, tamano, posicion, color, material)
    local parte = Instance.new("Part")
    parte.Name = nombre
    parte.Size = tamano
    parte.Position = posicion
    parte.Color = color
    parte.Material = material
    parte.Anchored = true
    parte.TopSurface = Enum.SurfaceType.Smooth
    parte.BottomSurface = Enum.SurfaceType.Smooth
    parte.Parent = arena
    return parte
end

local lado = Config.RADIO_ARENA * 2
nuevaParte("Suelo", Vector3.new(lado, 2, lado), Vector3.new(0, -1, 0),
    Color3.fromRGB(46, 50, 58), Enum.Material.Concrete)

local almacen = nuevaParte("Almacen", Vector3.new(18, 8, 18),
    Vector3.new(0, 4, 0), Config.COLOR_ALMACEN, Enum.Material.Metal)

local puntos = {}
for i = 1, Config.PUNTOS_ENTREGA do
    local angulo = math.rad(360 / Config.PUNTOS_ENTREGA * (i - 1))
    local radio = Config.RADIO_ARENA * 0.62
    local pos = Vector3.new(math.cos(angulo) * radio, 0.5, math.sin(angulo) * radio)
    puntos[i] = nuevaParte("Punto" .. i, Vector3.new(16, 1, 16), pos,
        Config.COLOR_INACTIVO, Enum.Material.SmoothPlastic)
end

-- La plantilla Baseplate ya trae un SpawnLocation. Poner otro no rompe nada
-- pero reparte a los jugadores entre dos sitios, asi que solo se crea si no
-- hay ninguno.
local hayAparicion = false
for _, objeto in ipairs(workspace:GetDescendants()) do
    if objeto:IsA("SpawnLocation") then
        hayAparicion = true
        break
    end
end

if not hayAparicion then
    local aparicion = Instance.new("SpawnLocation")
    aparicion.Name = "Aparicion"
    aparicion.Size = Vector3.new(12, 1, 12)
    aparicion.Position = Vector3.new(0, 0.5, 26)
    aparicion.Anchored = true
    aparicion.Duration = 0
    aparicion.Color = Color3.fromRGB(88, 148, 236)
    aparicion.Parent = arena
end

-- El letrero no se reparenta al cambiar de destino: se mueve con Adornee,
-- que es lo que evita recrear la instancia en cada entrega.
local letrero = Instance.new("BillboardGui")
letrero.Name = "Letrero"
letrero.Size = UDim2.new(0, 220, 0, 56)
letrero.StudsOffset = Vector3.new(0, 7, 0)
letrero.AlwaysOnTop = true
letrero.Enabled = false
letrero.Parent = almacen

local letreroTexto = Instance.new("TextLabel")
letreroTexto.Name = "Texto"
letreroTexto.Size = UDim2.new(1, 0, 1, 0)
letreroTexto.BackgroundTransparency = 1
letreroTexto.Font = Enum.Font.GothamBold
letreroTexto.TextSize = 26
letreroTexto.TextColor3 = Color3.fromRGB(255, 255, 255)
letreroTexto.TextStrokeTransparency = 0.35
letreroTexto.Text = "ENTREGA AQUI"
letreroTexto.Parent = letrero

-- -------------------------------------------------------------- datastore

local almacenDatos = nil
local okDatos, resultadoDatos = pcall(function()
    return ServicioDatos:GetDataStore(Config.CLAVE_DATASTORE)
end)
if okDatos then
    almacenDatos = resultadoDatos
end

local function cargarMejor(jugador)
    if not almacenDatos then
        return 0
    end
    local ok, valor = pcall(function()
        return almacenDatos:GetAsync("mejor_" .. jugador.UserId)
    end)
    if ok and type(valor) == "number" then
        return valor
    end
    return 0
end

local function guardarMejor(jugador, valor)
    if not almacenDatos then
        return
    end
    pcall(function()
        almacenDatos:SetAsync("mejor_" .. jugador.UserId, valor)
    end)
end

-- ----------------------------------------------------------------- estado

local function estadoDe(jugador)
    local estado = estados[jugador]
    if not estado then
        estado = {
            puntos = 0,
            racha = 0,
            mejor = 0,
            entregas = 0,
            llevaCaja = false,
            ultimoToque = 0,
            llamadas = {},
            conexion = nil,
        }
        estados[jugador] = estado
    end
    return estado
end

local function paquete(jugador)
    local estado = estadoDe(jugador)
    local destino = nil
    if ronda.destino > 0 then
        destino = puntos[ronda.destino].Position
    end
    return {
        activa = ronda.activa,
        finaliza = ronda.finaliza,
        segundosRonda = Config.SEGUNDOS_RONDA,
        puntos = estado.puntos,
        racha = estado.racha,
        mejor = estado.mejor,
        entregas = estado.entregas,
        llevaCaja = estado.llevaCaja,
        destino = destino,
        almacen = almacen.Position,
    }
end

local function avisar(jugador, mensaje)
    eventoEstado:FireClient(jugador, paquete(jugador), mensaje)
end

local function avisarATodos(mensaje)
    for _, jugador in ipairs(Jugadores:GetPlayers()) do
        avisar(jugador, mensaje)
    end
end

local function pintarPuntos()
    for i, pad in ipairs(puntos) do
        if i == ronda.destino then
            pad.Color = Config.COLOR_ACTIVO
            pad.Material = Enum.Material.Neon
        else
            pad.Color = Config.COLOR_INACTIVO
            pad.Material = Enum.Material.SmoothPlastic
        end
    end
end

local function elegirDestino()
    local total = #puntos
    local nuevo = 1
    if total > 1 then
        -- Se sortea entre los demas y luego se corrige el indice. Asi nunca
        -- sale dos veces el mismo punto y no hace falta bucle de reintento.
        nuevo = math.random(1, total - 1)
        if ronda.destino > 0 and nuevo >= ronda.destino then
            nuevo = nuevo + 1
        end
    end
    ronda.destino = nuevo
    pintarPuntos()
    letrero.Adornee = puntos[nuevo]
    letrero.Enabled = true
end

-- --------------------------------------------------------------- entregas

local function quitarCaja(personaje)
    if not personaje then
        return
    end
    local caja = personaje:FindFirstChild("CajaEntrega")
    if caja then
        caja:Destroy()
    end
end

local function ponerCaja(personaje)
    local raiz = personaje:FindFirstChild("HumanoidRootPart")
    if not raiz then
        return false
    end
    quitarCaja(personaje)
    local caja = Instance.new("Part")
    caja.Name = "CajaEntrega"
    caja.Size = Vector3.new(2.2, 2.2, 2.2)
    caja.Color = Config.COLOR_ALMACEN
    caja.Material = Enum.Material.WoodPlanks
    caja.CanCollide = false
    -- Massless para que la caja no cambie como salta el personaje, y sin
    -- anclar porque una WeldConstraint no une nada que este Anchored.
    caja.Massless = true
    caja.CFrame = raiz.CFrame * CFrame.new(0, 0.8, 1.6)
    caja.Parent = personaje
    local union = Instance.new("WeldConstraint")
    union.Part0 = raiz
    union.Part1 = caja
    union.Parent = caja
    return true
end

local function jugadorValido(parte)
    local personaje = parte:FindFirstAncestorOfClass("Model")
    if not personaje then
        return nil, nil
    end
    local humanoide = personaje:FindFirstChildOfClass("Humanoid")
    if not humanoide then
        return nil, nil
    end
    if humanoide.Health <= 0 then
        return nil, nil
    end
    local jugador = Jugadores:GetPlayerFromCharacter(personaje)
    if not jugador then
        return nil, nil
    end
    return jugador, personaje
end

local function recoger(jugador, personaje)
    local estado = estadoDe(jugador)
    local ahora = workspace:GetServerTimeNow()
    if not ronda.activa then
        return
    end
    if estado.llevaCaja then
        return
    end
    -- Touched se dispara muchas veces por segundo mientras se pisa la parte.
    if ahora - estado.ultimoToque < Config.ENFRIAMIENTO_TOQUE then
        return
    end
    estado.ultimoToque = ahora
    if not ponerCaja(personaje) then
        return
    end
    estado.llevaCaja = true
    avisar(jugador, "CAJA RECOGIDA")
end

local function entregar(jugador, personaje)
    local estado = estadoDe(jugador)
    local ahora = workspace:GetServerTimeNow()
    if not ronda.activa then
        return
    end
    if not estado.llevaCaja then
        return
    end
    if ahora - estado.ultimoToque < Config.ENFRIAMIENTO_TOQUE then
        return
    end
    estado.ultimoToque = ahora
    quitarCaja(personaje)
    estado.llevaCaja = false
    estado.racha = math.min(estado.racha + 1, Config.RACHA_MAXIMA)
    estado.entregas = estado.entregas + 1
    local ganado = Config.PUNTOS_BASE + Config.BONUS_RACHA * (estado.racha - 1)
    estado.puntos = estado.puntos + ganado
    ronda.entregas = ronda.entregas + 1
    elegirDestino()
    avisar(jugador, "ENTREGA +" .. ganado)
    for _, otro in ipairs(Jugadores:GetPlayers()) do
        if otro ~= jugador then
            avisar(otro, nil)
        end
    end
end

table.insert(conexiones, almacen.Touched:Connect(function(parte)
    local jugador, personaje = jugadorValido(parte)
    if jugador then
        recoger(jugador, personaje)
    end
end))

for i, pad in ipairs(puntos) do
    table.insert(conexiones, pad.Touched:Connect(function(parte)
        if i ~= ronda.destino then
            return
        end
        local jugador, personaje = jugadorValido(parte)
        if jugador then
            entregar(jugador, personaje)
        end
    end))
end

-- ----------------------------------------------------------------- rondas

local function terminarRonda()
    ronda.activa = false
    ronda.destino = 0
    letrero.Enabled = false
    pintarPuntos()
    for _, jugador in ipairs(Jugadores:GetPlayers()) do
        local estado = estadoDe(jugador)
        quitarCaja(jugador.Character)
        estado.llevaCaja = false
        estado.racha = 0
        if estado.puntos > estado.mejor then
            estado.mejor = estado.puntos
            guardarMejor(jugador, estado.mejor)
        end
        avisar(jugador, "FIN DE RONDA: " .. estado.puntos .. " puntos")
    end
end

local function empezarRonda()
    ronda.activa = true
    ronda.entregas = 0
    ronda.destino = 0
    ronda.finaliza = workspace:GetServerTimeNow() + Config.SEGUNDOS_RONDA
    for _, jugador in ipairs(Jugadores:GetPlayers()) do
        local estado = estadoDe(jugador)
        estado.puntos = 0
        estado.racha = 0
        estado.entregas = 0
        estado.llevaCaja = false
        quitarCaja(jugador.Character)
    end
    elegirDestino()
    avisarATodos("RONDA EN MARCHA")
end

-- ------------------------------------------------ remote con validacion

local function frecuenciaOk(estado, ahora)
    local recientes = {}
    for _, marca in ipairs(estado.llamadas) do
        if ahora - marca < 1 then
            table.insert(recientes, marca)
        end
    end
    estado.llamadas = recientes
    if #recientes >= Config.LLAMADAS_POR_SEGUNDO then
        return false
    end
    table.insert(estado.llamadas, ahora)
    return true
end

table.insert(conexiones, eventoAcciones.OnServerEvent:Connect(function(jugador, accion)
    local estado = estadoDe(jugador)
    local ahora = workspace:GetServerTimeNow()
    -- a) frecuencia
    if not frecuenciaOk(estado, ahora) then
        return
    end
    -- b) tipo
    if type(accion) ~= "string" then
        return
    end
    -- c) rango: solo las acciones declaradas en Config
    if not Config.ACCIONES[accion] then
        return
    end
    -- d) derecho
    local personaje = jugador.Character
    if not personaje then
        return
    end
    if accion == "empezar" then
        if ronda.activa then
            return
        end
        empezarRonda()
    elseif accion == "soltar" then
        if not estado.llevaCaja then
            return
        end
        quitarCaja(personaje)
        estado.llevaCaja = false
        estado.racha = 0
        avisar(jugador, "CAJA SOLTADA: racha a cero")
    end
end))

-- ------------------------------------------------------ bucle y jugadores

local ejecutando = true

local function entra(jugador)
    local estado = estadoDe(jugador)
    estado.mejor = cargarMejor(jugador)
    estado.conexion = jugador.CharacterAdded:Connect(function()
        estado.llevaCaja = false
        estado.racha = 0
        avisar(jugador, "HAS REAPARECIDO: vuelve al almacen")
    end)
    local interfaz = jugador:WaitForChild("PlayerGui", 10)
    if not interfaz then
        return
    end
    -- Un LocalScript dentro de Workspace no corre. La ScreenGui de la
    -- carpeta es solo plantilla: lo que se ejecuta es esta copia.
    local copia = plantilla:Clone()
    copia.Parent = interfaz
    avisar(jugador, "PULSA E O EL BOTON PARA EMPEZAR YA")
end

table.insert(conexiones, Jugadores.PlayerAdded:Connect(entra))

for _, jugador in ipairs(Jugadores:GetPlayers()) do
    task.spawn(entra, jugador)
end

table.insert(conexiones, Jugadores.PlayerRemoving:Connect(function(jugador)
    local estado = estados[jugador]
    if estado then
        if estado.conexion then
            estado.conexion:Disconnect()
        end
        if estado.puntos > estado.mejor then
            guardarMejor(jugador, estado.puntos)
        end
    end
    estados[jugador] = nil
end))

carpeta.Destroying:Connect(function()
    ejecutando = false
    for _, conexion in ipairs(conexiones) do
        conexion:Disconnect()
    end
    conexiones = {}
    if remotos then
        remotos:Destroy()
    end
end)

ronda.finaliza = workspace:GetServerTimeNow() + Config.SEGUNDOS_DESCANSO

task.spawn(function()
    while ejecutando do
        local ahora = workspace:GetServerTimeNow()
        if ronda.activa and ahora >= ronda.finaliza then
            terminarRonda()
            -- Se guarda el instante en que acaba el descanso, no un contador:
            -- asi la cuenta atras no se desincroniza si el servidor va lento.
            ronda.finaliza = ahora + Config.SEGUNDOS_DESCANSO
        elseif not ronda.activa and #Jugadores:GetPlayers() > 0 and ahora >= ronda.finaliza then
            empezarRonda()
        end
        avisarATodos(nil)
        task.wait(1)
    end
end)
