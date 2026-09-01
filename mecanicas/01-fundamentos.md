# 01 - Fundamentos y ejecucion sin errores

Modulo 1 del catalogo de mecanicas. Aqui esta la base que sostiene todo lo
demas: donde va cada script, como se pide un servicio, como se espera a que
algo exista y como se evitan los fallos que aparecen una y otra vez.

Si una mecanica de otro modulo falla, casi siempre la causa esta en este.
Leelo entero antes de tocar los demas.

## Indice

| # | Mecanica | Para que |
|---|---|---|
| 1 | Obtener servicios con GetService | Acceso fiable a la API |
| 2 | Script, LocalScript y ModuleScript | Elegir donde corre el codigo |
| 3 | Modulo reutilizable con require | No repetir codigo |
| 4 | Ciclo de vida del jugador | Entrada y salida de jugadores |
| 5 | Ciclo de vida del personaje | Respawn sin romper nada |
| 6 | Esperar instancias sin colgarse | Evitar el infinite yield |
| 7 | Bucle por frame con RunService | Logica continua |
| 8 | Libreria task | Esperas y tareas paralelas |
| 9 | pcall y xpcall | Que un fallo no tumbe el script |
| 10 | Tipado Luau estricto | Cazar errores antes de ejecutar |
| 11 | Attributes como estado replicado | Compartir datos sin remotes |
| 12 | CollectionService y tags | Comportamiento por etiqueta |
| 13 | Limpieza de conexiones (Trove) | Evitar fugas de memoria |
| 14 | Debris y destruccion diferida | Limpiar efectos temporales |
| 15 | Frontera cliente-servidor | Saber que se replica |
| 16 | Arranque ordenado y precarga | Evitar carreras de inicio |
| 17 | Diagnostico: mi script no corre | Checklist de arranque |
| 18 | APIs obsoletas y sus reemplazos | No heredar codigo roto |

---

## Mapa de contenedores

Donde pongas un script decide si funciona. Esta tabla es la referencia:

| Contenedor | Que corre ahi | Visible para el cliente |
|---|---|---|
| `ServerScriptService` | Script de servidor | No |
| `ServerStorage` | Modelos y modulos solo de servidor | No |
| `ReplicatedStorage` | Modulos y remotes compartidos | Si |
| `StarterPlayer/StarterPlayerScripts` | LocalScript del jugador | Si |
| `StarterPlayer/StarterCharacterScripts` | LocalScript que revive con el personaje | Si |
| `StarterGui` | ScreenGui y LocalScript de interfaz | Si |
| `StarterPack` | Tools que recibe el jugador al aparecer | Si |
| `Workspace` | Partes y modelos del mundo | Si |

Regla corta: **logica que decide, en el servidor. Logica que muestra, en el
cliente.**

---

### 1. Obtener servicios con GetService

- **Que es:** la forma correcta de pedir un servicio de Roblox.
- **Para que sirve:** conseguir `Players`, `ReplicatedStorage`, `RunService` y
  demas sin depender del nombre que tengan en el arbol.
- **API implicada:** `game:GetService()`.
- **Donde va:** en la cabecera de cualquier script.
- **Codigo listo para pegar:**

```lua
-- Cabecera estandar de cualquier script del proyecto
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local CollectionService = game:GetService("CollectionService")
local UserInputService = game:GetService("UserInputService")
local Debris = game:GetService("Debris")
```

- **Errores frecuentes:**
  - Usar `game.Players`. Funciona por casualidad; si alguien renombra el
    servicio o aun no existe, revienta.
  - Llamar a `GetService` dentro de un bucle. Guardalo en una variable local.
  - Pedir `ServerStorage` desde un LocalScript: el cliente no lo ve y devuelve
    error de permisos.
- **Checklist sin errores:**
  - [ ] Todos los servicios estan en variables locales al principio del script
  - [ ] Ningun `game.Servicio` con punto
  - [ ] Ningun servicio de servidor pedido desde el cliente

---

### 2. Script, LocalScript y ModuleScript

- **Que es:** los tres tipos de script y el contexto donde se ejecuta cada uno.
- **Para que sirve:** decidir donde escribir cada mecanica.
- **API implicada:** `Script`, `LocalScript`, `ModuleScript`, `RunContext`.
- **Donde va:** decision previa a escribir cualquier codigo.

| Tipo | Corre en | Contenedores validos | Uso tipico |
|---|---|---|---|
| `Script` | Servidor | ServerScriptService, Workspace | Dano, economia, guardado |
| `LocalScript` | Cliente | StarterPlayerScripts, StarterGui, StarterCharacterScripts, StarterPack | Entrada, camara, GUI |
| `ModuleScript` | El que lo requiere | ReplicatedStorage, ServerStorage | Logica reutilizable |

- **Codigo listo para pegar:**

```lua
-- Comprobacion defensiva al inicio de un modulo compartido
local RunService = game:GetService("RunService")

if RunService:IsServer() then
	print("Este codigo corre en el servidor")
else
	print("Este codigo corre en el cliente")
end
```

- **Errores frecuentes:**
  - Un `LocalScript` dentro de `Workspace` o `ServerScriptService`: no se
    ejecuta nunca y no avisa.
  - Un `Script` dentro de `StarterGui`: se ejecuta, pero no puede tocar la
    interfaz del jugador como esperas.
  - Creer que un `ModuleScript` corre solo. No corre hasta que alguien hace
    `require`.
- **Checklist sin errores:**
  - [ ] Cada script esta en un contenedor valido para su tipo
  - [ ] La logica que otorga recompensas esta en el servidor
  - [ ] La captura de teclado esta en el cliente

---

### 3. Modulo reutilizable con require

- **Que es:** un `ModuleScript` que devuelve una tabla con funciones.
- **Para que sirve:** compartir logica entre scripts sin copiar y pegar.
- **API implicada:** `require`, `ModuleScript`.
- **Donde va:** el modulo en `ReplicatedStorage/Modulos`, el consumidor donde
  haga falta.
- **Codigo listo para pegar:**

```lua
-- ModuleScript: ReplicatedStorage/Modulos/Utilidades
local Utilidades = {}

function Utilidades.redondear(valor: number, decimales: number): number
	local factor = 10 ^ decimales
	return math.floor(valor * factor + 0.5) / factor
end

function Utilidades.obtenerHumanoid(instancia: Instance): Humanoid?
	local modelo = instancia:FindFirstAncestorOfClass("Model")
	if not modelo then
		return nil
	end
	return modelo:FindFirstChildOfClass("Humanoid")
end

return Utilidades
```

```lua
-- Script consumidor
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Utilidades = require(ReplicatedStorage.Modulos.Utilidades)

print(Utilidades.redondear(3.14159, 2)) -- 3.14
```

- **Errores frecuentes:**
  - Olvidar el `return` final del modulo. Error: `Module code did not return
    exactly one value`.
  - Requerir en bucle: A requiere B y B requiere A. Error de dependencia
    circular.
  - Un modulo se cachea: si guarda estado, ese estado es compartido por todos
    los que lo requieren en el mismo contexto.
- **Checklist sin errores:**
  - [ ] El modulo termina con `return`
  - [ ] No hay dependencias circulares
  - [ ] El estado compartido es intencional

---

### 4. Ciclo de vida del jugador

- **Que es:** reaccionar a que un jugador entra o sale.
- **Para que sirve:** crear leaderstats, cargar datos, guardar al salir.
- **API implicada:** `Players.PlayerAdded`, `Players.PlayerRemoving`,
  `Players:GetPlayers()`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")

local function alEntrar(jugador: Player)
	local stats = Instance.new("Folder")
	stats.Name = "leaderstats"
	stats.Parent = jugador

	local monedas = Instance.new("IntValue")
	monedas.Name = "Monedas"
	monedas.Value = 0
	monedas.Parent = stats
end

local function alSalir(jugador: Player)
	print(jugador.Name .. " salio")
	-- aqui va el guardado
end

Players.PlayerAdded:Connect(alEntrar)
Players.PlayerRemoving:Connect(alSalir)

-- Cubre a los que ya estaban dentro antes de que el script arrancara
for _, jugador in Players:GetPlayers() do
	task.spawn(alEntrar, jugador)
end
```

- **Errores frecuentes:**
  - No recorrer `GetPlayers()` al inicio. En Studio el primer jugador suele
    entrar antes que el script y se queda sin leaderstats.
  - Poner esta logica en un LocalScript: cada cliente solo ve su propio evento.
  - Tardar demasiado en `PlayerRemoving`: el jugador puede desaparecer antes.
- **Checklist sin errores:**
  - [ ] Hay bucle sobre `GetPlayers()` ademas del evento
  - [ ] El script esta en `ServerScriptService`
  - [ ] El guardado tambien esta enganchado a `BindToClose`

---

### 5. Ciclo de vida del personaje

- **Que es:** reaccionar a cada aparicion del personaje.
- **Para que sirve:** aplicar velocidad, vida o efectos cada vez que revive.
- **API implicada:** `Player.CharacterAdded`, `Player.Character`,
  `Player.CharacterRemoving`, `Humanoid.Died`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")

local function alAparecerPersonaje(jugador: Player, personaje: Model)
	local humanoid = personaje:WaitForChild("Humanoid", 10) :: Humanoid?
	if not humanoid then
		warn("Sin Humanoid para " .. jugador.Name)
		return
	end

	humanoid.WalkSpeed = 18
	humanoid.MaxHealth = 150
	humanoid.Health = 150

	humanoid.Died:Connect(function()
		print(jugador.Name .. " murio")
	end)
end

Players.PlayerAdded:Connect(function(jugador)
	jugador.CharacterAdded:Connect(function(personaje)
		alAparecerPersonaje(jugador, personaje)
	end)

	-- Por si el personaje ya existia
	if jugador.Character then
		alAparecerPersonaje(jugador, jugador.Character)
	end
end)
```

- **Errores frecuentes:**
  - Guardar `jugador.Character` en una variable al inicio: tras el primer
    respawn apunta a un modelo destruido.
  - Usar `Character.Humanoid` directo. En el momento del evento puede no
    existir todavia.
  - Aplicar mejoras solo al entrar: se pierden en cada muerte.
- **Checklist sin errores:**
  - [ ] Todo lo del personaje se reaplica en `CharacterAdded`
  - [ ] Se usa `WaitForChild` con timeout para el Humanoid
  - [ ] Se cubre el caso de personaje ya existente

---

### 6. Esperar instancias sin colgarse

- **Que es:** las tres formas de acceder a un hijo y cuando usar cada una.
- **Para que sirve:** evitar el error mas comun de todos:
  `attempt to index nil with ...`.
- **API implicada:** `WaitForChild`, `FindFirstChild`, `ChildAdded:Wait()`.

| Funcion | Bloquea | Devuelve nil | Cuando usarla |
|---|---|---|---|
| `WaitForChild(nombre)` | Si, para siempre | Nunca | Algo que seguro llegara |
| `WaitForChild(nombre, 10)` | Si, 10 segundos | Si, al agotarse | Lo anterior, pero seguro |
| `FindFirstChild(nombre)` | No | Si | Puede no existir |

- **Donde va:** en cualquier script que acceda al arbol.
- **Codigo listo para pegar:**

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Correcto: con timeout y comprobacion
local remotes = ReplicatedStorage:WaitForChild("Remotes", 15)
if not remotes then
	warn("No aparecio la carpeta Remotes en 15 segundos")
	return
end

local disparar = remotes:WaitForChild("Disparar", 15)
if not disparar then
	warn("Falta el RemoteEvent Disparar")
	return
end

-- Correcto: para algo opcional
local casco = script.Parent:FindFirstChild("Casco")
if casco then
	casco.Transparency = 0.5
end
```

- **Errores frecuentes:**
  - `Infinite yield possible on 'X:WaitForChild("Y")'`. No es un error, es un
    aviso: el objeto nunca llego. Revisa el nombre exacto y si el objeto es
    visible desde ese contexto.
  - Usar `WaitForChild` en el servidor sobre algo que crea el cliente: no
    llegara nunca.
  - Encadenar sin comprobar: `a:FindFirstChild("b").c` revienta si `b` es nil.
- **Checklist sin errores:**
  - [ ] Ningun `WaitForChild` sin timeout en codigo critico
  - [ ] Cada `FindFirstChild` va seguido de un `if`
  - [ ] Los nombres coinciden exactamente, mayusculas incluidas

---

### 7. Bucle por frame con RunService

- **Que es:** ejecutar logica en cada fotograma o en cada paso de fisica.
- **Para que sirve:** camara, seguimiento, barras que se actualizan, fisica
  personalizada.
- **API implicada:** `RunService.Heartbeat`, `PreSimulation`, `PostSimulation`,
  `RenderStepped`, `PreRender`, `BindToRenderStep`.

| Evento | Contexto | Cuando dispara | Uso |
|---|---|---|---|
| `Heartbeat` | Ambos | Tras la fisica | Logica general por frame |
| `PreSimulation` | Ambos | Antes de la fisica | Empujar fuerzas |
| `PostSimulation` | Ambos | Despues de la fisica | Leer resultados |
| `PreRender` | Solo cliente | Antes de dibujar | Camara y GUI |
| `RenderStepped` | Solo cliente | Antes de dibujar (antiguo) | Igual que PreRender |

- **Donde va:** LocalScript para los de render, Script o LocalScript para el
  resto.
- **Codigo listo para pegar:**

```lua
local RunService = game:GetService("RunService")

local acumulado = 0
local INTERVALO = 0.25 -- ejecutar 4 veces por segundo, no 60

local conexion
conexion = RunService.Heartbeat:Connect(function(deltaTime: number)
	acumulado += deltaTime
	if acumulado < INTERVALO then
		return
	end
	acumulado = 0

	-- trabajo periodico barato
end)

-- Cuando ya no haga falta
-- conexion:Disconnect()
```

- **Errores frecuentes:**
  - Usar `RenderStepped` en el servidor: no existe y lanza error.
  - Hacer trabajo pesado cada frame. Usa un acumulador como el del ejemplo.
  - Nunca desconectar el bucle: sigue corriendo aunque el objeto ya no exista.
  - Ignorar `deltaTime` y asumir 60 FPS. En un movil corre a 30.
- **Checklist sin errores:**
  - [ ] El evento existe en ese contexto
  - [ ] Se usa `deltaTime` para todo lo que dependa del tiempo
  - [ ] La conexion se guarda y se desconecta

---

### 8. Libreria task

- **Que es:** el sistema moderno de esperas y tareas de Luau.
- **Para que sirve:** retrasos, paralelismo y cancelacion sin los defectos de
  `wait` y `spawn`.
- **API implicada:** `task.wait`, `task.spawn`, `task.defer`, `task.delay`,
  `task.cancel`.

| Funcion | Que hace |
|---|---|
| `task.wait(n)` | Pausa n segundos y devuelve el tiempo real esperado |
| `task.spawn(f, ...)` | Ejecuta f de inmediato en otro hilo |
| `task.defer(f, ...)` | Ejecuta f al final del ciclo actual |
| `task.delay(n, f, ...)` | Ejecuta f dentro de n segundos |
| `task.cancel(hilo)` | Cancela un hilo pendiente |

- **Donde va:** cualquier script.
- **Codigo listo para pegar:**

```lua
-- Espera precisa
local esperado = task.wait(0.5)
print("Esperado de verdad:", esperado)

-- Tarea paralela que no bloquea el script principal
task.spawn(function()
	for i = 3, 1, -1 do
		print("Cuenta atras:", i)
		task.wait(1)
	end
end)

-- Retraso cancelable
local hilo = task.delay(5, function()
	print("Esto solo sale si nadie lo cancela")
end)

task.wait(2)
task.cancel(hilo)
```

- **Errores frecuentes:**
  - Usar `wait()` a secas: es impreciso, puede tardar mas de lo pedido y esta
    obsoleto.
  - Usar `spawn()`: introduce un retraso oculto de hasta un frame.
  - `task.wait()` sin argumento espera un frame, no cero segundos.
  - Bucles `while true do task.wait() end` sin condicion de salida.
- **Checklist sin errores:**
  - [ ] Cero apariciones de `wait(` y `spawn(` sueltos
  - [ ] Todo bucle infinito tiene condicion de salida o se desconecta
  - [ ] Los `task.delay` que puedan sobrar se cancelan

---

### 9. pcall y xpcall

- **Que es:** ejecutar codigo que puede fallar sin que se caiga el script.
- **Para que sirve:** obligatorio en DataStore, HttpService, MarketplaceService
  y cualquier llamada de red.
- **API implicada:** `pcall`, `xpcall`, `error`, `assert`, `warn`,
  `debug.traceback`.
- **Donde va:** Script de servidor, sobre todo.
- **Codigo listo para pegar:**

```lua
local function intentarConReintentos(funcion, intentos: number)
	intentos = intentos or 3
	local espera = 1

	for i = 1, intentos do
		local ok, resultado = pcall(funcion)
		if ok then
			return true, resultado
		end

		warn(("Intento %d/%d fallo: %s"):format(i, intentos, tostring(resultado)))
		if i < intentos then
			task.wait(espera)
			espera *= 2 -- retroceso exponencial
		end
	end

	return false, nil
end

-- Uso
local ok, datos = intentarConReintentos(function()
	return game:GetService("DataStoreService")
		:GetDataStore("Progreso")
		:GetAsync("jugador_1")
end, 3)

if not ok then
	warn("No se pudieron cargar los datos")
end
```

- **Errores frecuentes:**
  - Envolver todo en `pcall` y no mirar el error. Un fallo silencioso es peor
    que un error visible.
  - Usar `pcall` sin reintentos en DataStore: un throttle puntual pierde datos.
  - `assert(condicion)` sin mensaje: el error no dice nada util.
- **Checklist sin errores:**
  - [ ] Toda llamada asincrona externa esta en `pcall`
  - [ ] Los fallos se registran con `warn`
  - [ ] Hay reintentos con espera creciente donde importa

---

### 10. Tipado Luau estricto

- **Que es:** anotar tipos para que el analizador detecte errores sin ejecutar.
- **Para que sirve:** cazar `nil` y nombres mal escritos en el editor.
- **API implicada:** `--!strict`, `type`, `export type`, operador `::`.
- **Donde va:** primera linea de cualquier script.
- **Codigo listo para pegar:**

```lua
--!strict

export type Arma = {
	nombre: string,
	dano: number,
	cadencia: number,
	municion: number?,
}

local function crearArma(nombre: string, dano: number): Arma
	return {
		nombre = nombre,
		dano = dano,
		cadencia = 0.5,
		municion = nil,
	}
end

local function aplicarDano(humanoid: Humanoid, arma: Arma)
	humanoid:TakeDamage(arma.dano)
end

local parte = workspace:FindFirstChild("Bloque") :: BasePart?
if parte then
	parte.Anchored = true
end
```

- **Errores frecuentes:**
  - Poner `--!strict` en codigo antiguo y llenarse de avisos. Empieza con
    `--!nonstrict` y sube despues.
  - Abusar de `:: any` para callar el analizador: pierdes toda la ventaja.
  - Olvidar el `?` en valores que pueden ser nil.
- **Checklist sin errores:**
  - [ ] Los scripts nuevos empiezan con `--!strict`
  - [ ] Los tipos opcionales llevan `?`
  - [ ] No hay avisos del analizador en el Script Analysis

---

### 11. Attributes como estado replicado

- **Que es:** valores con nombre pegados a cualquier instancia, que se replican
  solos del servidor al cliente.
- **Para que sirve:** compartir estado sin crear ValueObjects ni remotes.
- **API implicada:** `SetAttribute`, `GetAttribute`, `GetAttributeChangedSignal`,
  `GetAttributes`.
- **Donde va:** el servidor escribe, el cliente lee.
- **Codigo listo para pegar:**

```lua
-- Servidor
local jugador = game:GetService("Players"):GetPlayers()[1]
jugador:SetAttribute("Energia", 100)
jugador:SetAttribute("Clase", "Repartidor")
```

```lua
-- Cliente
local jugador = game:GetService("Players").LocalPlayer

local function pintarEnergia()
	local energia = jugador:GetAttribute("Energia") or 0
	print("Energia:", energia)
end

jugador:GetAttributeChangedSignal("Energia"):Connect(pintarEnergia)
pintarEnergia()
```

- **Errores frecuentes:**
  - Escribir un atributo desde el cliente esperando que el servidor lo vea. No
    se replica hacia arriba.
  - Guardar tablas: los atributos solo aceptan tipos simples (numero, texto,
    booleano, Vector3, Color3, UDim2 y similares).
  - Leer el atributo antes de que el servidor lo cree: devuelve nil, por eso el
    `or 0` del ejemplo.
- **Checklist sin errores:**
  - [ ] Solo el servidor escribe atributos de estado
  - [ ] Toda lectura tiene valor por defecto
  - [ ] No se guardan tablas en atributos

---

### 12. CollectionService y tags

- **Que es:** etiquetar instancias y darles comportamiento por etiqueta.
- **Para que sirve:** un solo script gobierna cien puertas, sin copiar scripts
  dentro de cada una.
- **API implicada:** `AddTag`, `HasTag`, `GetTagged`, `GetInstanceAddedSignal`,
  `GetInstanceRemovedSignal`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local CollectionService = game:GetService("CollectionService")
local TAG = "Curativo"

local function activar(parte: BasePart)
	local enUso = false

	parte.Touched:Connect(function(otro)
		if enUso then
			return
		end

		local humanoid = otro.Parent and otro.Parent:FindFirstChildOfClass("Humanoid")
		if not humanoid or humanoid.Health <= 0 then
			return
		end

		enUso = true
		humanoid.Health = math.min(humanoid.Health + 25, humanoid.MaxHealth)
		parte.Transparency = 0.8
		task.wait(5)
		parte.Transparency = 0
		enUso = false
	end)
end

for _, parte in CollectionService:GetTagged(TAG) do
	activar(parte)
end

CollectionService:GetInstanceAddedSignal(TAG):Connect(activar)
```

- **Errores frecuentes:**
  - Conectar solo `GetInstanceAddedSignal` y olvidar `GetTagged`: los objetos
    que ya existian se quedan muertos.
  - Etiquetar en el cliente esperando efecto en el servidor.
  - No comprobar que la instancia sigue existiendo tras un `task.wait`.
- **Checklist sin errores:**
  - [ ] Se recorren los ya existentes y ademas se escucha el evento
  - [ ] El nombre del tag esta en una constante, no repetido a mano
  - [ ] Hay debounce en los que reaccionan a `Touched`

---

### 13. Limpieza de conexiones (patron Trove)

- **Que es:** un objeto que recuerda todo lo que hay que soltar y lo suelta de
  golpe.
- **Para que sirve:** evitar fugas de memoria y comportamientos fantasma tras
  un respawn.
- **API implicada:** `RBXScriptConnection:Disconnect()`, `Instance:Destroy()`.
- **Donde va:** ModuleScript en `ReplicatedStorage/Modulos`.
- **Codigo listo para pegar:**

```lua
-- ModuleScript: Trove
local Trove = {}
Trove.__index = Trove

function Trove.new()
	return setmetatable({ _items = {} }, Trove)
end

function Trove:add(item)
	table.insert(self._items, item)
	return item
end

function Trove:clean()
	for i = #self._items, 1, -1 do
		local item = self._items[i]
		if typeof(item) == "RBXScriptConnection" then
			item:Disconnect()
		elseif typeof(item) == "Instance" then
			item:Destroy()
		elseif type(item) == "function" then
			item()
		end
		self._items[i] = nil
	end
end

return Trove
```

```lua
-- Uso en el ciclo del personaje
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Trove = require(ReplicatedStorage.Modulos.Trove)
local Players = game:GetService("Players")

Players.PlayerAdded:Connect(function(jugador)
	jugador.CharacterAdded:Connect(function(personaje)
		local trove = Trove.new()
		local humanoid = personaje:WaitForChild("Humanoid")

		trove:add(humanoid.Running:Connect(function(velocidad)
			-- logica de pasos
		end))

		trove:add(humanoid.Died:Connect(function()
			trove:clean() -- se suelta todo de una vez
		end))
	end)
end)
```

- **Errores frecuentes:**
  - Conectar dentro de `CharacterAdded` y no desconectar: tras diez muertes hay
    diez conexiones activas y el dano se aplica diez veces.
  - Destruir la instancia pero dejar viva la conexion.
  - Llamar a `clean` dos veces sin vaciar la lista.
- **Checklist sin errores:**
  - [ ] Toda conexion creada por personaje se limpia al morir
  - [ ] No hay conexiones duplicadas tras varios respawns
  - [ ] Las instancias temporales se destruyen

---

### 14. Debris y destruccion diferida

- **Que es:** programar la destruccion de un objeto sin bloquear el script.
- **Para que sirve:** balas, efectos, sonidos y partes temporales.
- **API implicada:** `Debris:AddItem`, `Instance:Destroy`, `task.delay`.
- **Donde va:** donde se cree el objeto temporal.
- **Codigo listo para pegar:**

```lua
local Debris = game:GetService("Debris")

local function crearChispa(posicion: Vector3)
	local parte = Instance.new("Part")
	parte.Size = Vector3.new(0.4, 0.4, 0.4)
	parte.Position = posicion
	parte.Anchored = true
	parte.CanCollide = false
	parte.CanQuery = false
	parte.CanTouch = false
	parte.Material = Enum.Material.Neon
	parte.Color = Color3.fromRGB(255, 200, 60)
	parte.Parent = workspace

	Debris:AddItem(parte, 1.5) -- se destruye sola
	return parte
end
```

- **Errores frecuentes:**
  - Crear efectos y no destruirlos: el Workspace se llena y el juego se
    ralentiza sin motivo aparente.
  - Dejar `CanCollide` y `CanQuery` activos en efectos: los raycast del combate
    empiezan a impactar contra las chispas.
  - Poner el `Parent` antes de configurar las propiedades: cuesta mas
    rendimiento.
- **Checklist sin errores:**
  - [ ] Todo objeto temporal tiene `Debris:AddItem`
  - [ ] Los efectos llevan `CanCollide`, `CanQuery` y `CanTouch` en false
  - [ ] El `Parent` se asigna al final

---

### 15. Frontera cliente-servidor

- **Que es:** que ve cada lado y que viaja entre ellos.
- **Para que sirve:** entender por que algo funciona en Studio y falla en el
  juego real.
- **API implicada:** `RunService:IsServer()`, `RunService:IsClient()`,
  `RunService:IsStudio()`, RemoteEvent.

| Cambio hecho en | Se ve en el otro lado |
|---|---|
| Servidor, en Workspace | Si |
| Servidor, en ReplicatedStorage | Si |
| Servidor, en ServerStorage | No |
| Cliente, en cualquier sitio | No |
| Cliente, en su propia GUI | Solo el |

- **Donde va:** conocimiento previo, mas comprobaciones en modulos compartidos.
- **Codigo listo para pegar:**

```lua
local RunService = game:GetService("RunService")

local Modulo = {}

function Modulo.soloServidor()
	if not RunService:IsServer() then
		error("Esta funcion solo puede llamarse desde el servidor", 2)
	end
	-- logica sensible
end

return Modulo
```

- **Errores frecuentes:**
  - Cambiar la vida desde el cliente: se ve bien en tu pantalla y nadie mas lo
    nota. El servidor manda.
  - Probar solo con Play Solo. Usa Test con 2 jugadores para ver la separacion
    real.
  - Guardar secretos en ReplicatedStorage: el cliente lo lee todo.
- **Checklist sin errores:**
  - [ ] Probado con Test y dos jugadores
  - [ ] Nada sensible en ReplicatedStorage
  - [ ] Los modulos compartidos comprueban el contexto

---

### 16. Arranque ordenado y precarga

- **Que es:** garantizar que todo existe antes de empezar.
- **Para que sirve:** evitar el parpadeo de texturas y los errores del primer
  segundo de partida.
- **API implicada:** `ContentProvider:PreloadAsync`, `game:IsLoaded()`,
  `game.Loaded`.
- **Donde va:** LocalScript en `StarterPlayerScripts`.
- **Codigo listo para pegar:**

```lua
local ContentProvider = game:GetService("ContentProvider")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

if not game:IsLoaded() then
	game.Loaded:Wait()
end

local aPrecargar = {}
for _, objeto in ReplicatedStorage:GetDescendants() do
	if objeto:IsA("ImageLabel")
		or objeto:IsA("ImageButton")
		or objeto:IsA("Sound")
		or objeto:IsA("Animation")
	then
		table.insert(aPrecargar, objeto)
	end
end

local ok, err = pcall(function()
	ContentProvider:PreloadAsync(aPrecargar)
end)

if not ok then
	warn("Fallo la precarga: " .. tostring(err))
end

print("Todo cargado")
```

- **Errores frecuentes:**
  - Precargar cientos de objetos de golpe: la pantalla de carga se eterniza.
  - No envolver `PreloadAsync` en `pcall`: un asset borrado tumba el script.
  - Asumir que el servidor termina de cargar antes que el cliente.
- **Checklist sin errores:**
  - [ ] Se espera a `game.Loaded` en el cliente
  - [ ] `PreloadAsync` esta dentro de `pcall`
  - [ ] Solo se precarga lo que se ve al principio

---

### 17. Diagnostico: mi script no corre

- **Que es:** el orden de comprobaciones cuando no pasa absolutamente nada.
- **Para que sirve:** ahorrar horas.
- **API implicada:** ventana Output, propiedad `Disabled`, `RunContext`.
- **Donde va:** proceso de depuracion.

| Comprobacion | Como se ve |
|---|---|
| Contenedor correcto | LocalScript en Workspace no corre |
| `Disabled` en false | Propiedad en el panel Properties |
| Hay un `print` al inicio | Si no sale, el script ni arranca |
| Output abierto y sin filtros | View -> Output |
| Un `return` prematuro | Corta el resto del archivo |
| Un `WaitForChild` colgado | Aviso de infinite yield |
| Error en otro script del mismo hilo | Mira toda la ventana Output |

- **Codigo listo para pegar:**

```lua
-- Pega esto como primera linea del script sospechoso
print("[ARRANQUE]", script:GetFullName(), "servidor =", game:GetService("RunService"):IsServer())
```

- **Errores frecuentes:**
  - Editar el script en la sesion de prueba: al parar, los cambios se pierden.
  - Tener dos scripts con el mismo nombre y editar el que no es.
  - Filtrar la ventana Output y no ver los errores.
- **Checklist sin errores:**
  - [ ] El print de arranque aparece
  - [ ] El Output no tiene filtro activo
  - [ ] No se esta editando durante una sesion de prueba

---

### 18. APIs obsoletas y sus reemplazos

- **Que es:** la lista de funciones viejas que aparecen en tutoriales antiguos
  y hoy fallan o dan avisos.
- **Para que sirve:** no heredar codigo roto de la toolbox.
- **API implicada:** varias.

| Obsoleto | Reemplazo | Por que |
|---|---|---|
| `wait(n)` | `task.wait(n)` | Impreciso y con retraso extra |
| `spawn(f)` | `task.spawn(f)` | Retraso oculto de hasta un frame |
| `delay(n, f)` | `task.delay(n, f)` | Mismo problema |
| `Humanoid:LoadAnimation` | `Animator:LoadAnimation` | No replica bien |
| `BodyVelocity` | `LinearVelocity` | Sustituido por constraints |
| `BodyPosition` | `AlignPosition` | Sustituido por constraints |
| `BodyGyro` | `AlignOrientation` | Sustituido por constraints |
| `Region3` | `Workspace:GetPartBoundsInBox` | Mas rapido y sin limites de tamano |
| `FilterType.Blacklist` | `FilterType.Exclude` | Renombrado |
| `FilterType.Whitelist` | `FilterType.Include` | Renombrado |
| `Model:SetPrimaryPartCFrame` | `Model:PivotTo` | No necesita PrimaryPart |
| `Model:MoveTo` para colocar exacto | `Model:PivotTo` | MoveTo evita colisiones y desplaza |
| `tick()` | `os.clock()` | Precision y coherencia |
| `Player:GetMouse()` | `UserInputService` | Cubre movil y mando |
| `game.Workspace` | `workspace` | Mas corto y estable |

- **Codigo listo para pegar:**

```lua
-- Antes
-- local bv = Instance.new("BodyVelocity")
-- bv.Velocity = Vector3.new(0, 0, 50)
-- bv.Parent = raiz

-- Ahora
local attachment = Instance.new("Attachment")
attachment.Parent = raiz

local impulso = Instance.new("LinearVelocity")
impulso.Attachment0 = attachment
impulso.MaxForce = 20000
impulso.VectorVelocity = raiz.CFrame.LookVector * 50
impulso.RelativeTo = Enum.ActuatorRelativeTo.World
impulso.Parent = raiz

game:GetService("Debris"):AddItem(impulso, 0.25)
game:GetService("Debris"):AddItem(attachment, 0.25)
```

- **Errores frecuentes:**
  - Copiar modelos de la toolbox sin revisar: casi todos usan `BodyVelocity` y
    `wait`.
  - Mezclar `Region3` con `OverlapParams`: no son compatibles.
  - Usar `tick()` para cooldowns: cambia con la zona horaria del servidor.
- **Checklist sin errores:**
  - [ ] Busqueda de `wait(`, `spawn(`, `BodyVelocity`, `Region3` sin resultados
  - [ ] Los constraints sustituyen a los Body movers
  - [ ] Los cooldowns usan `os.clock()`

---

## Siguiente paso

Con esto cubierto, sigue por `mecanicas/02-movimiento.md`. El catalogo completo
esta en `mecanicas/00-INDICE.md` y los fallos concretos en
`mecanicas/09-errores-y-checklist.md`.
