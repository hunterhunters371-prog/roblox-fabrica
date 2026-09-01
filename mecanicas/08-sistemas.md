# 08 - Sistemas de juego

Modulo 8 del catalogo. Aqui se juntan los modulos anteriores en sistemas
completos: inventario, economia, rondas, NPC, misiones, pase de batalla.

Todos los ejemplos siguen el mismo principio, que es el mas importante de todo
el catalogo:

> **El servidor decide. El cliente pide y dibuja.**

Si un sistema tuyo permite que el cliente diga "tengo 5000 monedas" o "complete
la mision", ese sistema esta roto aunque funcione en tus pruebas.

## Indice

| # | Sistema | Para que |
|---|---|---|
| 1 | Modulo base reutilizable | El patron de todos los demas |
| 2 | Economia y moneda | La base de todo progreso |
| 3 | Inventario con autoridad de servidor | Objetos que no se duplican |
| 4 | Barra rapida | Equipar desde el inventario |
| 5 | Tienda | Comprar sin exploits |
| 6 | Recogibles | Monedas y objetos en el mundo |
| 7 | Misiones con progreso | Objetivos con seguimiento |
| 8 | Logros | Hitos permanentes |
| 9 | Recompensas diarias | Retencion |
| 10 | Pase de batalla | Ligado a interfaces/pase.json |
| 11 | Maquina de estados de ronda | El corazon de una partida |
| 12 | Temporizador sincronizado | El reloj de 60 segundos |
| 13 | Equipos | Teams y reaparicion |
| 14 | Entregas contra reloj | El bucle de LAST DELIVERY |
| 15 | Checkpoints y puertas con llave | Progresion espacial |
| 16 | NPC con pathfinding | Que se muevan por el mapa |
| 17 | Maquina de estados de NPC | Que se comporten |
| 18 | Oleadas de enemigos | Dificultad creciente |
| 19 | Tabla de clasificacion | Competicion |
| 20 | Comandos de chat | Herramientas rapidas |
| 21 | Comandos de administrador | Con lista blanca |
| 22 | Anticheat basico | Lo minimo razonable |

---

### 1. Modulo base reutilizable

- **Que es:** la plantilla que siguen todos los sistemas de este modulo.
- **Para que sirve:** que cada sistema tenga la misma forma y sea facil de
  encontrar, arrancar y limpiar.
- **Donde va:** ModuleScript en `ServerScriptService/Sistemas/<Nombre>`.
- **Codigo listo para pegar:**

```lua
--!strict
-- Plantilla de sistema del servidor
local Players = game:GetService("Players")

local Sistema = {}
Sistema.__index = Sistema

export type Sistema = typeof(setmetatable({} :: {
    nombre: string,
    conexiones: { RBXScriptConnection },
    activo: boolean,
}, Sistema))

function Sistema.nuevo(nombre: string): Sistema
    return setmetatable({
        nombre = nombre,
        conexiones = {},
        activo = false,
    }, Sistema)
end

-- guarda la conexion para poder limpiarla luego
function Sistema.escuchar(self: Sistema, senal: RBXScriptSignal, funcion: (...any) -> ())
    table.insert(self.conexiones, senal:Connect(funcion))
end

function Sistema.iniciar(self: Sistema)
    if self.activo then
        return
    end
    self.activo = true
    print("[" .. self.nombre .. "] iniciado")
end

function Sistema.detener(self: Sistema)
    for _, conexion in self.conexiones do
        conexion:Disconnect()
    end
    table.clear(self.conexiones)
    self.activo = false
    print("[" .. self.nombre .. "] detenido")
end

return Sistema
```

Y un arrancador unico que los carga a todos:

```lua
-- Script: ServerScriptService/Arranque
local carpeta = script.Parent:WaitForChild("Sistemas")

local cargados = {}

for _, modulo in carpeta:GetChildren() do
    if not modulo:IsA("ModuleScript") then
        continue
    end

    local ok, resultado = pcall(require, modulo)
    if not ok then
        warn("Fallo al cargar " .. modulo.Name .. ": " .. tostring(resultado))
        continue
    end

    cargados[modulo.Name] = resultado
end

-- iniciar despues de cargarlos todos, por si dependen entre si
for nombre, sistema in cargados do
    if type(sistema) == "table" and type(sistema.iniciar) == "function" then
        local ok, err = pcall(function()
            sistema:iniciar()
        end)
        if not ok then
            warn("Fallo al iniciar " .. nombre .. ": " .. tostring(err))
        end
    end
end
```

- **Errores frecuentes:**
  - `require` sin `pcall`: un modulo con un error tumba el arranque entero y
    ningun sistema funciona.
  - Iniciar cada modulo segun se carga: si el sistema A necesita al B y B aun no
    esta cargado, falla. Carga todo primero, inicia despues.
  - Modulos que se requieren en circulo: `A` pide `B` y `B` pide `A`. Roblox
    lanza "Requested module experienced an error". Rompe el ciclo con eventos.
- **Checklist sin errores:**
  - [ ] Todo `require` esta en `pcall`
  - [ ] Carga y arranque son fases separadas
  - [ ] No hay dependencias circulares

---

### 2. Economia y moneda

- **Que es:** el sistema que anade y quita monedas.
- **Para que sirve:** que **una sola parte del codigo** toque el saldo. Si
  quince scripts suman monedas por su cuenta, no podras auditar nada.
- **Codigo listo para pegar:**

```lua
--!strict
local Players = game:GetService("Players")
local Datos = require(game.ServerScriptService.Datos)

local Economia = {}

local MAXIMO = 1000000000
local registro: { { jugador: string, cambio: number, motivo: string, momento: number } } = {}

local function reflejar(jugador: Player, saldo: number)
    jugador:SetAttribute("Monedas", saldo)

    local stats = jugador:FindFirstChild("leaderstats")
    local valor = stats and stats:FindFirstChild("Monedas")
    if valor and valor:IsA("IntValue") then
        valor.Value = saldo
    end
end

function Economia.saldo(jugador: Player): number
    local datos = Datos.obtener(jugador)
    return datos and datos.monedas or 0
end

function Economia.anadir(jugador: Player, cantidad: number, motivo: string): boolean
    if typeof(cantidad) ~= "number" or cantidad ~= cantidad or cantidad <= 0 then
        warn("Cantidad invalida al anadir: " .. tostring(cantidad))
        return false
    end

    local datos = Datos.obtener(jugador)
    if not datos then
        return false
    end

    datos.monedas = math.min(datos.monedas + math.floor(cantidad), MAXIMO)
    reflejar(jugador, datos.monedas)

    table.insert(registro, {
        jugador = jugador.Name,
        cambio = cantidad,
        motivo = motivo,
        momento = os.time(),
    })

    return true
end

-- Devuelve true SOLO si habia suficiente y se cobro
function Economia.cobrar(jugador: Player, cantidad: number, motivo: string): boolean
    if typeof(cantidad) ~= "number" or cantidad ~= cantidad or cantidad <= 0 then
        return false
    end

    local datos = Datos.obtener(jugador)
    if not datos then
        return false
    end

    cantidad = math.floor(cantidad)

    if datos.monedas < cantidad then
        return false -- no alcanza
    end

    datos.monedas -= cantidad
    reflejar(jugador, datos.monedas)

    table.insert(registro, {
        jugador = jugador.Name,
        cambio = -cantidad,
        motivo = motivo,
        momento = os.time(),
    })

    return true
end

function Economia.puedePagar(jugador: Player, cantidad: number): boolean
    return Economia.saldo(jugador) >= cantidad
end

Players.PlayerAdded:Connect(function(jugador)
    task.defer(function()
        reflejar(jugador, Economia.saldo(jugador))
    end)
end)

return Economia
```

- **Errores frecuentes:**
  - Comprobar el saldo y cobrar en dos pasos separados en el tiempo: entre uno y
    otro pueden entrar dos peticiones y el jugador compra dos cosas con el
    dinero de una. `cobrar` comprueba y descuenta en la misma funcion, sin
    esperas en medio.
  - Aceptar cantidades negativas: "cobrar -1000" se convierte en un regalo.
  - Aceptar `nan` o `inf`: la comparacion `datos.monedas < nan` es falsa y pasa
    el filtro. Por eso esta la comprobacion `cantidad ~= cantidad`.
  - Usar el `IntValue` de leaderstats como fuente de verdad: es un reflejo.
  - No registrar los cambios: cuando alguien reporte un fallo, no tendras nada.
- **Checklist sin errores:**
  - [ ] Comprobar y cobrar ocurren juntos, sin esperas en medio
  - [ ] Se rechazan cantidades negativas, cero, `nan` e infinito
  - [ ] Todo pasa por este modulo
  - [ ] Hay registro de movimientos

---

### 3. Inventario con autoridad de servidor

- **Que es:** la lista de objetos de un jugador, viviendo en el servidor.
- **Codigo listo para pegar:**

```lua
--!strict
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Datos = require(game.ServerScriptService.Datos)

local Inventario = {}

local CATALOGO = {
    caja_pequena = { nombre = "Caja pequena", apilable = true, maximo = 20, peso = 1 },
    caja_grande = { nombre = "Caja grande", apilable = true, maximo = 5, peso = 4 },
    mochila = { nombre = "Mochila rapida", apilable = false, maximo = 1, peso = 0 },
}

local CAPACIDAD_BASE = 12

local function bolsa(jugador: Player)
    local datos = Datos.obtener(jugador)
    if not datos then
        return nil
    end
    datos.inventario = datos.inventario or {}
    return datos.inventario
end

function Inventario.existe(id: string): boolean
    return CATALOGO[id] ~= nil
end

function Inventario.cantidad(jugador: Player, id: string): number
    local b = bolsa(jugador)
    return b and b[id] or 0
end

function Inventario.pesoTotal(jugador: Player): number
    local b = bolsa(jugador)
    if not b then
        return 0
    end

    local total = 0
    for id, cantidad in b do
        local def = CATALOGO[id]
        if def then
            total += def.peso * cantidad
        end
    end
    return total
end

function Inventario.anadir(jugador: Player, id: string, cantidad: number): (boolean, string?)
    local def = CATALOGO[id]
    if not def then
        return false, "Objeto desconocido"
    end
    if typeof(cantidad) ~= "number" or cantidad ~= math.floor(cantidad) or cantidad <= 0 then
        return false, "Cantidad invalida"
    end

    local b = bolsa(jugador)
    if not b then
        return false, "Sin datos"
    end

    local actual = b[id] or 0
    if actual + cantidad > def.maximo then
        return false, "Limite de ese objeto alcanzado"
    end

    local capacidad = CAPACIDAD_BASE + (jugador:GetAttribute("CapacidadExtra") or 0)
    if Inventario.pesoTotal(jugador) + def.peso * cantidad > capacidad then
        return false, "No hay espacio"
    end

    b[id] = actual + cantidad
    Inventario.sincronizar(jugador)
    return true, nil
end

function Inventario.quitar(jugador: Player, id: string, cantidad: number): boolean
    local b = bolsa(jugador)
    if not b then
        return false
    end
    if typeof(cantidad) ~= "number" or cantidad <= 0 then
        return false
    end

    local actual = b[id] or 0
    if actual < cantidad then
        return false
    end

    local restante = actual - cantidad
    b[id] = restante > 0 and restante or nil

    Inventario.sincronizar(jugador)
    return true
end

-- El cliente NUNCA modifica: solo recibe una copia para dibujar
function Inventario.sincronizar(jugador: Player)
    local b = bolsa(jugador)
    if not b then
        return
    end

    local copia = {}
    for id, cantidad in b do
        copia[id] = cantidad
    end

    local remote = ReplicatedStorage:FindFirstChild("Remotes")
    remote = remote and remote:FindFirstChild("InventarioCambio")
    if remote and remote:IsA("RemoteEvent") then
        remote:FireClient(jugador, copia)
    end
end

return Inventario
```

- **Errores frecuentes:**
  - Guardar el inventario en la mochila de Roblox (`Backpack`) como unica
    fuente: el cliente puede manipularla.
  - Enviar la tabla original al cliente en vez de una copia: si el cliente
    modifica su copia, no pasa nada, pero enviar la original acopla los dos
    lados y confunde.
  - No comprobar el limite por objeto y la capacidad total.
  - Usar `#tabla` con una tabla indexada por texto: siempre da cero.
- **Checklist sin errores:**
  - [ ] El inventario vive en los datos del servidor
  - [ ] Se valida el id contra un catalogo cerrado
  - [ ] Hay limite por objeto y capacidad total
  - [ ] Al cliente se le envia una copia

---

### 4. Barra rapida

- **Que es:** equipar un objeto del inventario a la mano.
- **Codigo listo para pegar:**

```lua
-- Servidor
local ServerStorage = game:GetService("ServerStorage")
local Inventario = require(game.ServerScriptService.Sistemas.Inventario)

local herramientas = ServerStorage:WaitForChild("Herramientas", 20)

local function equipar(jugador: Player, id: string): boolean
    if not Inventario.existe(id) then
        return false
    end
    if Inventario.cantidad(jugador, id) <= 0 then
        return false -- no lo tiene
    end

    local plantilla = herramientas and herramientas:FindFirstChild(id)
    if not plantilla or not plantilla:IsA("Tool") then
        return false
    end

    local personaje = jugador.Character
    local mochila = jugador:FindFirstChildOfClass("Backpack")
    if not personaje or not mochila then
        return false
    end

    -- quitar la anterior para que solo haya una
    for _, existente in mochila:GetChildren() do
        if existente:IsA("Tool") then
            existente:Destroy()
        end
    end
    for _, existente in personaje:GetChildren() do
        if existente:IsA("Tool") then
            existente:Destroy()
        end
    end

    local copia = plantilla:Clone()
    copia:SetAttribute("IdObjeto", id)
    copia.Parent = mochila

    return true
end

return equipar
```

- **Errores frecuentes:**
  - No comprobar que el jugador realmente posee el objeto: un cliente pide
    equipar cualquier cosa del almacen.
  - No limpiar la herramienta anterior: el jugador acumula veinte.
  - Buscar solo en `Backpack`: si la tiene equipada, esta dentro del personaje.
  - Guardar las plantillas en `ReplicatedStorage`: el cliente ve todo el
    catalogo de armas antes de tiempo.
- **Checklist sin errores:**
  - [ ] Se verifica la posesion en el servidor
  - [ ] Se limpia la herramienta anterior en mochila y personaje
  - [ ] Las plantillas estan en `ServerStorage`

---

### 5. Tienda

- **Que es:** cambiar monedas por objetos.
- **Codigo listo para pegar:**

```lua
--!strict
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Economia = require(game.ServerScriptService.Sistemas.Economia)
local Inventario = require(game.ServerScriptService.Sistemas.Inventario)

local CATALOGO_TIENDA = {
    caja_pequena = { precio = 50, requiereNivel = 0 },
    caja_grande = { precio = 180, requiereNivel = 3 },
    mochila = { precio = 900, requiereNivel = 8 },
}

local ultimaCompra: { [Player]: number } = {}

local function comprar(jugador: Player, id: any, cantidad: any): (boolean, string)
    -- 1. frecuencia
    local ahora = os.clock()
    if ahora - (ultimaCompra[jugador] or 0) < 0.5 then
        return false, "Demasiado rapido"
    end
    ultimaCompra[jugador] = ahora

    -- 2. tipos
    if typeof(id) ~= "string" then
        return false, "Objeto invalido"
    end
    if typeof(cantidad) ~= "number" or cantidad ~= math.floor(cantidad) then
        return false, "Cantidad invalida"
    end
    if cantidad < 1 or cantidad > 10 then
        return false, "Cantidad fuera de rango"
    end

    -- 3. el objeto existe en la tienda
    local oferta = CATALOGO_TIENDA[id]
    if not oferta then
        return false, "Ese objeto no esta a la venta"
    end

    -- 4. requisitos
    local nivel = jugador:GetAttribute("Nivel") or 0
    if nivel < oferta.requiereNivel then
        return false, "Necesitas nivel " .. oferta.requiereNivel
    end

    -- 5. hay sitio ANTES de cobrar
    local coste = oferta.precio * cantidad
    if not Economia.puedePagar(jugador, coste) then
        return false, "No tienes suficientes monedas"
    end

    -- 6. anadir primero en seco para saber si cabe
    local cabe, motivo = Inventario.anadir(jugador, id, cantidad)
    if not cabe then
        return false, motivo or "No cabe"
    end

    -- 7. cobrar. Si falla, deshacer
    if not Economia.cobrar(jugador, coste, "tienda:" .. id) then
        Inventario.quitar(jugador, id, cantidad)
        return false, "No se pudo cobrar"
    end

    return true, "Compra realizada"
end

game:GetService("Players").PlayerRemoving:Connect(function(jugador)
    ultimaCompra[jugador] = nil
end)

return comprar
```

- **Errores frecuentes:**
  - **Cobrar antes de comprobar que el objeto cabe.** El jugador paga y no
    recibe nada. Por eso aqui se anade primero y se deshace si el cobro falla.
  - Enviar el precio desde el cliente: el jugador compra por 0 monedas. El
    precio **siempre** sale del catalogo del servidor.
  - No limitar la cantidad: alguien pide comprar 999999999 y desborda el
    calculo del coste.
  - No limitar la frecuencia: peticiones simultaneas duplican objetos.
- **Checklist sin errores:**
  - [ ] El precio sale del catalogo del servidor, nunca del cliente
  - [ ] La cantidad tiene minimo y maximo
  - [ ] Si algo falla a mitad, se deshace lo hecho
  - [ ] Hay limite de frecuencia

---

### 6. Recogibles

- **Que es:** objetos en el mundo que se recogen al pasar.
- **Codigo listo para pegar:**

```lua
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local Debris = game:GetService("Debris")
local TweenService = game:GetService("TweenService")

local Economia = require(game.ServerScriptService.Sistemas.Economia)

local ETIQUETA = "Moneda"
local RESPAWN = 12

local function preparar(moneda: BasePart)
    if moneda:GetAttribute("Preparada") then
        return
    end
    moneda:SetAttribute("Preparada", true)

    moneda.Anchored = true
    moneda.CanCollide = false
    moneda.CanTouch = true

    local tomada = false
    local original = moneda.CFrame

    -- girito
    task.spawn(function()
        while moneda.Parent do
            moneda.CFrame = moneda.CFrame * CFrame.Angles(0, math.rad(2), 0)
            task.wait()
        end
    end)

    moneda.Touched:Connect(function(otra)
        if tomada then
            return
        end

        local personaje = otra:FindFirstAncestorOfClass("Model")
        if not personaje then
            return
        end

        local jugador = Players:GetPlayerFromCharacter(personaje)
        if not jugador then
            return
        end

        local humanoide = personaje:FindFirstChildOfClass("Humanoid")
        if not humanoide or humanoide.Health <= 0 then
            return
        end

        tomada = true

        local valor = moneda:GetAttribute("Valor") or 5
        Economia.anadir(jugador, valor, "recogible")

        moneda.CanTouch = false
        TweenService:Create(moneda, TweenInfo.new(0.2), {
            Size = moneda.Size * 1.6,
            Transparency = 1,
        }):Play()

        task.delay(RESPAWN, function()
            if not moneda.Parent then
                return
            end
            moneda.Transparency = 0
            moneda.CFrame = original
            moneda.CanTouch = true
            tomada = false
        end)
    end)
end

for _, moneda in CollectionService:GetTagged(ETIQUETA) do
    if moneda:IsA("BasePart") then
        preparar(moneda)
    end
end

CollectionService:GetInstanceAddedSignal(ETIQUETA):Connect(function(moneda)
    if moneda:IsA("BasePart") then
        preparar(moneda)
    end
end)
```

- **Errores frecuentes:**
  - Sin bandera `tomada`: `Touched` dispara varias veces y el jugador cobra diez
    veces por una moneda.
  - Destruir la moneda en vez de ocultarla si va a reaparecer: pierdes la
    referencia y la posicion.
  - Recoger desde el cliente: monedas infinitas.
  - No usar `CollectionService`: tendrias que enlazar cada moneda a mano.
  - `Size` cambiando en el tween sin devolverlo al original al reaparecer.
- **Checklist sin errores:**
  - [ ] Hay bandera contra recogidas dobles
  - [ ] El servidor otorga la recompensa
  - [ ] Se usa `CollectionService` con etiquetas
  - [ ] Al reaparecer se restauran todas las propiedades

---

### 7. Misiones con progreso

- **Que es:** objetivos con contador y recompensa.
- **Codigo listo para pegar:**

```lua
--!strict
local Datos = require(game.ServerScriptService.Datos)
local Economia = require(game.ServerScriptService.Sistemas.Economia)

local Misiones = {}

type Definicion = {
    titulo: string,
    descripcion: string,
    objetivo: number,
    recompensa: number,
    evento: string,
}

local CATALOGO: { [string]: Definicion } = {
    primeras_entregas = {
        titulo = "Repartidor novato",
        descripcion = "Completa 5 entregas",
        objetivo = 5,
        recompensa = 150,
        evento = "entrega",
    },
    sin_fallar = {
        titulo = "Pulso firme",
        descripcion = "Completa 3 entregas sin perder el paquete",
        objetivo = 3,
        recompensa = 300,
        evento = "entrega_limpia",
    },
}

local function estado(jugador: Player)
    local datos = Datos.obtener(jugador)
    if not datos then
        return nil
    end
    datos.misiones = datos.misiones or {}
    return datos.misiones
end

function Misiones.progreso(jugador: Player, id: string): (number, number, boolean)
    local m = estado(jugador)
    local def = CATALOGO[id]
    if not m or not def then
        return 0, 0, false
    end

    local registro = m[id] or { avance = 0, cobrada = false }
    return registro.avance, def.objetivo, registro.cobrada
end

-- Se llama desde donde ocurre la accion, no desde el cliente
function Misiones.avisar(jugador: Player, evento: string, cantidad: number?)
    local m = estado(jugador)
    if not m then
        return
    end

    local suma = cantidad or 1

    for id, def in CATALOGO do
        if def.evento ~= evento then
            continue
        end

        local registro = m[id] or { avance = 0, cobrada = false }
        if registro.cobrada then
            continue
        end

        registro.avance = math.min(registro.avance + suma, def.objetivo)
        m[id] = registro

        jugador:SetAttribute("Mision_" .. id, registro.avance)

        if registro.avance >= def.objetivo then
            -- marcar ANTES de pagar, para no pagar dos veces
            registro.cobrada = true
            m[id] = registro

            Economia.anadir(jugador, def.recompensa, "mision:" .. id)
            jugador:SetAttribute("MisionCompletada_" .. id, true)
        end
    end
end

return Misiones
```

- **Errores frecuentes:**
  - Pagar antes de marcar como cobrada: dos eventos casi simultaneos pagan dos
    veces.
  - Permitir que el cliente llame a `avisar`: se completa todas las misiones al
    instante. Esta funcion **solo** se llama desde codigo del servidor.
  - No acotar el avance al objetivo: contadores absurdos en la interfaz.
  - Cambiar el `objetivo` de una mision ya en curso sin migrar los datos.
- **Checklist sin errores:**
  - [ ] Se marca como cobrada antes de pagar
  - [ ] Solo el servidor dispara el avance
  - [ ] El avance esta acotado al objetivo

---

### 8. Logros

- **Que es:** hitos permanentes, a menudo con insignia de Roblox.
- **API implicada:** `BadgeService:AwardBadge`, `UserHasBadgeAsync`.
- **Codigo listo para pegar:**

```lua
local BadgeService = game:GetService("BadgeService")

local INSIGNIAS = {
    primera_entrega = 0,   -- pon aqui el BadgeId real
    cien_entregas = 0,
}

local function otorgar(jugador: Player, clave: string)
    local id = INSIGNIAS[clave]
    if not id or id == 0 then
        return
    end

    local okTiene, tiene = pcall(function()
        return BadgeService:UserHasBadgeAsync(jugador.UserId, id)
    end)

    if not okTiene then
        warn("No se pudo comprobar la insignia " .. clave)
        return
    end
    if tiene then
        return -- ya la tiene
    end

    local okDar, err = pcall(function()
        BadgeService:AwardBadge(jugador.UserId, id)
    end)

    if not okDar then
        warn("No se pudo otorgar la insignia " .. clave .. ": " .. tostring(err))
    end
end

return otorgar
```

- **Errores frecuentes:**
  - Otorgar sin comprobar: gasta cuota de la API sin necesidad.
  - Sin `pcall`: la API de insignias falla a menudo.
  - Otorgar desde el cliente: no se puede, es una API del servidor.
  - Otorgar en bucle a todos los jugadores a la vez: throttling.
- **Checklist sin errores:**
  - [ ] Se comprueba antes de otorgar
  - [ ] Todo en `pcall`
  - [ ] Solo desde el servidor

---

### 9. Recompensas diarias

- **Que es:** un premio por conectarse cada dia, con racha.
- **Codigo listo para pegar:**

```lua
local Datos = require(game.ServerScriptService.Datos)
local Economia = require(game.ServerScriptService.Sistemas.Economia)

local PREMIOS = { 50, 75, 110, 160, 230, 330, 500 }
local SEGUNDOS_DIA = 86400

local function diaDe(momento: number): number
    -- dia absoluto en UTC, evita problemas de zona horaria
    return math.floor(momento / SEGUNDOS_DIA)
end

local function reclamar(jugador: Player): (boolean, string, number?)
    local datos = Datos.obtener(jugador)
    if not datos then
        return false, "Sin datos", nil
    end

    local hoy = diaDe(os.time())
    local ultimo = datos.ultimoDiaReclamado or 0

    if ultimo == hoy then
        return false, "Ya reclamaste hoy", nil
    end

    -- racha: si el ultimo fue ayer, continua; si no, se reinicia
    if ultimo == hoy - 1 then
        datos.racha = math.min((datos.racha or 0) + 1, #PREMIOS)
    else
        datos.racha = 1
    end

    datos.ultimoDiaReclamado = hoy

    local premio = PREMIOS[datos.racha] or PREMIOS[#PREMIOS]
    Economia.anadir(jugador, premio, "diaria:dia" .. datos.racha)

    jugador:SetAttribute("Racha", datos.racha)

    return true, "Dia " .. datos.racha, premio
end

return reclamar
```

- **Errores frecuentes:**
  - Usar `os.date` con la zona local del servidor: los servidores estan en
    husos distintos y el jugador puede reclamar dos veces cambiando de servidor.
    Usa `os.time()`, que es UTC.
  - Guardar la marca de tiempo exacta y comparar con 24 horas: el jugador que
    juega a las 20:00 y luego a las 19:00 del dia siguiente pierde la racha.
    Comparar dias absolutos es mas justo.
  - Escribir la fecha despues de dar el premio: si falla en medio, se puede
    reclamar otra vez.
- **Checklist sin errores:**
  - [ ] Se compara por dia absoluto UTC
  - [ ] La fecha se marca antes o junto con el premio
  - [ ] La racha tiene tope

---

### 10. Pase de batalla

- **Que es:** el sistema que da vida a `interfaces/pase.json`.
- **Relacion con el modulo 5:** el JSON define **como se ve**. Esto define
  **como funciona**. Los niveles del JSON y los de aqui deben coincidir en
  numero.
- **Codigo listo para pegar:**

```lua
--!strict
local Datos = require(game.ServerScriptService.Datos)
local Economia = require(game.ServerScriptService.Sistemas.Economia)
local Inventario = require(game.ServerScriptService.Sistemas.Inventario)

local Pase = {}

local NIVEL_MAXIMO = 20        -- debe coincidir con los niveles del JSON
local XP_POR_NIVEL = 1000

-- Estructura paralela al JSON de interfaces/pase.json
local PREMIOS: { [number]: { gratis: any?, premium: any? } } = {
    [1] = {
        gratis = { tipo = "monedas", cantidad = 250 },
        premium = { tipo = "objeto", id = "mochila", cantidad = 1 },
    },
    [2] = {
        gratis = { tipo = "monedas", cantidad = 300 },
        premium = { tipo = "monedas", cantidad = 900 },
    },
}

local function estado(jugador: Player)
    local datos = Datos.obtener(jugador)
    if not datos then
        return nil
    end
    datos.pase = datos.pase or { xp = 0, nivel = 0, reclamados = {} }
    return datos.pase
end

local function reflejar(jugador: Player)
    local p = estado(jugador)
    if not p then
        return
    end
    jugador:SetAttribute("NivelPase", p.nivel)
    jugador:SetAttribute("XpPase", p.xp)
end

function Pase.darXp(jugador: Player, cantidad: number)
    if typeof(cantidad) ~= "number" or cantidad <= 0 then
        return
    end

    local p = estado(jugador)
    if not p then
        return
    end

    p.xp += math.floor(cantidad)

    local nuevoNivel = math.min(math.floor(p.xp / XP_POR_NIVEL), NIVEL_MAXIMO)
    if nuevoNivel > p.nivel then
        p.nivel = nuevoNivel
    end

    reflejar(jugador)
end

function Pase.reclamar(jugador: Player, nivel: any, tipo: any): (boolean, string)
    -- validacion completa
    if typeof(nivel) ~= "number" or nivel ~= math.floor(nivel) then
        return false, "Nivel invalido"
    end
    if nivel < 1 or nivel > NIVEL_MAXIMO then
        return false, "Nivel fuera de rango"
    end
    if tipo ~= "gratis" and tipo ~= "premium" then
        return false, "Tipo invalido"
    end

    local p = estado(jugador)
    if not p then
        return false, "Sin datos"
    end

    if nivel > p.nivel then
        return false, "Aun no has llegado a ese nivel"
    end
    if tipo == "premium" and not jugador:GetAttribute("TienePremium") then
        return false, "Necesitas el pase premium"
    end

    local clave = tipo .. "_" .. nivel
    if p.reclamados[clave] then
        return false, "Ya reclamado"
    end

    local premio = PREMIOS[nivel] and PREMIOS[nivel][tipo]
    if not premio then
        return false, "Ese nivel no tiene premio de ese tipo"
    end

    -- marcar ANTES de entregar
    p.reclamados[clave] = true

    if premio.tipo == "monedas" then
        Economia.anadir(jugador, premio.cantidad, "pase:" .. clave)
    elseif premio.tipo == "objeto" then
        local ok = Inventario.anadir(jugador, premio.id, premio.cantidad)
        if not ok then
            -- no cabe: deshacer la marca para que pueda reclamarlo luego
            p.reclamados[clave] = nil
            return false, "No tienes espacio en el inventario"
        end
    end

    jugador:SetAttribute("Reclamado_" .. clave, true)
    return true, "Premio entregado"
end

return Pase
```

- **Errores frecuentes:**
  - Que el numero de niveles del codigo y el del JSON no coincidan: la interfaz
    muestra 20 niveles y el servidor solo conoce 12.
  - No deshacer la marca si la entrega falla: el jugador pierde el premio.
  - Confiar en el atributo `TienePremium` puesto por el cliente: debe venir de
    `UserOwnsGamePassAsync` comprobado en el servidor.
  - Guardar `reclamados` como lista numerada en vez de tabla por clave: al
    guardar en DataStore, las listas con huecos se corrompen.
- **Checklist sin errores:**
  - [ ] `NIVEL_MAXIMO` coincide con los niveles del JSON
  - [ ] Se marca antes de entregar y se deshace si falla
  - [ ] `TienePremium` lo determina el servidor
  - [ ] `reclamados` es una tabla por clave de texto

---

### 11. Maquina de estados de ronda

- **Que es:** el reloj maestro de una partida.
- **Para que sirve:** que el juego tenga fases claras y no dependa de esperas
  sueltas repartidas por veinte scripts.
- **Codigo listo para pegar:**

```lua
--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Ronda = {}

export type Fase = "Espera" | "Preparacion" | "Partida" | "Fin"

local DURACIONES: { [string]: number } = {
    Espera = 0,        -- indefinido, depende de jugadores
    Preparacion = 10,
    Partida = 60,      -- los 60 segundos del juego
    Fin = 8,
}

local MINIMO_JUGADORES = 2

local faseActual: Fase = "Espera"
local finDeFase = 0
local generacion = 0 -- invalida las tareas de la fase anterior

local function anunciar(fase: Fase, segundos: number)
    local carpeta = ReplicatedStorage:FindFirstChild("Remotes")
    local remote = carpeta and carpeta:FindFirstChild("CambioDeFase")
    if remote and remote:IsA("RemoteEvent") then
        remote:FireAllClients(fase, segundos)
    end

    -- tambien como atributo, para clientes que entran a mitad
    ReplicatedStorage:SetAttribute("Fase", fase)
    ReplicatedStorage:SetAttribute("FinDeFase", os.time() + segundos)
end

local MANEJADORES: { [string]: () -> () } = {}

function MANEJADORES.Espera()
    -- no hacer nada, solo esperar jugadores
end

function MANEJADORES.Preparacion()
    for _, jugador in Players:GetPlayers() do
        jugador:LoadCharacter()
        jugador:SetAttribute("EnPartida", true)
        jugador:SetAttribute("Entregas", 0)
    end
end

function MANEJADORES.Partida()
    -- activar objetivos, abrir puertas, arrancar spawns
end

function MANEJADORES.Fin()
    for _, jugador in Players:GetPlayers() do
        jugador:SetAttribute("EnPartida", false)
    end
    -- repartir recompensas
end

local function cambiarA(nueva: Fase)
    generacion += 1
    local miGeneracion = generacion

    faseActual = nueva
    local duracion = DURACIONES[nueva] or 0
    finDeFase = os.time() + duracion

    anunciar(nueva, duracion)

    local manejador = MANEJADORES[nueva]
    if manejador then
        local ok, err = pcall(manejador)
        if not ok then
            warn("Error en la fase " .. nueva .. ": " .. tostring(err))
        end
    end

    return miGeneracion
end

function Ronda.fase(): Fase
    return faseActual
end

function Ronda.segundosRestantes(): number
    return math.max(finDeFase - os.time(), 0)
end

function Ronda.iniciar()
    task.spawn(function()
        while true do
            -- Espera
            cambiarA("Espera")
            while #Players:GetPlayers() < MINIMO_JUGADORES do
                task.wait(1)
            end

            -- Preparacion
            cambiarA("Preparacion")
            task.wait(DURACIONES.Preparacion)

            -- si se fueron los jugadores, volver a esperar
            if #Players:GetPlayers() < MINIMO_JUGADORES then
                continue
            end

            -- Partida
            cambiarA("Partida")
            local limite = os.time() + DURACIONES.Partida
            while os.time() < limite do
                if #Players:GetPlayers() == 0 then
                    break
                end
                task.wait(0.5)
            end

            -- Fin
            cambiarA("Fin")
            task.wait(DURACIONES.Fin)
        end
    end)
end

return Ronda
```

- **Errores frecuentes:**
  - Bucle de ronda sin comprobar que quedan jugadores: la ronda sigue corriendo
    en un servidor vacio.
  - Usar solo `task.wait(60)` para la fase de partida: no se puede terminar
    antes si se cumple el objetivo. El bucle con comprobacion permite salir.
  - No invalidar las tareas de la fase anterior: un `task.delay` de la fase
    anterior se ejecuta en medio de la siguiente. Para eso esta `generacion`.
  - Anunciar la fase solo por remote: quien entra a mitad no se entera. El
    atributo en `ReplicatedStorage` lo resuelve.
  - Manejador de fase sin `pcall`: un error rompe el bucle y la ronda se queda
    congelada para siempre.
- **Checklist sin errores:**
  - [ ] Se comprueba que hay jugadores en cada fase
  - [ ] Los manejadores estan en `pcall`
  - [ ] El estado se publica tambien como atributo
  - [ ] Las tareas viejas se invalidan al cambiar de fase

---

### 12. Temporizador sincronizado

- **Que es:** un reloj que todos los jugadores ven igual.
- **La clave:** no envies el numero cada segundo. Envia **cuando termina** y que
  cada cliente calcule.
- **Codigo listo para pegar:**

```lua
-- Servidor: publica el instante de fin una sola vez
ReplicatedStorage:SetAttribute("FinDeFase", os.time() + 60)
```

```lua
-- Cliente: calcula cada frame a partir de ese instante
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local etiqueta = script.Parent :: TextLabel

local function formatear(segundos: number): string
    segundos = math.max(math.floor(segundos), 0)
    local minutos = math.floor(segundos / 60)
    local resto = segundos % 60
    return string.format("%d:%02d", minutos, resto)
end

RunService.Heartbeat:Connect(function()
    local fin = ReplicatedStorage:GetAttribute("FinDeFase")
    if typeof(fin) ~= "number" then
        etiqueta.Text = "--:--"
        return
    end

    local restante = fin - os.time()
    etiqueta.Text = formatear(restante)

    -- aviso visual en los ultimos 10 segundos
    if restante <= 10 and restante > 0 then
        etiqueta.TextColor3 = Color3.fromRGB(240, 80, 80)
    else
        etiqueta.TextColor3 = Color3.fromRGB(240, 240, 240)
    end
end)
```

- **Errores frecuentes:**
  - Enviar el numero cada segundo por remote: 60 mensajes por jugador por ronda,
    y con lag el contador salta.
  - Contar en el cliente con `task.wait(1)`: se desincroniza porque `wait` nunca
    es exacto.
  - Usar `tick()` u `os.clock()` para el instante compartido: son relojes
    locales de cada maquina y no coinciden. `os.time()` es UTC y sirve.
  - No manejar el caso de que el atributo aun no exista.
- **Checklist sin errores:**
  - [ ] Se publica el instante de fin, no el numero
  - [ ] El cliente calcula con `os.time()`
  - [ ] Se maneja el caso de atributo ausente

---

### 13. Equipos

- **Que es:** repartir jugadores en bandos con reaparicion propia.
- **API implicada:** `Teams`, `Team`, `Player.Team`, `Player.TeamColor`,
  `SpawnLocation.TeamColor`, `Neutral`.
- **Codigo listo para pegar:**

```lua
local Teams = game:GetService("Teams")
local Players = game:GetService("Players")

local function crearEquipo(nombre: string, color: BrickColor): Team
    local existente = Teams:FindFirstChild(nombre)
    if existente and existente:IsA("Team") then
        return existente
    end

    local equipo = Instance.new("Team")
    equipo.Name = nombre
    equipo.TeamColor = color
    equipo.AutoAssignable = false -- lo repartimos nosotros
    equipo.Parent = Teams
    return equipo
end

local rojo = crearEquipo("Rojo", BrickColor.new("Bright red"))
local azul = crearEquipo("Azul", BrickColor.new("Bright blue"))

local function repartir()
    local jugadores = Players:GetPlayers()

    -- barajar para que no siempre caigan igual
    for i = #jugadores, 2, -1 do
        local j = math.random(i)
        jugadores[i], jugadores[j] = jugadores[j], jugadores[i]
    end

    for indice, jugador in jugadores do
        jugador.Team = (indice % 2 == 0) and azul or rojo
        jugador.Neutral = false
        jugador:LoadCharacter() -- reaparece en el spawn de su equipo
    end
end

local function mismoEquipo(a: Player, b: Player): boolean
    return a.Team ~= nil and a.Team == b.Team
end

return { repartir = repartir, mismoEquipo = mismoEquipo, rojo = rojo, azul = azul }
```

Y el `SpawnLocation` correspondiente:

```lua
local punto = Instance.new("SpawnLocation")
punto.Name = "SpawnRojo"
punto.Size = Vector3.new(8, 1, 8)
punto.Position = Vector3.new(-60, 4, 0)
punto.Anchored = true
punto.TeamColor = BrickColor.new("Bright red")
punto.Neutral = false      -- solo su equipo aparece aqui
punto.Duration = 0         -- sin escudo de invulnerabilidad
punto.AllowTeamChangeOnTouch = false
punto.Parent = workspace
```

- **Errores frecuentes:**
  - `SpawnLocation` con `Neutral = true`: todos aparecen ahi sin importar el
    equipo. Es la causa numero uno de "los equipos no funcionan".
  - Cambiar el equipo sin llamar a `LoadCharacter`: el jugador sigue en el otro
    lado del mapa hasta que muera.
  - `AutoAssignable` en true y ademas repartir a mano: Roblox asigna por su
    cuenta y se descuadra.
  - Comparar equipos con `TeamColor` en vez de con el objeto `Team`: dos equipos
    pueden compartir color por error.
- **Checklist sin errores:**
  - [ ] Los spawns tienen `Neutral = false` y el `TeamColor` correcto
  - [ ] Se llama a `LoadCharacter` tras cambiar de equipo
  - [ ] `AutoAssignable` esta en false si repartes tu
  - [ ] Se compara por objeto `Team`

---

### 14. Entregas contra reloj

- **Que es:** el bucle central del juego del repositorio: recoger un paquete,
  llevarlo a un destino antes de que acabe el tiempo.
- **Codigo listo para pegar:**

```lua
--!strict
local Players = game:GetService("Players")
local CollectionService = game:GetService("CollectionService")

local Economia = require(game.ServerScriptService.Sistemas.Economia)
local Misiones = require(game.ServerScriptService.Sistemas.Misiones)
local Pase = require(game.ServerScriptService.Sistemas.Pase)

local Entregas = {}

local activas: { [Player]: {
    paquete: Model,
    destino: BasePart,
    inicio: number,
    limite: number,
} } = {}

local RECOMPENSA_BASE = 100
local BONUS_MAXIMO = 150

local function limpiar(jugador: Player)
    local entrega = activas[jugador]
    if not entrega then
        return
    end

    if entrega.paquete and entrega.paquete.Parent then
        entrega.paquete:Destroy()
    end
    if entrega.destino then
        entrega.destino:SetAttribute("Ocupado", false)
    end

    activas[jugador] = nil
    jugador:SetAttribute("EntregaActiva", false)
    jugador:SetAttribute("EntregaLimite", 0)
end

function Entregas.iniciar(jugador: Player, paquete: Model, destino: BasePart, segundos: number)
    if activas[jugador] then
        return false, "Ya llevas un paquete"
    end
    if destino:GetAttribute("Ocupado") then
        return false, "Ese destino esta ocupado"
    end

    destino:SetAttribute("Ocupado", true)

    activas[jugador] = {
        paquete = paquete,
        destino = destino,
        inicio = os.time(),
        limite = os.time() + segundos,
    }

    jugador:SetAttribute("EntregaActiva", true)
    jugador:SetAttribute("EntregaLimite", os.time() + segundos)

    -- caducidad
    task.delay(segundos + 0.5, function()
        local entrega = activas[jugador]
        if entrega and os.time() >= entrega.limite then
            limpiar(jugador)
            jugador:SetAttribute("EntregaFallada", os.time())
        end
    end)

    return true, "Entrega iniciada"
end

function Entregas.completar(jugador: Player, destinoTocado: BasePart): (boolean, string)
    local entrega = activas[jugador]
    if not entrega then
        return false, "No llevas ningun paquete"
    end
    if destinoTocado ~= entrega.destino then
        return false, "Ese no es tu destino"
    end

    local ahora = os.time()
    if ahora > entrega.limite then
        limpiar(jugador)
        return false, "Llegaste tarde"
    end

    -- bonus por rapidez
    local total = entrega.limite - entrega.inicio
    local usado = ahora - entrega.inicio
    local fraccionSobrante = math.clamp(1 - usado / math.max(total, 1), 0, 1)
    local bonus = math.floor(BONUS_MAXIMO * fraccionSobrante)

    limpiar(jugador)

    Economia.anadir(jugador, RECOMPENSA_BASE + bonus, "entrega")
    Misiones.avisar(jugador, "entrega", 1)
    Pase.darXp(jugador, 120)

    jugador:SetAttribute("Entregas", (jugador:GetAttribute("Entregas") or 0) + 1)

    return true, "Entregado con " .. bonus .. " de bonus"
end

Players.PlayerRemoving:Connect(limpiar)

return Entregas
```

- **Errores frecuentes:**
  - No liberar el destino al fallar o al desconectarse: los destinos se agotan y
    nadie puede empezar una entrega.
  - Comprobar el tiempo solo en el cliente: el jugador entrega siempre a tiempo.
  - No comprobar que el destino tocado es **su** destino: cualquiera cobra en
    cualquier punto.
  - No limpiar en `PlayerRemoving`: fugas de memoria y destinos bloqueados.
  - Bonus calculado sin acotar: valores negativos o enormes.
- **Checklist sin errores:**
  - [ ] El servidor comprueba el tiempo
  - [ ] El destino se libera en todos los caminos de salida
  - [ ] Se verifica que el destino es el correcto
  - [ ] Se limpia en `PlayerRemoving`

---

### 15. Checkpoints y puertas con llave

- **Que es:** progresion por el mapa que se recuerda.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")
local CollectionService = game:GetService("CollectionService")
local Datos = require(game.ServerScriptService.Datos)

-- CHECKPOINTS
local function registrarCheckpoint(parte: BasePart)
    local indice = parte:GetAttribute("Indice")
    if typeof(indice) ~= "number" then
        warn("El checkpoint " .. parte.Name .. " no tiene atributo Indice")
        return
    end

    parte.Touched:Connect(function(otra)
        local personaje = otra:FindFirstAncestorOfClass("Model")
        local jugador = personaje and Players:GetPlayerFromCharacter(personaje)
        if not jugador then
            return
        end

        local datos = Datos.obtener(jugador)
        if not datos then
            return
        end

        -- solo avanzar, nunca retroceder
        if (datos.checkpoint or 0) >= indice then
            return
        end

        datos.checkpoint = indice
        jugador:SetAttribute("Checkpoint", indice)
    end)
end

for _, parte in CollectionService:GetTagged("Checkpoint") do
    if parte:IsA("BasePart") then
        registrarCheckpoint(parte)
    end
end

-- Reaparecer en el ultimo checkpoint
Players.PlayerAdded:Connect(function(jugador)
    jugador.CharacterAdded:Connect(function(personaje)
        local datos = Datos.obtener(jugador)
        local indice = datos and datos.checkpoint or 0
        if indice <= 0 then
            return
        end

        for _, parte in CollectionService:GetTagged("Checkpoint") do
            if parte:IsA("BasePart") and parte:GetAttribute("Indice") == indice then
                task.wait() -- dejar que el personaje termine de cargar
                personaje:PivotTo(parte.CFrame + Vector3.new(0, 4, 0))
                break
            end
        end
    end)
end)

-- PUERTA CON LLAVE
local Inventario = require(game.ServerScriptService.Sistemas.Inventario)

local function registrarPuerta(puerta: BasePart)
    local llave = puerta:GetAttribute("LlaveRequerida")
    if typeof(llave) ~= "string" then
        return
    end

    puerta.Touched:Connect(function(otra)
        if puerta:GetAttribute("Abriendo") then
            return
        end

        local personaje = otra:FindFirstAncestorOfClass("Model")
        local jugador = personaje and Players:GetPlayerFromCharacter(personaje)
        if not jugador then
            return
        end

        if Inventario.cantidad(jugador, llave) <= 0 then
            jugador:SetAttribute("MensajePuerta", "Necesitas: " .. llave)
            return
        end

        puerta:SetAttribute("Abriendo", true)
        puerta.CanCollide = false
        puerta.Transparency = 0.7

        task.delay(4, function()
            if puerta.Parent then
                puerta.CanCollide = true
                puerta.Transparency = 0
                puerta:SetAttribute("Abriendo", false)
            end
        end)
    end)
end
```

- **Errores frecuentes:**
  - Permitir que el checkpoint retroceda: el jugador vuelve al principio al
    pasar por uno anterior.
  - Teletransportar sin esperar a que el personaje cargue: el `PivotTo` se
    aplica y el sistema de spawn lo mueve encima.
  - Puerta que se queda abierta para siempre porque el `task.delay` fallo.
  - Comprobar la llave en el cliente.
- **Checklist sin errores:**
  - [ ] El checkpoint solo avanza
  - [ ] La reaparicion espera a que el personaje exista
  - [ ] La puerta se cierra en todos los casos
  - [ ] La llave se comprueba en el servidor

---

### 16. NPC con pathfinding

- **Que es:** un NPC que va de A a B rodeando obstaculos.
- **API implicada:** `PathfindingService:CreatePath`, `Path:ComputeAsync`,
  `Path:GetWaypoints`, `Humanoid:MoveTo`, `Humanoid.MoveToFinished`,
  `Path.Blocked`.
- **Codigo listo para pegar:**

```lua
local PathfindingService = game:GetService("PathfindingService")

local function crearNavegador(npc: Model)
    local humanoide = npc:FindFirstChildOfClass("Humanoid")
    local raiz = npc:FindFirstChild("HumanoidRootPart") :: BasePart?
    if not humanoide or not raiz then
        warn("El NPC " .. npc.Name .. " no tiene Humanoid o HumanoidRootPart")
        return nil
    end

    local camino = PathfindingService:CreatePath({
        AgentRadius = 2.5,
        AgentHeight = 5,
        AgentCanJump = true,
        AgentCanClimb = false,
        WaypointSpacing = 4,
        Costs = {
            Water = 20,     -- evitar el agua si hay alternativa
            Peligro = 100,  -- material personalizado con PathfindingModifier
        },
    })

    local viajeActual = 0

    local function ir(destino: Vector3): boolean
        viajeActual += 1
        local miViaje = viajeActual

        local ok, err = pcall(function()
            camino:ComputeAsync(raiz.Position, destino)
        end)

        if not ok then
            warn("Fallo al calcular la ruta: " .. tostring(err))
            return false
        end

        if camino.Status ~= Enum.PathStatus.Success then
            -- no hay ruta: intentar acercarse en linea recta
            humanoide:MoveTo(destino)
            return false
        end

        local puntos = camino:GetWaypoints()

        for indice = 2, #puntos do -- el 1 es donde ya estamos
            if miViaje ~= viajeActual then
                return false -- otro viaje cancelo este
            end
            if humanoide.Health <= 0 then
                return false
            end

            local punto = puntos[indice]

            if punto.Action == Enum.PathWaypointAction.Jump then
                humanoide.Jump = true
            end

            humanoide:MoveTo(punto.Position)

            -- esperar con tope, por si se atasca
            local llego = humanoide.MoveToFinished:Wait()
            if not llego then
                return false -- se agoto el tiempo, recalcular fuera
            end
        end

        return true
    end

    local function detener()
        viajeActual += 1
        humanoide:MoveTo(raiz.Position)
    end

    return { ir = ir, detener = detener, camino = camino }
end

return crearNavegador
```

- **Errores frecuentes:**
  - `ComputeAsync` sin `pcall`: falla y tumba el script del NPC.
  - No comprobar `camino.Status`: si no hay ruta, `GetWaypoints` devuelve una
    lista vacia y el NPC se queda quieto sin explicacion.
  - Empezar en el punto 1: es la posicion actual, y el NPC hace un gesto raro.
    Empieza en el 2.
  - No cancelar el viaje anterior: dos rutas dando ordenes al mismo Humanoid y
    el NPC vibra en el sitio.
  - Recalcular la ruta cada frame: `ComputeAsync` es caro. Cada 0.5 a 1 segundo
    es suficiente para perseguir.
  - `AgentRadius` demasiado pequeno: el NPC calcula rutas por huecos por los que
    no cabe y se queda atascado en las esquinas.
- **Checklist sin errores:**
  - [ ] `ComputeAsync` en `pcall`
  - [ ] Se comprueba `Path.Status`
  - [ ] El recorrido empieza en el punto 2
  - [ ] Los viajes anteriores se cancelan
  - [ ] `AgentRadius` y `AgentHeight` coinciden con el tamano real del NPC

---

### 17. Maquina de estados de NPC

- **Que es:** el comportamiento del NPC organizado en estados.
- **Codigo listo para pegar:**

```lua
--!strict
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

type Estado = "Patrulla" | "Persecucion" | "Ataque" | "Retirada"

local function crearCerebro(npc: Model, navegador: any, puntosPatrulla: { Vector3 })
    local humanoide = npc:FindFirstChildOfClass("Humanoid")
    local raiz = npc:FindFirstChild("HumanoidRootPart") :: BasePart?
    if not humanoide or not raiz then
        return nil
    end

    local RADIO_DETECCION = 45
    local RADIO_ATAQUE = 6
    local VIDA_RETIRADA = 0.25

    local estado: Estado = "Patrulla"
    local objetivo: Model? = nil
    local indicePatrulla = 1
    local ultimoAtaque = 0

    local function buscarObjetivo(): Model?
        local mejor: Model? = nil
        local mejorDistancia = RADIO_DETECCION

        for _, jugador in Players:GetPlayers() do
            local personaje = jugador.Character
            local otraRaiz = personaje and personaje:FindFirstChild("HumanoidRootPart")
            local otroHum = personaje and personaje:FindFirstChildOfClass("Humanoid")

            if not otraRaiz or not otroHum or otroHum.Health <= 0 then
                continue
            end

            local distancia = (otraRaiz.Position - raiz.Position).Magnitude
            if distancia >= mejorDistancia then
                continue
            end

            -- linea de vision
            local parametros = RaycastParams.new()
            parametros.FilterType = Enum.RaycastFilterType.Exclude
            parametros.FilterDescendantsInstances = { npc, personaje }

            local bloqueo = workspace:Raycast(
                raiz.Position,
                otraRaiz.Position - raiz.Position,
                parametros
            )

            if not bloqueo then
                mejor = personaje
                mejorDistancia = distancia
            end
        end

        return mejor
    end

    local function distanciaA(modelo: Model?): number
        if not modelo then
            return math.huge
        end
        local otraRaiz = modelo:FindFirstChild("HumanoidRootPart") :: BasePart?
        if not otraRaiz then
            return math.huge
        end
        return (otraRaiz.Position - raiz.Position).Magnitude
    end

    local ACCIONES: { [string]: () -> () } = {}

    ACCIONES.Patrulla = function()
        humanoide.WalkSpeed = 8

        local punto = puntosPatrulla[indicePatrulla]
        if punto then
            navegador.ir(punto)
            indicePatrulla = indicePatrulla % #puntosPatrulla + 1
        end
    end

    ACCIONES.Persecucion = function()
        humanoide.WalkSpeed = 17

        local otraRaiz = objetivo and objetivo:FindFirstChild("HumanoidRootPart")
        if otraRaiz and otraRaiz:IsA("BasePart") then
            navegador.ir(otraRaiz.Position)
        end
    end

    ACCIONES.Ataque = function()
        humanoide.WalkSpeed = 0

        local ahora = os.clock()
        if ahora - ultimoAtaque < 1.2 then
            return
        end
        ultimoAtaque = ahora

        local otroHum = objetivo and objetivo:FindFirstChildOfClass("Humanoid")
        if otroHum and otroHum.Health > 0 then
            otroHum:TakeDamage(12)
        end
    end

    ACCIONES.Retirada = function()
        humanoide.WalkSpeed = 20

        local otraRaiz = objetivo and objetivo:FindFirstChild("HumanoidRootPart")
        if otraRaiz and otraRaiz:IsA("BasePart") then
            local huida = raiz.Position + (raiz.Position - otraRaiz.Position).Unit * 40
            navegador.ir(huida)
        end
    end

    local function decidir(): Estado
        if humanoide.Health / humanoide.MaxHealth <= VIDA_RETIRADA and objetivo then
            return "Retirada"
        end

        objetivo = buscarObjetivo() or objetivo

        local d = distanciaA(objetivo)

        if d > RADIO_DETECCION * 1.4 then
            objetivo = nil
            return "Patrulla"
        end
        if d <= RADIO_ATAQUE then
            return "Ataque"
        end
        if objetivo then
            return "Persecucion"
        end

        return "Patrulla"
    end

    task.spawn(function()
        while npc.Parent and humanoide.Health > 0 do
            local nuevo = decidir()

            if nuevo ~= estado then
                estado = nuevo
                npc:SetAttribute("Estado", estado)
            end

            local accion = ACCIONES[estado]
            if accion then
                local ok, err = pcall(accion)
                if not ok then
                    warn("Error en el estado " .. estado .. ": " .. tostring(err))
                end
            end

            task.wait(0.5)
        end
    end)

    return { estadoActual = function() return estado end }
end

return crearCerebro
```

- **Errores frecuentes:**
  - Perseguir sin linea de vision: el NPC "ve" a traves de las paredes y resulta
    injusto.
  - Radio de perdida igual al de deteccion: el NPC entra y sale del estado sin
    parar. Por eso aqui se pierde a `RADIO_DETECCION * 1.4`. Esta holgura se
    llama histeresis y es imprescindible.
  - Decidir cada frame: caro e innecesario. Cada 0.3 a 0.5 segundos basta.
  - No comprobar la vida del objetivo: el NPC ataca a un cadaver eternamente.
  - Bucle sin `pcall`: un error mata al NPC para siempre.
- **Checklist sin errores:**
  - [ ] Hay comprobacion de linea de vision
  - [ ] El radio de perdida es mayor que el de deteccion
  - [ ] El bucle corre cada 0.3 a 0.5 segundos, no cada frame
  - [ ] Las acciones estan en `pcall`
  - [ ] El bucle termina cuando el NPC muere o se destruye

---

### 18. Oleadas de enemigos

- **Que es:** grupos de enemigos que llegan con dificultad creciente.
- **Codigo listo para pegar:**

```lua
local ServerStorage = game:GetService("ServerStorage")
local Debris = game:GetService("Debris")

local MAXIMO_VIVOS = 30

local function crearGestorOleadas(puntos: { BasePart }, plantilla: Model)
    local oleada = 0
    local vivos = 0
    local enCurso = false

    local function aparecer(): Model?
        if vivos >= MAXIMO_VIVOS then
            return nil
        end

        local punto = puntos[math.random(#puntos)]
        if not punto then
            return nil
        end

        local enemigo = plantilla:Clone()
        enemigo:PivotTo(punto.CFrame + Vector3.new(
            math.random(-4, 4),
            3,
            math.random(-4, 4)
        ))
        enemigo.Parent = workspace

        vivos += 1

        local humanoide = enemigo:FindFirstChildOfClass("Humanoid")
        if humanoide then
            -- escalar con la oleada, con tope
            humanoide.MaxHealth = math.min(100 + oleada * 20, 900)
            humanoide.Health = humanoide.MaxHealth

            humanoide.Died:Connect(function()
                vivos -= 1
                Debris:AddItem(enemigo, 4)
            end)
        else
            vivos -= 1
            enemigo:Destroy()
            return nil
        end

        -- red de seguridad por si muere sin disparar Died
        enemigo.Destroying:Connect(function()
            if humanoide and humanoide.Health > 0 then
                vivos -= 1
            end
        end)

        return enemigo
    end

    local function lanzarOleada()
        if enCurso then
            return
        end
        enCurso = true
        oleada += 1

        local cantidad = math.min(3 + oleada * 2, 24)

        for i = 1, cantidad do
            aparecer()
            task.wait(0.4) -- repartir la carga
        end

        -- esperar a que caigan todos, con tope de seguridad
        local limite = os.clock() + 240
        while vivos > 0 and os.clock() < limite do
            task.wait(1)
        end

        enCurso = false
    end

    return {
        lanzar = lanzarOleada,
        oleadaActual = function() return oleada end,
        vivos = function() return vivos end,
    }
end

return crearGestorOleadas
```

- **Errores frecuentes:**
  - Crear todos los enemigos en el mismo frame: el servidor se congela un
    segundo. Reparte con una pequena espera.
  - Contar los vivos con una variable que nunca baja si el enemigo se destruye
    sin morir: el juego se queda esperando para siempre. Por eso hay red de
    seguridad en `Destroying`.
  - Escalar la vida sin tope: en la oleada 50 los enemigos son invencibles.
  - No limitar el maximo de enemigos simultaneos.
  - Esperar sin tope a que la oleada termine: si un enemigo se queda atascado en
    la geometria, la partida no avanza nunca.
- **Checklist sin errores:**
  - [ ] La aparicion esta repartida en el tiempo
  - [ ] El contador de vivos baja en todos los casos
  - [ ] Hay tope de vida y de cantidad
  - [ ] La espera de fin de oleada tiene limite

---

### 19. Tabla de clasificacion

- **Que es:** el top global, mostrado en el mundo.
- **Codigo listo para pegar:**

```lua
local Clasificacion = require(game.ServerScriptService.Sistemas.Clasificacion)

local cartel = workspace:WaitForChild("CartelTop"):WaitForChild("SurfaceGui")
local lista = cartel:WaitForChild("Lista")

local REFRESCO = 90
local cache: { any } = {}

local function pintar()
    for _, hijo in lista:GetChildren() do
        if hijo:IsA("TextLabel") then
            hijo:Destroy()
        end
    end

    for posicion, entrada in cache do
        local fila = Instance.new("TextLabel")
        fila.Size = UDim2.new(1, 0, 0, 40)
        fila.LayoutOrder = posicion
        fila.BackgroundTransparency = 1
        fila.TextScaled = true
        fila.Font = Enum.Font.GothamBold
        fila.TextColor3 = Color3.new(1, 1, 1)
        fila.TextXAlignment = Enum.TextXAlignment.Left
        fila.RichText = false -- nombres de jugadores
        fila.Text = string.format("%d. %s - %d", posicion, entrada.nombre, entrada.puntuacion)
        fila.Parent = lista
    end
end

task.spawn(function()
    while true do
        local resultado = Clasificacion.leerTop(10)
        if #resultado > 0 then
            cache = resultado
            pintar()
        end
        task.wait(REFRESCO)
    end
end)
```

- **Errores frecuentes:**
  - Consultar el `OrderedDataStore` cada vez que alguien mira el cartel: cuota
    agotada en minutos.
  - Sobrescribir la cache con una lista vacia cuando la lectura falla: el cartel
    se queda en blanco. Por eso solo se actualiza si hay resultados.
  - `RichText` activo con nombres de jugadores.
  - Destruir y recrear las filas cada segundo: mejor cada 60 a 120 segundos.
- **Checklist sin errores:**
  - [ ] La lectura esta cacheada
  - [ ] Un fallo no borra lo que ya se mostraba
  - [ ] `RichText` desactivado

---

### 20. Comandos de chat

- **Que es:** acciones escribiendo en el chat.
- **API implicada:** `TextChatService`, `TextChatCommand`. El sistema antiguo
  (`Chat`, `Chatted`) sigue funcionando pero `TextChatService` es el actual.
- **Codigo listo para pegar:**

```lua
local TextChatService = game:GetService("TextChatService")
local Players = game:GetService("Players")

local comandos = TextChatService:FindFirstChild("TextChatCommands")
if not comandos then
    comandos = Instance.new("Folder")
    comandos.Name = "TextChatCommands"
    comandos.Parent = TextChatService
end

local function crearComando(nombre: string, alias: string, accion: (Player, { string }) -> ())
    local comando = Instance.new("TextChatCommand")
    comando.Name = nombre
    comando.PrimaryAlias = "/" .. alias
    comando.Parent = comandos

    comando.Triggered:Connect(function(origen, texto)
        local jugador = Players:GetPlayerByUserId(origen.UserId)
        if not jugador then
            return
        end

        local partes = {}
        for trozo in string.gmatch(texto, "%S+") do
            table.insert(partes, trozo)
        end
        table.remove(partes, 1) -- quitar el propio comando

        local ok, err = pcall(accion, jugador, partes)
        if not ok then
            warn("Error en el comando " .. nombre .. ": " .. tostring(err))
        end
    end)

    return comando
end

crearComando("Saldo", "saldo", function(jugador)
    local monedas = jugador:GetAttribute("Monedas") or 0
    print(jugador.Name .. " tiene " .. monedas .. " monedas")
end)

return crearComando
```

- **Errores frecuentes:**
  - No validar los argumentos: `/dar 999999999` sin comprobaciones.
  - Ejecutar la accion sin `pcall`: un error rompe el comando para todos.
  - Crear el comando en el cliente: no tiene efecto en el servidor.
  - Asumir que el texto tiene argumentos: comprueba `partes[1]` antes de usarlo.
- **Checklist sin errores:**
  - [ ] Los argumentos se validan
  - [ ] La accion esta en `pcall`
  - [ ] El comando se registra en el servidor

---

### 21. Comandos de administrador

- **Que es:** comandos restringidos a personas concretas.
- **La regla:** lista blanca de `UserId`. **Nunca** por nombre, porque los
  nombres se pueden cambiar y suplantar visualmente.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")

-- Lista blanca por UserId. Nunca por nombre.
local ADMINS: { [number]: boolean } = {
    [1] = true, -- sustituye por tu UserId real
}

local function esAdmin(jugador: Player): boolean
    if ADMINS[jugador.UserId] then
        return true
    end

    -- el creador del juego, con comprobacion segura
    if game.CreatorType == Enum.CreatorType.User and jugador.UserId == game.CreatorId then
        return true
    end

    return false
end

local function buscarJugador(texto: string): Player?
    local minuscula = string.lower(texto)
    for _, jugador in Players:GetPlayers() do
        if string.sub(string.lower(jugador.Name), 1, #minuscula) == minuscula then
            return jugador
        end
    end
    return nil
end

local ACCIONES: { [string]: (Player, { string }) -> string } = {}

ACCIONES.velocidad = function(quien, args)
    local objetivo = args[1] and buscarJugador(args[1]) or quien
    local valor = tonumber(args[2])

    if not objetivo then
        return "Jugador no encontrado"
    end
    if not valor or valor ~= valor or valor < 0 or valor > 200 then
        return "Velocidad invalida"
    end

    local hum = objetivo.Character and objetivo.Character:FindFirstChildOfClass("Humanoid")
    if not hum then
        return "Ese jugador no tiene personaje"
    end

    hum.WalkSpeed = valor
    return "Velocidad de " .. objetivo.Name .. " ajustada a " .. valor
end

ACCIONES.traer = function(quien, args)
    local objetivo = args[1] and buscarJugador(args[1])
    if not objetivo then
        return "Jugador no encontrado"
    end

    local origen = quien.Character
    local destino = objetivo.Character
    if not origen or not destino then
        return "Falta algun personaje"
    end

    destino:PivotTo(origen:GetPivot() * CFrame.new(0, 0, -4))
    return objetivo.Name .. " traido"
end

local function ejecutar(jugador: Player, comando: string, args: { string }): string
    -- LA COMPROBACION VA AQUI, ANTES DE NADA
    if not esAdmin(jugador) then
        warn("Intento de comando admin por " .. jugador.Name .. " (" .. jugador.UserId .. ")")
        return "Sin permiso"
    end

    local accion = ACCIONES[string.lower(comando)]
    if not accion then
        return "Comando desconocido"
    end

    local ok, resultado = pcall(accion, jugador, args)
    if not ok then
        return "Error: " .. tostring(resultado)
    end

    return resultado
end

return { ejecutar = ejecutar, esAdmin = esAdmin }
```

- **Errores frecuentes:**
  - Lista blanca por nombre: alguien se cambia el nombre o usa caracteres
    parecidos y entra.
  - Comprobar el permiso en el cliente y confiar en un remote: cualquiera puede
    llamar al remote. La comprobacion va **en el servidor, al principio de la
    funcion**.
  - Comandos sin limites: `/velocidad 99999` rompe la fisica del personaje.
  - No registrar los intentos fallidos: no te enteras de que alguien lo esta
    probando.
  - Dejar los comandos activos en la version publicada sin quererlo.
- **Checklist sin errores:**
  - [ ] La lista blanca usa `UserId`
  - [ ] La comprobacion ocurre en el servidor, antes de cualquier accion
  - [ ] Todos los valores tienen rango
  - [ ] Los intentos no autorizados se registran

---

### 22. Anticheat basico

- **Que es:** comprobaciones minimas contra lo mas obvio.
- **Aviso honesto:** ningun anticheat del lado del cliente sirve. Lo unico que
  funciona de verdad es que **el servidor sea la autoridad** en todo lo que
  importa. Lo de abajo detecta lo evidente, no a alguien decidido.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local VELOCIDAD_MAXIMA = 60      -- studs por segundo, con margen
local MARGEN_TELEPORT = 120      -- studs en un solo intervalo
local INTERVALO = 1

local ultimaPosicion: { [Player]: Vector3 } = {}
local avisos: { [Player]: number } = {}

local function revisar(jugador: Player)
    local personaje = jugador.Character
    local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
    local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")

    if not raiz or not humanoide or humanoide.Health <= 0 then
        ultimaPosicion[jugador] = nil
        return
    end

    -- ignorar si esta sentado o cayendo, dan falsos positivos
    if humanoide.Sit or humanoide:GetState() == Enum.HumanoidStateType.Freefall then
        ultimaPosicion[jugador] = raiz.Position
        return
    end

    local anterior = ultimaPosicion[jugador]
    ultimaPosicion[jugador] = raiz.Position

    if not anterior then
        return
    end

    local recorrido = (raiz.Position - anterior).Magnitude

    if recorrido > MARGEN_TELEPORT then
        avisos[jugador] = (avisos[jugador] or 0) + 1
        warn(string.format(
            "Anticheat: %s recorrio %.1f studs en %.1f s (aviso %d)",
            jugador.Name, recorrido, INTERVALO, avisos[jugador]
        ))

        -- correccion suave: devolverlo, no expulsarlo
        raiz.CFrame = CFrame.new(anterior)
        ultimaPosicion[jugador] = anterior
    end

    -- velocidad declarada absurda
    if humanoide.WalkSpeed > VELOCIDAD_MAXIMA then
        warn("Anticheat: WalkSpeed anomalo en " .. jugador.Name)
        humanoide.WalkSpeed = 16
    end
end

task.spawn(function()
    while true do
        task.wait(INTERVALO)
        for _, jugador in Players:GetPlayers() do
            local ok, err = pcall(revisar, jugador)
            if not ok then
                warn("Error en anticheat: " .. tostring(err))
            end
        end
    end
end)

Players.PlayerRemoving:Connect(function(jugador)
    ultimaPosicion[jugador] = nil
    avisos[jugador] = nil
end)
```

- **Errores frecuentes:**
  - Expulsar al primer aviso: los falsos positivos por lag son constantes.
    Corrige la posicion, acumula avisos, y actua solo con muchos.
  - No ignorar caidas, vehiculos ni teletransportes legitimos del propio juego:
    tu anticheat expulsara a jugadores honestos.
  - Poner el anticheat en el cliente: se desactiva en dos minutos.
  - Creer que esto sustituye a validar en el servidor. No lo hace. Es un extra.
- **Checklist sin errores:**
  - [ ] Corre en el servidor
  - [ ] Ignora estados que dan falsos positivos
  - [ ] Corrige antes de castigar
  - [ ] La validacion real vive en cada sistema, no aqui

---

## Como encaja todo

```text
                    Datos (modulo 06)
                          |
        +-----------------+-----------------+
        |                 |                 |
    Economia          Inventario          Pase
        |                 |                 |
        +-------+---------+--------+--------+
                |                  |
             Tienda            Entregas
                                   |
                    +--------------+--------------+
                    |              |              |
                Misiones        Logros         Ronda
                                                  |
                                    +-------------+-------------+
                                    |             |             |
                                 Equipos       Oleadas    Temporizador
                                                  |
                                                 NPC

    Todo lo de arriba vive en el SERVIDOR.
    La interfaz (modulo 05) solo lee atributos y llama a remotes validados.
```

---

## Checklist maestro de sistemas

- [ ] Cada sistema es un ModuleScript con `iniciar` y `detener`
- [ ] Todos los `require` estan en `pcall` y no hay ciclos
- [ ] Una sola puerta de entrada para modificar monedas
- [ ] Comprobar y cobrar ocurren juntos, sin esperas en medio
- [ ] Los precios y catalogos viven solo en el servidor
- [ ] Las recompensas se marcan antes de entregarse
- [ ] Si una entrega falla, la marca se deshace
- [ ] El inventario vive en los datos del servidor
- [ ] Las misiones solo avanzan desde codigo del servidor
- [ ] La maquina de rondas comprueba que hay jugadores
- [ ] Los manejadores de fase estan en `pcall`
- [ ] El temporizador publica el instante de fin, no el numero
- [ ] Los NPC tienen histeresis en la deteccion
- [ ] `ComputeAsync` esta en `pcall` y se revisa `Path.Status`
- [ ] Hay tope de enemigos vivos y de vida por oleada
- [ ] La lista de admins usa `UserId` y se comprueba en el servidor
- [ ] Todo estado por jugador se limpia en `PlayerRemoving`
- [ ] Probado con dos jugadores, muriendo, saliendo y volviendo

---

## Siguiente paso

El catalogo completo de errores y todas las listas de comprobacion en
`mecanicas/09-errores-y-checklist.md`. Para pedirle mecanicas nuevas a otra IA,
`prompts/PROMPT-3-MECANICAS.md`.
