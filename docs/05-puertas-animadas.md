# Puertas animadas

Anadidas el 2 de septiembre de 2026. Viven enteras en `Cliente.lua` y se montan
solas en marcha dentro de `workspace.PuertasCliente`. El servidor no sabe que
existen.

## Que hay

| Puerta | Cantidad | Medidas | Mira hacia |
| --- | --- | --- | --- |
| `PuertaAlmacen` | 1 | 16 x 12 | el centro de la arena |
| `PuertaPunto1..8` | hasta 8 | 8 x 7 | el almacen |

Total verificado en marcha: 9 modelos y 198 piezas.

## Anatomia de cada puerta

- Dos `Pilar` de metal con una `Tira` de neon cada uno.
- Un `Dintel` de metal y un `Faro` de neon con `PointLight` de rango 30 y sin sombras.
- Un `Umbral` de neon en el suelo que pasa de transparencia 0.6 a 0.1 al abrirse.
- Una `Baliza` que gira a 150 grados por segundo solo mientras la puerta esta abierta.
- Dos `Hoja`, cada una un `Model` con `PrimaryPart`: `Panel` oscuro con reflectancia
  0.08, `Canto` de neon y tres `Galon` inclinados 20 grados.

## Logica de apertura

| Puerta | Se abre cuando | Color |
| --- | --- | --- |
| Almacen | el jugador esta a menos de `PUERTA_DISTANCIA_ABRE` (26 studs) | oro si aun caben cajas, cian si vas lleno |
| Punto k | hay un pedido vivo a menos de 8 studs de ese punto | verde normal, rojo si el pedido es urgente |

La apertura se interpola cada fotograma con factor `PUERTA_VELOCIDAD` (5.5) y las
hojas se separan `ancho * 0.52 * apertura` a cada lado.

## Por que no altera el juego

- Todas las piezas: `CanCollide=false`, `CanTouch=false`, `CanQuery=false`,
  `CastShadow=false`, `Anchored=true`. No estorban al andar, no disparan `Touched`
  y no aparecen en los `Raycast`.
- Solo existen en el cliente. No hay remotos nuevos ni trafico de red anadido.
- Leen el estado que ya llegaba (`cajas`, `cajasMaximas`, `pedidos`); no lo modifican.
- No se cambio ningun valor de juego de `Config`, solo se anadieron claves `PUERTA_*`.
- Coste por fotograma: dos `PivotTo` por puerta y solo si la apertura cambio de
  verdad (umbral de 0.0005). Los colores se repintan solo al cambiar de estado.

## Verificacion en marcha

```
modelos=9  piezas=198
ALMACEN   hueco=24.6  (cerrada 8)   dist=12.0   luz=3.03
PUNTOS    abiertos=3 de 8 -> P3 h=12.3 ; P4 h=12.3 ; P8 h=12.3   rgb=80,220,120
```

Tres puertas de punto abiertas coinciden con `PEDIDOS_ACTIVOS = 3`. Hueco cerrado
de una puerta de punto: 4. Abierto: 12.3. Consola sin errores.

## Como tocarlas

- Mas altas o anchas: `PUERTA_ANCHO`, `PUERTA_ALTO`, `PUERTA_PUNTO_ANCHO`, `PUERTA_PUNTO_ALTO`.
- Que abran antes o despues: `PUERTA_DISTANCIA_ABRE`.
- Mas lentas o mas secas: `PUERTA_VELOCIDAD`.
- Quitarlas del todo: borrar la llamada `moverPuertas(paso, ultimo)` de
  `RenderStepped` y el `task.spawn` de montaje. Nada mas depende de ellas.

## Enganche en el bucle de camara

La primera linea del `RenderStepped` del cliente:

```lua
table.insert(conexiones, Ejecucion.RenderStepped:Connect(function(paso)
    moverPuertas(paso, ultimo)
    acumulado = acumulado + paso
```

`ultimo` es la ultima copia del estado recibida por `eventoEstado.OnClientEvent`.

## Codigo completo

```lua
local Gente = game:GetService("Players")
local carpetaPuertas = nil
local puertas = { almacen = nil, puntos = {} }
local relojPuertas = 0

local function piezaPuerta(nombre, tamano, color, material, padre)
    local parte = Instance.new("Part")
    parte.Name = nombre
    parte.Size = tamano
    parte.Color = color
    parte.Material = material
    parte.Anchored = true
    parte.CanCollide = false
    parte.CanTouch = false
    parte.CanQuery = false
    parte.CastShadow = false
    parte.TopSurface = Enum.SurfaceType.Smooth
    parte.BottomSurface = Enum.SurfaceType.Smooth
    parte.Parent = padre
    return parte
end

local function hojaDePuerta(padre, base, lado, ancho, alto, color)
    local grosor = Config.PUERTA_GROSOR
    local hoja = Instance.new("Model")
    hoja.Name = "Hoja"
    local centro = base * CFrame.new(lado * ancho * 0.25, alto * 0.5, 0)
    local panel = piezaPuerta("Panel", Vector3.new(ancho * 0.5, alto, grosor), Config.COLOR_PANEL, Enum.Material.SmoothPlastic, hoja)
    panel.CFrame = centro
    panel.Reflectance = 0.08
    local canto = piezaPuerta("Canto", Vector3.new(0.2, alto, grosor + 0.14), color, Enum.Material.Neon, hoja)
    canto.CFrame = centro * CFrame.new(-lado * (ancho * 0.25 - 0.1), 0, 0)
    local neones = { canto }
    for fila = 1, 3 do
        local galon = piezaPuerta("Galon", Vector3.new(ancho * 0.28, alto * 0.045, grosor + 0.12), color, Enum.Material.Neon, hoja)
        galon.CFrame = centro * CFrame.new(0, (fila - 2) * alto * 0.24, 0) * CFrame.Angles(0, 0, math.rad(lado * 20))
        table.insert(neones, galon)
    end
    hoja.PrimaryPart = panel
    hoja.Parent = padre
    return { modelo = hoja, cerrada = centro, lado = lado, neones = neones }
end

local function armarPuerta(nombre, posicion, mirandoA, ancho, alto, color)
    local base = CFrame.lookAt(posicion, Vector3.new(mirandoA.X, posicion.Y, mirandoA.Z))
    local modelo = Instance.new("Model")
    modelo.Name = nombre
    local neones = {}
    for lado = -1, 1, 2 do
        local pilar = piezaPuerta("Pilar", Vector3.new(0.9, alto + 1.8, 1.3), Config.COLOR_MURO, Enum.Material.Metal, modelo)
        pilar.CFrame = base * CFrame.new(lado * (ancho * 0.5 + 0.45), (alto + 1.8) * 0.5, 0)
        local tira = piezaPuerta("Tira", Vector3.new(0.26, alto * 0.9, 1.42), color, Enum.Material.Neon, modelo)
        tira.CFrame = base * CFrame.new(lado * (ancho * 0.5 + 0.45), alto * 0.5, 0)
        table.insert(neones, tira)
    end
    local dintel = piezaPuerta("Dintel", Vector3.new(ancho + 2.6, 1.6, 1.5), Config.COLOR_MURO, Enum.Material.Metal, modelo)
    dintel.CFrame = base * CFrame.new(0, alto + 0.8, 0)
    local faro = piezaPuerta("Faro", Vector3.new(ancho + 1.4, 0.36, 1.6), color, Enum.Material.Neon, modelo)
    faro.CFrame = base * CFrame.new(0, alto + 0.08, 0)
    local umbral = piezaPuerta("Umbral", Vector3.new(ancho + 1.4, 0.14, 2.6), color, Enum.Material.Neon, modelo)
    umbral.CFrame = base * CFrame.new(0, 0.07, 0)
    umbral.Transparency = 0.6
    local baliza = piezaPuerta("Baliza", Vector3.new(ancho * 0.95, 0.18, 0.18), color, Enum.Material.Neon, modelo)
    baliza.CFrame = base * CFrame.new(0, alto + 1.9, 0)
    local luz = Instance.new("PointLight")
    luz.Color = color
    luz.Range = 30
    luz.Brightness = 0.8
    luz.Shadows = false
    luz.Parent = faro
    table.insert(neones, faro)
    table.insert(neones, umbral)
    table.insert(neones, baliza)
    local hojas = { hojaDePuerta(modelo, base, -1, ancho, alto, color), hojaDePuerta(modelo, base, 1, ancho, alto, color) }
    for _, hoja in ipairs(hojas) do
        for _, neon in ipairs(hoja.neones) do
            table.insert(neones, neon)
        end
    end
    modelo.Parent = carpetaPuertas
    return {
        base = base,
        ancho = ancho,
        hojas = hojas,
        neones = neones,
        luz = luz,
        umbral = umbral,
        baliza = baliza,
        balizaBase = baliza.CFrame,
        color = color,
        pintada = color,
        apertura = 0,
        objetivo = 0,
    }
end

local function montarPuertas()
    local almacen = workspace:FindFirstChild("Almacen", true)
    if not almacen or not almacen:IsA("BasePart") then
        return false
    end
    local arena = almacen.Parent
    carpetaPuertas = Instance.new("Folder")
    carpetaPuertas.Name = "PuertasCliente"
    carpetaPuertas.Parent = workspace
    local suelo = almacen.Position.Y - almacen.Size.Y * 0.5
    local centro = Vector3.new(0, suelo, 0)
    local hacia = Vector3.new(centro.X - almacen.Position.X, 0, centro.Z - almacen.Position.Z)
    if hacia.Magnitude < 1 then
        hacia = Vector3.new(0, 0, 1)
    end
    local frente = almacen.Position + hacia.Unit * (almacen.Size.X * 0.5 + 2)
    puertas.almacen = armarPuerta("PuertaAlmacen", Vector3.new(frente.X, suelo, frente.Z), centro, Config.PUERTA_ANCHO, Config.PUERTA_ALTO, Config.COLOR_ORO)
    for k = 1, Config.PUNTOS_ENTREGA do
        local punto = arena and arena:FindFirstChild("Punto" .. k, true)
        if punto and punto:IsA("BasePart") then
            local pie = Vector3.new(punto.Position.X, punto.Position.Y - punto.Size.Y * 0.5, punto.Position.Z)
            local marco = armarPuerta("PuertaPunto" .. k, pie, almacen.Position, Config.PUERTA_PUNTO_ANCHO, Config.PUERTA_PUNTO_ALTO, Config.COLOR_ACTIVO)
            marco.posicion = punto.Position
            table.insert(puertas.puntos, marco)
        end
    end
    return true
end

local function moverPuertas(paso, estado)
    if not carpetaPuertas then
        return
    end
    local datos = estado or {}
    relojPuertas = relojPuertas + paso
    local personaje = Gente.LocalPlayer.Character
    local raizViva = personaje and personaje:FindFirstChild("HumanoidRootPart")
    local principal = puertas.almacen
    if principal then
        local cerca = false
        if raizViva then
            local aqui = principal.base.Position
            local pos = raizViva.Position
            cerca = (Vector3.new(pos.X, aqui.Y, pos.Z) - aqui).Magnitude < Config.PUERTA_DISTANCIA_ABRE
        end
        local hayHueco = (datos.cajas or 0) < (datos.cajasMaximas or Config.CAJAS_MAXIMAS)
        principal.objetivo = (cerca and 1) or 0
        principal.color = (hayHueco and Config.COLOR_ORO) or Config.COLOR_NEON
    end
    for _, puerta in ipairs(puertas.puntos) do
        local activo = false
        local urgente = false
        for _, pedido in ipairs(datos.pedidos or {}) do
            if pedido.posicion and puerta.posicion and (pedido.posicion - puerta.posicion).Magnitude < 8 then
                activo = true
                urgente = pedido.urgente == true
            end
        end
        puerta.objetivo = (activo and 1) or 0
        puerta.color = (urgente and Config.COLOR_URGENTE) or Config.COLOR_ACTIVO
    end
    local latido = 0.6 + 0.4 * math.abs(math.sin(relojPuertas * 3.4))
    local giro = CFrame.Angles(0, math.rad(relojPuertas * 150), 0)
    local lista = { principal }
    for _, puerta in ipairs(puertas.puntos) do
        table.insert(lista, puerta)
    end
    for _, puerta in ipairs(lista) do
        local antes = puerta.apertura
        puerta.apertura = antes + (puerta.objetivo - antes) * math.min(1, paso * Config.PUERTA_VELOCIDAD)
        if math.abs(puerta.objetivo - puerta.apertura) < 0.002 then
            puerta.apertura = puerta.objetivo
        end
        if math.abs(puerta.apertura - antes) > 0.0005 then
            local recorrido = puerta.ancho * 0.52 * puerta.apertura
            for _, hoja in ipairs(puerta.hojas) do
                hoja.modelo:PivotTo(hoja.cerrada * CFrame.new(hoja.lado * recorrido, 0, 0))
            end
            puerta.umbral.Transparency = 0.6 - 0.5 * puerta.apertura
        end
        if puerta.pintada ~= puerta.color then
            for _, neon in ipairs(puerta.neones) do
                neon.Color = puerta.color
            end
            puerta.luz.Color = puerta.color
            puerta.pintada = puerta.color
        end
        puerta.luz.Brightness = 0.5 + 2.6 * puerta.apertura * latido
        if puerta.apertura > 0.02 then
            puerta.baliza.CFrame = puerta.balizaBase * giro
        end
    end
end

task.spawn(function()
    for _ = 1, 40 do
        if montarPuertas() then
            return
        end
        task.wait(1)
    end
end)
```
