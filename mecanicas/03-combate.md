# 03 - Combate, dano y habilidades

Modulo 3 del catalogo. Golpes, disparos, hitbox, estados alterados y muerte.

Regla de oro de este modulo, sin excepciones: **el cliente pide, el servidor
decide.** El cliente puede reproducir la animacion y el sonido al instante para
que se sienta bien, pero quien resta vida es siempre el servidor, y siempre
despues de comprobar distancia, enfriamiento y estado.

## Indice

| # | Mecanica | Para que |
|---|---|---|
| 1 | Hitbox por volumen | Detectar a quien alcanza el golpe |
| 2 | Raycast y RaycastParams | Disparos instantaneos |
| 3 | Shapecast | Proyectiles con grosor |
| 4 | Enfriamiento con os.clock | Limitar la cadencia |
| 5 | Aplicar dano correctamente | TakeDamage y no Health |
| 6 | Remote de ataque validado | La frontera de seguridad |
| 7 | Proyectil con prediccion | Se siente instantaneo y es justo |
| 8 | Combos encadenados | Golpes M1 con ventana |
| 9 | Fotogramas de invulnerabilidad | Esquivas que perdonan |
| 10 | Aturdimiento | Bloquear acciones un instante |
| 11 | Empuje al golpear | Peso del impacto |
| 12 | Equipos y fuego amigo | No matar a los tuyos |
| 13 | Criticos y variacion de dano | Que no sea plano |
| 14 | Dano en el tiempo | Veneno y quemadura |
| 15 | Curacion y regeneracion | Recuperar vida |
| 16 | Escudos y armadura | Capa antes de la vida |
| 17 | Hitstop y retroalimentacion | Que el golpe se sienta |
| 18 | Muerte, respawn y killfeed | Cerrar el ciclo |
| 19 | Tool como arma | Equipar y usar |
| 20 | Municion y recarga | Gestion de recursos |
| 21 | Dano en area | Explosiones |
| 22 | Gestor de estados alterados | Un solo sitio para todo |

---

## Estructura recomendada

```text
ReplicatedStorage/
  Remotes/
    PedirAtaque      (RemoteEvent)
    AvisarImpacto    (RemoteEvent)
  Modulos/
    ConfigCombate    (ModuleScript)
    Estados          (ModuleScript)
ServerScriptService/
  Combate/
    ServidorCombate  (Script)
    Validacion       (ModuleScript)
StarterPlayer/StarterPlayerScripts/
  ClienteCombate     (LocalScript)
```

---

### 1. Hitbox por volumen

- **Que es:** preguntar al motor que partes hay dentro de una caja o esfera.
- **Para que sirve:** golpes cuerpo a cuerpo, ondas expansivas, zonas de dano.
- **API implicada:** `workspace:GetPartBoundsInBox`, `GetPartBoundsInRadius`,
  `GetPartsInPart`, `OverlapParams`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local function buscarObjetivos(atacante: Model, alcance: number, ancho: number)
	local raiz = atacante:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not raiz then
		return {}
	end

	local params = OverlapParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { atacante }
	params.MaxParts = 30

	-- caja delante del atacante
	local centro = raiz.CFrame * CFrame.new(0, 0, -alcance / 2)
	local tamano = Vector3.new(ancho, 6, alcance)

	local partes = workspace:GetPartBoundsInBox(centro, tamano, params)

	local encontrados: { Humanoid } = {}
	local yaVistos: { [Humanoid]: boolean } = {}

	for _, parte in partes do
		local modelo = parte:FindFirstAncestorOfClass("Model")
		local hum = modelo and modelo:FindFirstChildOfClass("Humanoid")
		if hum and hum.Health > 0 and not yaVistos[hum] then
			yaVistos[hum] = true
			table.insert(encontrados, hum)
		end
	end

	return encontrados
end

return buscarObjetivos
```

- **Errores frecuentes:**
  - No deduplicar: un personaje tiene 15 partes y recibe 15 golpes de una vez.
    La tabla `yaVistos` lo evita.
  - Usar `Region3`: obsoleto, mas lento y siempre alineado a los ejes del mundo.
  - Usar `Touched` como hitbox: falla a alta velocidad y dispara mil veces.
  - No excluir al atacante: se golpea a si mismo.
- **Checklist sin errores:**
  - [ ] Cada Humanoid se cuenta una sola vez
  - [ ] El atacante esta excluido
  - [ ] Se ignoran los muertos (`Health > 0`)
  - [ ] `MaxParts` puesto para no recorrer medio mapa

---

### 2. Raycast y RaycastParams

- **Que es:** lanzar una linea y ver que golpea primero.
- **Para que sirve:** disparos instantaneos, linea de vision, deteccion de
  suelo y paredes.
- **API implicada:** `workspace:Raycast`, `RaycastParams`,
  `FilterDescendantsInstances`, `Enum.RaycastFilterType`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local function disparar(origen: Vector3, direccion: Vector3, alcance: number, ignorar: { Instance })
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignorar
	params.IgnoreWater = true
	params.RespectCanCollide = true

	local resultado = workspace:Raycast(origen, direccion.Unit * alcance, params)
	if not resultado then
		return nil
	end

	local modelo = resultado.Instance:FindFirstAncestorOfClass("Model")
	local hum = modelo and modelo:FindFirstChildOfClass("Humanoid")

	return {
		posicion = resultado.Position,
		normal = resultado.Normal,
		instancia = resultado.Instance,
		humanoid = hum,
		esCabeza = resultado.Instance.Name == "Head",
	}
end

return disparar
```

- **Errores frecuentes:**
  - Pasar la direccion sin normalizar: el alcance real no es el que crees. El
    segundo argumento de `Raycast` es un vector cuya longitud ES la distancia.
  - Olvidar excluir al tirador: se dispara al pecho.
  - No excluir efectos y balas: el rayo choca contra una chispa.
  - `FilterType.Blacklist` esta renombrado a `Exclude`.
- **Checklist sin errores:**
  - [ ] La direccion va normalizada y multiplicada por el alcance
  - [ ] El tirador y los efectos estan excluidos
  - [ ] Se usa `Exclude` / `Include`, no los nombres antiguos

---

### 3. Shapecast

- **Que es:** un raycast con volumen: mueve una caja o una esfera por el espacio.
- **Para que sirve:** proyectiles gruesos, espadas anchas, comprobar si cabe un
  personaje.
- **API implicada:** `workspace:Blockcast`, `workspace:Spherecast`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local function balaGruesa(origen: CFrame, distancia: number, radio: number, ignorar: { Instance })
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignorar

	-- esfera de radio dado recorriendo la direccion indicada
	local resultado = workspace:Spherecast(
		origen.Position,
		radio,
		origen.LookVector * distancia,
		params
	)

	return resultado
end
```

- **Errores frecuentes:**
  - Radios grandes con muchos objetos: cuesta mas que un raycast normal. No lo
    uses cada frame para todo.
  - Esperar que detecte objetos que ya estan solapados en el origen: el
    shapecast empieza a comprobar desde el origen hacia adelante.
  - Confundir el segundo argumento de `Blockcast` (es un `Vector3` de tamano,
    no un `CFrame`).
- **Checklist sin errores:**
  - [ ] El radio es razonable (menos de 3 studs en la mayoria de casos)
  - [ ] Solo se usa donde un raycast fino falla
  - [ ] Los filtros son los mismos que en el raycast normal

---

### 4. Enfriamiento con os.clock

- **Que es:** limitar cada cuanto puede repetirse una accion.
- **Para que sirve:** cadencia de disparo, habilidades, evitar spam de remotes.
- **API implicada:** `os.clock()`.
- **Donde va:** Script en `ServerScriptService`. Se puede duplicar en el cliente
  solo para la interfaz.
- **Codigo listo para pegar:**

```lua
-- ModuleScript: Enfriamientos
local Enfriamientos = {}
local registro: { [any]: { [string]: number } } = {}

function Enfriamientos.listo(clave: any, accion: string, segundos: number): boolean
	local ahora = os.clock()
	registro[clave] = registro[clave] or {}

	local ultimo = registro[clave][accion]
	if ultimo and ahora - ultimo < segundos then
		return false
	end

	registro[clave][accion] = ahora
	return true
end

function Enfriamientos.restante(clave: any, accion: string, segundos: number): number
	local ultimo = registro[clave] and registro[clave][accion]
	if not ultimo then
		return 0
	end
	return math.max(0, segundos - (os.clock() - ultimo))
end

function Enfriamientos.limpiar(clave: any)
	registro[clave] = nil
end

game:GetService("Players").PlayerRemoving:Connect(function(jugador)
	Enfriamientos.limpiar(jugador)
end)

return Enfriamientos
```

- **Errores frecuentes:**
  - Usar `tick()`: depende de la zona horaria del servidor y puede saltar.
  - Usar `os.time()`: solo tiene resolucion de un segundo, inservible para
    cadencias.
  - Guardar el enfriamiento solo en el cliente: cualquiera lo desactiva.
  - No limpiar la tabla al salir el jugador: fuga de memoria.
- **Checklist sin errores:**
  - [ ] Se usa `os.clock()`
  - [ ] El enfriamiento autoritativo esta en el servidor
  - [ ] La tabla se limpia en `PlayerRemoving`

---

### 5. Aplicar dano correctamente

- **Que es:** la forma correcta de restar vida.
- **Para que sirve:** que ForceField, escudos y equipos funcionen.
- **API implicada:** `Humanoid:TakeDamage`, `Humanoid.Health`,
  `Humanoid.MaxHealth`, `ForceField`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local function aplicarDano(objetivo: Humanoid, cantidad: number, atacante: Player?)
	if objetivo.Health <= 0 then
		return 0
	end

	local modelo = objetivo.Parent
	if modelo and modelo:FindFirstChildOfClass("ForceField") then
		return 0 -- protegido al aparecer
	end

	local antes = objetivo.Health
	objetivo:TakeDamage(cantidad)
	local real = antes - objetivo.Health

	if atacante then
		objetivo:SetAttribute("UltimoAtacanteId", atacante.UserId)
		objetivo:SetAttribute("UltimoGolpe", os.clock())
	end

	return real
end

return aplicarDano
```

- **Errores frecuentes:**
  - `humanoid.Health -= 10`: ignora ForceField y no dispara los eventos que
    espera el motor.
  - No comprobar si ya esta muerto: se cuentan muertes dobles en el killfeed.
  - Aplicar dano desde el cliente: no se replica y el jugador se cura solo.
  - No guardar quien golpeo: luego no se sabe a quien dar el punto.
- **Checklist sin errores:**
  - [ ] Se usa `TakeDamage`, nunca `Health -=`
  - [ ] Se ignora a los que ya estan a 0
  - [ ] Se registra el ultimo atacante
  - [ ] Corre en el servidor

---

### 6. Remote de ataque validado

- **Que es:** el patron completo de peticion de ataque, con todas las
  comprobaciones.
- **Para que sirve:** es la plantilla de seguridad de todo el modulo. Copiala.
- **API implicada:** `RemoteEvent.OnServerEvent`, validacion de tipos, distancia,
  enfriamiento y estado.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local remotes = ReplicatedStorage:WaitForChild("Remotes")
local pedirAtaque = remotes:WaitForChild("PedirAtaque") :: RemoteEvent

local Enfriamientos = require(ReplicatedStorage.Modulos.Enfriamientos)

local ALCANCE_MAXIMO = 14
local DANO = 22
local CADENCIA = 0.55

pedirAtaque.OnServerEvent:Connect(function(jugador, objetivoModelo)
	-- 1. tipo de argumento
	if typeof(objetivoModelo) ~= "Instance" or not objetivoModelo:IsA("Model") then
		return
	end

	-- 2. cadencia
	if not Enfriamientos.listo(jugador, "AtaqueBasico", CADENCIA) then
		return
	end

	-- 3. el atacante existe y esta vivo
	local personaje = jugador.Character
	local raizAtacante = personaje and personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
	local humAtacante = personaje and personaje:FindFirstChildOfClass("Humanoid")
	if not raizAtacante or not humAtacante or humAtacante.Health <= 0 then
		return
	end

	-- 4. el objetivo existe y esta vivo
	local humObjetivo = objetivoModelo:FindFirstChildOfClass("Humanoid")
	local raizObjetivo = objetivoModelo:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not humObjetivo or not raizObjetivo or humObjetivo.Health <= 0 then
		return
	end

	-- 5. no atacarse a si mismo
	if objetivoModelo == personaje then
		return
	end

	-- 6. distancia real, con margen por latencia
	local distancia = (raizAtacante.Position - raizObjetivo.Position).Magnitude
	if distancia > ALCANCE_MAXIMO then
		return
	end

	-- 7. equipos
	local victima = Players:GetPlayerFromCharacter(objetivoModelo)
	if victima and victima.Team and victima.Team == jugador.Team then
		return
	end

	-- todo correcto
	humObjetivo:TakeDamage(DANO)
end)
```

- **Errores frecuentes:**
  - Confiar en un dano enviado por el cliente. El cliente manda a QUIEN golpea,
    nunca CUANTO.
  - No comprobar el tipo del argumento: un cliente modificado envia una tabla y
    tumba el script.
  - Poner el alcance exacto sin margen: con 150 ms de latencia el golpe legitimo
    se rechaza. Anade un 20 por ciento.
  - Olvidar el `return` en cada comprobacion.
- **Checklist sin errores:**
  - [ ] Se valida el tipo de cada argumento
  - [ ] Se valida cadencia, vida, distancia y equipo
  - [ ] El dano es una constante del servidor
  - [ ] Probado enviando basura desde la consola del cliente

---

### 7. Proyectil con prediccion

- **Que es:** el cliente dibuja la bala al instante y el servidor decide el
  impacto.
- **Para que sirve:** que disparar se sienta inmediato aunque haya latencia.
- **API implicada:** RemoteEvent en dos sentidos, `Raycast`, `TweenService`.
- **Donde va:** LocalScript para el visual, Script para la verdad.
- **Codigo listo para pegar:**

```lua
-- LocalScript: efecto inmediato, sin autoridad
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Debris = game:GetService("Debris")
local remotes = ReplicatedStorage:WaitForChild("Remotes")
local pedirDisparo = remotes:WaitForChild("PedirDisparo") :: RemoteEvent

local function dibujarTrazo(desde: Vector3, hasta: Vector3)
	local trazo = Instance.new("Part")
	trazo.Anchored = true
	trazo.CanCollide = false
	trazo.CanQuery = false
	trazo.CanTouch = false
	trazo.Material = Enum.Material.Neon
	trazo.Color = Color3.fromRGB(255, 230, 120)
	local distancia = (hasta - desde).Magnitude
	trazo.Size = Vector3.new(0.12, 0.12, distancia)
	trazo.CFrame = CFrame.lookAt(desde, hasta) * CFrame.new(0, 0, -distancia / 2)
	trazo.Parent = workspace
	Debris:AddItem(trazo, 0.08)
end

local function disparar(origen: Vector3, direccion: Vector3)
	dibujarTrazo(origen, origen + direccion.Unit * 300)
	pedirDisparo:FireServer(origen, direccion.Unit) -- el servidor comprueba
end

return disparar
```

```lua
-- Script: la verdad la dice el servidor
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local remotes = ReplicatedStorage:WaitForChild("Remotes")
local pedirDisparo = remotes:WaitForChild("PedirDisparo") :: RemoteEvent
local Enfriamientos = require(ReplicatedStorage.Modulos.Enfriamientos)

local ALCANCE = 300
local DANO_CUERPO = 25
local DANO_CABEZA = 60
local CADENCIA = 0.12
local MARGEN_ORIGEN = 12 -- studs de tolerancia respecto al personaje

pedirDisparo.OnServerEvent:Connect(function(jugador, origen, direccion)
	if typeof(origen) ~= "Vector3" or typeof(direccion) ~= "Vector3" then
		return
	end
	if direccion.Magnitude < 0.9 or direccion.Magnitude > 1.1 then
		return -- debe venir normalizada
	end
	if not Enfriamientos.listo(jugador, "Disparo", CADENCIA) then
		return
	end

	local personaje = jugador.Character
	local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = personaje and personaje:FindFirstChildOfClass("Humanoid")
	if not raiz or not hum or hum.Health <= 0 then
		return
	end

	-- el origen declarado no puede estar lejos del jugador real
	if (origen - raiz.Position).Magnitude > MARGEN_ORIGEN then
		return
	end

	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { personaje }

	local golpe = workspace:Raycast(origen, direccion * ALCANCE, params)
	if not golpe then
		return
	end

	local modelo = golpe.Instance:FindFirstAncestorOfClass("Model")
	local humObjetivo = modelo and modelo:FindFirstChildOfClass("Humanoid")
	if not humObjetivo or humObjetivo.Health <= 0 then
		return
	end

	local victima = Players:GetPlayerFromCharacter(modelo)
	if victima and victima.Team and victima.Team == jugador.Team then
		return
	end

	local dano = golpe.Instance.Name == "Head" and DANO_CABEZA or DANO_CUERPO
	humObjetivo:TakeDamage(dano)
end)
```

- **Errores frecuentes:**
  - Aceptar el origen del cliente sin comparar con la posicion real: permite
    disparar desde el otro lado del mapa.
  - No comprobar que la direccion viene normalizada: un vector gigante alarga
    el alcance.
  - Repetir el raycast en el cliente y aplicar dano ahi tambien: doble dano.
- **Checklist sin errores:**
  - [ ] El origen se compara con la posicion real del jugador
  - [ ] La direccion se valida como unitaria
  - [ ] Solo el servidor aplica dano
  - [ ] Hay cadencia en el servidor

---

### 8. Combos encadenados

- **Que es:** golpes que se suceden si pulsas dentro de una ventana de tiempo.
- **Para que sirve:** combate cuerpo a cuerpo con ritmo.
- **API implicada:** contador por jugador, `os.clock()`, prioridades de
  animacion.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")

local COMBO = {
	{ dano = 14, cadencia = 0.35, empuje = 12 },
	{ dano = 16, cadencia = 0.35, empuje = 14 },
	{ dano = 28, cadencia = 0.70, empuje = 40 }, -- final
}
local VENTANA = 0.9 -- si tardas mas, el combo se reinicia

local estado: { [Player]: { paso: number, ultimo: number } } = {}

local function siguientePaso(jugador: Player)
	local ahora = os.clock()
	local actual = estado[jugador]

	if not actual or ahora - actual.ultimo > VENTANA then
		actual = { paso = 0, ultimo = 0 }
		estado[jugador] = actual
	end

	local siguiente = actual.paso + 1
	local datos = COMBO[siguiente]
	if not datos then
		siguiente = 1
		datos = COMBO[1]
	end

	if ahora - actual.ultimo < datos.cadencia then
		return nil -- demasiado rapido
	end

	actual.paso = siguiente
	actual.ultimo = ahora
	return datos, siguiente
end

Players.PlayerRemoving:Connect(function(jugador)
	estado[jugador] = nil
end)

return siguientePaso
```

- **Errores frecuentes:**
  - No reiniciar el combo tras la ventana: el jugador vuelve una hora despues y
    sigue en el golpe 3.
  - Guardar el paso en el cliente: se puede forzar siempre el golpe final.
  - No limpiar la tabla al salir el jugador.
- **Checklist sin errores:**
  - [ ] El combo se reinicia pasada la ventana
  - [ ] El estado vive en el servidor
  - [ ] Cada paso tiene su propia cadencia

---

### 9. Fotogramas de invulnerabilidad

- **Que es:** un periodo corto sin recibir dano tras esquivar o ser golpeado.
- **Para que sirve:** que un solo error no encadene diez golpes.
- **API implicada:** Attributes, `os.clock()`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local function darInvulnerabilidad(humanoid: Humanoid, segundos: number)
	humanoid:SetAttribute("InvulnerableHasta", os.clock() + segundos)
end

local function esInvulnerable(humanoid: Humanoid): boolean
	local hasta = humanoid:GetAttribute("InvulnerableHasta")
	return typeof(hasta) == "number" and os.clock() < hasta
end

-- Uso dentro del aplicador de dano
local function aplicarDanoSeguro(humanoid: Humanoid, cantidad: number)
	if humanoid.Health <= 0 or esInvulnerable(humanoid) then
		return 0
	end
	humanoid:TakeDamage(cantidad)
	darInvulnerabilidad(humanoid, 0.25) -- respiro tras cada golpe
	return cantidad
end

return { dar = darInvulnerabilidad, es = esInvulnerable, danar = aplicarDanoSeguro }
```

- **Errores frecuentes:**
  - Invulnerabilidad demasiado larga: el combate se rompe.
  - Usar un booleano en vez de una marca de tiempo: si dos efectos la activan,
    el primero en terminar la quita.
  - Comprobarla solo en un sitio y aplicar dano desde otro.
- **Checklist sin errores:**
  - [ ] Se guarda un instante de fin, no un booleano
  - [ ] Todo el dano pasa por la misma funcion
  - [ ] La duracion esta ajustada al ritmo del juego

---

### 10. Aturdimiento

- **Que es:** bloquear el movimiento y las acciones durante un instante.
- **Para que sirve:** que los golpes fuertes tengan consecuencia.
- **API implicada:** `Humanoid.WalkSpeed`, `JumpHeight`, Attributes.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local aturdidos: { [Humanoid]: number } = {}

local function aturdir(humanoid: Humanoid, segundos: number)
	if humanoid.Health <= 0 then
		return
	end

	local token = (aturdidos[humanoid] or 0) + 1
	aturdidos[humanoid] = token

	if token == 1 then
		humanoid:SetAttribute("VelocidadPrevia", humanoid.WalkSpeed)
		humanoid:SetAttribute("SaltoPrevio", humanoid.JumpHeight)
	end

	humanoid:SetAttribute("Aturdido", true)
	humanoid.WalkSpeed = 0
	humanoid.JumpHeight = 0

	task.delay(segundos, function()
		if aturdidos[humanoid] ~= token then
			return -- llego otro aturdimiento despues, que lo gestione el
		end
		aturdidos[humanoid] = nil

		if humanoid.Parent and humanoid.Health > 0 then
			humanoid.WalkSpeed = humanoid:GetAttribute("VelocidadPrevia") or 16
			humanoid.JumpHeight = humanoid:GetAttribute("SaltoPrevio") or 7.2
		end
		humanoid:SetAttribute("Aturdido", false)
	end)
end

return aturdir
```

- **Errores frecuentes:**
  - Dos aturdimientos solapados: el primero en acabar devuelve la velocidad y el
    jugador se mueve estando aturdido. El token del ejemplo lo resuelve.
  - Guardar la velocidad previa cuando ya vale 0: el jugador queda paralizado
    para siempre.
  - No restaurar si el jugador muere y revive.
- **Checklist sin errores:**
  - [ ] Los aturdimientos solapados se gestionan con token
  - [ ] La velocidad previa se guarda solo la primera vez
  - [ ] Se comprueba que el Humanoid siga vivo al restaurar

---

### 11. Empuje al golpear

- **Que es:** desplazar al objetivo en la direccion del golpe.
- **Para que sirve:** peso, control de espacio, empujar al vacio.
- **API implicada:** `BasePart.AssemblyLinearVelocity`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local function empujarDesde(objetivo: Model, origen: Vector3, fuerza: number)
	local raiz = objetivo:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not raiz then
		return
	end

	local direccion = raiz.Position - origen
	direccion = Vector3.new(direccion.X, 0, direccion.Z)
	if direccion.Magnitude < 0.01 then
		direccion = Vector3.new(0, 0, 1)
	end

	raiz.AssemblyLinearVelocity = direccion.Unit * fuerza + Vector3.new(0, fuerza * 0.35, 0)
end

return empujarDesde
```

- **Errores frecuentes:**
  - No anular la componente Y del vector direccion: si el atacante esta arriba,
    el empuje clava al objetivo contra el suelo.
  - Sumar velocidad en vez de reemplazarla.
  - Empujar a alguien con la propiedad de red en su cliente sin margen: se ve
    a saltos.
- **Checklist sin errores:**
  - [ ] La direccion se aplana en el plano XZ
  - [ ] Se anade una componente vertical pequena
  - [ ] La velocidad se reemplaza

---

### 12. Equipos y fuego amigo

- **Que es:** agrupar jugadores y decidir quien puede danar a quien.
- **Para que sirve:** modos por equipos, NPC aliados.
- **API implicada:** `Teams`, `Player.Team`, `Player.TeamColor`,
  `Player.Neutral`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local Teams = game:GetService("Teams")
local Players = game:GetService("Players")

local FUEGO_AMIGO = false

local function crearEquipo(nombre: string, color: BrickColor): Team
	local existente = Teams:FindFirstChild(nombre)
	if existente and existente:IsA("Team") then
		return existente
	end

	local equipo = Instance.new("Team")
	equipo.Name = nombre
	equipo.TeamColor = color
	equipo.AutoAssignable = false
	equipo.Parent = Teams
	return equipo
end

local repartidores = crearEquipo("Repartidores", BrickColor.new("Bright blue"))
local saboteadores = crearEquipo("Saboteadores", BrickColor.new("Bright red"))

local function puedeDanar(atacante: Model, objetivo: Model): boolean
	if atacante == objetivo then
		return false
	end

	local a = Players:GetPlayerFromCharacter(atacante)
	local b = Players:GetPlayerFromCharacter(objetivo)

	if not a or not b then
		return true -- al menos uno es NPC
	end
	if FUEGO_AMIGO then
		return true
	end
	if a.Team and b.Team and a.Team == b.Team then
		return false
	end

	return true
end

return { puedeDanar = puedeDanar, repartidores = repartidores, saboteadores = saboteadores }
```

- **Errores frecuentes:**
  - Comparar `TeamColor` en vez de `Team`: dos equipos pueden compartir color.
  - Olvidar el caso de los NPC, que no tienen `Player`.
  - Dejar `AutoAssignable` en true en equipos de partida: los jugadores entran
    solos al equipo equivocado.
- **Checklist sin errores:**
  - [ ] Se compara `Team`, no `TeamColor`
  - [ ] Los NPC estan contemplados
  - [ ] La comprobacion esta en un solo modulo reutilizado

---

### 13. Criticos y variacion de dano

- **Que es:** que el dano no sea siempre el mismo numero.
- **Para que sirve:** que el combate no se sienta mecanico.
- **API implicada:** `Random.new()`, `math.random`.
- **Donde va:** ModuleScript usado desde el servidor.
- **Codigo listo para pegar:**

```lua
local generador = Random.new()

local function calcularDano(base: number, probabilidadCritico: number, multiplicador: number)
	-- variacion de +/-10 por ciento
	local variacion = generador:NextNumber(0.9, 1.1)
	local total = base * variacion
	local esCritico = generador:NextNumber() < probabilidadCritico

	if esCritico then
		total *= multiplicador
	end

	return math.floor(total + 0.5), esCritico
end

-- Uso: calcularDano(25, 0.15, 2) -> critico del 15 por ciento que dobla
return calcularDano
```

- **Errores frecuentes:**
  - Calcular el critico en el cliente: siempre saldria critico.
  - Usar `math.randomseed(os.time())` en cada llamada: patrones repetidos.
  - Variacion demasiado alta: el jugador no entiende cuantos golpes hacen falta.
- **Checklist sin errores:**
  - [ ] El calculo esta en el servidor
  - [ ] Se usa un unico objeto `Random`
  - [ ] La variacion es discreta (10 a 15 por ciento)

---

### 14. Dano en el tiempo

- **Que es:** dano repetido durante unos segundos.
- **Para que sirve:** veneno, quemadura, sangrado.
- **API implicada:** `task.spawn`, `task.wait`, Attributes.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local activos: { [Humanoid]: { [string]: boolean } } = {}

local function aplicarDoT(humanoid: Humanoid, nombre: string, danoPorTick: number, ticks: number, intervalo: number)
	activos[humanoid] = activos[humanoid] or {}
	if activos[humanoid][nombre] then
		return -- ya lo tiene, no acumular
	end
	activos[humanoid][nombre] = true

	task.spawn(function()
		for _ = 1, ticks do
			task.wait(intervalo)

			if not humanoid.Parent or humanoid.Health <= 0 then
				break
			end

			humanoid:TakeDamage(danoPorTick)
		end

		if activos[humanoid] then
			activos[humanoid][nombre] = nil
		end
	end)
end

-- Uso: aplicarDoT(hum, "Veneno", 4, 5, 1) -> 4 de dano cada segundo, 5 veces
return aplicarDoT
```

- **Errores frecuentes:**
  - Permitir apilar el mismo efecto infinitas veces: diez venenos matan al
    instante. Decide si se apila o se refresca.
  - No comprobar `humanoid.Parent` dentro del bucle: sigue danando a un
    personaje ya destruido y lanza errores.
  - Usar `while true` sin salida.
- **Checklist sin errores:**
  - [ ] El efecto no se apila sin control
  - [ ] El bucle se rompe si el objetivo muere o desaparece
  - [ ] El registro se limpia al terminar

---

### 15. Curacion y regeneracion

- **Que es:** devolver vida, de golpe o poco a poco.
- **Para que sirve:** botiquines, zonas seguras, regeneracion pasiva.
- **API implicada:** `Humanoid.Health`, `MaxHealth`, `math.min`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local RETRASO_TRAS_GOLPE = 6 -- segundos sin recibir dano antes de regenerar
local VIDA_POR_SEGUNDO = 4

local function curar(humanoid: Humanoid, cantidad: number)
	if humanoid.Health <= 0 then
		return 0
	end
	local antes = humanoid.Health
	humanoid.Health = math.min(humanoid.Health + cantidad, humanoid.MaxHealth)
	return humanoid.Health - antes
end

local acumulado = 0
RunService.Heartbeat:Connect(function(dt)
	acumulado += dt
	if acumulado < 0.5 then
		return
	end
	local paso = acumulado
	acumulado = 0

	for _, jugador in Players:GetPlayers() do
		local personaje = jugador.Character
		local hum = personaje and personaje:FindFirstChildOfClass("Humanoid")
		if not hum or hum.Health <= 0 or hum.Health >= hum.MaxHealth then
			continue
		end

		local ultimoGolpe = hum:GetAttribute("UltimoGolpe")
		if typeof(ultimoGolpe) == "number" and os.clock() - ultimoGolpe < RETRASO_TRAS_GOLPE then
			continue
		end

		curar(hum, VIDA_POR_SEGUNDO * paso)
	end
end)

return curar
```

- **Errores frecuentes:**
  - Curar por encima de `MaxHealth`: la barra se desborda. Usa `math.min`.
  - Regenerar durante el combate: las peleas no terminan nunca.
  - Dejar activa la regeneracion nativa de Roblox junto con la tuya. Si quieres
    la tuya, borra el script `Health` que Roblox inserta en el personaje.
- **Checklist sin errores:**
  - [ ] La vida nunca pasa de `MaxHealth`
  - [ ] Hay retraso tras recibir dano
  - [ ] No conviven dos sistemas de regeneracion

---

### 16. Escudos y armadura

- **Que es:** una capa que absorbe dano antes de tocar la vida.
- **Para que sirve:** objetos defensivos, jefes, clases con aguante.
- **API implicada:** Attributes, funcion unica de dano.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local function danoConEscudo(humanoid: Humanoid, cantidad: number)
	if humanoid.Health <= 0 then
		return 0
	end

	-- reduccion porcentual de la armadura (0 a 0.75)
	local armadura = math.clamp(humanoid:GetAttribute("Armadura") or 0, 0, 0.75)
	local restante = cantidad * (1 - armadura)

	-- escudo absorbe primero
	local escudo = humanoid:GetAttribute("Escudo") or 0
	if escudo > 0 then
		local absorbido = math.min(escudo, restante)
		humanoid:SetAttribute("Escudo", escudo - absorbido)
		restante -= absorbido
	end

	if restante > 0 then
		humanoid:TakeDamage(restante)
	end

	return cantidad - restante
end

return danoConEscudo
```

- **Errores frecuentes:**
  - Armadura del 100 por ciento: invulnerabilidad accidental. Ponle tope.
  - Escudo negativo por no comprobar el minimo.
  - Tener dos rutas de dano y que una se salte el escudo.
- **Checklist sin errores:**
  - [ ] La armadura esta acotada con `math.clamp`
  - [ ] El escudo nunca baja de cero
  - [ ] Todo el dano del juego pasa por esta funcion

---

### 17. Hitstop y retroalimentacion

- **Que es:** congelar un instante la animacion al impactar, con sonido y
  particulas.
- **Para que sirve:** que el golpe se sienta contundente. Es lo que separa un
  combate soso de uno bueno.
- **API implicada:** `AnimationTrack:AdjustSpeed`, `Sound`, `ParticleEmitter`,
  sacudida de camara.
- **Donde va:** LocalScript (efecto) avisado por RemoteEvent desde el servidor.
- **Codigo listo para pegar:**

```lua
-- LocalScript: reacciona al aviso del servidor
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Debris = game:GetService("Debris")
local remotes = ReplicatedStorage:WaitForChild("Remotes")
local avisarImpacto = remotes:WaitForChild("AvisarImpacto") :: RemoteEvent
local Sacudida = require(ReplicatedStorage.Modulos.SacudidaCamara)

local function hitstop(track: AnimationTrack?, duracion: number)
	if not track or not track.IsPlaying then
		return
	end
	local velocidadPrevia = track.Speed
	track:AdjustSpeed(0.05)
	task.delay(duracion, function()
		if track.IsPlaying then
			track:AdjustSpeed(velocidadPrevia)
		end
	end)
end

avisarImpacto.OnClientEvent:Connect(function(posicion: Vector3, esCritico: boolean)
	Sacudida.aplicar(esCritico and 0.6 or 0.28, 0.18)

	local sonido = Instance.new("Sound")
	sonido.SoundId = "rbxassetid://9118823101"
	sonido.Volume = esCritico and 1 or 0.6
	sonido.RollOffMaxDistance = 80

	local ancla = Instance.new("Part")
	ancla.Anchored = true
	ancla.CanCollide = false
	ancla.CanQuery = false
	ancla.CanTouch = false
	ancla.Transparency = 1
	ancla.Size = Vector3.one
	ancla.Position = posicion
	ancla.Parent = workspace

	sonido.Parent = ancla
	sonido:Play()
	Debris:AddItem(ancla, 2)
end)

return hitstop
```

- **Errores frecuentes:**
  - Hitstop demasiado largo: parece que el juego se cuelga. Entre 0.05 y 0.12
    segundos basta.
  - Crear el sonido en el servidor: se oye en todo el mapa y se replica mal.
  - No limpiar la parte ancla: se acumulan miles.
- **Checklist sin errores:**
  - [ ] El hitstop dura menos de 0.15 segundos
  - [ ] La velocidad de la animacion se restaura
  - [ ] Los efectos se destruyen con Debris

---

### 18. Muerte, respawn y killfeed

- **Que es:** cerrar el ciclo de combate y anunciarlo.
- **Para que sirve:** puntuacion, feedback, reinicio limpio.
- **API implicada:** `Humanoid.Died`, `Player:LoadCharacter`,
  `Players.RespawnTime`, RemoteEvent.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local remotes = ReplicatedStorage:WaitForChild("Remotes")
local anunciarMuerte = remotes:WaitForChild("AnunciarMuerte") :: RemoteEvent

local TIEMPO_RESPAWN = 4
local VENTANA_CREDITO = 10 -- segundos para atribuir la muerte

Players.CharacterAutoLoads = false

local function gestionarMuerte(jugador: Player, humanoid: Humanoid)
	local idAtacante = humanoid:GetAttribute("UltimoAtacanteId")
	local instante = humanoid:GetAttribute("UltimoGolpe")

	local asesino: Player? = nil
	if typeof(idAtacante) == "number"
		and typeof(instante) == "number"
		and os.clock() - instante <= VENTANA_CREDITO
	then
		asesino = Players:GetPlayerByUserId(idAtacante)
	end

	anunciarMuerte:FireAllClients(asesino and asesino.Name or nil, jugador.Name)

	if asesino and asesino ~= jugador then
		local stats = asesino:FindFirstChild("leaderstats")
		local bajas = stats and stats:FindFirstChild("Bajas")
		if bajas and bajas:IsA("IntValue") then
			bajas.Value += 1
		end
	end

	task.delay(TIEMPO_RESPAWN, function()
		if jugador.Parent then
			jugador:LoadCharacter()
		end
	end)
end

Players.PlayerAdded:Connect(function(jugador)
	jugador.CharacterAdded:Connect(function(personaje)
		local hum = personaje:WaitForChild("Humanoid", 10) :: Humanoid?
		if not hum then
			return
		end

		local yaMuerto = false
		hum.Died:Connect(function()
			if yaMuerto then
				return
			end
			yaMuerto = true
			gestionarMuerte(jugador, hum)
		end)
	end)

	jugador:LoadCharacter()
end)
```

- **Errores frecuentes:**
  - `Died` puede dispararse mas de una vez. La bandera `yaMuerto` lo corta.
  - Llamar a `LoadCharacter` sin comprobar que el jugador sigue conectado:
    error al salir justo al morir.
  - Atribuir la muerte a alguien que golpeo hace cinco minutos. Por eso la
    ventana de credito.
- **Checklist sin errores:**
  - [ ] `Died` esta protegido contra doble disparo
  - [ ] Se comprueba `jugador.Parent` antes del respawn
  - [ ] La atribucion tiene ventana de tiempo

---

### 19. Tool como arma

- **Que es:** el objeto equipable nativo de Roblox.
- **Para que sirve:** armas, herramientas de reparto, objetos usables.
- **API implicada:** `Tool.Equipped`, `Unequipped`, `Activated`,
  `Tool.RequiresHandle`, `Handle`.
- **Donde va:** Script dentro del Tool.
- **Codigo listo para pegar:**

```lua
-- Script dentro del Tool
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Enfriamientos = require(ReplicatedStorage.Modulos.Enfriamientos)

local herramienta = script.Parent :: Tool
local CADENCIA = 0.5
local DANO = 20
local ALCANCE = 12

herramienta.RequiresHandle = true

local function propietario(): (Player?, Model?)
	local personaje = herramienta.Parent
	if not personaje or not personaje:IsA("Model") then
		return nil, nil
	end
	return Players:GetPlayerFromCharacter(personaje), personaje
end

herramienta.Activated:Connect(function()
	local jugador, personaje = propietario()
	if not jugador or not personaje then
		return
	end
	if not Enfriamientos.listo(jugador, "Tool_" .. herramienta.Name, CADENCIA) then
		return
	end

	local raiz = personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not raiz then
		return
	end

	local params = OverlapParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { personaje }

	local centro = raiz.CFrame * CFrame.new(0, 0, -ALCANCE / 2)
	local golpeados: { [Humanoid]: boolean } = {}

	for _, parte in workspace:GetPartBoundsInBox(centro, Vector3.new(6, 6, ALCANCE), params) do
		local modelo = parte:FindFirstAncestorOfClass("Model")
		local hum = modelo and modelo:FindFirstChildOfClass("Humanoid")
		if hum and hum.Health > 0 and not golpeados[hum] then
			golpeados[hum] = true
			hum:TakeDamage(DANO)
		end
	end
end)

herramienta.Unequipped:Connect(function()
	-- detener animaciones o efectos aqui
end)
```

- **Errores frecuentes:**
  - Tool sin una parte llamada `Handle` y con `RequiresHandle` en true: no se
    puede equipar y no avisa claramente.
  - Poner el Script como LocalScript dentro del Tool y esperar que aplique
    dano real.
  - No comprobar el propietario: al soltar el Tool, `Parent` es Workspace.
- **Checklist sin errores:**
  - [ ] Existe la parte `Handle`
  - [ ] El dano lo aplica un Script de servidor
  - [ ] Se comprueba que el Tool esta equipado por un personaje

---

### 20. Municion y recarga

- **Que es:** limitar los disparos y obligar a recargar.
- **Para que sirve:** ritmo, decisiones, tension.
- **API implicada:** Attributes sobre el Tool, `task.delay`.
- **Donde va:** Script dentro del Tool.
- **Codigo listo para pegar:**

```lua
local herramienta = script.Parent :: Tool

local CARGADOR = 12
local RESERVA_MAX = 60
local TIEMPO_RECARGA = 1.8

herramienta:SetAttribute("Municion", CARGADOR)
herramienta:SetAttribute("Reserva", RESERVA_MAX)
herramienta:SetAttribute("Recargando", false)

local function recargar()
	if herramienta:GetAttribute("Recargando") then
		return
	end

	local municion = herramienta:GetAttribute("Municion") or 0
	local reserva = herramienta:GetAttribute("Reserva") or 0
	if municion >= CARGADOR or reserva <= 0 then
		return
	end

	herramienta:SetAttribute("Recargando", true)

	task.delay(TIEMPO_RECARGA, function()
		if not herramienta.Parent then
			return
		end

		local falta = CARGADOR - (herramienta:GetAttribute("Municion") or 0)
		local disponible = herramienta:GetAttribute("Reserva") or 0
		local aCargar = math.min(falta, disponible)

		herramienta:SetAttribute("Municion", (herramienta:GetAttribute("Municion") or 0) + aCargar)
		herramienta:SetAttribute("Reserva", disponible - aCargar)
		herramienta:SetAttribute("Recargando", false)
	end)
end

local function consumirBala(): boolean
	if herramienta:GetAttribute("Recargando") then
		return false
	end
	local municion = herramienta:GetAttribute("Municion") or 0
	if municion <= 0 then
		recargar()
		return false
	end
	herramienta:SetAttribute("Municion", municion - 1)
	return true
end

return { recargar = recargar, consumir = consumirBala }
```

- **Errores frecuentes:**
  - Guardar la municion en el cliente: municion infinita.
  - Permitir recargar dos veces a la vez y duplicar balas. La bandera
    `Recargando` lo evita.
  - No comprobar que el Tool sigue existiendo tras el `task.delay`.
- **Checklist sin errores:**
  - [ ] La municion vive en el servidor como atributo
  - [ ] No se puede recargar dos veces en paralelo
  - [ ] Se comprueba `herramienta.Parent` tras la espera

---

### 21. Dano en area

- **Que es:** dano a todo lo que este dentro de un radio, con caida por
  distancia.
- **Para que sirve:** explosiones, granadas, habilidades de zona.
- **API implicada:** `workspace:GetPartBoundsInRadius`, `workspace:Raycast`
  para comprobar linea de vision.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local function explosion(centro: Vector3, radio: number, danoMaximo: number, ignorar: { Instance })
	local params = OverlapParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignorar

	local rayParams = RaycastParams.new()
	rayParams.FilterType = Enum.RaycastFilterType.Exclude
	rayParams.FilterDescendantsInstances = ignorar

	local alcanzados: { [Humanoid]: boolean } = {}

	for _, parte in workspace:GetPartBoundsInRadius(centro, radio, params) do
		local modelo = parte:FindFirstAncestorOfClass("Model")
		local hum = modelo and modelo:FindFirstChildOfClass("Humanoid")
		local raiz = modelo and modelo:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not hum or not raiz or hum.Health <= 0 or alcanzados[hum] then
			continue
		end
		alcanzados[hum] = true

		-- linea de vision: una pared protege de la explosion
		local direccion = raiz.Position - centro
		local bloqueo = workspace:Raycast(centro, direccion, rayParams)
		if bloqueo and not bloqueo.Instance:IsDescendantOf(modelo) then
			continue
		end

		local distancia = direccion.Magnitude
		local factor = math.clamp(1 - distancia / radio, 0, 1)
		hum:TakeDamage(danoMaximo * factor)
	end
end

return explosion
```

- **Errores frecuentes:**
  - Dano plano en todo el radio: no se siente como una explosion.
  - No comprobar obstaculos: mata a traves de los muros.
  - Usar `Explosion` nativa y aplicar dano tambien a mano: dano doble. Si usas
    `Instance.new("Explosion")`, pon `BlastPressure` y `DestroyJointRadiusPercent`
    a 0 y controla tu el dano.
- **Checklist sin errores:**
  - [ ] El dano decae con la distancia
  - [ ] Se comprueba linea de vision
  - [ ] Cada Humanoid recibe dano una sola vez

---

### 22. Gestor de estados alterados

- **Que es:** un unico modulo que aplica, apila y retira efectos.
- **Para que sirve:** no tener veneno en un script, lentitud en otro y que se
  pisen entre si.
- **API implicada:** Attributes, `task.delay`, tabla de definiciones.
- **Donde va:** ModuleScript en `ServerStorage/Modulos`.
- **Codigo listo para pegar:**

```lua
local Estados = {}

local DEFINICIONES = {
	Lentitud = {
		aplicar = function(hum: Humanoid)
			hum:SetAttribute("VelocidadBase", hum:GetAttribute("VelocidadBase") or hum.WalkSpeed)
			hum.WalkSpeed = (hum:GetAttribute("VelocidadBase") or 16) * 0.5
		end,
		quitar = function(hum: Humanoid)
			hum.WalkSpeed = hum:GetAttribute("VelocidadBase") or 16
		end,
	},
	Debilidad = {
		aplicar = function(hum: Humanoid)
			hum:SetAttribute("MultiplicadorDano", 0.6)
		end,
		quitar = function(hum: Humanoid)
			hum:SetAttribute("MultiplicadorDano", 1)
		end,
	},
}

local tokens: { [Humanoid]: { [string]: number } } = {}

function Estados.aplicar(hum: Humanoid, nombre: string, duracion: number)
	local def = DEFINICIONES[nombre]
	if not def or hum.Health <= 0 then
		return
	end

	tokens[hum] = tokens[hum] or {}
	local token = (tokens[hum][nombre] or 0) + 1
	tokens[hum][nombre] = token

	def.aplicar(hum)
	hum:SetAttribute("Estado_" .. nombre, true)

	task.delay(duracion, function()
		if not tokens[hum] or tokens[hum][nombre] ~= token then
			return -- se refresco, no quitar
		end
		tokens[hum][nombre] = nil

		if hum.Parent then
			def.quitar(hum)
			hum:SetAttribute("Estado_" .. nombre, false)
		end
	end)
end

function Estados.limpiarTodo(hum: Humanoid)
	if not tokens[hum] then
		return
	end
	for nombre in tokens[hum] do
		local def = DEFINICIONES[nombre]
		if def and hum.Parent then
			def.quitar(hum)
			hum:SetAttribute("Estado_" .. nombre, false)
		end
	end
	tokens[hum] = nil
end

return Estados
```

- **Errores frecuentes:**
  - Refrescar un efecto y que el temporizador viejo lo quite antes de tiempo.
    Los tokens lo resuelven.
  - No limpiar los estados al morir: revives lento y debil.
  - Guardar la velocidad base cuando ya esta reducida: cada aplicacion la baja
    otra vez hasta dejarla en cero.
- **Checklist sin errores:**
  - [ ] Los refrescos usan token
  - [ ] `limpiarTodo` se llama en `Died` y en `CharacterAdded`
  - [ ] La velocidad base se guarda una sola vez

---

## Checklist maestro de combate

- [ ] Ningun dano se aplica desde el cliente
- [ ] Todo remote valida tipo, cadencia, vida, distancia y equipo
- [ ] Las hitbox deduplican por Humanoid
- [ ] Se usa `TakeDamage`, nunca `Health -=`
- [ ] Los raycast excluyen al tirador y a los efectos
- [ ] Los enfriamientos usan `os.clock()` y viven en el servidor
- [ ] Los estados alterados pasan por un unico gestor
- [ ] Las tablas por jugador se limpian en `PlayerRemoving`
- [ ] Probado con Test y dos jugadores, no solo con Play Solo
- [ ] Probado enviando argumentos invalidos por los remotes

---

## Siguiente paso

Animacion de los golpes en `mecanicas/04-animacion.md`. Interfaz de vida y
municion en `mecanicas/05-gui.md`. Errores concretos en
`mecanicas/09-errores-y-checklist.md`.
