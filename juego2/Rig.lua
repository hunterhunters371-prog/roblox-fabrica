-- TIPO: ModuleScript
-- RUTA: PlayerGui > Interfaz > Rig
--
-- Construye maniquis R6 y R15 y los mueve con cinematica directa: calcula
-- la CFrame de cada parte a partir de su padre en lugar de dejar que lo
-- haga el solver de fisica. Asi el resultado es identico en Studio y en
-- ejecucion, y ninguna colision puede deformar la pose.
--
-- Formula por parte:  mundoHijo = mundoPadre * c0 * pose * c1:Inverse()
-- Es la misma que aplica un Motor6D, solo que evaluada a mano.

local TweenService = game:GetService("TweenService")

local M = {}

local PI = math.pi
local rad = math.rad
local ang = CFrame.fromEulerAnglesXYZ
local CF = CFrame.new
local V3 = Vector3.new

M.CERO = {0, 0, 0, 0, 0, 0}

-- ---------------------------------------------------------------- paletas

M.PALETAS = {
    original = {
        cuerpo = Color3.fromRGB(196, 74, 74),
        cabeza = Color3.fromRGB(232, 190, 96),
        brazo = Color3.fromRGB(232, 190, 96),
        pierna = Color3.fromRGB(78, 88, 110),
    },
    corregido = {
        cuerpo = Color3.fromRGB(62, 152, 110),
        cabeza = Color3.fromRGB(232, 190, 96),
        brazo = Color3.fromRGB(232, 190, 96),
        pierna = Color3.fromRGB(64, 92, 88),
    },
    r15 = {
        cuerpo = Color3.fromRGB(58, 108, 178),
        cabeza = Color3.fromRGB(232, 190, 96),
        brazo = Color3.fromRGB(232, 190, 96),
        pierna = Color3.fromRGB(70, 80, 104),
    },
}

-- ------------------------------------------------------------ definiciones

-- R6: los c0/c1 llevan las rotaciones del rig real de Roblox. Se anulan en
-- la pose de reposo (c0 * c1:Inverse() queda traslacion pura) pero conjugan
-- la rotacion de la pose, y eso es lo que hace que en R6 el eje Z sea el
-- vaiven adelante/atras y el eje X la elevacion lateral, tal como documenta
-- el repositorio.
M.R6 = {
    nombre = "R6",
    raiz = "HumanoidRootPart",
    altura = 3,
    partes = {
        {nombre = "HumanoidRootPart", tam = V3(2, 2, 1), oculto = true},
        {nombre = "Torso", padre = "HumanoidRootPart", tam = V3(2, 2, 1),
         tono = "cuerpo", c0 = ang(-PI / 2, 0, PI), c1 = ang(-PI / 2, 0, PI)},
        {nombre = "Head", padre = "Torso", tam = V3(2, 1, 1), tono = "cabeza",
         c0 = CF(0, 1, 0) * ang(-PI / 2, 0, PI),
         c1 = CF(0, -0.5, 0) * ang(-PI / 2, 0, PI)},
        {nombre = "Right Arm", padre = "Torso", tam = V3(1, 2, 1),
         tono = "brazo",
         c0 = CF(1, 0.5, 0) * ang(0, PI / 2, 0),
         c1 = CF(-0.5, 0.5, 0) * ang(0, PI / 2, 0)},
        {nombre = "Left Arm", padre = "Torso", tam = V3(1, 2, 1),
         tono = "brazo",
         c0 = CF(-1, 0.5, 0) * ang(0, -PI / 2, 0),
         c1 = CF(0.5, 0.5, 0) * ang(0, -PI / 2, 0)},
        {nombre = "Right Leg", padre = "Torso", tam = V3(1, 2, 1),
         tono = "pierna",
         c0 = CF(1, -1, 0) * ang(0, PI / 2, 0),
         c1 = CF(0.5, 1, 0) * ang(0, PI / 2, 0)},
        {nombre = "Left Leg", padre = "Torso", tam = V3(1, 2, 1),
         tono = "pierna",
         c0 = CF(-1, -1, 0) * ang(0, -PI / 2, 0),
         c1 = CF(-0.5, 1, 0) * ang(0, -PI / 2, 0)},
    },
}

-- R15: articulaciones alineadas con los ejes del mundo, que es la
-- convencion que usan los modelos R15 del repositorio (X adelante/atras,
-- Z elevacion lateral).
M.R15 = {
    nombre = "R15",
    raiz = "HumanoidRootPart",
    altura = 3.5,
    partes = {
        {nombre = "HumanoidRootPart", tam = V3(2, 2, 1), oculto = true},
        {nombre = "LowerTorso", padre = "HumanoidRootPart",
         tam = V3(2, 0.8, 1), tono = "cuerpo", c0 = CF(), c1 = CF()},
        {nombre = "UpperTorso", padre = "LowerTorso", tam = V3(2, 1.6, 1),
         tono = "cuerpo", c0 = CF(0, 0.4, 0), c1 = CF(0, -0.8, 0)},
        {nombre = "Head", padre = "UpperTorso", tam = V3(1.2, 1.2, 1.2),
         tono = "cabeza", c0 = CF(0, 0.8, 0), c1 = CF(0, -0.6, 0)},

        {nombre = "RightUpperArm", padre = "UpperTorso",
         tam = V3(0.9, 1.2, 0.9), tono = "brazo",
         c0 = CF(1.45, 0.55, 0), c1 = CF(0, 0.6, 0)},
        {nombre = "RightLowerArm", padre = "RightUpperArm",
         tam = V3(0.8, 1.1, 0.8), tono = "brazo",
         c0 = CF(0, -0.6, 0), c1 = CF(0, 0.55, 0)},
        {nombre = "RightHand", padre = "RightLowerArm",
         tam = V3(0.9, 0.4, 0.9), tono = "brazo",
         c0 = CF(0, -0.55, 0), c1 = CF(0, 0.2, 0)},

        {nombre = "LeftUpperArm", padre = "UpperTorso",
         tam = V3(0.9, 1.2, 0.9), tono = "brazo",
         c0 = CF(-1.45, 0.55, 0), c1 = CF(0, 0.6, 0)},
        {nombre = "LeftLowerArm", padre = "LeftUpperArm",
         tam = V3(0.8, 1.1, 0.8), tono = "brazo",
         c0 = CF(0, -0.6, 0), c1 = CF(0, 0.55, 0)},
        {nombre = "LeftHand", padre = "LeftLowerArm",
         tam = V3(0.9, 0.4, 0.9), tono = "brazo",
         c0 = CF(0, -0.55, 0), c1 = CF(0, 0.2, 0)},

        {nombre = "RightUpperLeg", padre = "LowerTorso",
         tam = V3(1, 1.4, 1), tono = "pierna",
         c0 = CF(0.5, -0.4, 0), c1 = CF(0, 0.7, 0)},
        {nombre = "RightLowerLeg", padre = "RightUpperLeg",
         tam = V3(0.9, 1.3, 0.9), tono = "pierna",
         c0 = CF(0, -0.7, 0), c1 = CF(0, 0.65, 0)},
        {nombre = "RightFoot", padre = "RightLowerLeg",
         tam = V3(1, 0.4, 1.1), tono = "pierna",
         c0 = CF(0, -0.65, 0), c1 = CF(0, 0.2, 0)},

        {nombre = "LeftUpperLeg", padre = "LowerTorso",
         tam = V3(1, 1.4, 1), tono = "pierna",
         c0 = CF(-0.5, -0.4, 0), c1 = CF(0, 0.7, 0)},
        {nombre = "LeftLowerLeg", padre = "LeftUpperLeg",
         tam = V3(0.9, 1.3, 0.9), tono = "pierna",
         c0 = CF(0, -0.7, 0), c1 = CF(0, 0.65, 0)},
        {nombre = "LeftFoot", padre = "LeftLowerLeg",
         tam = V3(1, 0.4, 1.1), tono = "pierna",
         c0 = CF(0, -0.65, 0), c1 = CF(0, 0.2, 0)},
    },
}

function M.definicion(rig)
    if rig == "R15" then
        return M.R15
    end
    return M.R6
 end

-- ------------------------------------------------------------ construccion

function M.construir(def, cfBase, padre, nombre, paleta)
    local pal = paleta or M.PALETAS.original
    local modelo = Instance.new("Model")
    modelo.Name = nombre

    local partes = {}
    for _, p in ipairs(def.partes) do
        local parte = Instance.new("Part")
        parte.Name = p.nombre
        parte.Size = p.tam
        parte.Anchored = true
        parte.CanCollide = false
        parte.CanTouch = false
        parte.CastShadow = not p.oculto
        parte.Material = Enum.Material.SmoothPlastic
        parte.TopSurface = Enum.SurfaceType.Smooth
        parte.BottomSurface = Enum.SurfaceType.Smooth
        parte.Color = pal[p.tono] or Color3.fromRGB(160, 160, 160)
        if p.oculto then
            parte.Transparency = 1
        end
        parte.Parent = modelo
        partes[p.nombre] = parte
    end

    modelo.PrimaryPart = partes[def.raiz]
    modelo.Parent = padre

    local rig = {
        def = def,
        modelo = modelo,
        partes = partes,
        base = cfBase,
    }
    M.aplicar(rig, nil)
    return rig
end

function M.destruir(rig)
    if rig and rig.modelo then
        rig.modelo:Destroy()
    end
end

-- ---------------------------------------------------------------- cinematica

local function poseCF(v)
    if not v then
        return CF()
    end
    return CF(v[4] or 0, v[5] or 0, v[6] or 0)
        * ang(rad(v[1] or 0), rad(v[2] or 0), rad(v[3] or 0))
end
M.poseCF = poseCF

-- Recorre las partes en orden (padres antes que hijos) y coloca cada una.
function M.aplicar(rig, poses)
    local def = rig.def
    local mundo = {}
    for _, p in ipairs(def.partes) do
        local parte = rig.partes[p.nombre]
        if parte then
            local cf
            if not p.padre then
                cf = rig.base
            else
                local cfPadre = mundo[p.padre] or rig.base
                local pose = poses and poses[p.nombre] or nil
                cf = cfPadre * p.c0 * poseCF(pose) * p.c1:Inverse()
            end
            mundo[p.nombre] = cf
            parte.CFrame = cf
        end
    end
end

function M.mover(rig, cfBase)
    rig.base = cfBase
end

-- ------------------------------------------------------------------ easing

local ESTILOS = {
    suave = {Enum.EasingStyle.Sine, Enum.EasingDirection.InOut},
    lineal = {Enum.EasingStyle.Linear, Enum.EasingDirection.In},
    rebote = {Enum.EasingStyle.Bounce, Enum.EasingDirection.Out},
    elastica = {Enum.EasingStyle.Elastic, Enum.EasingDirection.Out},
}

function M.suavizar(al, easing)
    if easing == "instantaneo" then
        return 0
    end
    local e = ESTILOS[easing] or ESTILOS.suave
    local ok, v = pcall(TweenService.GetValue, TweenService, al, e[1], e[2])
    if ok and typeof(v) == "number" then
        return v
    end
    return al
end

-- ---------------------------------------------------------------- evaluacion

local function lerp6(a, b, al)
    local r = {}
    for i = 1, 6 do
        local va = a and a[i] or 0
        local vb = b and b[i] or 0
        r[i] = va + (vb - va) * al
    end
    return r
end

-- Devuelve la tabla articulacion -> {rx,ry,rz,px,py,pz} en el instante t.
function M.evaluar(kfs, t, easing)
    local n = #kfs
    if n == 0 then
        return {}
    end
    if n == 1 or t <= kfs[1].t then
        return kfs[1].poses
    end
    if t >= kfs[n].t then
        return kfs[n].poses
    end

    local i = 1
    while i < n - 1 and kfs[i + 1].t <= t do
        i = i + 1
    end
    local a, b = kfs[i], kfs[i + 1]
    local tramo = b.t - a.t
    local al = 0
    if tramo > 0 then
        al = (t - a.t) / tramo
    end
    al = M.suavizar(al, easing)

    local arts = {}
    for k in pairs(a.poses) do
        arts[k] = true
    end
    for k in pairs(b.poses) do
        arts[k] = true
    end

    local out = {}
    for art in pairs(arts) do
        out[art] = lerp6(a.poses[art], b.poses[art], al)
    end
    return out
end

-- Indice del keyframe activo, para mostrarlo en la interfaz.
function M.indice(kfs, t)
    local i = 1
    for k = 1, #kfs do
        if kfs[k].t <= t + 1e-6 then
            i = k
        end
    end
    return i
end

return M
