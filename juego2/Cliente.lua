-- TIPO: LocalScript
-- RUTA: PlayerGui > Interfaz > Cliente
--
-- Banco de pruebas de animacion. Dos modos:
--   VISOR  reproduce cualquiera de los 11 modelos del repositorio y, si es
--          un ciclo de locomocion, muestra al lado una variante DIDACTICA
--          ROTA para comparar en directo. Ojo: esa variante NO es una
--          correccion, es el error que hay que evitar. Los modelos del
--          repositorio alternan bien; ver Datos.convenciones.
--   RETO   juego de 60 segundos: se muestra un solo maniqui y hay que
--          decidir si los miembros alternan o van en fase.

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local jugador = Players.LocalPlayer
local pantalla = script.Parent
local camara = workspace.CurrentCamera

-- Con timeout, como pide el checklist del repositorio: si falta un hijo
-- avisamos en la consola en lugar de colgarnos para siempre.
local function pedir(padre, nombre)
    local hijo = padre:WaitForChild(nombre, 10)
    if not hijo then
        warn("[Banco] falta " .. padre:GetFullName() .. "." .. nombre)
    end
    return hijo
end

local modDatos = pedir(pantalla, "Datos")
local modRig = pedir(pantalla, "Rig")
if not modDatos or not modRig then
    return
end

local okD, Datos = pcall(require, modDatos)
local okR, Rig = pcall(require, modRig)
if not okD or not okR then
    warn("[Banco] no se pudieron cargar los modulos")
    return
end

local ANIMS = Datos.animaciones
if not ANIMS or #ANIMS == 0 then
    warn("[Banco] no hay animaciones en Datos")
    return
end

-- ------------------------------------------------------------------ paleta

local COL = {
    panel = Color3.fromRGB(24, 27, 34),
    panel2 = Color3.fromRGB(32, 36, 45),
    borde = Color3.fromRGB(56, 62, 78),
    texto = Color3.fromRGB(233, 237, 245),
    suave = Color3.fromRGB(150, 158, 174),
    acento = Color3.fromRGB(18, 138, 166),
    malo = Color3.fromRGB(198, 62, 62),
    bueno = Color3.fromRGB(64, 168, 92),
    aviso = Color3.fromRGB(214, 168, 40),
}

local function nuevo(clase, props, padre)
    local i = Instance.new(clase)
    for k, v in pairs(props) do
        i[k] = v
    end
    if padre then
        i.Parent = padre
    end
    return i
end

local function redondear(obj, r)
    nuevo("UICorner", {CornerRadius = UDim.new(0, r or 8)}, obj)
end

local function contorno(obj, col, gr)
    nuevo("UIStroke", {
        Color = col or COL.borde,
        Thickness = gr or 1,
        ApplyStrokeMode = Enum.ApplyStrokeMode.Border,
    }, obj)
end

-- ---------------------------------------------------------------- escenario

local SUELO = 0.5
local escena = nuevo("Folder", {Name = "EscenaBanco"}, workspace)

local function pedestal(x, z, col)
    local p = nuevo("Part", {
        Name = "Pedestal",
        Size = Vector3.new(9, 1, 9),
        Position = Vector3.new(x, SUELO, z),
        Anchored = true,
        CanCollide = true,
        Material = Enum.Material.Slate,
        Color = col,
        TopSurface = Enum.SurfaceType.Smooth,
        BottomSurface = Enum.SurfaceType.Smooth,
    }, escena)
    return p
end

pedestal(-7, 0, Color3.fromRGB(48, 40, 44))
pedestal(7, 0, Color3.fromRGB(38, 48, 44))

-- rejilla de referencia detras, para juzgar el desplazamiento del torso
for i = -3, 3 do
    nuevo("Part", {
        Name = "Guia",
        Size = Vector3.new(0.15, 12, 0.15),
        Position = Vector3.new(i * 4, SUELO + 6.5, -9),
        Anchored = true,
        CanCollide = false,
        Material = Enum.Material.Neon,
        Color = Color3.fromRGB(44, 52, 66),
        Transparency = 0.35,
    }, escena)
end

nuevo("Part", {
    Name = "Telon",
    Size = Vector3.new(60, 26, 1),
    Position = Vector3.new(0, SUELO + 13, -12),
    Anchored = true,
    CanCollide = false,
    Material = Enum.Material.SmoothPlastic,
    Color = Color3.fromRGB(20, 23, 29),
}, escena)

-- ------------------------------------------------------------------- ranuras

local BASE_A = CFrame.new(-7, SUELO + 0.5 + 3, 0)
local BASE_B = CFrame.new(7, SUELO + 0.5 + 3, 0)

-- La ranura A lleva el dato real del repositorio, que alterna bien, asi que
-- se pinta en verde. La ranura B lleva la variante rota, en rojo.
local ranuras = {
    A = {rig = nil, tipo = nil, base = BASE_A, paleta = Rig.PALETAS.corregido},
    B = {rig = nil, tipo = nil, base = BASE_B, paleta = Rig.PALETAS.original},
}

local function alturaBase(def, base)
    return CFrame.new(base.Position.X, SUELO + 0.5 + def.altura, base.Position.Z)
end

local function asegurar(clave, tipoRig)
    local r = ranuras[clave]
    if r.tipo == tipoRig and r.rig then
        return r.rig
    end
    if r.rig then
        Rig.destruir(r.rig)
        r.rig = nil
    end
    local def = Rig.definicion(tipoRig)
    local paleta = r.paleta
    if tipoRig == "R15" and clave == "A" then
        paleta = Rig.PALETAS.r15
    end
    r.rig = Rig.construir(def, alturaBase(def, r.base), escena,
        "Maniqui" .. clave, paleta)
    r.tipo = tipoRig
    return r.rig
end

local function ocultar(clave)
    local r = ranuras[clave]
    if r.rig then
        Rig.destruir(r.rig)
        r.rig = nil
        r.tipo = nil
    end
end

-- ------------------------------------------------------------------- estado

local est = {
    sel = 1,
    t = 0,
    corriendo = true,
    bucle = true,
    vel = 1,
    comparar = true,
    modo = "visor",
}

local VELS = {0.25, 0.5, 1, 2}
local velIdx = 3

local reto = {
    activo = false,
    puntos = 0,
    racha = 0,
    mejorRacha = 0,
    aciertos = 0,
    rondas = 0,
    resta = 60,
    mostrandoRoto = false,
    esperando = false,
}

local function anim()
    return ANIMS[est.sel]
end

local function duracion(a)
    return a.duracion or 1
end

-- ---------------------------------------------------------------------- gui

pantalla.ResetOnSpawn = false
pantalla.ZIndexBehavior = Enum.ZIndexBehavior.Global
pantalla.IgnoreGuiInset = true

-- panel izquierdo: lista de modelos
local izq = nuevo("Frame", {
    Name = "Modelos",
    Position = UDim2.new(0, 16, 0, 16),
    Size = UDim2.new(0, 296, 1, -32),
    BackgroundColor3 = COL.panel,
    BorderSizePixel = 0,
}, pantalla)
redondear(izq, 12)
contorno(izq)

nuevo("TextLabel", {
    Name = "Titulo",
    Position = UDim2.new(0, 16, 0, 14),
    Size = UDim2.new(1, -32, 0, 22),
    BackgroundTransparency = 1,
    Font = Enum.Font.GothamBold,
    Text = "BANCO DE ANIMACIONES",
    TextColor3 = COL.texto,
    TextSize = 15,
    TextXAlignment = Enum.TextXAlignment.Left,
}, izq)

nuevo("TextLabel", {
    Name = "Sub",
    Position = UDim2.new(0, 16, 0, 36),
    Size = UDim2.new(1, -32, 0, 18),
    BackgroundTransparency = 1,
    Font = Enum.Font.Gotham,
    Text = #ANIMS .. " modelos reales del repositorio",
    TextColor3 = COL.suave,
    TextSize = 12,
    TextXAlignment = Enum.TextXAlignment.Left,
}, izq)

local lista = nuevo("ScrollingFrame", {
    Name = "Lista",
    Position = UDim2.new(0, 12, 0, 62),
    Size = UDim2.new(1, -24, 1, -122),
    BackgroundTransparency = 1,
    BorderSizePixel = 0,
    ScrollBarThickness = 4,
    ScrollBarImageColor3 = COL.borde,
    CanvasSize = UDim2.new(0, 0, 0, 0),
    ScrollingDirection = Enum.ScrollingDirection.Y,
}, izq)
nuevo("UIListLayout", {
    Padding = UDim.new(0, 6),
    SortOrder = Enum.SortOrder.LayoutOrder,
}, lista)

local botones = {}

for i, a in ipairs(ANIMS) do
    local malo = #a.defectos > 0
    local avisa = #a.avisos > 0
    local comparable = a.roto ~= nil
    local fila = nuevo("TextButton", {
        Name = "Item" .. i,
        Size = UDim2.new(1, 0, 0, 46),
        BackgroundColor3 = COL.panel2,
        BorderSizePixel = 0,
        AutoButtonColor = false,
        Font = Enum.Font.GothamMedium,
        Text = "",
        LayoutOrder = i,
    }, lista)
    redondear(fila, 8)

    nuevo("Frame", {
        Name = "Marca",
        Position = UDim2.new(0, 0, 0, 0),
        Size = UDim2.new(0, 4, 1, 0),
        BackgroundColor3 = malo and COL.malo
            or (avisa and COL.aviso or COL.bueno),
        BorderSizePixel = 0,
    }, fila)

    nuevo("TextLabel", {
        Name = "Nombre",
        Position = UDim2.new(0, 14, 0, 6),
        Size = UDim2.new(1, -60, 0, 18),
        BackgroundTransparency = 1,
        Font = Enum.Font.GothamMedium,
        Text = a.titulo,
        TextColor3 = COL.texto,
        TextSize = 13,
        TextXAlignment = Enum.TextXAlignment.Left,
        TextTruncate = Enum.TextTruncate.AtEnd,
    }, fila)

    local detalle = a.rig .. "  |  " .. #a.keyframes .. " kf  |  "
        .. string.format("%.2f", duracion(a)) .. "s"
    nuevo("TextLabel", {
        Name = "Detalle",
        Position = UDim2.new(0, 14, 0, 24),
        Size = UDim2.new(1, -60, 0, 16),
        BackgroundTransparency = 1,
        Font = Enum.Font.Gotham,
        Text = detalle,
        TextColor3 = COL.suave,
        TextSize = 11,
        TextXAlignment = Enum.TextXAlignment.Left,
    }, fila)

    if comparable then
        local et = nuevo("TextLabel", {
            Name = "Etiqueta",
            Position = UDim2.new(1, -52, 0, 14),
            Size = UDim2.new(0, 44, 0, 18),
            BackgroundColor3 = COL.acento,
            BorderSizePixel = 0,
            Font = Enum.Font.GothamBold,
            Text = "CICLO",
            TextColor3 = COL.texto,
            TextSize = 10,
        }, fila)
        redondear(et, 4)
    end

    botones[i] = fila
    fila.MouseButton1Click:Connect(function()
        est.sel = i
        est.t = 0
        est.corriendo = true
    end)
end

task.defer(function()
    local lay = lista:FindFirstChildOfClass("UIListLayout")
    if lay then
        lista.CanvasSize = UDim2.new(0, 0, 0, lay.AbsoluteContentSize.Y + 8)
    end
end)

-- boton de modo
local btnModo = nuevo("TextButton", {
    Name = "Modo",
    Position = UDim2.new(0, 12, 1, -52),
    Size = UDim2.new(1, -24, 0, 38),
    BackgroundColor3 = COL.acento,
    BorderSizePixel = 0,
    AutoButtonColor = false,
    Font = Enum.Font.GothamBold,
    Text = "JUGAR EL RETO DE FASE",
    TextColor3 = COL.texto,
    TextSize = 13,
}, izq)
redondear(btnModo, 8)

-- ------------------------------------------------------- barra inferior

local barra = nuevo("Frame", {
    Name = "Controles",
    AnchorPoint = Vector2.new(0.5, 1),
    Position = UDim2.new(0.5, 150, 1, -16),
    Size = UDim2.new(0, 660, 0, 104),
    BackgroundColor3 = COL.panel,
    BorderSizePixel = 0,
}, pantalla)
redondear(barra, 12)
contorno(barra)

local function ctrl(x, w, txt, nom)
    local b = nuevo("TextButton", {
        Name = nom,
        Position = UDim2.new(0, x, 0, 14),
        Size = UDim2.new(0, w, 0, 34),
        BackgroundColor3 = COL.panel2,
        BorderSizePixel = 0,
        AutoButtonColor = false,
        Font = Enum.Font.GothamMedium,
        Text = txt,
        TextColor3 = COL.texto,
        TextSize = 12,
    }, barra)
    redondear(b, 7)
    return b
end

local btnPlay = ctrl(16, 96, "PAUSA", "Play")
local btnReset = ctrl(120, 74, "REINICIAR", "Reset")
local btnBucle = ctrl(202, 92, "BUCLE: SI", "Bucle")
local btnVel = ctrl(302, 86, "VEL 1x", "Vel")
local btnComp = ctrl(396, 128, "COMPARAR: SI", "Comparar")
local btnCam = ctrl(532, 112, "ORBITA: SI", "Camara")

-- pista de tiempo
local pista = nuevo("Frame", {
    Name = "Pista",
    Position = UDim2.new(0, 16, 0, 62),
    Size = UDim2.new(1, -32, 0, 10),
    BackgroundColor3 = COL.panel2,
    BorderSizePixel = 0,
}, barra)
redondear(pista, 5)

local relleno = nuevo("Frame", {
    Name = "Relleno",
    Size = UDim2.new(0, 0, 1, 0),
    BackgroundColor3 = COL.acento,
    BorderSizePixel = 0,
}, pista)
redondear(relleno, 5)

local marcas = nuevo("Frame", {
    Name = "Marcas",
    Position = UDim2.new(0, 16, 0, 76),
    Size = UDim2.new(1, -32, 0, 8),
    BackgroundTransparency = 1,
    BorderSizePixel = 0,
}, barra)

local lblTiempo = nuevo("TextLabel", {
    Name = "Tiempo",
    Position = UDim2.new(0, 16, 0, 84),
    Size = UDim2.new(1, -32, 0, 16),
    BackgroundTransparency = 1,
    Font = Enum.Font.Gotham,
    Text = "",
    TextColor3 = COL.suave,
    TextSize = 11,
    TextXAlignment = Enum.TextXAlignment.Left,
}, barra)

local function dibujarMarcas(a)
    marcas:ClearAllChildren()
    local dur = duracion(a)
    if dur <= 0 then
        return
    end
    for _, kf in ipairs(a.keyframes) do
        nuevo("Frame", {
            Name = "Marca",
            Position = UDim2.new(kf.t / dur, -1, 0, 0),
            Size = UDim2.new(0, 2, 0, 6),
            BackgroundColor3 = COL.borde,
            BorderSizePixel = 0,
        }, marcas)
    end
end

-- arrastre de la pista
local arrastrando = false

local function buscarEn(px)
    local x0 = pista.AbsolutePosition.X
    local w = pista.AbsoluteSize.X
    if w <= 0 then
        return
    end
    local al = math.clamp((px - x0) / w, 0, 1)
    est.t = al * duracion(anim())
end

pista.InputBegan:Connect(function(input)
    if input.UserInputType == Enum.UserInputType.MouseButton1
        or input.UserInputType == Enum.UserInputType.Touch then
        arrastrando = true
        est.corriendo = false
        buscarEn(input.Position.X)
    end
end)

UserInputService.InputChanged:Connect(function(input)
    if arrastrando and (input.UserInputType == Enum.UserInputType.MouseMovement
        or input.UserInputType == Enum.UserInputType.Touch) then
        buscarEn(input.Position.X)
    end
end)

UserInputService.InputEnded:Connect(function(input)
    if input.UserInputType == Enum.UserInputType.MouseButton1
        or input.UserInputType == Enum.UserInputType.Touch then
        arrastrando = false
    end
end)

-- ------------------------------------------------------- panel diagnostico

local der = nuevo("Frame", {
    Name = "Diagnostico",
    Position = UDim2.new(1, -336, 0, 16),
    Size = UDim2.new(0, 320, 0, 300),
    BackgroundColor3 = COL.panel,
    BorderSizePixel = 0,
}, pantalla)
redondear(der, 12)
contorno(der)

local dTitulo = nuevo("TextLabel", {
    Name = "Titulo",
    Position = UDim2.new(0, 16, 0, 14),
    Size = UDim2.new(1, -32, 0, 20),
    BackgroundTransparency = 1,
    Font = Enum.Font.GothamBold,
    Text = "",
    TextColor3 = COL.texto,
    TextSize = 15,
    TextXAlignment = Enum.TextXAlignment.Left,
}, der)

local dMeta = nuevo("TextLabel", {
    Name = "Meta",
    Position = UDim2.new(0, 16, 0, 36),
    Size = UDim2.new(1, -32, 0, 34),
    BackgroundTransparency = 1,
    Font = Enum.Font.Gotham,
    Text = "",
    TextColor3 = COL.suave,
    TextSize = 11,
    TextXAlignment = Enum.TextXAlignment.Left,
    TextYAlignment = Enum.TextYAlignment.Top,
    TextWrapped = true,
}, der)

local dVeredicto = nuevo("TextLabel", {
    Name = "Veredicto",
    Position = UDim2.new(0, 16, 0, 78),
    Size = UDim2.new(1, -32, 0, 26),
    BackgroundColor3 = COL.bueno,
    BorderSizePixel = 0,
    Font = Enum.Font.GothamBold,
    Text = "",
    TextColor3 = COL.texto,
    TextSize = 12,
}, der)
redondear(dVeredicto, 6)

local dTexto = nuevo("TextLabel", {
    Name = "Texto",
    Position = UDim2.new(0, 16, 0, 114),
    Size = UDim2.new(1, -32, 1, -130),
    BackgroundTransparency = 1,
    Font = Enum.Font.Gotham,
    Text = "",
    TextColor3 = COL.suave,
    TextSize = 12,
    TextXAlignment = Enum.TextXAlignment.Left,
    TextYAlignment = Enum.TextYAlignment.Top,
    TextWrapped = true,
}, der)

-- rotulos sobre los maniquis
local function rotulo(texto, col)
    local b = nuevo("BillboardGui", {
        Name = "Rotulo",
        Size = UDim2.new(0, 220, 0, 30),
        StudsOffsetWorldSpace = Vector3.new(0, 4.4, 0),
        AlwaysOnTop = true,
    }, escena)
    local f = nuevo("TextLabel", {
        Size = UDim2.new(1, 0, 1, 0),
        BackgroundColor3 = col,
        BorderSizePixel = 0,
        Font = Enum.Font.GothamBold,
        Text = texto,
        TextColor3 = COL.texto,
        TextSize = 13,
    }, b)
    redondear(f, 6)
    return b
end

local rotA = rotulo("REPOSITORIO: ALTERNA BIEN", COL.bueno)
local rotB = rotulo("ERROR TIPICO: VAN EN FASE", COL.malo)

-- ------------------------------------------------------------- panel reto

local pReto = nuevo("Frame", {
    Name = "Reto",
    Position = UDim2.new(1, -336, 0, 16),
    Size = UDim2.new(0, 320, 0, 330),
    BackgroundColor3 = COL.panel,
    BorderSizePixel = 0,
    Visible = false,
}, pantalla)
redondear(pReto, 12)
contorno(pReto)

nuevo("TextLabel", {
    Position = UDim2.new(0, 16, 0, 14),
    Size = UDim2.new(1, -32, 0, 20),
    BackgroundTransparency = 1,
    Font = Enum.Font.GothamBold,
    Text = "RETO DE FASE",
    TextColor3 = COL.texto,
    TextSize = 15,
    TextXAlignment = Enum.TextXAlignment.Left,
}, pReto)

local rReloj = nuevo("TextLabel", {
    Position = UDim2.new(0, 16, 0, 40),
    Size = UDim2.new(1, -32, 0, 40),
    BackgroundTransparency = 1,
    Font = Enum.Font.GothamBold,
    Text = "60",
    TextColor3 = COL.acento,
    TextSize = 34,
    TextXAlignment = Enum.TextXAlignment.Left,
}, pReto)

local rMarcador = nuevo("TextLabel", {
    Position = UDim2.new(0, 16, 0, 84),
    Size = UDim2.new(1, -32, 0, 18),
    BackgroundTransparency = 1,
    Font = Enum.Font.Gotham,
    Text = "",
    TextColor3 = COL.suave,
    TextSize = 12,
    TextXAlignment = Enum.TextXAlignment.Left,
}, pReto)

nuevo("TextLabel", {
    Position = UDim2.new(0, 16, 0, 112),
    Size = UDim2.new(1, -32, 0, 36),
    BackgroundTransparency = 1,
    Font = Enum.Font.Gotham,
    Text = "Mira el maniqui. Brazos y piernas, alternan o van juntos?",
    TextColor3 = COL.texto,
    TextSize = 12,
    TextXAlignment = Enum.TextXAlignment.Left,
    TextYAlignment = Enum.TextYAlignment.Top,
    TextWrapped = true,
}, pReto)

local btnBien = nuevo("TextButton", {
    Position = UDim2.new(0, 16, 0, 156),
    Size = UDim2.new(1, -32, 0, 40),
    BackgroundColor3 = COL.bueno,
    BorderSizePixel = 0,
    AutoButtonColor = false,
    Font = Enum.Font.GothamBold,
    Text = "ALTERNAN BIEN",
    TextColor3 = COL.texto,
    TextSize = 13,
}, pReto)
redondear(btnBien, 8)

local btnMal = nuevo("TextButton", {
    Position = UDim2.new(0, 16, 0, 202),
    Size = UDim2.new(1, -32, 0, 40),
    BackgroundColor3 = COL.malo,
    BorderSizePixel = 0,
    AutoButtonColor = false,
    Font = Enum.Font.GothamBold,
    Text = "VAN EN FASE",
    TextColor3 = COL.texto,
    TextSize = 13,
}, pReto)
redondear(btnMal, 8)

local rAviso = nuevo("TextLabel", {
    Position = UDim2.new(0, 16, 0, 250),
    Size = UDim2.new(1, -32, 0, 64),
    BackgroundTransparency = 1,
    Font = Enum.Font.GothamMedium,
    Text = "",
    TextColor3 = COL.suave,
    TextSize = 12,
    TextXAlignment = Enum.TextXAlignment.Left,
    TextYAlignment = Enum.TextYAlignment.Top,
    TextWrapped = true,
}, pReto)

-- --------------------------------------------------------------- interfaz

local function pintarSeleccion()
    for i, b in ipairs(botones) do
        if i == est.sel then
            b.BackgroundColor3 = COL.acento
        else
            b.BackgroundColor3 = COL.panel2
        end
    end
end

local function refrescarPanel()
    local a = anim()
    dTitulo.Text = a.titulo
    dMeta.Text = string.format(
        "%s   %s   %d keyframes   %.2f s\nnombre interno: %s\neasing %s   prioridad %s",
        a.rig, a.loop and "en bucle" or "una vez", #a.keyframes,
        duracion(a), a.nombre, a.easing, a.prioridad)

    local lineas = {}
    if a.fases and #a.fases > 0 then
        table.insert(lineas, "FASE MEDIDA SOBRE LA POSICION REAL")
        for _, f in ipairs(a.fases) do
            local r = "sin vaiven"
            if f.r then
                r = string.format("r = %+.2f", f.r)
            end
            table.insert(lineas, "  " .. f.par .. ": " .. f.veredicto
                .. "  (" .. r .. ")")
        end
        table.insert(lineas, "")
    end
    table.insert(lineas, Datos.convenciones[a.rig] or "")

    if #a.defectos > 0 then
        dVeredicto.BackgroundColor3 = COL.malo
        dVeredicto.Text = "DEFECTO: " .. table.concat(a.defectos, " + ")
    elseif #a.avisos > 0 then
        dVeredicto.BackgroundColor3 = COL.aviso
        dVeredicto.Text = "CORRECTA, CON AVISO"
        table.insert(lineas, "")
        table.insert(lineas, "AVISO: " .. table.concat(a.avisos, "; "))
    else
        dVeredicto.BackgroundColor3 = COL.bueno
        dVeredicto.Text = a.ciclo and "CICLO CORRECTO" or "CORRECTA"
    end
    dTexto.Text = table.concat(lineas, "\n")
    dibujarMarcas(a)
    pintarSeleccion()
end

local function refrescarBotones()
    btnPlay.Text = est.corriendo and "PAUSA" or "SEGUIR"
    btnBucle.Text = est.bucle and "BUCLE: SI" or "BUCLE: NO"
    btnVel.Text = "VEL " .. tostring(est.vel) .. "x"
    btnComp.Text = est.comparar and "COMPARAR: SI" or "COMPARAR: NO"
end

-- ------------------------------------------------------------------ camara

local orbita = true
local giro = math.rad(20)
local alturaCam = 5.5
local dist = 22
local foco = Vector3.new(0, SUELO + 3.5, 0)
local girando = false

btnCam.MouseButton1Click:Connect(function()
    orbita = not orbita
    btnCam.Text = orbita and "ORBITA: SI" or "ORBITA: NO"
    if orbita then
        camara.CameraType = Enum.CameraType.Scriptable
    else
        camara.CameraType = Enum.CameraType.Custom
    end
end)

UserInputService.InputBegan:Connect(function(input, capturado)
    if capturado then
        return
    end
    if input.UserInputType == Enum.UserInputType.MouseButton2 then
        girando = true
    end
end)

UserInputService.InputEnded:Connect(function(input)
    if input.UserInputType == Enum.UserInputType.MouseButton2 then
        girando = false
    end
end)

UserInputService.InputChanged:Connect(function(input, capturado)
    if input.UserInputType == Enum.UserInputType.MouseWheel then
        dist = math.clamp(dist - input.Position.Z * 2, 8, 48)
    elseif girando
        and input.UserInputType == Enum.UserInputType.MouseMovement then
        giro = giro - input.Delta.X * 0.006
        alturaCam = math.clamp(alturaCam + input.Delta.Y * 0.04, -2, 16)
    end
end)

-- ------------------------------------------------------------------- reto

local conRoto = {}
for i, a in ipairs(ANIMS) do
    if a.roto then
        table.insert(conRoto, i)
    end
end

local function siguienteRonda()
    reto.esperando = false
    rAviso.Text = ""
    -- Solo entran los ciclos que tienen variante de contraste, y la mitad de
    -- las veces se ensena la rota. Asi no vale memorizar la lista.
    if #conRoto > 0 then
        est.sel = conRoto[math.random(1, #conRoto)]
        reto.mostrandoRoto = math.random() < 0.5
    else
        est.sel = math.random(1, #ANIMS)
        reto.mostrandoRoto = false
    end
    est.t = 0
    est.corriendo = true
    refrescarPanel()
end

-- "Correcta" quiere decir que lo que se ve alterna. El dato del repositorio
-- alterna; la variante rota mueve los dos miembros a la vez.
local function verdadActual()
    return not reto.mostrandoRoto
end

local function responder(dijoBien)
    if not reto.activo or reto.esperando then
        return
    end
    reto.esperando = true
    reto.rondas = reto.rondas + 1
    local verdad = verdadActual()
    if dijoBien == verdad then
        reto.aciertos = reto.aciertos + 1
        reto.racha = reto.racha + 1
        reto.puntos = reto.puntos + 10 + math.min(reto.racha, 5) * 2
        if reto.racha > reto.mejorRacha then
            reto.mejorRacha = reto.racha
        end
        rAviso.TextColor3 = COL.bueno
        rAviso.Text = "Correcto. " .. anim().titulo
            .. (reto.mostrandoRoto and " (variante rota)"
                or " (dato del repositorio)")
    else
        reto.racha = 0
        rAviso.TextColor3 = COL.malo
        local a = anim()
        if verdad then
            rAviso.Text = "Fallo. Era " .. a.titulo
                .. " tal cual esta en el repositorio, y si alterna."
        else
            rAviso.Text = "Fallo. Era la variante rota de " .. a.titulo
                .. ": los dos miembros iban a la vez."
        end
    end
    task.delay(1.4, function()
        if reto.activo then
            siguienteRonda()
        end
    end)
end

btnBien.MouseButton1Click:Connect(function()
    responder(true)
end)
btnMal.MouseButton1Click:Connect(function()
    responder(false)
end)

local function terminarReto()
    reto.activo = false
    local prec = 0
    if reto.rondas > 0 then
        prec = math.floor(reto.aciertos / reto.rondas * 100 + 0.5)
    end
    rAviso.TextColor3 = COL.texto
    rAviso.Text = string.format(
        "Fin. %d puntos, %d de %d aciertos (%d%%), mejor racha %d.",
        reto.puntos, reto.aciertos, reto.rondas, prec, reto.mejorRacha)
    rReloj.Text = "0"
end

local function entrarModo(m)
    est.modo = m
    if m == "reto" then
        pReto.Visible = true
        der.Visible = false
        barra.Visible = false
        btnModo.Text = "VOLVER AL VISOR"
        btnModo.BackgroundColor3 = COL.panel2
        est.comparar = false
        -- azul neutro: el color no debe delatar la respuesta
        ranuras.A.paleta = Rig.PALETAS.r15
        ocultar("A")
        ocultar("B")
        reto.activo = true
        reto.puntos = 0
        reto.racha = 0
        reto.mejorRacha = 0
        reto.aciertos = 0
        reto.rondas = 0
        reto.resta = 60
        siguienteRonda()
    else
        pReto.Visible = false
        der.Visible = true
        barra.Visible = true
        btnModo.Text = "JUGAR EL RETO DE FASE"
        btnModo.BackgroundColor3 = COL.acento
        est.comparar = true
        reto.activo = false
        ranuras.A.paleta = Rig.PALETAS.corregido
        ocultar("A")
        refrescarPanel()
    end
    refrescarBotones()
end

btnModo.MouseButton1Click:Connect(function()
    if est.modo == "visor" then
        entrarModo("reto")
    else
        entrarModo("visor")
    end
end)

-- --------------------------------------------------------------- controles

btnPlay.MouseButton1Click:Connect(function()
    est.corriendo = not est.corriendo
    refrescarBotones()
end)

btnReset.MouseButton1Click:Connect(function()
    est.t = 0
end)

btnBucle.MouseButton1Click:Connect(function()
    est.bucle = not est.bucle
    refrescarBotones()
end)

btnVel.MouseButton1Click:Connect(function()
    velIdx = velIdx % #VELS + 1
    est.vel = VELS[velIdx]
    refrescarBotones()
end)

btnComp.MouseButton1Click:Connect(function()
    est.comparar = not est.comparar
    refrescarBotones()
end)

UserInputService.InputBegan:Connect(function(input, capturado)
    if capturado or input.UserInputType ~= Enum.UserInputType.Keyboard then
        return
    end
    if input.KeyCode == Enum.KeyCode.Space then
        est.corriendo = not est.corriendo
        refrescarBotones()
    elseif input.KeyCode == Enum.KeyCode.R then
        est.t = 0
    elseif input.KeyCode == Enum.KeyCode.Down then
        est.sel = est.sel % #ANIMS + 1
        est.t = 0
        refrescarPanel()
    elseif input.KeyCode == Enum.KeyCode.Up then
        est.sel = (est.sel - 2) % #ANIMS + 1
        est.t = 0
        refrescarPanel()
    end
end)

-- -------------------------------------------------------------- bucle vivo

camara.CameraType = Enum.CameraType.Scriptable
refrescarBotones()
refrescarPanel()

RunService.RenderStepped:Connect(function(dt)
    local a = anim()
    local dur = duracion(a)

    -- tiempo
    if est.corriendo and dur > 0 then
        est.t = est.t + dt * est.vel
        if est.t > dur then
            if est.bucle or est.modo == "reto" then
                est.t = est.t % dur
            else
                est.t = dur
                est.corriendo = false
                refrescarBotones()
            end
        end
    end

    -- que maniqui mostramos en cada ranura
    local kfsA, kfsB
    if est.modo == "reto" then
        kfsA = (reto.mostrandoRoto and a.roto) or a.keyframes
        kfsB = nil
    else
        kfsA = a.keyframes
        if est.comparar and a.roto then
            kfsB = a.roto
        end
    end

    local rigA = asegurar("A", a.rig)
    if kfsA and rigA then
        Rig.aplicar(rigA, Rig.evaluar(kfsA, est.t, a.easing))
    end

    if kfsB then
        local rigB = asegurar("B", a.rig)
        if rigB then
            Rig.aplicar(rigB, Rig.evaluar(kfsB, est.t, a.easing))
        end
    else
        ocultar("B")
    end

    -- rotulos
    if rigA and rigA.partes[a.rig == "R15" and "UpperTorso" or "Torso"] then
        rotA.Adornee = rigA.partes[a.rig == "R15" and "UpperTorso" or "Torso"]
    end
    if est.modo == "reto" then
        rotA.Enabled = false
        rotB.Enabled = false
    else
        rotA.Enabled = kfsB ~= nil
        rotB.Enabled = kfsB ~= nil
        if kfsB and ranuras.B.rig then
            local nb = a.rig == "R15" and "UpperTorso" or "Torso"
            rotB.Adornee = ranuras.B.rig.partes[nb]
        end
    end

    -- pista
    if dur > 0 then
        relleno.Size = UDim2.new(math.clamp(est.t / dur, 0, 1), 0, 1, 0)
        lblTiempo.Text = string.format(
            "t = %.3f s de %.2f s      keyframe %d de %d",
            est.t, dur, Rig.indice(a.keyframes, est.t), #a.keyframes)
    end

    -- reloj del reto
    if reto.activo then
        reto.resta = reto.resta - dt
        if reto.resta <= 0 then
            reto.resta = 0
            terminarReto()
        end
        rReloj.Text = tostring(math.max(0, math.ceil(reto.resta)))
        rMarcador.Text = string.format(
            "%d puntos   |   racha %d   |   ronda %d",
            reto.puntos, reto.racha, reto.rondas + 1)
    end

    -- camara
    if orbita then
        if not girando then
            giro = giro + dt * 0.12
        end
        local ancho = (kfsB ~= nil) and 1 or 0
        local centro = Vector3.new(ancho == 1 and 0 or -7, foco.Y, foco.Z)
        local d = dist + (ancho == 1 and 6 or 0)
        local pos = centro + Vector3.new(
            math.sin(giro) * d, alturaCam, math.cos(giro) * d)
        camara.CFrame = CFrame.lookAt(pos, centro)
    end
end)

print("[Banco] listo: " .. #ANIMS .. " modelos, "
    .. #conRoto .. " con variante de contraste")
