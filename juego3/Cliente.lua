-- TIPO: LocalScript
-- RUTA: PlayerGui > Interfaz > Cliente
--
-- El servidor copia la plantilla Workspace > EntregaFinal > Interfaz al
-- PlayerGui de cada jugador; este script solo corre en esa copia.
-- No decide nada: dibuja el estado que llega y pide acciones.
-- La interfaz se construye en tiempo de ejecucion, igual que en juego2.

local Jugadores = game:GetService("Players")
local Compartido = game:GetService("ReplicatedStorage")
local Ejecucion = game:GetService("RunService")
local Entrada = game:GetService("UserInputService")

local jugador = Jugadores.LocalPlayer
local pantalla = script.Parent

local moduloConfig = pantalla:WaitForChild("Config", 10)
if not moduloConfig then
    warn("EntregaFinal: la copia de la interfaz llego sin Config")
    return
end

local Config = require(moduloConfig)

local carpetaRemotos = Compartido:WaitForChild("EntregaFinalRemotos", 20)
if not carpetaRemotos then
    warn("EntregaFinal: no hay remotos; el servidor no ha arrancado")
    return
end

local eventoEstado = carpetaRemotos:WaitForChild("Estado", 10)
local eventoAcciones = carpetaRemotos:WaitForChild("Acciones", 10)
if not eventoEstado or not eventoAcciones then
    warn("EntregaFinal: faltan remotos dentro de la carpeta")
    return
end

-- ------------------------------------------------------------- interfaz

local NEGRO = Color3.fromRGB(18, 20, 26)
local BLANCO = Color3.fromRGB(238, 242, 248)
local GRIS = Color3.fromRGB(150, 160, 175)
local VERDE = Color3.fromRGB(80, 220, 120)
local AMBAR = Color3.fromRGB(240, 180, 60)
local ROJO = Color3.fromRGB(238, 92, 92)

local function nuevo(clase, propiedades, padre)
    local objeto = Instance.new(clase)
    for clave, valor in pairs(propiedades) do
        objeto[clave] = valor
    end
    objeto.Parent = padre
    return objeto
end

local barra = nuevo("Frame", {
    Name = "Barra",
    Size = UDim2.new(0, 460, 0, 80),
    Position = UDim2.new(0.5, 0, 0, 14),
    AnchorPoint = Vector2.new(0.5, 0),
    BackgroundColor3 = NEGRO,
    BackgroundTransparency = 0.15,
    BorderSizePixel = 0,
}, pantalla)

nuevo("UICorner", { CornerRadius = UDim.new(0, 12) }, barra)

local reloj = nuevo("TextLabel", {
    Name = "Reloj",
    Size = UDim2.new(0, 120, 1, 0),
    Position = UDim2.new(0, 14, 0, 0),
    BackgroundTransparency = 1,
    Font = Enum.Font.GothamBlack,
    TextSize = 42,
    TextColor3 = BLANCO,
    TextXAlignment = Enum.TextXAlignment.Left,
    Text = tostring(Config.SEGUNDOS_RONDA),
}, barra)

local marcador = nuevo("TextLabel", {
    Name = "Puntos",
    Size = UDim2.new(0, 180, 0, 40),
    Position = UDim2.new(0, 140, 0, 8),
    BackgroundTransparency = 1,
    Font = Enum.Font.GothamBold,
    TextSize = 26,
    TextColor3 = BLANCO,
    TextXAlignment = Enum.TextXAlignment.Left,
    Text = "0 pts",
}, barra)

local rachaTexto = nuevo("TextLabel", {
    Name = "Racha",
    Size = UDim2.new(0, 180, 0, 26),
    Position = UDim2.new(0, 140, 0, 48),
    BackgroundTransparency = 1,
    Font = Enum.Font.Gotham,
    TextSize = 16,
    TextColor3 = AMBAR,
    TextXAlignment = Enum.TextXAlignment.Left,
    Text = "racha x1",
}, barra)

local mejorTexto = nuevo("TextLabel", {
    Name = "Mejor",
    Size = UDim2.new(0, 130, 1, 0),
    Position = UDim2.new(1, -144, 0, 0),
    BackgroundTransparency = 1,
    Font = Enum.Font.Gotham,
    TextSize = 16,
    TextColor3 = GRIS,
    TextXAlignment = Enum.TextXAlignment.Right,
    Text = "mejor 0",
}, barra)

local aviso = nuevo("TextLabel", {
    Name = "Aviso",
    Size = UDim2.new(0, 520, 0, 38),
    Position = UDim2.new(0.5, 0, 0, 104),
    AnchorPoint = Vector2.new(0.5, 0),
    BackgroundTransparency = 1,
    Font = Enum.Font.GothamBold,
    TextSize = 22,
    TextColor3 = VERDE,
    Text = Config.NOMBRE .. ": 60 SEGUNDOS",
}, pantalla)

local panel = nuevo("Frame", {
    Name = "Objetivo",
    Size = UDim2.new(0, 430, 0, 96),
    Position = UDim2.new(0.5, 0, 1, -150),
    AnchorPoint = Vector2.new(0.5, 0),
    BackgroundColor3 = NEGRO,
    BackgroundTransparency = 0.2,
    BorderSizePixel = 0,
}, pantalla)

nuevo("UICorner", { CornerRadius = UDim.new(0, 12) }, panel)

-- La flecha es texto rotado, no una imagen: asi el archivo no depende de
-- ningun asset subido a Roblox.
local flecha = nuevo("TextLabel", {
    Name = "Flecha",
    Size = UDim2.new(0, 64, 0, 64),
    Position = UDim2.new(0, 14, 0, 16),
    BackgroundTransparency = 1,
    Font = Enum.Font.GothamBlack,
    TextSize = 46,
    TextColor3 = VERDE,
    Text = "^",
}, panel)

local objetivoTexto = nuevo("TextLabel", {
    Name = "Texto",
    Size = UDim2.new(0, 330, 0, 34),
    Position = UDim2.new(0, 90, 0, 16),
    BackgroundTransparency = 1,
    Font = Enum.Font.GothamBold,
    TextSize = 20,
    TextColor3 = BLANCO,
    TextXAlignment = Enum.TextXAlignment.Left,
    Text = "ESPERANDO AL SERVIDOR",
}, panel)

local distanciaTexto = nuevo("TextLabel", {
    Name = "Distancia",
    Size = UDim2.new(0, 330, 0, 28),
    Position = UDim2.new(0, 90, 0, 52),
    BackgroundTransparency = 1,
    Font = Enum.Font.Gotham,
    TextSize = 16,
    TextColor3 = GRIS,
    TextXAlignment = Enum.TextXAlignment.Left,
    Text = "",
}, panel)

local function nuevoBoton(nombre, texto, desplazamiento)
    local boton = nuevo("TextButton", {
        Name = nombre,
        Size = UDim2.new(0, 152, 0, 44),
        Position = UDim2.new(0.5, desplazamiento, 1, -50),
        AnchorPoint = Vector2.new(0.5, 1),
        BackgroundColor3 = NEGRO,
        BackgroundTransparency = 0.1,
        BorderSizePixel = 0,
        AutoButtonColor = true,
        Font = Enum.Font.GothamBold,
        TextSize = 18,
        TextColor3 = BLANCO,
        Text = texto,
    }, pantalla)
    nuevo("UICorner", { CornerRadius = UDim.new(0, 10) }, boton)
    return boton
end

-- Los dos botones existen para que el juego se pueda jugar en movil, donde
-- no hay teclado.
local botonEmpezar = nuevoBoton("Empezar", "EMPEZAR (E)", -82)
local botonSoltar = nuevoBoton("Soltar", "SOLTAR (Q)", 82)

-- ---------------------------------------------------------------- logica

local conexiones = {}
local ultimo = nil
local ultimaPeticion = 0
local turnoMensaje = 0

local function pedir(accion)
    local ahora = os.clock()
    -- El servidor ya limita la frecuencia; este freno solo evita gastar
    -- llamadas cuando alguien machaca el boton.
    if ahora - ultimaPeticion < 0.5 then
        return
    end
    ultimaPeticion = ahora
    eventoAcciones:FireServer(accion)
end

local function mostrarMensaje(texto)
    if type(texto) ~= "string" then
        return
    end
    aviso.Text = texto
    turnoMensaje = turnoMensaje + 1
    local mio = turnoMensaje
    task.delay(2.5, function()
        if mio == turnoMensaje then
            aviso.Text = ""
        end
    end)
end

local function anguloHacia(objetivo)
    local camara = workspace.CurrentCamera
    if not camara then
        return 0
    end
    local hacia = objetivo - camara.CFrame.Position
    local plano = Vector3.new(hacia.X, 0, hacia.Z)
    local frente = camara.CFrame.LookVector
    local frentePlano = Vector3.new(frente.X, 0, frente.Z)
    if plano.Magnitude < 0.5 or frentePlano.Magnitude < 0.05 then
        return 0
    end
    plano = plano.Unit
    frentePlano = frentePlano.Unit
    -- Derecha de la camara proyectada en el suelo. El signo sale de que
    -- Roblox usa la mano izquierda: mirar a -Z es mirar al frente.
    local derecha = Vector3.new(frentePlano.Z, 0, -frentePlano.X)
    return math.deg(math.atan2(plano:Dot(derecha), plano:Dot(frentePlano)))
end

table.insert(conexiones, eventoEstado.OnClientEvent:Connect(function(estado, mensaje)
    if type(estado) ~= "table" then
        return
    end
    ultimo = estado
    mostrarMensaje(mensaje)
end))

table.insert(conexiones, Ejecucion.RenderStepped:Connect(function()
    if not ultimo then
        return
    end
    -- La cuenta atras se calcula aqui con el reloj del servidor: el servidor
    -- solo manda el instante de fin y nada se desincroniza.
    local restante = math.max(0, (ultimo.finaliza or 0) - workspace:GetServerTimeNow())
    reloj.Text = tostring(math.ceil(restante))
    if ultimo.activa then
        if restante <= 10 then
            reloj.TextColor3 = ROJO
        else
            reloj.TextColor3 = BLANCO
        end
    else
        reloj.TextColor3 = GRIS
    end

    marcador.Text = tostring(ultimo.puntos or 0) .. " pts"
    rachaTexto.Text = "racha x" .. tostring((ultimo.racha or 0) + 1)
    mejorTexto.Text = "mejor " .. tostring(ultimo.mejor or 0)

    local objetivo = ultimo.almacen
    local texto = "RECOGE UNA CAJA EN EL ALMACEN"
    if ultimo.llevaCaja and ultimo.destino then
        objetivo = ultimo.destino
        texto = "LLEVA LA CAJA AL PUNTO VERDE"
    end
    if not ultimo.activa then
        texto = "RONDA EN PAUSA: PULSA EMPEZAR"
    end
    objetivoTexto.Text = texto

    local personaje = jugador.Character
    local raiz = nil
    if personaje then
        raiz = personaje:FindFirstChild("HumanoidRootPart")
    end
    if objetivo and raiz then
        local metros = (objetivo - raiz.Position).Magnitude
        distanciaTexto.Text = tostring(math.floor(metros)) .. " studs"
        flecha.Rotation = anguloHacia(objetivo)
        flecha.Visible = true
    else
        distanciaTexto.Text = ""
        flecha.Visible = false
    end

    botonSoltar.Visible = ultimo.llevaCaja == true
    botonEmpezar.Visible = ultimo.activa ~= true
end))

table.insert(conexiones, botonEmpezar.MouseButton1Click:Connect(function()
    pedir("empezar")
end))

table.insert(conexiones, botonSoltar.MouseButton1Click:Connect(function()
    pedir("soltar")
end))

table.insert(conexiones, Entrada.InputBegan:Connect(function(objeto, procesado)
    if procesado then
        return
    end
    if objeto.KeyCode == Enum.KeyCode.E then
        pedir("empezar")
    elseif objeto.KeyCode == Enum.KeyCode.Q then
        pedir("soltar")
    end
end))

pantalla.Destroying:Connect(function()
    for _, conexion in ipairs(conexiones) do
        conexion:Disconnect()
    end
    conexiones = {}
end)
