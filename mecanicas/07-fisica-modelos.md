# 07 - Fisica, CFrame y modelos

Modulo 7 del catalogo. Como colocar, unir, mover y detectar cosas en el mundo 3D
sin que se desarmen, tiemblen o atraviesen paredes.

La idea central del modulo: en Roblox hay **dos formas de mover algo**, y
mezclarlas es la causa de casi todos los problemas raros de fisica.

| Forma | Como | Cuando |
|---|---|---|
| Cinematica | Escribes `CFrame` o `PivotTo` directamente | Puertas, plataformas, teletransportes, todo lo anclado |
| Dinamica | Usas restricciones y velocidades, el motor decide | Vehiculos, empujones, objetos sueltos, ragdolls |

Si escribes el `CFrame` de una parte no anclada cada frame, estas peleando con
el motor de fisica y perderas: temblores, atravesar paredes y jugadores que ven
cosas distintas.

## Indice

| # | Mecanica | Para que |
|---|---|---|
| 1 | Propiedades de BasePart | La base de todo objeto |
| 2 | CFrame explicado | Posicion y rotacion juntas |
| 3 | PivotTo y GetPivot | Mover modelos enteros |
| 4 | PrimaryPart | Que parte manda |
| 5 | Soldaduras | Que las piezas no se separen |
| 6 | Motor6D y articulaciones | Lo que permite animar |
| 7 | Restricciones de movimiento | Mover con fisica |
| 8 | Grupos de colision | Que atraviese que |
| 9 | Touched con antirrebote | Deteccion simple |
| 10 | Consultas espaciales | Deteccion fiable |
| 11 | Raycast | La linea de vision |
| 12 | Tamano y limites de un modelo | Medir sin adivinar |
| 13 | Escalar un modelo | ScaleTo |
| 14 | Propiedad de red | Quien simula que |
| 15 | Clonar desde almacenamiento | El patron correcto |
| 16 | Debris y limpieza | No dejar basura |
| 17 | Puertas | Cinematica bien hecha |
| 18 | Plataformas moviles | Sin tirar al jugador |
| 19 | Ascensores | Movimiento vertical |
| 20 | Cintas transportadoras | Empuje continuo |
| 21 | Partes destructibles | Romper cosas |
| 22 | Terreno por codigo | Generar el mundo |
| 23 | StreamingEnabled | Mundos grandes |
| 24 | Por que mi modelo se desarma | Diagnostico |

---

### 1. Propiedades de BasePart

- **Que es:** la clase base de `Part`, `MeshPart`, `WedgePart` y demas.
- **Para que sirve:** casi todo el comportamiento fisico se controla desde aqui.

| Propiedad | Que hace | Cuidado |
|---|---|---|
| `Anchored` | La parte no se mueve por fisica | Lo primero que hay que revisar siempre |
| `CanCollide` | Choca con otras partes | Si esta en false, se atraviesa |
| `CanQuery` | Aparece en raycasts y consultas | Ponlo en false en decoracion |
| `CanTouch` | Dispara `Touched` | Ponlo en false si no lo usas, ahorra mucho |
| `Massless` | No aporta masa al conjunto | Util en accesorios soldados |
| `CollisionGroup` | A que grupo pertenece | Ver punto 8 |
| `CustomPhysicalProperties` | Densidad, friccion, rebote | Para hielo, goma, metal |
| `AssemblyLinearVelocity` | Velocidad del conjunto | Solo si no esta anclado |
| `AssemblyAngularVelocity` | Giro del conjunto | Idem |
| `RootPart` | La parte raiz del conjunto | Solo lectura |

- **Codigo listo para pegar:**

```lua
local parte = Instance.new("Part")
parte.Size = Vector3.new(4, 1, 4)
parte.Position = Vector3.new(0, 10, 0)
parte.Anchored = true
parte.CanCollide = true
parte.CanQuery = true
parte.CanTouch = false -- no usamos Touched, ahorramos trabajo
parte.Material = Enum.Material.Metal
parte.Color = Color3.fromRGB(90, 90, 100)
parte.TopSurface = Enum.SurfaceType.Smooth
parte.BottomSurface = Enum.SurfaceType.Smooth
parte.Parent = workspace

-- Hielo: poca friccion
local hielo = Instance.new("Part")
hielo.Anchored = true
hielo.Material = Enum.Material.Ice
hielo.CustomPhysicalProperties = PhysicalProperties.new(
    0.9,  -- densidad
    0.02, -- friccion, muy baja
    0.1,  -- elasticidad
    1,    -- peso de la friccion
    1     -- peso de la elasticidad
)
hielo.Parent = workspace
```

- **Errores frecuentes:**
  - Crear la parte y poner `Parent = workspace` **antes** de configurarla: se
    ve un frame en el sitio equivocado y la fisica la simula antes de tiempo.
    Configura primero, asigna el padre al final.
  - Dejar `CanTouch` en true en cientos de partes decorativas: coste inutil.
  - Confundir `CanCollide = false` con "invisible": la parte sigue viendose.
  - Cambiar `Position` de una parte no anclada esperando que se quede ahi.
- **Checklist sin errores:**
  - [ ] El padre se asigna al final
  - [ ] `Anchored` es coherente con lo que la parte debe hacer
  - [ ] La decoracion tiene `CanTouch` y `CanQuery` en false

---

### 2. CFrame explicado

- **Que es:** posicion y rotacion en un solo valor.
- **Para que sirve:** todo lo que implique orientar algo.

| Constructor | Que hace |
|---|---|
| `CFrame.new(x, y, z)` | Posicion sin rotacion |
| `CFrame.new(posicion)` | Igual, desde un Vector3 |
| `CFrame.Angles(rx, ry, rz)` | Rotacion en **radianes** |
| `CFrame.fromEulerAnglesXYZ(...)` | Igual que Angles |
| `CFrame.lookAt(desde, hacia)` | Orientado mirando a un punto |

| Metodo | Que hace |
|---|---|
| `:ToWorldSpace(otro)` | Convierte un CFrame local a global |
| `:ToObjectSpace(otro)` | Convierte un CFrame global a local |
| `:PointToWorldSpace(v)` | Un punto local a global |
| `:PointToObjectSpace(v)` | Un punto global a local |
| `:Lerp(destino, alfa)` | Interpola entre dos CFrame |
| `:Inverse()` | El CFrame inverso |

| Propiedad | Que devuelve |
|---|---|
| `.Position` | El Vector3 de posicion |
| `.LookVector` | Hacia donde mira, unitario |
| `.RightVector` | Su derecha |
| `.UpVector` | Su arriba |

- **Codigo listo para pegar:**

```lua
-- Colocar algo 5 studs delante del jugador, a su altura
local raiz = personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
if raiz then
    parte.CFrame = raiz.CFrame * CFrame.new(0, 0, -5)
    -- multiplicar por la DERECHA es espacio local:
    -- "5 studs hacia adelante desde donde mira"
end

-- Rotar 90 grados sobre su propio eje Y
parte.CFrame = parte.CFrame * CFrame.Angles(0, math.rad(90), 0)

-- Rotar 90 grados alrededor del eje Y del MUNDO
parte.CFrame = CFrame.Angles(0, math.rad(90), 0) * parte.CFrame

-- Mirar hacia un objetivo sin inclinarse
local desde = torreta.Position
local hacia = Vector3.new(objetivo.Position.X, desde.Y, objetivo.Position.Z)
torreta.CFrame = CFrame.lookAt(desde, hacia)

-- Interpolar suavemente
local alfa = 0.12
parte.CFrame = parte.CFrame:Lerp(destino, alfa)
```

- **Errores frecuentes:**
  - **Pasar grados donde se esperan radianes.** `CFrame.Angles(0, 90, 0)` no gira
    90 grados, gira 90 radianes. Usa siempre `math.rad(90)`. Este es el error
    numero uno con CFrame.
  - Confundir el orden de la multiplicacion. `a * b` aplica `b` en el espacio
    local de `a`. `b * a` lo aplica en el espacio del mundo.
  - Sumar un `Vector3` a un `CFrame` esperando movimiento local:
    `cf + Vector3.new(0,0,-5)` mueve en el eje del **mundo**, no hacia donde
    mira.
  - `CFrame.lookAt` con origen y destino identicos: da un resultado invalido.
  - `CFrame.lookAt` a un objetivo mas alto: la parte se inclina. Iguala la Y si
    solo quieres giro horizontal.
- **Checklist sin errores:**
  - [ ] Todos los angulos pasan por `math.rad`
  - [ ] El orden de multiplicacion es el correcto para local o mundo
  - [ ] `lookAt` nunca recibe dos puntos iguales

---

### 3. PivotTo y GetPivot

- **Que es:** la forma moderna y correcta de mover un modelo completo.
- **Para que sirve:** teletransportar, colocar, orientar un modelo entero sin
  desarmarlo.

| Metodo | Que hace | Notas |
|---|---|---|
| `modelo:GetPivot()` | Devuelve el CFrame del pivote | Funciona sin PrimaryPart |
| `modelo:PivotTo(cf)` | Mueve todo el modelo | Mantiene las posiciones relativas |
| `modelo:MoveTo(v3)` | Mueve evitando solapamientos | Puede subirlo si hay algo debajo |
| `modelo:SetPrimaryPartCFrame(cf)` | Obsoleto | Usa `PivotTo` |

- **Codigo listo para pegar:**

```lua
-- Teletransportar un personaje entero, correctamente
local function teletransportar(personaje: Model, destino: CFrame)
    local humanoide = personaje:FindFirstChildOfClass("Humanoid")
    if humanoide then
        humanoide:ChangeState(Enum.HumanoidStateType.Physics)
    end

    personaje:PivotTo(destino + Vector3.new(0, 3, 0))

    task.wait(0.1)

    if humanoide then
        humanoide:ChangeState(Enum.HumanoidStateType.GettingUp)
    end
end

-- Colocar un modelo sobre el suelo en un punto
local function colocarEnSuelo(modelo: Model, x: number, z: number)
    local origen = Vector3.new(x, 500, z)
    local parametros = RaycastParams.new()
    parametros.FilterType = Enum.RaycastFilterType.Exclude
    parametros.FilterDescendantsInstances = { modelo }

    local golpe = workspace:Raycast(origen, Vector3.new(0, -1000, 0), parametros)
    if not golpe then
        return false
    end

    local _, tamano = modelo:GetBoundingBox()
    modelo:PivotTo(CFrame.new(golpe.Position + Vector3.new(0, tamano.Y / 2, 0)))
    return true
end
```

- **Errores frecuentes:**
  - Mover las partes de un modelo una a una: se desarma. Usa `PivotTo`.
  - Usar `SetPrimaryPartCFrame`, que esta obsoleto y es mas lento.
  - `MoveTo` en un modelo grande: Roblox lo sube para evitar solapes y acaba en
    el aire. Para colocacion exacta usa `PivotTo`.
  - Teletransportar un personaje sin cambiar su estado: a veces se queda
    atascado o rebota de vuelta.
- **Checklist sin errores:**
  - [ ] Los modelos se mueven con `PivotTo`
  - [ ] No se usa `SetPrimaryPartCFrame`
  - [ ] Al teletransportar personajes se ajusta el estado del Humanoid

---

### 4. PrimaryPart

- **Que es:** la parte que define el pivote y la referencia del modelo.
- **Para que sirve:** que `GetPivot` devuelva lo que esperas y que las
  soldaduras tengan un ancla clara.
- **Codigo listo para pegar:**

```lua
local function asegurarPrimaryPart(modelo: Model): BasePart?
    if modelo.PrimaryPart and modelo.PrimaryPart:IsDescendantOf(modelo) then
        return modelo.PrimaryPart
    end

    -- buscar una candidata sensata
    local candidata = modelo:FindFirstChild("Base")
        or modelo:FindFirstChild("Root")
        or modelo:FindFirstChildWhichIsA("BasePart")

    if candidata and candidata:IsA("BasePart") then
        modelo.PrimaryPart = candidata
        return candidata
    end

    warn("El modelo " .. modelo.Name .. " no tiene ninguna BasePart")
    return nil
end

return asegurarPrimaryPart
```

- **Errores frecuentes:**
  - Modelo sin `PrimaryPart` y codigo que asume que existe: error de nil.
  - `PrimaryPart` apuntando a una parte que ya se destruyo: el modelo pierde su
    pivote.
  - Suponer que el `PrimaryPart` esta en el centro: no tiene por que.
- **Checklist sin errores:**
  - [ ] Se comprueba que existe antes de usarla
  - [ ] Sigue siendo descendiente del modelo

---

### 5. Soldaduras

- **Que es:** unir dos partes para que se muevan juntas.

| Tipo | Que hace | Cuando usarlo |
|---|---|---|
| `WeldConstraint` | Une dos partes tal como estan | Casi siempre. Es el moderno |
| `Weld` | Une con un desplazamiento `C0`/`C1` que tu defines | Cuando necesitas control exacto del offset |
| `Motor6D` | Como `Weld` pero animable | Personajes y articulaciones |
| `RigidConstraint` | Une dos Attachment de forma rigida | Alternativa moderna con attachments |

- **Codigo listo para pegar:**

```lua
-- Soldar todas las partes de un modelo a su PrimaryPart
local function soldarModelo(modelo: Model)
    local raiz = modelo.PrimaryPart
    if not raiz then
        warn("Sin PrimaryPart, no se puede soldar " .. modelo.Name)
        return
    end

    for _, descendiente in modelo:GetDescendants() do
        if descendiente:IsA("BasePart") and descendiente ~= raiz then
            local union = Instance.new("WeldConstraint")
            union.Part0 = raiz
            union.Part1 = descendiente
            union.Parent = raiz

            -- las partes soldadas NO deben estar ancladas
            descendiente.Anchored = false
        end
    end

    -- solo la raiz decide si el conjunto esta anclado
    raiz.Anchored = false
end

return soldarModelo
```

- **Errores frecuentes:**
  - **Soldar partes que estan ancladas.** Una parte anclada no se mueve, punto.
    Si sueldas A anclada con B anclada, ninguna se mueve; si sueldas anclada con
    no anclada, el conjunto se queda clavado. Suelda primero, desancla despues,
    o desancla todo menos lo que quieras fijo.
  - Crear el `WeldConstraint` **antes** de colocar las partes en su sitio: la
    soldadura congela la posicion relativa del momento en que se activa.
  - Usar `Weld` sin entender `C0` y `C1`: las partes saltan a posiciones raras.
    Empieza siempre con `WeldConstraint`.
  - Soldar cientos de piezas pequenas: el rendimiento cae. Agrupa o usa
    `MeshPart` unicos.
- **Checklist sin errores:**
  - [ ] Las partes estan en su posicion final antes de soldar
  - [ ] Solo se ancla el conjunto, no las piezas sueltas
  - [ ] Se usa `WeldConstraint` salvo que haga falta control de offset

---

### 6. Motor6D y articulaciones

- **Que es:** la union animable. Es lo que hace que un rig se pueda animar.
- **Para que sirve:** personajes, armas agarradas, puertas articuladas,
  criaturas.
- **Relacion con el modulo 4:** los nombres de las articulaciones de R6 y R15
  que aparecen en `mecanicas/04-animacion.md` son precisamente los nombres de
  los `Motor6D`.
- **Codigo listo para pegar:**

```lua
-- Agarrar un objeto en la mano derecha
local function agarrar(personaje: Model, objeto: BasePart)
    local esR15 = personaje:FindFirstChild("RightHand") ~= nil
    local mano = esR15
        and personaje:FindFirstChild("RightHand")
        or personaje:FindFirstChild("Right Arm")

    if not mano or not mano:IsA("BasePart") then
        warn("No se encontro la mano derecha")
        return nil
    end

    -- limpiar un agarre anterior
    local previo = mano:FindFirstChild("AgarreObjeto")
    if previo then
        previo:Destroy()
    end

    objeto.Anchored = false
    objeto.CanCollide = false
    objeto.Massless = true

    local motor = Instance.new("Motor6D")
    motor.Name = "AgarreObjeto"
    motor.Part0 = mano
    motor.Part1 = objeto
    -- C0 define donde queda el objeto respecto a la mano
    motor.C0 = CFrame.new(0, -0.6, 0) * CFrame.Angles(math.rad(-90), 0, 0)
    motor.Parent = mano

    return motor
end

return agarrar
```

- **Errores frecuentes:**
  - Objeto agarrado con `CanCollide = true`: empuja al personaje y lo tira.
  - Objeto agarrado sin `Massless = true`: el personaje se mueve raro por el
    peso extra.
  - No limpiar el Motor6D anterior: se acumulan y el objeto queda pegado a dos
    sitios.
  - Cambiar `Part0` o `Part1` de un Motor6D existente: hazlo destruyendo y
    creando uno nuevo, es mas fiable.
- **Checklist sin errores:**
  - [ ] El objeto agarrado es `Massless` y sin colision
  - [ ] Se destruye el agarre anterior
  - [ ] `C0` esta ajustado para que se vea natural

---

### 7. Restricciones de movimiento

- **Que es:** objetos que mueven partes usando el motor de fisica.
- **Para que sirve:** movimiento que respeta colisiones y se ve natural.

| Restriccion | Que hace |
|---|---|
| `AlignPosition` | Lleva un Attachment hacia otro |
| `AlignOrientation` | Orienta un Attachment hacia otro |
| `LinearVelocity` | Impone una velocidad lineal |
| `AngularVelocity` | Impone una velocidad de giro |
| `VectorForce` | Aplica una fuerza constante |
| `RopeConstraint` | Cuerda con longitud maxima |
| `SpringConstraint` | Muelle |
| `PrismaticConstraint` | Deslizamiento en un eje |
| `HingeConstraint` | Bisagra, con motor opcional |
| `BallSocketConstraint` | Rotula, base del ragdoll |
| `TorsionSpringConstraint` | Muelle de torsion |

Casi todas necesitan uno o dos `Attachment`.

- **Codigo listo para pegar:**

```lua
-- Objeto que flota siguiendo un punto, con fisica
local function crearSeguidor(objeto: BasePart, objetivo: BasePart)
    objeto.Anchored = false

    local a0 = Instance.new("Attachment")
    a0.Name = "Origen"
    a0.Parent = objeto

    local a1 = Instance.new("Attachment")
    a1.Name = "Destino"
    a1.Position = Vector3.new(0, 4, 0)
    a1.Parent = objetivo

    local alinear = Instance.new("AlignPosition")
    alinear.Attachment0 = a0
    alinear.Attachment1 = a1
    alinear.MaxForce = 30000
    alinear.Responsiveness = 20 -- cuanto mas alto, mas rigido
    alinear.Parent = objeto

    local orientar = Instance.new("AlignOrientation")
    orientar.Attachment0 = a0
    orientar.Attachment1 = a1
    orientar.MaxTorque = 10000
    orientar.Responsiveness = 15
    orientar.Parent = objeto

    return { alinear = alinear, orientar = orientar, a0 = a0, a1 = a1 }
end

-- Puerta con bisagra motorizada
local function crearBisagra(marco: BasePart, hoja: BasePart)
    hoja.Anchored = false

    local aMarco = Instance.new("Attachment")
    aMarco.Parent = marco

    local aHoja = Instance.new("Attachment")
    aHoja.Parent = hoja

    local bisagra = Instance.new("HingeConstraint")
    bisagra.Attachment0 = aMarco
    bisagra.Attachment1 = aHoja
    bisagra.ActuatorType = Enum.ActuatorType.Servo
    bisagra.ServoMaxTorque = 25000
    bisagra.AngularSpeed = 4
    bisagra.TargetAngle = 0
    bisagra.Parent = marco

    local function abrir()
        bisagra.TargetAngle = 95
    end
    local function cerrar()
        bisagra.TargetAngle = 0
    end

    return { abrir = abrir, cerrar = cerrar }
end
```

- **Errores frecuentes:**
  - Restriccion sobre una parte **anclada**: no pasa absolutamente nada. Es el
    fallo mas comun con restricciones.
  - `MaxForce` o `MaxTorque` demasiado bajos: el objeto no llega a moverse.
  - `MaxForce` infinito: el objeto atraviesa paredes y hace cosas violentas.
  - Olvidar asignar los dos `Attachment`: la restriccion no hace nada y no
    avisa.
  - Usar `BodyPosition`, `BodyVelocity` o `BodyGyro`: estan obsoletos. Sus
    sustitutos son `AlignPosition`, `LinearVelocity` y `AlignOrientation`.
- **Checklist sin errores:**
  - [ ] Las partes afectadas NO estan ancladas
  - [ ] Los dos Attachment estan asignados
  - [ ] `MaxForce` y `MaxTorque` tienen valores razonables
  - [ ] No se usa ningun objeto `Body...` obsoleto

---

### 8. Grupos de colision

- **Que es:** decidir que grupos de partes chocan entre si.
- **Para que sirve:** que los jugadores se atraviesen, que los proyectiles no
  choquen con quien dispara, que los NPC no empujen.
- **API implicada:** `PhysicsService:RegisterCollisionGroup`,
  `CollisionGroupSetCollidable`, `BasePart.CollisionGroup`.
- **Donde va:** Script en `ServerScriptService`, al arrancar.
- **Codigo listo para pegar:**

```lua
local PhysicsService = game:GetService("PhysicsService")
local Players = game:GetService("Players")

local GRUPOS = { "Jugadores", "Proyectiles", "NPC", "Decoracion" }

for _, nombre in GRUPOS do
    local ok = pcall(function()
        PhysicsService:RegisterCollisionGroup(nombre)
    end)
    if not ok then
        -- ya existia, no pasa nada
    end
end

-- los jugadores no chocan entre si
PhysicsService:CollisionGroupSetCollidable("Jugadores", "Jugadores", false)
-- los proyectiles no chocan entre si
PhysicsService:CollisionGroupSetCollidable("Proyectiles", "Proyectiles", false)
-- la decoracion no choca con nada
for _, nombre in GRUPOS do
    PhysicsService:CollisionGroupSetCollidable("Decoracion", nombre, false)
end

local function asignarGrupo(raiz: Instance, grupo: string)
    for _, d in raiz:GetDescendants() do
        if d:IsA("BasePart") then
            d.CollisionGroup = grupo
        end
    end
    if raiz:IsA("BasePart") then
        raiz.CollisionGroup = grupo
    end
end

Players.PlayerAdded:Connect(function(jugador)
    jugador.CharacterAdded:Connect(function(personaje)
        asignarGrupo(personaje, "Jugadores")

        -- las partes anadidas despues tambien
        personaje.DescendantAdded:Connect(function(d)
            if d:IsA("BasePart") then
                d.CollisionGroup = "Jugadores"
            end
        end)
    end)
end)

return asignarGrupo
```

- **Errores frecuentes:**
  - Registrar el grupo sin `pcall` y que ya exista: error al reiniciar el
    script.
  - Asignar el grupo solo al crear el personaje y no a los accesorios que se
    anaden despues: por eso esta el `DescendantAdded`.
  - Hacerlo desde el cliente: los grupos de colision son cosa del servidor.
  - Nombres de grupo distintos por un espacio o una mayuscula.
- **Checklist sin errores:**
  - [ ] El registro esta en `pcall`
  - [ ] Se cubren las partes anadidas despues
  - [ ] Todo ocurre en el servidor

---

### 9. Touched con antirrebote

- **Que es:** el evento que se dispara cuando dos partes se tocan.
- **Cuidado:** `Touched` se dispara muchisimas veces por segundo y con partes
  inesperadas. Nunca lo uses sin filtro y sin antirrebote.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")

local function alTocarJugador(parte: BasePart, enfriamiento: number, accion: (Player, Model) -> ())
    local recientes: { [Player]: number } = {}

    parte.Touched:Connect(function(otra)
        local personaje = otra:FindFirstAncestorOfClass("Model")
        if not personaje then
            return
        end

        local humanoide = personaje:FindFirstChildOfClass("Humanoid")
        if not humanoide or humanoide.Health <= 0 then
            return
        end

        local jugador = Players:GetPlayerFromCharacter(personaje)
        if not jugador then
            return
        end

        local ahora = os.clock()
        if ahora - (recientes[jugador] or 0) < enfriamiento then
            return
        end
        recientes[jugador] = ahora

        accion(jugador, personaje)
    end)

    Players.PlayerRemoving:Connect(function(jugador)
        recientes[jugador] = nil
    end)
end

return alTocarJugador
```

- **Errores frecuentes:**
  - Sin antirrebote: una moneda se recoge cuarenta veces en medio segundo.
  - Antirrebote global en vez de por jugador: un jugador bloquea a los demas.
  - Asumir que `otra.Parent` es el personaje: puede ser un accesorio, una
    herramienta o una parte de un sombrero. Usa `FindFirstAncestorOfClass`.
  - `Touched` en una parte con `CanTouch = false`: no se dispara nunca.
  - Usar `Touched` para detectar zonas grandes: es poco fiable a alta velocidad.
    Para eso, consultas espaciales del punto 10.
- **Checklist sin errores:**
  - [ ] Hay antirrebote por jugador
  - [ ] Se sube por el arbol hasta el modelo del personaje
  - [ ] Se comprueba que el Humanoid esta vivo
  - [ ] `CanTouch` esta en true en esa parte

---

### 10. Consultas espaciales

- **Que es:** preguntarle al motor que hay dentro de un volumen.
- **Para que sirve:** deteccion fiable de zonas, area de dano, cofres cercanos.
- **API implicada:** `workspace:GetPartBoundsInBox`,
  `GetPartBoundsInRadius`, `GetPartsInPart`, `OverlapParams`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")

local function humanoidesEnRadio(centro: Vector3, radio: number, excluir: { Instance }?)
    local parametros = OverlapParams.new()
    parametros.FilterType = Enum.RaycastFilterType.Exclude
    parametros.FilterDescendantsInstances = excluir or {}
    parametros.MaxParts = 60

    local partes = workspace:GetPartBoundsInRadius(centro, radio, parametros)

    local encontrados: { Humanoid } = {}
    local vistos: { [Humanoid]: boolean } = {}

    for _, parte in partes do
        local modelo = parte:FindFirstAncestorOfClass("Model")
        if modelo then
            local hum = modelo:FindFirstChildOfClass("Humanoid")
            if hum and hum.Health > 0 and not vistos[hum] then
                vistos[hum] = true
                table.insert(encontrados, hum)
            end
        end
    end

    return encontrados
end

-- Zona de entrada y salida, revisada cada medio segundo
local function vigilarZona(zona: BasePart, alEntrar: (Player) -> (), alSalir: (Player) -> ())
    local dentro: { [Player]: boolean } = {}

    local parametros = OverlapParams.new()
    parametros.FilterType = Enum.RaycastFilterType.Exclude
    parametros.FilterDescendantsInstances = { zona }

    task.spawn(function()
        while zona.Parent do
            local actuales: { [Player]: boolean } = {}

            for _, parte in workspace:GetPartsInPart(zona, parametros) do
                local modelo = parte:FindFirstAncestorOfClass("Model")
                if modelo then
                    local jugador = Players:GetPlayerFromCharacter(modelo)
                    if jugador then
                        actuales[jugador] = true
                    end
                end
            end

            for jugador in actuales do
                if not dentro[jugador] then
                    dentro[jugador] = true
                    alEntrar(jugador)
                end
            end

            for jugador in dentro do
                if not actuales[jugador] then
                    dentro[jugador] = nil
                    alSalir(jugador)
                end
            end

            task.wait(0.4)
        end
    end)
end

return { enRadio = humanoidesEnRadio, zona = vigilarZona }
```

- **Errores frecuentes:**
  - No deduplicar por Humanoid: un personaje tiene quince partes y recibe quince
    veces el efecto.
  - No excluir la propia zona ni al lanzador.
  - Consultar cada frame en un radio enorme: caro. Cada 0.3 a 0.5 segundos basta
    para zonas.
  - `GetPartsInPart` con la zona sin `CanQuery`: no encuentra nada.
  - Olvidar `MaxParts`: en una zona llena devuelve miles de partes.
- **Checklist sin errores:**
  - [ ] Se deduplica por Humanoid
  - [ ] La zona y el lanzador estan excluidos
  - [ ] La frecuencia de consulta es razonable
  - [ ] `MaxParts` esta puesto

---

### 11. Raycast

- **Que es:** lanzar una linea y ver con que choca primero.
- **Para que sirve:** linea de vision, disparos, detectar el suelo, colocar
  objetos.
- **API implicada:** `workspace:Raycast`, `RaycastParams`, `RaycastResult`.
- **Codigo listo para pegar:**

```lua
local function haciaElSuelo(desde: Vector3, ignorar: { Instance }): RaycastResult?
    local parametros = RaycastParams.new()
    parametros.FilterType = Enum.RaycastFilterType.Exclude
    parametros.FilterDescendantsInstances = ignorar
    parametros.IgnoreWater = false
    parametros.RespectCanCollide = true

    return workspace:Raycast(desde, Vector3.new(0, -50, 0), parametros)
end

local function hayLineaDeVision(a: Vector3, b: Vector3, ignorar: { Instance }): boolean
    local parametros = RaycastParams.new()
    parametros.FilterType = Enum.RaycastFilterType.Exclude
    parametros.FilterDescendantsInstances = ignorar

    local direccion = b - a
    local golpe = workspace:Raycast(a, direccion, parametros)

    -- si no golpea nada, el camino esta libre
    return golpe == nil
end

-- El resultado trae informacion util
local golpe = haciaElSuelo(Vector3.new(0, 100, 0), {})
if golpe then
    print("Choco con:", golpe.Instance:GetFullName())
    print("En:", golpe.Position)
    print("Normal de la superficie:", golpe.Normal)
    print("Distancia:", golpe.Distance)
    print("Material:", golpe.Material.Name)
end
```

- **Errores frecuentes:**
  - **Pasar un punto de destino como direccion.** El segundo argumento es un
    **vector direccion cuya longitud es el alcance**, no una posicion. Para ir
    de A a B, pasa `b - a`.
  - Direccion de longitud cero: no golpea nada nunca.
  - No excluir al propio personaje: el rayo choca con su propio pie.
  - Usar `FindPartOnRay`, que esta obsoleto. Usa `workspace:Raycast`.
  - Olvidar que las partes con `CanQuery = false` son invisibles al rayo. A
    veces es lo que quieres, a veces es el bug.
- **Checklist sin errores:**
  - [ ] El segundo argumento es una direccion, no un punto
  - [ ] El lanzador esta excluido
  - [ ] Se comprueba que el resultado no es `nil`
  - [ ] No se usa `FindPartOnRay`

---

### 12. Tamano y limites de un modelo

- **Que es:** medir un modelo sin adivinar.
- **API implicada:** `Model:GetExtentsSize`, `Model:GetBoundingBox`,
  `BasePart.Size`.
- **Codigo listo para pegar:**

```lua
local function describir(modelo: Model)
    local cf, tamano = modelo:GetBoundingBox()

    print("Centro:", cf.Position)
    print("Tamano:", tamano)
    print("Altura:", tamano.Y)
    print("Base (Y minima):", cf.Position.Y - tamano.Y / 2)

    return cf, tamano
end

-- Poner un modelo justo encima de una superficie
local function apoyarSobre(modelo: Model, superficie: BasePart)
    local _, tamano = modelo:GetBoundingBox()
    local arribaDeLaSuperficie = superficie.Position.Y + superficie.Size.Y / 2

    modelo:PivotTo(CFrame.new(
        superficie.Position.X,
        arribaDeLaSuperficie + tamano.Y / 2,
        superficie.Position.Z
    ))
end
```

- **Errores frecuentes:**
  - Usar `Size` de la `PrimaryPart` como tamano del modelo: solo mide esa parte.
  - `GetExtentsSize` en un modelo vacio: da error.
  - Suponer que el pivote esta en la base: normalmente esta en el centro.
- **Checklist sin errores:**
  - [ ] Se usa `GetBoundingBox` para medir modelos
  - [ ] Se comprueba que el modelo tiene partes
  - [ ] Se resta la mitad del alto para apoyar en el suelo

---

### 13. Escalar un modelo

- **Que es:** cambiar el tamano de un modelo entero manteniendo proporciones.
- **API implicada:** `Model:ScaleTo`, `Model:GetScale`.
- **Codigo listo para pegar:**

```lua
-- Un modelo al doble de tamano
modelo:ScaleTo(2)

-- Escalar suavemente
local function escalarSuave(modelo: Model, destino: number, duracion: number)
    local inicio = modelo:GetScale()
    local t0 = os.clock()

    task.spawn(function()
        while true do
            local avance = (os.clock() - t0) / duracion
            if avance >= 1 or not modelo.Parent then
                if modelo.Parent then
                    modelo:ScaleTo(destino)
                end
                break
            end

            local suavizado = avance * avance * (3 - 2 * avance)
            modelo:ScaleTo(inicio + (destino - inicio) * suavizado)
            task.wait()
        end
    end)
end

return escalarSuave
```

- **Errores frecuentes:**
  - Cambiar el `Size` de cada parte a mano: las posiciones relativas y las
    soldaduras se rompen. `ScaleTo` lo hace bien.
  - Escalar un personaje con `ScaleTo` esperando cambiar su altura de
    movimiento: para eso estan los valores `BodyHeightScale` y similares dentro
    del Humanoid.
  - Escalar a cero o a un valor negativo.
- **Checklist sin errores:**
  - [ ] Se usa `ScaleTo`, no `Size` parte por parte
  - [ ] La escala es mayor que cero

---

### 14. Propiedad de red

- **Que es:** que maquina simula la fisica de un conjunto.
- **Para que sirve:** que los vehiculos y objetos que el jugador maneja se
  sientan sin retardo.
- **API implicada:** `BasePart:SetNetworkOwner`, `GetNetworkOwner`,
  `SetNetworkOwnershipAuto`.
- **Codigo listo para pegar:**

```lua
-- Servidor: dar el control de un vehiculo a su conductor
local function darControl(vehiculo: Model, jugador: Player?)
    local raiz = vehiculo.PrimaryPart
    if not raiz or raiz.Anchored then
        return -- una parte anclada no tiene propietario de red
    end

    local ok, err = pcall(function()
        raiz:SetNetworkOwner(jugador) -- nil = el servidor
    end)

    if not ok then
        warn("No se pudo asignar la propiedad de red: " .. tostring(err))
    end
end

-- Al salir del asiento, devolver el control al servidor
asiento:GetPropertyChangedSignal("Occupant"):Connect(function()
    local ocupante = asiento.Occupant
    if ocupante then
        local personaje = ocupante.Parent
        local jugador = personaje and Players:GetPlayerFromCharacter(personaje)
        darControl(vehiculo, jugador)
    else
        darControl(vehiculo, nil)
    end
end)
```

- **Errores frecuentes:**
  - Llamarlo sobre una parte **anclada**: lanza error. Comprueba primero.
  - Llamarlo desde el cliente: solo el servidor puede.
  - No devolver el control al servidor al bajarse: si el jugador se va, el
    vehiculo se congela.
  - Dar el control a un jugador de objetos importantes del juego: un cliente
    modificado puede moverlos a su antojo. Solo para lo que el jugador conduce.
- **Checklist sin errores:**
  - [ ] La parte no esta anclada
  - [ ] Se llama desde el servidor
  - [ ] Se devuelve el control al terminar
  - [ ] Solo se cede en objetos que el jugador maneja

---

### 15. Clonar desde almacenamiento

- **Que es:** el patron correcto para instanciar modelos.

| Contenedor | Lo ve el cliente | Para que |
|---|---|---|
| `ReplicatedStorage` | Si | Plantillas que el cliente tambien necesita |
| `ServerStorage` | No | Plantillas solo del servidor, premios, secretos |
| `ServerScriptService` | No | Scripts del servidor |
| `Workspace` | Si | El mundo activo |

- **Codigo listo para pegar:**

```lua
local ServerStorage = game:GetService("ServerStorage")

local plantillas = ServerStorage:WaitForChild("Plantillas", 20)
if not plantillas then
    error("Falta la carpeta Plantillas en ServerStorage")
end

local function crear(nombre: string, donde: CFrame): Model?
    local original = plantillas:FindFirstChild(nombre)
    if not original or not original:IsA("Model") then
        warn("No existe la plantilla " .. nombre)
        return nil
    end

    local copia = original:Clone()
    copia:PivotTo(donde)      -- colocar ANTES de meterlo en workspace
    copia.Parent = workspace  -- el padre siempre al final

    return copia
end

return crear
```

- **Errores frecuentes:**
  - Asignar `Parent = workspace` y luego mover: se ve un parpadeo en la posicion
    original y la fisica lo simula ahi.
  - Guardar plantillas en `Workspace` con `Anchored` y esconderlas bajo el mapa:
    ocupan memoria y aparecen en las consultas.
  - Poner plantillas con premios en `ReplicatedStorage`: los jugadores pueden
    inspeccionarlas.
  - Clonar dentro de un bucle sin limite: miles de instancias y el servidor se
    ahoga.
- **Checklist sin errores:**
  - [ ] Se coloca antes de asignar el padre
  - [ ] Las plantillas sensibles estan en `ServerStorage`
  - [ ] Hay un limite de instancias vivas

---

### 16. Debris y limpieza

- **Que es:** borrar cosas pasado un tiempo.
- **API implicada:** `Debris:AddItem`, `Instance:Destroy`,
  `Instance.Destroying`.
- **Codigo listo para pegar:**

```lua
local Debris = game:GetService("Debris")

-- Efecto que se limpia solo
local function chispas(posicion: Vector3)
    local ancla = Instance.new("Part")
    ancla.Size = Vector3.new(0.2, 0.2, 0.2)
    ancla.Transparency = 1
    ancla.Anchored = true
    ancla.CanCollide = false
    ancla.CanQuery = false
    ancla.CanTouch = false
    ancla.Position = posicion
    ancla.Parent = workspace

    local emisor = Instance.new("ParticleEmitter")
    emisor.Lifetime = NumberRange.new(0.3, 0.6)
    emisor.Speed = NumberRange.new(8, 14)
    emisor.Rate = 0
    emisor.Parent = ancla
    emisor:Emit(24)

    Debris:AddItem(ancla, 2) -- se destruye a los 2 segundos
end

-- Contador de instancias, para no pasarse
local VIVOS = 0
local MAXIMO = 120

local function crearProyectil(): BasePart?
    if VIVOS >= MAXIMO then
        return nil
    end

    VIVOS += 1

    local bala = Instance.new("Part")
    bala.Parent = workspace

    bala.Destroying:Connect(function()
        VIVOS -= 1
    end)

    Debris:AddItem(bala, 5)
    return bala
end
```

- **Errores frecuentes:**
  - No limpiar nada: el servidor acumula miles de partes y va cada vez peor.
  - `Debris:AddItem` con un tiempo enorme: es lo mismo que no limpiar.
  - Destruir una parte y seguir usando la variable despues: `parte.Parent` sera
    `nil` y las propiedades daran error.
  - No desconectar las conexiones de un objeto destruido. `Destroy` desconecta
    las de sus propios eventos, pero no las que tu creaste hacia otros objetos.
- **Checklist sin errores:**
  - [ ] Todo lo temporal tiene `Debris:AddItem`
  - [ ] Hay un maximo de instancias vivas
  - [ ] Las conexiones se limpian

---

### 17. Puertas

- **Que es:** el ejemplo clasico de movimiento cinematico bien hecho.
- **Codigo listo para pegar:**

```lua
local TweenService = game:GetService("TweenService")

local function crearPuertaDeslizante(hoja: BasePart, desplazamiento: Vector3)
    hoja.Anchored = true -- cinematica: siempre anclada

    local cerrada = hoja.CFrame
    local abierta = cerrada * CFrame.new(desplazamiento)

    local abiertaAhora = false
    local moviendo = false

    local INFO = TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut)

    local function alternar()
        if moviendo then
            return
        end
        moviendo = true

        local destino = abiertaAhora and cerrada or abierta
        abiertaAhora = not abiertaAhora

        -- mientras se mueve, que no bloquee
        hoja.CanCollide = false

        local tween = TweenService:Create(hoja, INFO, { CFrame = destino })
        tween.Completed:Connect(function()
            hoja.CanCollide = not abiertaAhora
            moviendo = false
        end)
        tween:Play()
    end

    return { alternar = alternar }
end

return crearPuertaDeslizante
```

- **Errores frecuentes:**
  - Puerta sin anclar movida con tween: la fisica pelea con el tween y la puerta
    tiembla o sale volando.
  - Sin bandera `moviendo`: pulsar dos veces lanza dos tweens a la vez.
  - Dejar `CanCollide = true` mientras se abre: la puerta empuja al jugador y lo
    lanza o lo mete en la pared.
  - Guardar la posicion abierta como un valor absoluto: si mueves la puerta en
    Studio, deja de funcionar. Calcularla desde la cerrada, como aqui, es
    robusto.
- **Checklist sin errores:**
  - [ ] La hoja esta anclada
  - [ ] Hay bandera contra dobles activaciones
  - [ ] La colision se desactiva mientras se mueve
  - [ ] Las posiciones se calculan desde la inicial

---

### 18. Plataformas moviles

- **Que es:** una plataforma que lleva al jugador encima.
- **El problema clasico:** el jugador se queda quieto mientras la plataforma se
  va, o se cae al llegar al extremo.
- **Codigo listo para pegar:**

```lua
local RunService = game:GetService("RunService")

local function crearPlataforma(plataforma: BasePart, destino: Vector3, velocidad: number)
    plataforma.Anchored = true

    -- MUY IMPORTANTE: friccion alta para que el jugador no resbale
    plataforma.CustomPhysicalProperties = PhysicalProperties.new(0.7, 2, 0, 100, 1)

    local inicio = plataforma.Position
    local total = (destino - inicio).Magnitude
    local avance = 0
    local sentido = 1

    RunService.Heartbeat:Connect(function(dt)
        if not plataforma.Parent then
            return
        end

        avance += (velocidad / total) * dt * sentido

        if avance >= 1 then
            avance = 1
            sentido = -1
        elseif avance <= 0 then
            avance = 0
            sentido = 1
        end

        plataforma.CFrame = CFrame.new(inicio:Lerp(destino, avance))
    end)
end

return crearPlataforma
```

Si el jugador se sigue quedando atras, la solucion mas fiable es soldarlo
temporalmente:

```lua
local function pegarAlPasajero(plataforma: BasePart, raizPersonaje: BasePart)
    local union = Instance.new("WeldConstraint")
    union.Name = "PegadoPlataforma"
    union.Part0 = plataforma
    union.Part1 = raizPersonaje
    union.Parent = plataforma
    return union
end
```

- **Errores frecuentes:**
  - Mover con `Position` en vez de `CFrame`: se pierde la rotacion.
  - Friccion por defecto: el jugador resbala y se queda atras.
  - Mover en `RenderStepped` desde el servidor: `RenderStepped` solo existe en
    el cliente. En el servidor usa `Heartbeat`.
  - Plataforma no anclada: la fisica la tira.
  - Velocidad tan alta que el jugador atraviesa la plataforma.
- **Checklist sin errores:**
  - [ ] La plataforma esta anclada
  - [ ] La friccion es alta
  - [ ] Se usa `Heartbeat` en el servidor
  - [ ] Se ha probado subido encima de ida y de vuelta

---

### 19. Ascensores

- **Que es:** movimiento vertical con paradas.
- **Codigo listo para pegar:**

```lua
local TweenService = game:GetService("TweenService")

local function crearAscensor(cabina: BasePart, alturas: { number }, esperaPorPiso: number)
    cabina.Anchored = true
    cabina.CustomPhysicalProperties = PhysicalProperties.new(0.7, 2, 0, 100, 1)

    local pisoActual = 1
    local ocupado = false

    local function irA(piso: number)
        if ocupado or piso == pisoActual or not alturas[piso] then
            return
        end
        ocupado = true

        local recorrido = math.abs(alturas[piso] - alturas[pisoActual])
        local duracion = math.clamp(recorrido / 12, 0.8, 8)

        local destino = CFrame.new(
            cabina.Position.X,
            alturas[piso],
            cabina.Position.Z
        ) * (cabina.CFrame - cabina.Position)

        local tween = TweenService:Create(
            cabina,
            TweenInfo.new(duracion, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut),
            { CFrame = destino }
        )

        tween.Completed:Connect(function()
            pisoActual = piso
            task.wait(esperaPorPiso)
            ocupado = false
        end)

        tween:Play()
    end

    return { irA = irA, pisoActual = function() return pisoActual end }
end

return crearAscensor
```

- **Errores frecuentes:**
  - Subida instantanea: el jugador se queda flotando o atraviesa el techo de la
    cabina.
  - No marcar el ascensor como ocupado: llamadas simultaneas lo vuelven loco.
  - Duracion fija para recorridos distintos: de un piso al siguiente va lento y
    de la planta baja al ultimo, absurdamente rapido. Calculala por distancia.
- **Checklist sin errores:**
  - [ ] La cabina esta anclada y con friccion alta
  - [ ] Hay bandera de ocupado
  - [ ] La duracion depende de la distancia

---

### 20. Cintas transportadoras

- **Que es:** una superficie que empuja lo que tiene encima.
- **API implicada:** `BasePart.AssemblyLinearVelocity` en una parte anclada.
  Con la parte anclada, esta velocidad no la mueve a ella: mueve a lo que se
  apoya encima. Es un truco clasico de Roblox.
- **Codigo listo para pegar:**

```lua
local function crearCinta(parte: BasePart, direccionLocal: Vector3, velocidad: number)
    parte.Anchored = true

    local function aplicar()
        -- la direccion se interpreta en el espacio de la cinta
        local mundo = parte.CFrame:VectorToWorldSpace(direccionLocal.Unit)
        parte.AssemblyLinearVelocity = mundo * velocidad
    end

    aplicar()

    -- si la cinta se mueve o gira, hay que recalcular
    parte:GetPropertyChangedSignal("CFrame"):Connect(aplicar)

    local function cambiarVelocidad(nueva: number)
        velocidad = nueva
        aplicar()
    end

    local function parar()
        parte.AssemblyLinearVelocity = Vector3.zero
    end

    return { cambiar = cambiarVelocidad, parar = parar }
end

return crearCinta
```

- **Errores frecuentes:**
  - Parte sin anclar: en vez de empujar, sale disparada.
  - Usar `Velocity`, que esta obsoleto. Es `AssemblyLinearVelocity`.
  - Direccion sin normalizar: la velocidad real no es la que crees.
  - Cinta con friccion muy baja: no arrastra nada.
  - Esperar que empuje partes que estan tambien ancladas: no puede.
- **Checklist sin errores:**
  - [ ] La cinta esta anclada
  - [ ] La direccion esta normalizada
  - [ ] Se usa `AssemblyLinearVelocity`
  - [ ] La friccion permite el arrastre

---

### 21. Partes destructibles

- **Que es:** objetos con vida que se rompen.
- **Codigo listo para pegar:**

```lua
local Debris = game:GetService("Debris")

local function hacerDestructible(parte: BasePart, vidaMaxima: number, alRomper: (() -> ())?)
    parte:SetAttribute("Vida", vidaMaxima)
    parte:SetAttribute("VidaMaxima", vidaMaxima)

    local roto = false

    local function romper()
        if roto then
            return
        end
        roto = true

        -- fragmentos
        for i = 1, 6 do
            local trozo = Instance.new("Part")
            trozo.Size = parte.Size / 3
            trozo.CFrame = parte.CFrame * CFrame.new(
                math.random(-15, 15) / 10,
                math.random(-15, 15) / 10,
                math.random(-15, 15) / 10
            )
            trozo.Color = parte.Color
            trozo.Material = parte.Material
            trozo.Anchored = false
            trozo.CanCollide = true
            trozo.CanQuery = false
            trozo.CanTouch = false
            trozo.Parent = workspace

            trozo.AssemblyLinearVelocity = Vector3.new(
                math.random(-18, 18),
                math.random(6, 20),
                math.random(-18, 18)
            )

            Debris:AddItem(trozo, 4)
        end

        if alRomper then
            alRomper()
        end

        parte:Destroy()
    end

    local function danar(cantidad: number)
        if roto then
            return
        end
        if typeof(cantidad) ~= "number" or cantidad <= 0 then
            return
        end

        local vida = (parte:GetAttribute("Vida") or 0) - cantidad
        parte:SetAttribute("Vida", math.max(vida, 0))

        -- feedback visual
        local fraccion = vida / vidaMaxima
        parte.Transparency = math.clamp((1 - fraccion) * 0.4, 0, 0.4)

        if vida <= 0 then
            romper()
        end
    end

    return { danar = danar, romper = romper }
end

return hacerDestructible
```

- **Errores frecuentes:**
  - Crear cincuenta fragmentos por objeto: con diez objetos rotos el servidor se
    hunde. Seis u ocho es suficiente.
  - Fragmentos sin `Debris`: se acumulan para siempre.
  - Fragmentos con `CanTouch` y `CanQuery` en true: disparan eventos y aparecen
    en raycasts sin motivo.
  - Sin bandera `roto`: dos golpes simultaneos generan dos veces los fragmentos.
- **Checklist sin errores:**
  - [ ] Pocos fragmentos por rotura
  - [ ] Todos con `Debris`
  - [ ] Los fragmentos no disparan eventos
  - [ ] Hay bandera contra roturas dobles

---

### 22. Terreno por codigo

- **Que es:** generar o modificar el terreno voxel.
- **API implicada:** `workspace.Terrain:FillBlock`, `FillBall`,
  `FillRegion`, `ReplaceMaterial`, `Clear`.
- **Codigo listo para pegar:**

```lua
local terreno = workspace.Terrain

-- Una plataforma de roca
terreno:FillBlock(
    CFrame.new(0, 0, 0),
    Vector3.new(200, 8, 200),
    Enum.Material.Rock
)

-- Un lago
terreno:FillBall(
    Vector3.new(40, -2, 40),
    18,
    Enum.Material.Water
)

-- Vaciar una cueva
terreno:FillBall(
    Vector3.new(-30, -6, 20),
    12,
    Enum.Material.Air
)

-- Cambiar un material por otro en una region
local region = Region3.new(
    Vector3.new(-100, -20, -100),
    Vector3.new(100, 20, 100)
):ExpandToGrid(4)

terreno:ReplaceMaterial(
    region,
    4,
    Enum.Material.Grass,
    Enum.Material.Snow
)
```

- **Errores frecuentes:**
  - Rellenar volumenes gigantes de golpe: el servidor se congela varios
    segundos. Hazlo en trozos con `task.wait()` entre ellos.
  - `Region3` sin `ExpandToGrid(4)`: el terreno trabaja en rejilla de 4 studs.
  - Generar terreno en el cliente: no se replica al servidor.
  - Olvidar que el terreno cuenta para el peso del lugar y no se puede deshacer
    facilmente si lo generas en ejecucion.
- **Checklist sin errores:**
  - [ ] Los rellenos grandes se hacen por trozos
  - [ ] Las regiones estan alineadas con `ExpandToGrid(4)`
  - [ ] La generacion ocurre en el servidor

---

### 23. StreamingEnabled

- **Que es:** que el cliente solo cargue la parte del mundo cercana.
- **Para que sirve:** mapas grandes sin que el juego tarde una eternidad en
  cargar.
- **Donde se activa:** propiedad `StreamingEnabled` de `Workspace`.

| Propiedad | Que hace |
|---|---|
| `StreamingEnabled` | Activa el sistema |
| `StreamingMinRadius` | Radio que siempre esta cargado |
| `StreamingTargetRadius` | Radio al que aspira |
| `Model.ModelStreamingMode` | Como se trata cada modelo |

| ModelStreamingMode | Efecto |
|---|---|
| `Default` | Comportamiento normal |
| `Atomic` | El modelo entero llega junto o no llega |
| `Persistent` | Siempre cargado en todos los clientes |
| `PersistentPerPlayer` | Siempre cargado para jugadores concretos |

- **Codigo listo para pegar:**

```lua
-- Cliente: esperar a que exista algo lejano
local function esperarParte(ruta: string, segundos: number): BasePart?
    local objetivo: Instance? = workspace

    for trozo in string.gmatch(ruta, "[^%.]+") do
        if not objetivo then
            return nil
        end
        objetivo = objetivo:WaitForChild(trozo, segundos)
    end

    return objetivo and objetivo:IsA("BasePart") and objetivo or nil
end

-- Cliente: pedir que una zona siga cargada mientras la usamos
local jugador = game:GetService("Players").LocalPlayer
local ok = pcall(function()
    jugador:RequestStreamAroundAsync(Vector3.new(500, 20, 500), 5)
end)

if not ok then
    warn("No se pudo pedir la carga de esa zona")
end
```

- **Errores frecuentes:**
  - Cliente que busca `workspace.Mapa.Puerta` directamente: con streaming, esa
    parte puede no existir todavia. Todo acceso del cliente a partes lejanas
    necesita `WaitForChild` con timeout.
  - Modelo importante en `Default`: llega a medias y se ve incompleto. Marca los
    modelos que deben llegar enteros como `Atomic`.
  - Suponer que el servidor tambien pierde partes: no. **El servidor siempre lo
    tiene todo.** El streaming solo afecta al cliente.
  - Activar streaming en un mapa pequeno: no aporta nada y anade complicaciones.
- **Checklist sin errores:**
  - [ ] El cliente nunca asume que una parte lejana existe
  - [ ] Los modelos que deben llegar completos son `Atomic`
  - [ ] La logica importante vive en el servidor
  - [ ] Probado caminando hasta el extremo del mapa

---

### 24. Por que mi modelo se desarma

Diagnostico ordenado del problema mas frecuente de este modulo.

| # | Comprobacion | Que significa si falla |
|---|---|---|
| 1 | Todas las piezas estan soldadas a la raiz | Sin soldar, cada pieza cae por su lado |
| 2 | Las soldaduras se crearon con las piezas ya colocadas | Se congelo la posicion equivocada |
| 3 | Ninguna pieza esta anclada salvo, si acaso, la raiz | Mezclar anclado y no anclado rompe el conjunto |
| 4 | Hay `PrimaryPart` asignada | Sin ella, `PivotTo` usa un pivote poco predecible |
| 5 | El modelo se movio con `PivotTo`, no parte por parte | Mover piezas sueltas lo desarma |
| 6 | Las piezas no se solapan al colocar el modelo | La fisica las empuja violentamente para separarlas |
| 7 | No hay dos soldaduras contradictorias sobre la misma pieza | Se pelean entre si |
| 8 | Las piezas pequenas son `Massless` | Masas raras hacen que el conjunto se retuerza |
| 9 | No se cambio el `Size` de las piezas tras soldar | Cambiar el tamano rompe las uniones |
| 10 | Ninguna restriccion contradice las soldaduras | Una restriccion tirando de una pieza soldada la arranca |

---

## Tabla resumen: como mover cada cosa

| Quiero mover | Anclada | Como |
|---|---|---|
| Una puerta | Si | Tween sobre `CFrame` |
| Una plataforma | Si | `CFrame` en `Heartbeat` |
| Un modelo entero | Si o no | `PivotTo` |
| Un vehiculo | No | Restricciones + `SetNetworkOwner` |
| Un objeto empujado | No | `AssemblyLinearVelocity` o `LinearVelocity` |
| Un objeto que sigue a otro | No | `AlignPosition` + `AlignOrientation` |
| Una pieza articulada | No | `HingeConstraint` con servo |
| Lo que hay sobre una cinta | Si la cinta | `AssemblyLinearVelocity` en la cinta anclada |
| Un personaje | - | `Humanoid:MoveTo` o `PivotTo` para teletransportar |

---

## Checklist maestro de fisica y modelos

- [ ] Cada parte tiene el `Anchored` correcto para lo que hace
- [ ] La decoracion tiene `CanTouch` y `CanQuery` en false
- [ ] Todos los angulos de CFrame pasan por `math.rad`
- [ ] Los modelos se mueven con `PivotTo`
- [ ] Todo modelo importante tiene `PrimaryPart`
- [ ] Las soldaduras se crean con las piezas ya en su sitio
- [ ] Ninguna restriccion apunta a una parte anclada
- [ ] No se usa ningun `Body...` obsoleto
- [ ] Los raycasts reciben una direccion, no un punto
- [ ] Todas las detecciones deduplican por Humanoid
- [ ] Las plataformas tienen friccion alta
- [ ] Todo lo temporal pasa por `Debris`
- [ ] Hay un maximo de instancias vivas por sistema
- [ ] Si hay streaming, el cliente nunca asume que una parte existe
- [ ] Probado con dos jugadores a la vez

---

## Siguiente paso

Los sistemas que usan todo esto en `mecanicas/08-sistemas.md`. El combate que
depende de raycasts y consultas en `mecanicas/03-combate.md`. Errores concretos
en `mecanicas/09-errores-y-checklist.md`.
