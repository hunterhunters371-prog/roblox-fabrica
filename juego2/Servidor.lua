-- TIPO: Script
-- RUTA: Workspace > BancoDeAnimaciones > Servidor
--
-- Prepara el escenario minimo (suelo, aparicion, luz) y entrega la interfaz
-- a cada jugador. La interfaz vive aqui como plantilla inerte: un
-- LocalScript dentro de Workspace no se ejecuta, solo arranca cuando la
-- copia llega a PlayerGui.

local Players = game:GetService("Players")
local Lighting = game:GetService("Lighting")

local raiz = script.Parent

local plantilla = raiz:WaitForChild("Interfaz", 10)
if not plantilla then
    warn("[Banco] no encuentro la plantilla Interfaz, no puedo arrancar")
    return
end

-- ------------------------------------------------------------------ suelo

if not workspace:FindFirstChild("SueloBanco") then
    local suelo = Instance.new("Part")
    suelo.Name = "SueloBanco"
    suelo.Size = Vector3.new(140, 1, 140)
    suelo.Position = Vector3.new(0, 0, 0)
    suelo.Anchored = true
    suelo.CanCollide = true
    suelo.Material = Enum.Material.Concrete
    suelo.Color = Color3.fromRGB(34, 37, 44)
    suelo.TopSurface = Enum.SurfaceType.Smooth
    suelo.BottomSurface = Enum.SurfaceType.Smooth
    suelo.Parent = workspace
end

if not workspace:FindFirstChildWhichIsA("SpawnLocation", true) then
    local ap = Instance.new("SpawnLocation")
    ap.Name = "AparicionBanco"
    ap.Size = Vector3.new(6, 1, 6)
    ap.Position = Vector3.new(0, 1, 20)
    ap.Anchored = true
    ap.Duration = 0
    ap.Material = Enum.Material.SmoothPlastic
    ap.Color = Color3.fromRGB(18, 138, 166)
    ap.TopSurface = Enum.SurfaceType.Smooth
    ap.BottomSurface = Enum.SurfaceType.Smooth
    ap.Parent = workspace
end

-- Luz neutra para que los maniquis se lean bien. Va en pcall porque
-- Lighting puede estar restringido segun la configuracion del lugar.
pcall(function()
    Lighting.Ambient = Color3.fromRGB(72, 76, 86)
    Lighting.OutdoorAmbient = Color3.fromRGB(84, 88, 100)
    Lighting.Brightness = 2
    Lighting.ClockTime = 15
    Lighting.GlobalShadows = true
end)

-- ------------------------------------------------------------- interfaz

local function equipar(jugador)
    local pg = jugador:WaitForChild("PlayerGui", 10)
    if not pg then
        warn("[Banco] sin PlayerGui para " .. jugador.Name)
        return
    end
    if pg:FindFirstChild("Interfaz") then
        return
    end
    local copia = plantilla:Clone()
    copia.Parent = pg
end

Players.PlayerAdded:Connect(equipar)

for _, p in ipairs(Players:GetPlayers()) do
    task.spawn(equipar, p)
end

print("[Banco] servidor listo")
