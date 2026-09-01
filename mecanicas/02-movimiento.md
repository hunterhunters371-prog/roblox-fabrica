# 02 - Movimiento, control y camara

Modulo 2 del catalogo. Todo lo que hace que el personaje se mueva bien: correr,
saltar, deslizarse, trepar, la camara y la entrada de teclado, mando y movil.

Regla general de este modulo: **el movimiento se siente en el cliente y se
valida en el servidor.** Si mueves al jugador solo desde el servidor, se siente
pesado. Si solo desde el cliente, cualquiera puede volar.

## Indice

| # | Mecanica | Para que |
|---|---|---|
| 1 | Velocidad y salto del Humanoid | Ajuste base del personaje |
| 2 | Estados del Humanoid | Controlar saltar, caer, nadar |
| 3 | Sprint con resistencia | Correr con coste |
| 4 | Dash con LinearVelocity | Impulso corto direccional |
| 5 | Doble salto | Salto extra en el aire |
| 6 | Agacharse | Reducir altura y velocidad |
| 7 | Deslizamiento | Slide con friccion |
| 8 | Correr por la pared | Wall run con raycast |
| 9 | Agarre de borde | Ledge grab |
| 10 | Escalada con TrussPart | Trepar escaleras |
| 11 | Nadar y zonas de agua | Estado Swimming |
| 12 | UserInputService y ContextActionService | Capturar entrada |
| 13 | Botones tactiles para movil | Soporte de telefono |
| 14 | Primera persona y bloqueo de hombro | Modos de camara |
| 15 | Sacudida de camara | Impacto y peso |
| 16 | Asientos y VehicleSeat | Vehiculos |
| 17 | Teletransporte con PivotTo | Mover al personaje |
| 18 | Puntos de aparicion | SpawnLocation y equipos |
| 19 | Ragdoll al morir | Muerte con fisica |
| 20 | Dano por caida | Castigo por altura |
| 21 | Empuje | Knockback |
| 22 | Plataformas moviles | Sin jitter |
| 23 | Zonas que cambian la velocidad | Barro, hielo, turbo |

---

### 1. Velocidad y salto del Humanoid

- **Que es:** las propiedades que definen como se mueve el personaje.
- **Para que sirve:** ajustar el ritmo del juego. En un juego de entregas contra
  reloj, la velocidad base es la decision de diseno mas importante.
- **API implicada:** `Humanoid.WalkSpeed`, `JumpPower`, `JumpHeight`,
  `UseJumpPower`, `HipHeight`, `MaxSlopeAngle`, `AutoRotate`.

| Propiedad | Valor por defecto | Que hace |
|---|---|---|
| `WalkSpeed` | 16 | Studs por segundo |
| `JumpPower` | 50 | Fuerza de salto (si `UseJumpPower` es true) |
| `JumpHeight` | 7.2 | Altura en studs (si `UseJumpPower` es false) |
| `HipHeight` | 2 | Separacion del suelo |
| `MaxSlopeAngle` | 89 | Pendiente maxima que sube |
| `AutoRotate` | true | Si gira hacia donde camina |

- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")

local CONFIG = {
	walkSpeed = 18,
	jumpHeight = 8,
	maxHealth = 100,
}

local function configurar(personaje: Model)
	local humanoid = personaje:WaitForChild("Humanoid", 10) :: Humanoid?
	if not humanoid then
		return
	end

	humanoid.UseJumpPower = false -- trabajar en altura es mas predecible
	humanoid.JumpHeight = CONFIG.jumpHeight
	humanoid.WalkSpeed = CONFIG.walkSpeed
	humanoid.MaxHealth = CONFIG.maxHealth
	humanoid.Health = CONFIG.maxHealth
	humanoid.MaxSlopeAngle = 60
end

Players.PlayerAdded:Connect(function(jugador)
	jugador.CharacterAdded:Connect(configurar)
end)
```

- **Errores frecuentes:**
  - Cambiar `JumpPower` con `UseJumpPower` en false: no hace nada y no avisa.
  - Aplicar la configuracion solo al entrar: se pierde en cada respawn.
  - Subir `WalkSpeed` por encima de 100 sin tocar nada mas: el personaje
    atraviesa paredes finas.
- **Checklist sin errores:**
  - [ ] Se reaplica en `CharacterAdded`
  - [ ] `UseJumpPower` coherente con la propiedad que tocas
  - [ ] Probado en pendientes y escaleras

---

### 2. Estados del Humanoid

- **Que es:** la maquina de estados interna del personaje.
- **Para que sirve:** bloquear el salto, forzar una caida, detectar aterrizajes.
- **API implicada:** `Humanoid:GetState()`, `ChangeState()`, `SetStateEnabled()`,
  `StateChanged`, `Enum.HumanoidStateType`.

| Estado | Cuando ocurre |
|---|---|
| `Running` | Caminando o corriendo por el suelo |
| `Jumping` | Justo al saltar |
| `Freefall` | En el aire cayendo |
| `Landed` | Al tocar suelo |
| `Climbing` | Trepando una TrussPart |
| `Swimming` | En agua |
| `Seated` | Sentado |
| `PlatformStanding` | Sin control, de pie |
| `Physics` | Controlado por fisica pura (ragdoll) |
| `Dead` | Muerto |

- **Donde va:** Script o LocalScript segun el uso.
- **Codigo listo para pegar:**

```lua
local humanoid = script.Parent:WaitForChild("Humanoid") :: Humanoid

-- Prohibir el salto durante una animacion de ataque
local function bloquearSalto(bloquear: boolean)
	humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, not bloquear)
	humanoid:SetStateEnabled(Enum.HumanoidStateType.Freefall, not bloquear)
end

-- Detectar aterrizaje
humanoid.StateChanged:Connect(function(anterior, nuevo)
	if nuevo == Enum.HumanoidStateType.Landed then
		print("Aterrizo")
	end
end)

-- Forzar caida (por ejemplo al recibir un golpe en el aire)
humanoid:ChangeState(Enum.HumanoidStateType.Freefall)
```

- **Errores frecuentes:**
  - Desactivar `Freefall` y olvidarse: el personaje se queda flotando.
  - Usar `GetState()` en un bucle por frame en vez de `StateChanged`.
  - Cambiar estados desde el servidor mientras el cliente tiene la propiedad de
    red: el cliente los revierte.
- **Checklist sin errores:**
  - [ ] Todo estado desactivado se vuelve a activar
  - [ ] Se usa `StateChanged` en vez de sondear
  - [ ] Probado saltando, cayendo y nadando

---

### 3. Sprint con resistencia

- **Que es:** correr mas rapido gastando una barra que se recupera.
- **Para que sirve:** dar ritmo y decisiones al movimiento.
- **API implicada:** `ContextActionService`, `Humanoid.WalkSpeed`, `RemoteEvent`,
  Attributes.
- **Donde va:** LocalScript en `StarterPlayerScripts` mas Script de validacion en
  `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
-- LocalScript: StarterPlayerScripts/Sprint
local ContextActionService = game:GetService("ContextActionService")
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")

local jugador = Players.LocalPlayer

local VELOCIDAD_NORMAL = 18
local VELOCIDAD_SPRINT = 30
local ESTAMINA_MAX = 100
local GASTO = 22   -- por segundo
local RECUPERA = 14 -- por segundo

local estamina = ESTAMINA_MAX
local corriendo = false

local function humanoid(): Humanoid?
	local personaje = jugador.Character
	return personaje and personaje:FindFirstChildOfClass("Humanoid")
end

local function alternarSprint(_, estado: Enum.UserInputState)
	if estado == Enum.UserInputState.Begin then
		corriendo = true
	elseif estado == Enum.UserInputState.End then
		corriendo = false
	end
	return Enum.ContextActionResult.Pass
end

ContextActionService:BindAction(
	"Sprint",
	alternarSprint,
	true, -- crea boton tactil en movil
	Enum.KeyCode.LeftShift,
	Enum.KeyCode.ButtonL3
)
ContextActionService:SetTitle("Sprint", "CORRER")

RunService.Heartbeat:Connect(function(dt)
	local hum = humanoid()
	if not hum or hum.Health <= 0 then
		return
	end

	local enMovimiento = hum.MoveDirection.Magnitude > 0

	if corriendo and enMovimiento and estamina > 0 then
		estamina = math.max(0, estamina - GASTO * dt)
		hum.WalkSpeed = VELOCIDAD_SPRINT
	else
		estamina = math.min(ESTAMINA_MAX, estamina + RECUPERA * dt)
		hum.WalkSpeed = VELOCIDAD_NORMAL
	end

	jugador:SetAttribute("EstaminaVisual", math.floor(estamina))
end)
```

```lua
-- Script: ServerScriptService/AntiVelocidad
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local VELOCIDAD_MAXIMA_PERMITIDA = 32

RunService.Heartbeat:Connect(function()
	for _, jugador in Players:GetPlayers() do
		local personaje = jugador.Character
		local hum = personaje and personaje:FindFirstChildOfClass("Humanoid")
		if hum and hum.WalkSpeed > VELOCIDAD_MAXIMA_PERMITIDA then
			hum.WalkSpeed = VELOCIDAD_MAXIMA_PERMITIDA
		end
	end
end)
```

- **Errores frecuentes:**
  - Gastar resistencia estando quieto. Comprueba `MoveDirection.Magnitude`.
  - No poner tope en el servidor: el cliente puede escribir cualquier WalkSpeed.
  - Usar `UserInputService` en vez de `ContextActionService`: pierdes el boton
    automatico de movil.
- **Checklist sin errores:**
  - [ ] Solo gasta al moverse
  - [ ] El servidor limita la velocidad maxima
  - [ ] Funciona con teclado, mando y movil

---

### 4. Dash con LinearVelocity

- **Que es:** un impulso corto y fuerte en la direccion que mira el jugador.
- **Para que sirve:** esquivar, cruzar huecos, dar movilidad.
- **API implicada:** `LinearVelocity`, `Attachment`, `Debris`,
  `AssemblyLinearVelocity`.
- **Donde va:** LocalScript para la entrada, Script para aplicar el impulso.
- **Codigo listo para pegar:**

```lua
-- Script: ServerScriptService/Dash
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Debris = game:GetService("Debris")

local remote = Instance.new("RemoteEvent")
remote.Name = "PedirDash"
remote.Parent = ReplicatedStorage

local FUERZA = 90
local DURACION = 0.18
local ENFRIAMIENTO = 1.5

local ultimoUso: { [Player]: number } = {}

remote.OnServerEvent:Connect(function(jugador)
	local ahora = os.clock()
	if ahora - (ultimoUso[jugador] or 0) < ENFRIAMIENTO then
		return -- validacion de enfriamiento en el servidor
	end

	local personaje = jugador.Character
	local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = personaje and personaje:FindFirstChildOfClass("Humanoid")
	if not raiz or not hum or hum.Health <= 0 then
		return
	end

	ultimoUso[jugador] = ahora

	local attachment = Instance.new("Attachment")
	attachment.Parent = raiz

	local impulso = Instance.new("LinearVelocity")
	impulso.Attachment0 = attachment
	impulso.RelativeTo = Enum.ActuatorRelativeTo.World
	impulso.MaxForce = 100000
	impulso.VectorVelocity = raiz.CFrame.LookVector * FUERZA
	impulso.Parent = raiz

	Debris:AddItem(impulso, DURACION)
	Debris:AddItem(attachment, DURACION)
end)

game:GetService("Players").PlayerRemoving:Connect(function(jugador)
	ultimoUso[jugador] = nil
end)
```

```lua
-- LocalScript: StarterPlayerScripts/DashInput
local ContextActionService = game:GetService("ContextActionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local remote = ReplicatedStorage:WaitForChild("PedirDash", 15)
if not remote then
	return
end

ContextActionService:BindAction("Dash", function(_, estado)
	if estado == Enum.UserInputState.Begin then
		remote:FireServer()
	end
	return Enum.ContextActionResult.Pass
end, true, Enum.KeyCode.Q, Enum.KeyCode.ButtonB)

ContextActionService:SetTitle("Dash", "DASH")
```

- **Errores frecuentes:**
  - Usar `BodyVelocity`: esta obsoleto.
  - No destruir el `LinearVelocity`: el jugador sale volando para siempre.
  - No limpiar `ultimoUso` en `PlayerRemoving`: fuga de memoria.
  - Aplicar el dash sin `MaxForce` suficiente: no pasa nada.
- **Checklist sin errores:**
  - [ ] El enfriamiento se valida en el servidor
  - [ ] `LinearVelocity` y `Attachment` se destruyen con Debris
  - [ ] La tabla de enfriamientos se limpia al salir el jugador

---

### 5. Doble salto

- **Que es:** un segundo salto mientras se esta en el aire.
- **Para que sirve:** movilidad vertical y correccion de saltos fallidos.
- **API implicada:** `Humanoid.StateChanged`, `AssemblyLinearVelocity`,
  `UserInputService.JumpRequest`.
- **Donde va:** LocalScript en `StarterCharacterScripts`.
- **Codigo listo para pegar:**

```lua
-- LocalScript: StarterPlayer/StarterCharacterScripts/DobleSalto
local UserInputService = game:GetService("UserInputService")

local personaje = script.Parent
local humanoid = personaje:WaitForChild("Humanoid") :: Humanoid
local raiz = personaje:WaitForChild("HumanoidRootPart") :: BasePart

local SALTOS_MAXIMOS = 2
local FUERZA_SEGUNDO_SALTO = 55

local saltosUsados = 0

humanoid.StateChanged:Connect(function(_, nuevo)
	if nuevo == Enum.HumanoidStateType.Landed
		or nuevo == Enum.HumanoidStateType.Running
		or nuevo == Enum.HumanoidStateType.Climbing
	then
		saltosUsados = 0
	elseif nuevo == Enum.HumanoidStateType.Jumping then
		saltosUsados = math.max(saltosUsados, 1)
	end
end)

UserInputService.JumpRequest:Connect(function()
	if saltosUsados <= 0 or saltosUsados >= SALTOS_MAXIMOS then
		return
	end

	local estado = humanoid:GetState()
	if estado ~= Enum.HumanoidStateType.Freefall then
		return
	end

	saltosUsados += 1
	local v = raiz.AssemblyLinearVelocity
	raiz.AssemblyLinearVelocity = Vector3.new(v.X, FUERZA_SEGUNDO_SALTO, v.Z)
end)
```

- **Errores frecuentes:**
  - `JumpRequest` se dispara varias veces si mantienes la tecla. Por eso se
    comprueba el estado y el contador.
  - Sumar a la velocidad Y en vez de reemplazarla: el salto sale gigante si el
    jugador ya subia.
  - No reiniciar el contador al trepar o nadar.
- **Checklist sin errores:**
  - [ ] El contador se reinicia al tocar suelo
  - [ ] La velocidad Y se reemplaza, no se suma
  - [ ] No se puede encadenar saltos infinitos manteniendo espacio

---

### 6. Agacharse

- **Que es:** reducir altura y velocidad para pasar por huecos o cubrirse.
- **Para que sirve:** sigilo, coberturas, pasillos bajos.
- **API implicada:** `Humanoid.HipHeight`, `WalkSpeed`, `CameraOffset`.
- **Donde va:** LocalScript en `StarterPlayerScripts`.
- **Codigo listo para pegar:**

```lua
local ContextActionService = game:GetService("ContextActionService")
local TweenService = game:GetService("TweenService")
local Players = game:GetService("Players")

local jugador = Players.LocalPlayer
local agachado = false

local INFO = TweenInfo.new(0.18, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)

local function aplicar(estadoAgachado: boolean)
	local personaje = jugador.Character
	local hum = personaje and personaje:FindFirstChildOfClass("Humanoid")
	if not hum then
		return
	end

	local objetivo = estadoAgachado
		and { HipHeight = 0.8, WalkSpeed = 8, CameraOffset = Vector3.new(0, -1.2, 0) }
		or { HipHeight = 2, WalkSpeed = 18, CameraOffset = Vector3.zero }

	TweenService:Create(hum, INFO, objetivo):Play()
end

ContextActionService:BindAction("Agachar", function(_, estado)
	if estado == Enum.UserInputState.Begin then
		agachado = not agachado
		aplicar(agachado)
	end
	return Enum.ContextActionResult.Pass
end, true, Enum.KeyCode.C, Enum.KeyCode.ButtonR3)

jugador.CharacterAdded:Connect(function()
	agachado = false
end)
```

- **Errores frecuentes:**
  - No reiniciar el estado al respawnear: apareces agachado sin querer.
  - Cambiar `HipHeight` de golpe: el personaje pega un salto visual. Usa tween.
  - Olvidar que la hitbox no cambia sola: hay que redimensionar partes si
    quieres que agacharse esquive balas.
- **Checklist sin errores:**
  - [ ] Se reinicia en `CharacterAdded`
  - [ ] La transicion usa TweenService
  - [ ] La velocidad vuelve al valor correcto al levantarse

---

### 7. Deslizamiento

- **Que es:** un deslizamiento que conserva la inercia y frena poco a poco.
- **Para que sirve:** movimiento fluido, atajos, esquivar a ras de suelo.
- **API implicada:** `LinearVelocity`, `Humanoid.PlatformStand`, `RunService`.
- **Donde va:** Script en `ServerScriptService`, disparado por RemoteEvent.
- **Codigo listo para pegar:**

```lua
local Debris = game:GetService("Debris")

local DURACION = 0.7
local VELOCIDAD_INICIAL = 55

local function deslizar(personaje: Model)
	local raiz = personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = personaje:FindFirstChildOfClass("Humanoid")
	if not raiz or not hum then
		return
	end

	-- solo se desliza si va con velocidad y toca suelo
	if hum.MoveDirection.Magnitude < 0.1 then
		return
	end
	if hum:GetState() == Enum.HumanoidStateType.Freefall then
		return
	end

	local attachment = Instance.new("Attachment")
	attachment.Parent = raiz

	local impulso = Instance.new("LinearVelocity")
	impulso.Attachment0 = attachment
	impulso.RelativeTo = Enum.ActuatorRelativeTo.World
	impulso.MaxForce = 60000
	impulso.Parent = raiz

	local direccion = raiz.CFrame.LookVector
	local inicio = os.clock()
	local alturaOriginal = hum.HipHeight
	hum.HipHeight = 0.6

	local conexion
	conexion = game:GetService("RunService").Heartbeat:Connect(function()
		local t = (os.clock() - inicio) / DURACION
		if t >= 1 or not raiz.Parent then
			conexion:Disconnect()
			if hum.Parent then
				hum.HipHeight = alturaOriginal
			end
			return
		end
		-- friccion: la velocidad decae de forma cuadratica
		local factor = (1 - t) ^ 2
		impulso.VectorVelocity = direccion * (VELOCIDAD_INICIAL * factor)
	end)

	Debris:AddItem(impulso, DURACION)
	Debris:AddItem(attachment, DURACION)
end

return deslizar
```

- **Errores frecuentes:**
  - No desconectar el `Heartbeat`: se acumula un bucle por cada deslizamiento.
  - No restaurar `HipHeight` si el personaje muere a mitad.
  - Permitir deslizarse en el aire: se convierte en vuelo.
- **Checklist sin errores:**
  - [ ] El bucle se desconecta siempre
  - [ ] `HipHeight` se restaura incluso si el personaje muere
  - [ ] No funciona en el aire

---

### 8. Correr por la pared

- **Que es:** detectar una pared al lado y pegarse a ella mientras se corre.
- **Para que sirve:** parkour y rutas alternativas.
- **API implicada:** `workspace:Raycast`, `RaycastParams`, `AlignOrientation`,
  `Humanoid`.
- **Donde va:** LocalScript en `StarterCharacterScripts` con validacion de
  servidor para la posicion final.
- **Codigo listo para pegar:**

```lua
local RunService = game:GetService("RunService")

local personaje = script.Parent
local humanoid = personaje:WaitForChild("Humanoid") :: Humanoid
local raiz = personaje:WaitForChild("HumanoidRootPart") :: BasePart

local DISTANCIA = 3.2
local GRAVEDAD_REDUCIDA = 0.25

local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Exclude
params.FilterDescendantsInstances = { personaje }
params.IgnoreWater = true

local function detectarPared(): (RaycastResult?, number)
	local derecha = workspace:Raycast(raiz.Position, raiz.CFrame.RightVector * DISTANCIA, params)
	if derecha then
		return derecha, 1
	end
	local izquierda = workspace:Raycast(raiz.Position, -raiz.CFrame.RightVector * DISTANCIA, params)
	if izquierda then
		return izquierda, -1
	end
	return nil, 0
end

RunService.Heartbeat:Connect(function()
	if humanoid:GetState() ~= Enum.HumanoidStateType.Freefall then
		return
	end

	local resultado = detectarPared()
	if not resultado then
		return
	end

	-- frena la caida mientras haya pared al lado
	local v = raiz.AssemblyLinearVelocity
	if v.Y < 0 then
		raiz.AssemblyLinearVelocity = Vector3.new(v.X, v.Y * GRAVEDAD_REDUCIDA, v.Z)
	end
end)
```

- **Errores frecuentes:**
  - No excluir al propio personaje del raycast: se detecta a si mismo.
  - Detectar cualquier parte, incluidos efectos y balas. Filtra por
    `CollisionGroup` o por tag.
  - Permitir wall run sobre partes con `CanCollide` en false.
- **Checklist sin errores:**
  - [ ] El personaje esta en `FilterDescendantsInstances`
  - [ ] Solo cuenta como pared lo que es solido y vertical
  - [ ] No se puede quedar pegado indefinidamente

---

### 9. Agarre de borde

- **Que es:** engancharse al borde de una plataforma al caer junto a ella.
- **Para que sirve:** perdonar saltos justos y anadir verticalidad.
- **API implicada:** dos raycast (uno horizontal y otro hacia abajo),
  `Humanoid.PlatformStand`, `AlignPosition`.
- **Donde va:** LocalScript en `StarterCharacterScripts`.
- **Codigo listo para pegar:**

```lua
local RunService = game:GetService("RunService")

local personaje = script.Parent
local humanoid = personaje:WaitForChild("Humanoid") :: Humanoid
local raiz = personaje:WaitForChild("HumanoidRootPart") :: BasePart

local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Exclude
params.FilterDescendantsInstances = { personaje }

local agarrado = false

local function intentarAgarrar()
	if agarrado or humanoid:GetState() ~= Enum.HumanoidStateType.Freefall then
		return
	end
	if raiz.AssemblyLinearVelocity.Y > 2 then
		return -- solo al caer
	end

	local frente = workspace:Raycast(raiz.Position + Vector3.new(0, 1.5, 0), raiz.CFrame.LookVector * 2.5, params)
	if not frente then
		return
	end

	local arriba = raiz.Position + Vector3.new(0, 3.5, 0) + raiz.CFrame.LookVector * 1.5
	local haciaAbajo = workspace:Raycast(arriba, Vector3.new(0, -3, 0), params)
	if not haciaAbajo then
		return
	end

	agarrado = true
	humanoid.PlatformStand = true
	raiz.Anchored = true
	raiz.CFrame = CFrame.new(
		Vector3.new(raiz.Position.X, haciaAbajo.Position.Y - 2.6, raiz.Position.Z)
	) * CFrame.Angles(0, math.atan2(-frente.Normal.X, -frente.Normal.Z), 0)
end

local function soltar()
	if not agarrado then
		return
	end
	agarrado = false
	raiz.Anchored = false
	humanoid.PlatformStand = false
end

RunService.Heartbeat:Connect(intentarAgarrar)
game:GetService("UserInputService").JumpRequest:Connect(soltar)
humanoid.Died:Connect(soltar)
```

- **Errores frecuentes:**
  - Dejar `Anchored` en true al morir: el cadaver flota y el respawn falla.
  - No comprobar que se esta cayendo: te agarras subiendo.
  - Anclar la raiz en el servidor mientras el cliente tiene propiedad de red:
    provoca tirones.
- **Checklist sin errores:**
  - [ ] `Anchored` vuelve a false al soltar y al morir
  - [ ] Solo se agarra cayendo
  - [ ] Hay una tecla para soltarse

---

### 10. Escalada con TrussPart

- **Que es:** el sistema nativo de trepar de Roblox.
- **Para que sirve:** escaleras de mano, andamios, rejas.
- **API implicada:** `TrussPart`, `Enum.HumanoidStateType.Climbing`,
  `Humanoid.ClimbSpeed`.
- **Donde va:** el TrussPart en Workspace; el ajuste en un Script.
- **Codigo listo para pegar:**

```lua
-- Script: ServerScriptService/Escalada
local Players = game:GetService("Players")

Players.PlayerAdded:Connect(function(jugador)
	jugador.CharacterAdded:Connect(function(personaje)
		local hum = personaje:WaitForChild("Humanoid", 10) :: Humanoid?
		if not hum then
			return
		end

		hum:SetStateEnabled(Enum.HumanoidStateType.Climbing, true)
		hum.ClimbSpeed = 12

		hum.StateChanged:Connect(function(_, nuevo)
			if nuevo == Enum.HumanoidStateType.Climbing then
				print(personaje.Name .. " esta trepando")
			end
		end)
	end)
end)
```

- **Errores frecuentes:**
  - Usar una Part normal en vez de un `TrussPart`: no se puede trepar.
  - El TrussPart no esta anclado y se cae.
  - `Climbing` desactivado por otro script.
- **Checklist sin errores:**
  - [ ] La pieza es `TrussPart` y esta `Anchored`
  - [ ] El estado `Climbing` esta habilitado
  - [ ] La parte de arriba permite salir sin quedarse atascado

---

### 11. Nadar y zonas de agua

- **Que es:** el estado de natacion y como controlarlo.
- **Para que sirve:** rios, alcantarillas, zonas de agua sin usar Terreno.
- **API implicada:** `Terrain:FillBlock` con `Enum.Material.Water`,
  `Enum.HumanoidStateType.Swimming`, `Humanoid.Swimming`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")

Players.PlayerAdded:Connect(function(jugador)
	jugador.CharacterAdded:Connect(function(personaje)
		local hum = personaje:WaitForChild("Humanoid", 10) :: Humanoid?
		if not hum then
			return
		end

		hum.StateChanged:Connect(function(_, nuevo)
			if nuevo == Enum.HumanoidStateType.Swimming then
				hum.WalkSpeed = 12 -- se nada mas lento
			elseif nuevo == Enum.HumanoidStateType.Running then
				hum.WalkSpeed = 18
			end
		end)
	end)
end)
```

- **Errores frecuentes:**
  - Esperar que una Part azul con transparencia haga nadar: solo el material
    Water del Terreno activa `Swimming`.
  - Cambiar `WalkSpeed` al nadar y no restaurarlo al salir.
  - Desactivar el estado `Swimming` y ahogar al jugador dentro del agua.
- **Checklist sin errores:**
  - [ ] El agua es Terreno con material Water
  - [ ] La velocidad se restaura al salir
  - [ ] El estado `Swimming` esta habilitado

---

### 12. UserInputService y ContextActionService

- **Que es:** las dos formas de leer la entrada del jugador.
- **Para que sirve:** teclado, raton, mando y pantalla tactil.

| Servicio | Ventaja | Cuando usarlo |
|---|---|---|
| `UserInputService` | Control total, eventos crudos | Camara, gestos, deteccion de dispositivo |
| `ContextActionService` | Boton movil automatico, prioridades, desvincular por contexto | Acciones del juego: atacar, dash, interactuar |

- **Donde va:** LocalScript en `StarterPlayerScripts`.
- **Codigo listo para pegar:**

```lua
local UserInputService = game:GetService("UserInputService")
local ContextActionService = game:GetService("ContextActionService")

-- Deteccion de dispositivo
local esMovil = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
local hayMando = UserInputService.GamepadEnabled
print("Movil:", esMovil, "Mando:", hayMando)

-- Entrada cruda, ignorando cuando el jugador escribe en el chat
UserInputService.InputBegan:Connect(function(input, procesado)
	if procesado then
		return -- el jugador estaba escribiendo
	end
	if input.KeyCode == Enum.KeyCode.M then
		print("Abrir mapa")
	end
end)

-- Accion de juego, con boton en movil
local function interactuar(_, estado)
	if estado == Enum.UserInputState.Begin then
		print("Interactuar")
	end
	return Enum.ContextActionResult.Sink
end

ContextActionService:BindAction("Interactuar", interactuar, true,
	Enum.KeyCode.E, Enum.KeyCode.ButtonX)
ContextActionService:SetTitle("Interactuar", "USAR")
ContextActionService:SetPosition("Interactuar", UDim2.new(1, -140, 1, -140))

-- Desvincular cuando la accion deja de tener sentido
-- ContextActionService:UnbindAction("Interactuar")
```

- **Errores frecuentes:**
  - Ignorar el parametro `gameProcessedEvent`: el jugador escribe "queso" en el
    chat y dispara cuatro habilidades.
  - Usar `Player:GetMouse()`: obsoleto y no cubre movil ni mando.
  - No desvincular acciones: se acumulan botones tactiles en pantalla.
- **Checklist sin errores:**
  - [ ] Se comprueba `gameProcessedEvent`
  - [ ] Las acciones de juego usan `ContextActionService`
  - [ ] Cada `BindAction` tiene su `UnbindAction`

---

### 13. Botones tactiles para movil

- **Que es:** botones en pantalla generados automaticamente o a mano.
- **Para que sirve:** que el juego sea jugable en telefono, que es la mayoria
  del publico de Roblox.
- **API implicada:** `ContextActionService:BindAction` con `createTouchButton`,
  `SetImage`, `SetPosition`, `GetButton`.
- **Donde va:** LocalScript en `StarterPlayerScripts`.
- **Codigo listo para pegar:**

```lua
local ContextActionService = game:GetService("ContextActionService")
local UserInputService = game:GetService("UserInputService")

if not UserInputService.TouchEnabled then
	return -- no crear botones en escritorio
end

local function atacar(_, estado)
	if estado == Enum.UserInputState.Begin then
		print("Ataque")
	end
	return Enum.ContextActionResult.Sink
end

ContextActionService:BindAction("Atacar", atacar, true, Enum.KeyCode.F)
ContextActionService:SetTitle("Atacar", "")
ContextActionService:SetPosition("Atacar", UDim2.new(1, -150, 1, -160))

local boton = ContextActionService:GetButton("Atacar")
if boton then
	boton.Size = UDim2.fromOffset(84, 84)
end
```

- **Errores frecuentes:**
  - Crear botones tactiles en PC: ocupan pantalla sin motivo.
  - Colocar botones encima del joystick virtual de la esquina inferior
    izquierda.
  - No probar en el emulador de dispositivo de Studio.
- **Checklist sin errores:**
  - [ ] Solo se crean si `TouchEnabled` es true
  - [ ] No tapan el joystick ni el boton de salto
  - [ ] Probado en el emulador con un telefono pequeno

---

### 14. Primera persona y bloqueo de hombro

- **Que es:** cambiar el modo de camara del jugador.
- **Para que sirve:** apuntar, inmersion, juegos de disparos.
- **API implicada:** `Player.CameraMode`, `CameraMaxZoomDistance`,
  `CameraMinZoomDistance`, `UserInputService.MouseBehavior`,
  `Humanoid.CameraOffset`.
- **Donde va:** LocalScript en `StarterPlayerScripts`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")

local jugador = Players.LocalPlayer

local function primeraPersona()
	jugador.CameraMode = Enum.CameraMode.LockFirstPerson
end

local function terceraPersona()
	jugador.CameraMode = Enum.CameraMode.Classic
	jugador.CameraMinZoomDistance = 6
	jugador.CameraMaxZoomDistance = 18
end

local function bloqueoHombro(activo: boolean)
	local personaje = jugador.Character
	local hum = personaje and personaje:FindFirstChildOfClass("Humanoid")
	if not hum then
		return
	end

	if activo then
		UserInputService.MouseBehavior = Enum.MouseBehavior.LockCenter
		hum.AutoRotate = true
		hum.CameraOffset = Vector3.new(2, 0, 0)
	else
		UserInputService.MouseBehavior = Enum.MouseBehavior.Default
		hum.CameraOffset = Vector3.zero
	end
end

terceraPersona()
```

- **Errores frecuentes:**
  - Dejar `MouseBehavior` en `LockCenter` al abrir un menu: el jugador no puede
    hacer clic en nada.
  - Cambiar `CameraMode` sin restaurarlo al morir.
  - Poner `CameraMinZoomDistance` igual a `CameraMaxZoomDistance` y bloquear el
    zoom sin querer.
- **Checklist sin errores:**
  - [ ] El raton se libera al abrir cualquier interfaz
  - [ ] El modo de camara se restaura en `CharacterAdded`
  - [ ] Probado con el chat abierto

---

### 15. Sacudida de camara

- **Que es:** un temblor corto de la camara.
- **Para que sirve:** impactos, explosiones, pasos de un jefe.
- **API implicada:** `Camera.CFrame`, `RunService.RenderStepped`, ruido
  aleatorio.
- **Donde va:** ModuleScript en `ReplicatedStorage/Modulos`, usado desde el
  cliente.
- **Codigo listo para pegar:**

```lua
-- ModuleScript: SacudidaCamara
local RunService = game:GetService("RunService")

local Sacudida = {}

function Sacudida.aplicar(intensidad: number, duracion: number)
	local camara = workspace.CurrentCamera
	if not camara then
		return
	end

	local inicio = os.clock()
	local nombre = "SacudidaCamara_" .. tostring(inicio)

	RunService:BindToRenderStep(nombre, Enum.RenderPriority.Camera.Value + 1, function()
		local t = (os.clock() - inicio) / duracion
		if t >= 1 then
			RunService:UnbindFromRenderStep(nombre)
			return
		end

		local fuerza = intensidad * (1 - t) -- se apaga sola
		local desvio = Vector3.new(
			(math.random() - 0.5) * fuerza,
			(math.random() - 0.5) * fuerza,
			0
		)
		camara.CFrame = camara.CFrame * CFrame.new(desvio)
	end)
end

return Sacudida
```

- **Errores frecuentes:**
  - Modificar `Camera.CFrame` sin desvincular: la camara queda temblando para
    siempre.
  - Sacudir con intensidad alta: marea y tapa la accion. Valores de 0.2 a 0.6
    suelen bastar.
  - Ejecutarlo en el servidor: la camara es del cliente.
- **Checklist sin errores:**
  - [ ] Siempre se llama a `UnbindFromRenderStep`
  - [ ] La intensidad decae con el tiempo
  - [ ] Corre solo en el cliente

---

### 16. Asientos y VehicleSeat

- **Que es:** sentar al personaje y, con `VehicleSeat`, darle control de un
  vehiculo.
- **Para que sirve:** motos de reparto, coches, sillas de lobby.
- **API implicada:** `Seat`, `VehicleSeat`, `Seat.Occupant`, `Sit`,
  `VehicleSeat.Throttle`, `Steer`, `MaxSpeed`, `TurnSpeed`.
- **Donde va:** Script dentro del asiento.
- **Codigo listo para pegar:**

```lua
-- Script dentro del VehicleSeat
local asiento = script.Parent :: VehicleSeat
local Players = game:GetService("Players")

asiento.MaxSpeed = 60
asiento.TurnSpeed = 6
asiento.Torque = 25

asiento:GetPropertyChangedSignal("Occupant"):Connect(function()
	local ocupante = asiento.Occupant
	if ocupante then
		local jugador = Players:GetPlayerFromCharacter(ocupante.Parent)
		if jugador then
			print(jugador.Name .. " subio al vehiculo")
			asiento:SetNetworkOwner(jugador) -- control suave para el conductor
		end
	else
		print("Vehiculo libre")
		asiento:SetNetworkOwnershipAuto()
	end
end)
```

- **Errores frecuentes:**
  - No dar propiedad de red al conductor: el vehiculo va a tirones.
  - Dejar la propiedad de red asignada tras bajarse.
  - Usar `Seat` en vez de `VehicleSeat` y esperar que responda al teclado.
- **Checklist sin errores:**
  - [ ] La propiedad de red se asigna al subir y se libera al bajar
  - [ ] El asiento esta soldado al resto del vehiculo
  - [ ] Probado con dos jugadores

---

### 17. Teletransporte con PivotTo

- **Que es:** mover al personaje entero a otro punto.
- **Para que sirve:** portales, checkpoints, volver al lobby.
- **API implicada:** `Model:PivotTo`, `Model:GetPivot`, `CFrame`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local function teletransportar(personaje: Model, destino: CFrame)
	local hum = personaje:FindFirstChildOfClass("Humanoid")
	if not hum or hum.Health <= 0 then
		return false
	end

	local raiz = personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not raiz then
		return false
	end

	-- Se sube un poco para no quedar dentro del suelo
	personaje:PivotTo(destino + Vector3.new(0, 3, 0))
	raiz.AssemblyLinearVelocity = Vector3.zero
	raiz.AssemblyAngularVelocity = Vector3.zero
	return true
end

return teletransportar
```

- **Errores frecuentes:**
  - Mover solo `HumanoidRootPart.Position`: el resto del cuerpo se queda atras
    o el modelo se estira.
  - No poner la velocidad a cero: el jugador llega al destino a 80 studs por
    segundo y sale disparado.
  - Teletransportar al ras del suelo: el personaje se hunde.
- **Checklist sin errores:**
  - [ ] Se usa `PivotTo` sobre el modelo completo
  - [ ] Las velocidades se ponen a cero
  - [ ] Hay margen vertical en el destino

---

### 18. Puntos de aparicion

- **Que es:** donde aparece cada jugador.
- **Para que sirve:** lobby, equipos, rondas.
- **API implicada:** `SpawnLocation`, `Player.RespawnLocation`,
  `Player:LoadCharacter()`, `Teams`.
- **Donde va:** Script en `ServerScriptService`; los SpawnLocation en Workspace.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")

local function asignarSpawn(jugador: Player, nombreSpawn: string)
	local spawn = workspace:FindFirstChild(nombreSpawn, true)
	if not spawn or not spawn:IsA("SpawnLocation") then
		warn("No existe el SpawnLocation " .. nombreSpawn)
		return
	end

	jugador.RespawnLocation = spawn
end

Players.PlayerAdded:Connect(function(jugador)
	asignarSpawn(jugador, "SpawnLobby")
	jugador:LoadCharacter()
end)

-- Al empezar la ronda
local function moverTodosAPartida()
	for _, jugador in Players:GetPlayers() do
		asignarSpawn(jugador, "SpawnPartida")
		jugador:LoadCharacter()
	end
end
```

- **Errores frecuentes:**
  - Varios SpawnLocation con `Neutral` en true repartidos por el mapa: el
    jugador aparece donde no toca.
  - Cambiar `RespawnLocation` y no recargar el personaje.
  - `SpawnLocation` sin anclar: se cae del mapa.
- **Checklist sin errores:**
  - [ ] Los SpawnLocation estan anclados
  - [ ] Solo estan activos los que corresponden a la fase actual
  - [ ] Se llama a `LoadCharacter` tras cambiar el spawn

---

### 19. Ragdoll al morir

- **Que es:** convertir el esqueleto rigido en un cuerpo con fisica.
- **Para que sirve:** muertes con peso, caidas comicas, impacto visual.
- **API implicada:** `Motor6D`, `BallSocketConstraint`, `Attachment`,
  `Humanoid.PlatformStand`, `Enum.HumanoidStateType.Physics`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")

local function activarRagdoll(personaje: Model)
	local hum = personaje:FindFirstChildOfClass("Humanoid")
	if not hum then
		return
	end

	hum:ChangeState(Enum.HumanoidStateType.Physics)
	hum.PlatformStand = true

	for _, motor in personaje:GetDescendants() do
		if motor:IsA("Motor6D") and motor.Name ~= "RootJoint" then
			local a0 = Instance.new("Attachment")
			a0.CFrame = motor.C0
			a0.Parent = motor.Part0

			local a1 = Instance.new("Attachment")
			a1.CFrame = motor.C1
			a1.Parent = motor.Part1

			local socket = Instance.new("BallSocketConstraint")
			socket.Attachment0 = a0
			socket.Attachment1 = a1
			socket.LimitsEnabled = true
			socket.TwistLimitsEnabled = true
			socket.Parent = motor.Part0

			motor:Destroy()
		end
	end
end

Players.PlayerAdded:Connect(function(jugador)
	jugador.CharacterAdded:Connect(function(personaje)
		local hum = personaje:WaitForChild("Humanoid", 10) :: Humanoid?
		if hum then
			hum.Died:Connect(function()
				activarRagdoll(personaje)
			end)
		end
	end)
end)
```

- **Errores frecuentes:**
  - Destruir `RootJoint`: el personaje se desmonta entero.
  - Hacer ragdoll sin `PlatformStand`: el Humanoid intenta levantarse y da
    espasmos.
  - Ragdoll en el cliente: los demas ven al personaje de pie.
- **Checklist sin errores:**
  - [ ] `RootJoint` se conserva
  - [ ] `PlatformStand` en true y estado `Physics`
  - [ ] Se ejecuta en el servidor

---

### 20. Dano por caida

- **Que es:** restar vida segun la altura de la caida.
- **Para que sirve:** hacer que el mapa tenga riesgo vertical.
- **API implicada:** `Humanoid.StateChanged`, `HumanoidRootPart.Position`,
  `Humanoid:TakeDamage`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")

local ALTURA_SEGURA = 12   -- studs sin dano
local DANO_POR_STUD = 3.5

local function vigilar(personaje: Model)
	local hum = personaje:WaitForChild("Humanoid", 10) :: Humanoid?
	local raiz = personaje:WaitForChild("HumanoidRootPart", 10) :: BasePart?
	if not hum or not raiz then
		return
	end

	local alturaMaxima: number? = nil

	hum.StateChanged:Connect(function(_, nuevo)
		if nuevo == Enum.HumanoidStateType.Freefall then
			alturaMaxima = raiz.Position.Y
		elseif nuevo == Enum.HumanoidStateType.Landed then
			if not alturaMaxima then
				return
			end
			local caida = alturaMaxima - raiz.Position.Y
			alturaMaxima = nil

			if caida > ALTURA_SEGURA then
				local dano = (caida - ALTURA_SEGURA) * DANO_POR_STUD
				hum:TakeDamage(dano)
			end
		end
	end)
end

Players.PlayerAdded:Connect(function(jugador)
	jugador.CharacterAdded:Connect(vigilar)
end)
```

- **Errores frecuentes:**
  - Guardar la altura al saltar en vez de al empezar a caer: el salto normal
    hace dano.
  - No reiniciar `alturaMaxima`: acumula caidas.
  - Restar `Health` directamente en vez de `TakeDamage`: ignora ForceField.
- **Checklist sin errores:**
  - [ ] Un salto normal no hace dano
  - [ ] La altura se reinicia tras aterrizar
  - [ ] Se usa `TakeDamage`

---

### 21. Empuje

- **Que es:** lanzar al personaje en una direccion.
- **Para que sirve:** explosiones, golpes fuertes, trampas.
- **API implicada:** `AssemblyLinearVelocity`, `LinearVelocity`,
  `Humanoid.PlatformStand`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local function empujar(personaje: Model, direccion: Vector3, fuerza: number)
	local raiz = personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = personaje:FindFirstChildOfClass("Humanoid")
	if not raiz or not hum or hum.Health <= 0 then
		return
	end

	local unitaria = direccion.Magnitude > 0 and direccion.Unit or Vector3.new(0, 1, 0)
	local vector = (unitaria + Vector3.new(0, 0.45, 0)).Unit * fuerza

	raiz.AssemblyLinearVelocity = vector

	-- pequeno aturdimiento para que el empuje se note
	hum.PlatformStand = true
	task.delay(0.35, function()
		if hum.Parent and hum.Health > 0 then
			hum.PlatformStand = false
		end
	end)
end

return empujar
```

- **Errores frecuentes:**
  - Sumar a la velocidad existente: empujes encadenados mandan al jugador al
    espacio.
  - Dejar `PlatformStand` en true si el jugador muere durante el empuje.
  - Empujar desde el cliente: solo lo ve quien lo hace.
- **Checklist sin errores:**
  - [ ] La velocidad se reemplaza, no se suma
  - [ ] `PlatformStand` siempre vuelve a false
  - [ ] Se ejecuta en el servidor

---

### 22. Plataformas moviles

- **Que es:** partes que se mueven llevando al jugador encima.
- **Para que sirve:** ascensores, plataformas de salto, cintas.
- **API implicada:** `TweenService` sobre partes ancladas, `AlignPosition`,
  `BasePart.AssemblyLinearVelocity` para cintas.
- **Donde va:** Script dentro de la plataforma.
- **Codigo listo para pegar:**

```lua
-- Script dentro de la plataforma anclada
local TweenService = game:GetService("TweenService")

local plataforma = script.Parent :: BasePart
plataforma.Anchored = true

local PUNTO_A = plataforma.Position
local PUNTO_B = plataforma.Position + Vector3.new(0, 24, 0)
local DURACION = 4

local info = TweenInfo.new(
	DURACION,
	Enum.EasingStyle.Sine,
	Enum.EasingDirection.InOut,
	-1,   -- repetir infinito
	true, -- ida y vuelta
	0.5   -- pausa entre ciclos
)

TweenService:Create(plataforma, info, { Position = PUNTO_B }):Play()
```

```lua
-- Cinta transportadora: parte anclada con velocidad de superficie
local cinta = script.Parent :: BasePart
cinta.Anchored = true
cinta.AssemblyLinearVelocity = Vector3.zero
cinta.Velocity = cinta.CFrame.LookVector * 18 -- arrastra lo que este encima
```

- **Errores frecuentes:**
  - Plataforma sin anclar movida con tween: la fisica pelea con el tween y todo
    tiembla.
  - Mover la plataforma desde el cliente: cada jugador la ve en un sitio.
  - Plataformas rapidas sin `CanCollide`: el jugador la atraviesa.
- **Checklist sin errores:**
  - [ ] La plataforma esta `Anchored`
  - [ ] El movimiento lo hace el servidor
  - [ ] Probado con dos jugadores encima

---

### 23. Zonas que cambian la velocidad

- **Que es:** volumenes que modifican al jugador mientras esta dentro.
- **Para que sirve:** barro, hielo, turbo, zona de descanso.
- **API implicada:** `Workspace:GetPartsInPart`, `OverlapParams`,
  `CollectionService`, `RunService.Heartbeat`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local CollectionService = game:GetService("CollectionService")
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")

local TAG = "ZonaVelocidad"
local VELOCIDAD_BASE = 18

local params = OverlapParams.new()
params.FilterType = Enum.RaycastFilterType.Include

local acumulado = 0

RunService.Heartbeat:Connect(function(dt)
	acumulado += dt
	if acumulado < 0.2 then
		return
	end
	acumulado = 0

	local zonas = CollectionService:GetTagged(TAG)
	if #zonas == 0 then
		return
	end

	for _, jugador in Players:GetPlayers() do
		local personaje = jugador.Character
		local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
		local hum = personaje and personaje:FindFirstChildOfClass("Humanoid")
		if not raiz or not hum then
			continue
		end

		local multiplicador = 1
		for _, zona in zonas do
			if not zona:IsA("BasePart") then
				continue
			end
			local relativo = zona.CFrame:PointToObjectSpace(raiz.Position)
			local mitad = zona.Size / 2
			if math.abs(relativo.X) <= mitad.X
				and math.abs(relativo.Y) <= mitad.Y
				and math.abs(relativo.Z) <= mitad.Z
			then
				multiplicador = zona:GetAttribute("Multiplicador") or 1
				break
			end
		end

		hum.WalkSpeed = VELOCIDAD_BASE * multiplicador
	end
end)
```

- **Errores frecuentes:**
  - Usar `Touched` y `TouchEnded`: `TouchEnded` no dispara de forma fiable y el
    jugador se queda lento para siempre.
  - Comprobar cada frame para cada jugador: caro. Usa un intervalo.
  - No restaurar la velocidad al salir de la zona.
- **Checklist sin errores:**
  - [ ] La velocidad vuelve a la base fuera de las zonas
  - [ ] La comprobacion es periodica, no por frame
  - [ ] Las zonas tienen `CanCollide` en false y el atributo `Multiplicador`

---

## Siguiente paso

Sigue por `mecanicas/03-combate.md`. Los fallos concretos de este modulo estan
catalogados en `mecanicas/09-errores-y-checklist.md`.
