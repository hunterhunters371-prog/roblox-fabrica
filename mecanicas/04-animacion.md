# 04 - Animacion

Modulo 4 del catalogo. Se divide en dos partes:

- **Parte A: los modelos JSON de este repositorio.** El formato que genera la IA,
  sus campos, sus limites y como se convierte en algo que Studio entiende.
- **Parte B: animacion en tiempo de ejecucion.** El codigo Luau que reproduce,
  mezcla, detiene y sincroniza animaciones dentro del juego.

Si lo que quieres es **crear** una animacion, ve a la Parte A.
Si ya tienes el ID de la animacion y quieres **usarla**, ve a la Parte B.

---

# PARTE A - Los modelos JSON

El contrato completo esta en `prompts/PROMPT-2-ANIMACION.md`. Esta seccion lo
resume y anade el analisis de los archivos que ya existen en `animaciones/`.

## A.1 Campos del JSON

| Campo | Tipo | Obligatorio | Limites |
|---|---|---|---|
| `nombre` | texto | si | Hasta 40 caracteres, sin `<` `>` `&` |
| `rig` | texto | si | Solo `R6` o `R15` |
| `loop` | booleano | si | `true` o `false` |
| `prioridad` | texto | si | `core`, `idle`, `movimiento`, `accion` |
| `keyframes` | lista | si | Entre 2 y 40 elementos |
| `keyframes[].t` | numero | si | Segundos, estrictamente creciente, total 30 s maximo |
| `keyframes[].easing` | texto | no | `suave`, `lineal`, `rebote`, `elastica`, `instantaneo` |
| `keyframes[].poses` | objeto | si | Nombre de articulacion como clave |

### Formato de una pose

Cada pose acepta **3 valores** (solo rotacion) o **6 valores** (rotacion mas
desplazamiento):

```json
{
  "Right Arm": [-70, 0, 20],
  "Torso": [4, 0, 0, 0, 0.15, 0]
}
```

| Posicion | Significado | Limite |
|---|---|---|
| 1, 2, 3 | Rotacion X, Y, Z en grados | -180 a 180 |
| 4, 5, 6 | Desplazamiento X, Y, Z en studs | -2.5 a 2.5 |

## A.2 Articulaciones por rig

**Nunca mezcles los dos.** Solo `Head` existe en ambos, asi que si te equivocas
de rig lo unico que se movera es la cabeza. Ese es el sintoma clasico.

### R6 (6 articulaciones)

```text
Torso, Head, Left Arm, Right Arm, Left Leg, Right Leg
```

### R15 (15 articulaciones)

```text
LowerTorso, UpperTorso, Head,
LeftUpperArm, LeftLowerArm, LeftHand,
RightUpperArm, RightLowerArm, RightHand,
LeftUpperLeg, LeftLowerLeg, LeftFoot,
RightUpperLeg, RightLowerLeg, RightFoot
```

`HumanoidRootPart` **nunca** se anima. Si necesitas que el cuerpo suba o baje,
usa el desplazamiento del torso.

## A.3 Ejes: la parte que mas errores causa

Los ejes no significan lo mismo en R6 que en R15. Esta tabla es la referencia.

### R15

| Articulacion | Eje X | Eje Y | Eje Z |
|---|---|---|---|
| Brazos | Adelante y atras (igual en ambos lados) | Rotacion interna | Levantar de lado: **Z+ sube el derecho, Z- sube el izquierdo** |
| Piernas | Adelante y atras | Abrir y cerrar | Separar de lado |
| Head | Asentir (si) | Negar (no) | Inclinar |
| Torsos | Inclinar adelante y atras | Girar | Inclinar de lado |

### R6

| Articulacion | Eje X | Eje Y | Eje Z |
|---|---|---|---|
| Brazos | Levantar de lado: **siempre NEGATIVO en ambos brazos** | Torsion | Adelante y atras: **Z+ adelanta el lado derecho, Z- adelanta el izquierdo** |
| Piernas | Levantar de lado | Torsion | Adelante y atras, misma regla de signo |
| Head | Asentir | Negar | Inclinar |
| Torso | Inclinar adelante y atras | Girar | Inclinar de lado |

Memoriza estas dos frases:

- **En R15, para levantar un brazo de lado se usa Z.**
- **En R6, para levantar un brazo de lado se usa X y siempre en negativo.**

## A.4 Fases de un ciclo de caminar o correr

Un ciclo creible tiene cuatro fases. Si te faltan, la animacion parece rigida.

| Fase | Que pasa | Detalle que la hace buena |
|---|---|---|
| Contacto | El talon toca el suelo | La pierna delantera estirada, el torso adelantado |
| Amortiguacion | El peso baja | El torso baja de 0.1 a 0.25 studs, la rodilla se dobla |
| Impulso | El pie empuja | El torso sube, la cadera se extiende |
| Vuelo | El pie se despega | Al correr, los dos pies pueden estar en el aire |

Un ciclo de caminar suele necesitar de 5 a 9 keyframes. Uno de correr, de 6 a 10.

## A.5 Reglas de oro

1. **Si es bucle, la ultima pose debe ser igual a la primera.** Si no, hay un
   salto visible en cada repeticion.
2. **Piernas en contrafase.** Cuando una va adelante, la otra va atras. En R6
   eso es un `z` positivo en una y negativo en la otra.
3. **Brazos en fase con la pierna opuesta.** Brazo derecho adelante con pierna
   izquierda adelante.
4. **Nada esta perfectamente simetrico ni perfectamente quieto.** Un valor de 2
   o 3 grados de diferencia entre lados da vida.
5. **El torso siempre hace algo.** Un balanceo vertical de 0.1 a 0.3 studs y una
   inclinacion constante hacia adelante al correr.
6. **Amplitudes realistas.** Caminar mueve las piernas unos 25 a 40 grados.
   Correr, 45 a 70. Mas de 90 grados parece una caricatura.
7. **Algo tiene que moverse.** Un JSON con todas las poses a cero no pasa el
   validador.

## A.6 Truco de flujo (el que usa `correr_flujo_r6.json`)

Este conjunto de valores es el que produce la sensacion de peso en R6:

| Elemento | Valor tipico | Motivo |
|---|---|---|
| Piernas | `z` de +50 y -50 en contrafase | Zancada amplia |
| Pierna adelantada | `px` de -1.2 | La pierna se separa del eje, no solo gira |
| Brazos | `z` de 0.3 a 0.5 del valor de las piernas | Acompanan sin exagerar |
| Extremidades en el punto alto | `py` de +0.2 o +0.3 | El paso despega |
| Brazos | `py` de -0.1 o -0.2 | Los hombros caen al correr |
| Torso | Desplazamiento menor a 0.3 | Balanceo, no teletransporte |
| Torso | Inclinacion adelante constante | Peso hacia la carrera |
| Root | Siempre cero | Nunca se toca |

## A.7 Los archivos que ya existen

| Archivo | Rig | Que resuelve |
|---|---|---|
| `caminar_r6.json` | R6 | Ciclo base de caminar, punto de partida limpio |
| `caminar_vida_r6.json` | R6 | Caminar con balanceo de torso y asimetria |
| `caminar_chulo_r6.json` | R6 | Caminar con actitud, hombros marcados |
| `caminar_r15.json` | R15 | El mismo ciclo traducido a R15, util para comparar ejes |
| `caminar_vida_r15.json` | R15 | Version con vida en R15 |
| `correr_ref_r6.json` | R6 | Carrera de referencia, medida en `referencias/` |
| `correr_pro_r6.json` | R6 | Carrera pulida, la mejor plantilla de correr |
| `correr_flujo_r6.json` | R6 | Carrera con el truco de flujo de la seccion A.6 |
| `salto_r6.json` | R6 | Salto, no es bucle |
| `saludar_r6.json` | R6 | Gesto de brazo, prioridad de accion |
| `baile_r6.json` | R6 | Animacion larga de cuerpo completo |

Para aprender el formato, abre `correr_pro_r6.json` y `caminar_vida_r6.json`.
Para entender la diferencia de ejes, compara `caminar_r6.json` con
`caminar_r15.json`: es la misma animacion escrita para dos rigs distintos.

## A.8 Del JSON a Studio

```text
1. La IA devuelve un bloque JSON y nada mas
2. Guardas el archivo en animaciones/  (por ejemplo mi_correr.json)
3. Arrastras el archivo encima de herramientas/revisar_pase.bat
   - detecta la clave "rig" y sabe que es una animacion
   - valida campos, limites y articulaciones
   - si falla, imprime la ruta exacta del error
   - si pasa, genera mi_correr.rbxmx
4. Opcional: python ver_anim.py mi_correr.json  ->  mi_correr.gif
   para revisar el movimiento sin abrir Studio
5. En Studio:
   - Modelo > Rig Builder > R6 o R15  (el MISMO rig del JSON)
   - Avatar > Animation Editor, selecciona el Dummy
   - arrastra mi_correr.rbxmx dentro de la carpeta AnimSaves del Dummy
     (o clic derecho en AnimSaves > Insert from File...)
   - en el editor, menu de tres puntos > Export to Roblox
   - copia el Asset ID que te da
6. Ese ID va en la propiedad AnimationId de un objeto Animation
```

Comandos directos, si prefieres consola:

```bat
python spec_anim.py mi_correr.json
python ver_anim.py mi_correr.json
```

## A.9 Errores del validador de animacion

| Mensaje | Causa real | Solucion |
|---|---|---|
| Articulacion desconocida | Nombre de otro rig o mal escrito | Copia el nombre de la lista A.2 |
| `t` no creciente | Dos keyframes con el mismo tiempo, o desordenados | Ordena y separa al menos 0.01 s |
| Rotacion fuera de rango | Un valor mayor de 180 o menor de -180 | Acota los grados |
| Desplazamiento fuera de rango | Un valor mayor de 2.5 studs | Reduce el desplazamiento |
| Demasiados keyframes | Mas de 40 | Simplifica el ciclo |
| Duracion excedida | El ultimo `t` pasa de 30 | Acorta la animacion |
| Nada se mueve | Todas las poses a cero | Anade movimiento real |
| Prioridad invalida | Texto distinto de los cuatro permitidos | Usa `core`, `idle`, `movimiento` o `accion` |
| Rig invalido | Texto distinto de `R6` o `R15` | Corrige la clave `rig` |

Las rutas de error tienen esta forma, y te dicen exactamente donde mirar:

```text
raiz.keyframes[1].poses.RightUpperArm
```

Si pegas el error a la IA, **exige que devuelva el JSON completo corregido**, no
un fragmento. Un fragmento pegado a mano rompe el archivo.

---

# PARTE B - Animacion en tiempo de ejecucion

Aqui empieza el codigo Luau. Todo lo de esta parte da por hecho que ya tienes un
Asset ID de animacion.

## Indice de la Parte B

| # | Mecanica | Para que |
|---|---|---|
| 1 | Animator y LoadAnimation | La forma correcta de cargar |
| 2 | Play y Stop con fundido | Transiciones limpias |
| 3 | Prioridades | Que animacion gana |
| 4 | Bucle y velocidad | Ajustar el ritmo |
| 5 | Peso y mezcla | Combinar dos animaciones |
| 6 | TimePosition | Saltar a un instante |
| 7 | Marcadores | Sincronizar con eventos |
| 8 | Precarga | Que no se vea el tiron |
| 9 | Sustituir las animaciones por defecto | Caminar propio |
| 10 | Animaciones de Tool | Armas y objetos |
| 11 | Motor6D y agarre | Sujetar objetos |
| 12 | Animacion procedural con CFrame | Sin editor |
| 13 | IKControl | Pies y manos que se adaptan |
| 14 | Viewmodel en primera persona | Manos propias |
| 15 | Sincronizar sonido y particulas | Impacto |
| 16 | Inspeccionar pistas activas | Depurar |
| 17 | Animaciones en NPC | Sin Player |
| 18 | Detener todo al morir | Limpieza |

---

### 1. Animator y LoadAnimation

- **Que es:** el objeto que reproduce animaciones sobre un Humanoid.
- **Para que sirve:** es el punto de entrada de todo lo demas.
- **API implicada:** `Animator`, `Animator:LoadAnimation`, `Animation`,
  `AnimationTrack`.
- **Donde va:** Script en `ServerScriptService` o LocalScript, segun quien deba
  decidir.
- **Codigo listo para pegar:**

```lua
local function obtenerAnimator(personaje: Model): Animator?
    local humanoid = personaje:FindFirstChildOfClass("Humanoid")
    if not humanoid then
        return nil
    end

    -- el Animator lo crea Roblox, pero puede tardar un instante
    local animator = humanoid:FindFirstChildOfClass("Animator")
    if not animator then
        animator = Instance.new("Animator")
        animator.Parent = humanoid
    end

    return animator
end

local function cargar(personaje: Model, assetId: number): AnimationTrack?
    local animator = obtenerAnimator(personaje)
    if not animator then
        return nil
    end

    local animacion = Instance.new("Animation")
    animacion.AnimationId = "rbxassetid://" .. tostring(assetId)

    local ok, pista = pcall(function()
        return animator:LoadAnimation(animacion)
    end)

    if not ok then
        warn("No se pudo cargar la animacion " .. tostring(assetId) .. ": " .. tostring(pista))
        return nil
    end

    return pista
end

return cargar
```

- **Errores frecuentes:**
  - Usar `Humanoid:LoadAnimation`: **obsoleto**. Usa siempre `Animator`.
  - Cargar la animacion en cada pulsacion: crea una pista nueva cada vez y
    consume memoria. Cargala una vez y guardala.
  - Olvidar el prefijo `rbxassetid://`.
  - Usar un ID de animacion subido por otra cuenta sin permiso: no carga.
- **Checklist sin errores:**
  - [ ] Se usa `Animator:LoadAnimation`
  - [ ] El ID lleva el prefijo `rbxassetid://`
  - [ ] Las pistas se cargan una vez y se reutilizan
  - [ ] La carga esta envuelta en `pcall`

---

### 2. Play y Stop con fundido

- **Que es:** iniciar y detener una animacion con transicion suave.
- **Para que sirve:** que no haya saltos entre animaciones.
- **API implicada:** `AnimationTrack:Play(fadeTime, weight, speed)`,
  `Stop(fadeTime)`, `IsPlaying`.
- **Codigo listo para pegar:**

```lua
-- Play(tiempoDeFundido, peso, velocidad)
pista:Play(0.15, 1, 1)   -- entra en 0.15 s
pista:Stop(0.25)         -- sale en 0.25 s

-- Cambio entre dos animaciones sin parpadeo
local function cambiar(actual: AnimationTrack?, nueva: AnimationTrack, fundido: number)
    if actual == nueva then
        return actual
    end
    if actual and actual.IsPlaying then
        actual:Stop(fundido)
    end
    nueva:Play(fundido, 1, 1)
    return nueva
end
```

| Situacion | Fundido recomendado |
|---|---|
| Idle a caminar | 0.2 a 0.3 s |
| Caminar a correr | 0.15 s |
| Cualquier cosa a un ataque | 0.05 a 0.1 s |
| Salto y caida | 0.1 s |

- **Errores frecuentes:**
  - `Play()` sin argumentos usa el fundido por defecto de 0.1 s, que a veces es
    demasiado para un ataque.
  - Llamar a `Play` sobre una pista que ya suena: la reinicia. Comprueba
    `IsPlaying`.
  - Detener sin fundido en animaciones largas: corte brusco.
- **Checklist sin errores:**
  - [ ] Se comprueba `IsPlaying` antes de reproducir
  - [ ] Los fundidos estan ajustados por tipo de animacion
  - [ ] La animacion anterior siempre se detiene

---

### 3. Prioridades

- **Que es:** el orden que decide que animacion se ve cuando hay varias.
- **Para que sirve:** que un ataque tape el caminar, y que el caminar tape el
  idle.
- **API implicada:** `AnimationTrack.Priority`, `Enum.AnimationPriority`.

| Prioridad | Valor en el JSON | Uso |
|---|---|---|
| `Core` | `core` | Animaciones base del motor, casi nunca la tocas |
| `Idle` | `idle` | Quieto, respirar |
| `Movement` | `movimiento` | Caminar, correr, saltar |
| `Action` | `accion` | Ataques, gestos, habilidades |
| `Action2` a `Action4` | no disponible en el JSON | Capas por encima, se ajustan en codigo |

- **Codigo listo para pegar:**

```lua
pistaIdle.Priority = Enum.AnimationPriority.Idle
pistaCaminar.Priority = Enum.AnimationPriority.Movement
pistaAtaque.Priority = Enum.AnimationPriority.Action
pistaGesto.Priority = Enum.AnimationPriority.Action2 -- por encima del ataque
```

- **Errores frecuentes:**
  - Un ataque con prioridad `Movement`: el caminar lo tapa a medias y se ve
    tembloroso. Este es el sintoma numero uno de "mi animacion se ve rara".
  - Poner todo en `Action`: las animaciones se pelean entre si.
  - Cambiar `Priority` despues de llamar a `Play`: hazlo antes.
- **Checklist sin errores:**
  - [ ] Los ataques estan en `Action` o superior
  - [ ] El movimiento esta en `Movement`
  - [ ] La prioridad se asigna antes de `Play`

---

### 4. Bucle y velocidad

- **Que es:** repetir la animacion y ajustar su ritmo.
- **Para que sirve:** que el ciclo de correr acompane la velocidad real.
- **API implicada:** `AnimationTrack.Looped`, `AdjustSpeed`, `Speed`, `Length`.
- **Codigo listo para pegar:**

```lua
local RunService = game:GetService("RunService")

local VELOCIDAD_BASE_ANIMACION = 16 -- a que WalkSpeed se diseno el ciclo

pistaCaminar.Looped = true
pistaCaminar:Play(0.2)

RunService.Heartbeat:Connect(function()
    local hum = personaje:FindFirstChildOfClass("Humanoid")
    if not hum or not pistaCaminar.IsPlaying then
        return
    end

    local velocidadReal = hum.MoveDirection.Magnitude * hum.WalkSpeed
    if velocidadReal < 0.1 then
        return
    end

    -- el ciclo se acelera con el personaje: los pies no patinan
    pistaCaminar:AdjustSpeed(velocidadReal / VELOCIDAD_BASE_ANIMACION)
end)
```

- **Errores frecuentes:**
  - `Looped` en false en un ciclo de caminar: se reproduce una vez y el
    personaje se congela de pie.
  - `Looped` en true en un ataque: el golpe se repite eternamente.
  - No ajustar la velocidad: con `WalkSpeed` 30 y un ciclo hecho para 16, los
    pies patinan por el suelo.
  - `AdjustSpeed(0)`: la animacion se congela, no se detiene.
- **Checklist sin errores:**
  - [ ] `Looped` coherente con el tipo de animacion
  - [ ] La velocidad del ciclo se escala con la del personaje
  - [ ] `Looped` se puede fijar tambien en el JSON con la clave `loop`

---

### 5. Peso y mezcla

- **Que es:** reproducir dos animaciones a la vez repartiendo influencia.
- **Para que sirve:** transiciones caminar a correr, apuntar mientras caminas.
- **API implicada:** `AdjustWeight(peso, tiempo)`, `WeightCurrent`,
  `WeightTarget`.
- **Codigo listo para pegar:**

```lua
-- Mezcla continua entre caminar y correr segun la velocidad
local function mezclarLocomocion(velocidad: number)
    local factor = math.clamp((velocidad - 8) / (28 - 8), 0, 1)

    if not pistaCaminar.IsPlaying then
        pistaCaminar:Play(0.2, 1 - factor, 1)
    end
    if not pistaCorrer.IsPlaying then
        pistaCorrer:Play(0.2, factor, 1)
    end

    pistaCaminar:AdjustWeight(1 - factor, 0.1)
    pistaCorrer:AdjustWeight(factor, 0.1)
end
```

- **Errores frecuentes:**
  - Mezclar animaciones de prioridad distinta: la de mayor prioridad gana y el
    peso no hace nada visible. Para mezclar, usa la misma prioridad.
  - Peso 0 con la pista sonando: gasta rendimiento sin verse. Detenla.
  - Pesos que suman mas de 1 en la misma prioridad: el resultado se deforma.
- **Checklist sin errores:**
  - [ ] Las pistas mezcladas comparten prioridad
  - [ ] Los pesos suman aproximadamente 1
  - [ ] Las pistas con peso 0 se detienen

---

### 6. TimePosition

- **Que es:** el instante exacto de la animacion que se esta mostrando.
- **Para que sirve:** empezar por la mitad, congelar una pose, sincronizar dos
  personajes.
- **API implicada:** `AnimationTrack.TimePosition`, `Length`, `Speed`.
- **Codigo listo para pegar:**

```lua
-- Congelar en una pose concreta (por ejemplo, mantener el arma en alto)
pista:Play(0)
pista:AdjustSpeed(0)
pista.TimePosition = pista.Length * 0.4

-- Reanudar
pista:AdjustSpeed(1)

-- Dos jugadores bailando exactamente igual
local function sincronizar(pistaA: AnimationTrack, pistaB: AnimationTrack)
    pistaB.TimePosition = pistaA.TimePosition
end
```

- **Errores frecuentes:**
  - Asignar `TimePosition` antes de `Play`: se ignora. Primero `Play`, luego
    `TimePosition`.
  - Asignar un valor mayor que `Length`: la animacion salta al final.
  - Leer `Length` antes de que la animacion haya cargado: devuelve 0. Espera un
    frame o usa `pista.Length > 0` como condicion.
- **Checklist sin errores:**
  - [ ] `Play` se llama antes de tocar `TimePosition`
  - [ ] El valor esta entre 0 y `Length`
  - [ ] No se lee `Length` sin comprobar que es mayor que 0

---

### 7. Marcadores

- **Que es:** avisos colocados en instantes concretos de la animacion.
- **Para que sirve:** aplicar dano justo cuando la espada pasa, soltar el
  proyectil justo cuando la mano se abre.
- **API implicada:** `AnimationTrack:GetMarkerReachedSignal(nombre)`,
  `KeyframeReached`.
- **Codigo listo para pegar:**

```lua
-- Los marcadores se anaden en el Animation Editor, sobre un keyframe
local conexion = pistaAtaque:GetMarkerReachedSignal("Impacto"):Connect(function(parametro)
    -- este es el frame exacto en que la espada toca
    aplicarDanoDelGolpe()
end)

-- Alternativa sin marcadores, por nombre de keyframe
pistaAtaque.KeyframeReached:Connect(function(nombreKeyframe)
    if nombreKeyframe == "Impacto" then
        aplicarDanoDelGolpe()
    end
end)

-- Limpieza obligatoria
pistaAtaque.Stopped:Connect(function()
    conexion:Disconnect()
end)
```

- **Errores frecuentes:**
  - Conectar el marcador dentro del manejador de la pulsacion: se acumula una
    conexion por cada golpe y a los cien golpes el dano se aplica cien veces.
    Conecta **una sola vez** al cargar la pista.
  - Marcador mal escrito: no salta nunca y no hay error visible.
  - Confiar el dano a un marcador en el cliente: manipulable. El marcador
    marca el momento; el dano lo aplica el servidor.
- **Checklist sin errores:**
  - [ ] Los marcadores se conectan una sola vez
  - [ ] El nombre coincide exactamente con el del editor
  - [ ] Las conexiones se desconectan

---

### 8. Precarga

- **Que es:** pedir a Roblox que descargue la animacion antes de necesitarla.
- **Para que sirve:** que el primer uso no se vea como un tiron o una pose T.
- **API implicada:** `ContentProvider:PreloadAsync`.
- **Donde va:** LocalScript en `StarterPlayerScripts`, lo antes posible.
- **Codigo listo para pegar:**

```lua
local ContentProvider = game:GetService("ContentProvider")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local contenedor = ReplicatedStorage:WaitForChild("Animaciones")
local aPrecargar = {}

for _, hijo in contenedor:GetDescendants() do
    if hijo:IsA("Animation") then
        table.insert(aPrecargar, hijo)
    end
end

local ok, err = pcall(function()
    ContentProvider:PreloadAsync(aPrecargar)
end)

if not ok then
    warn("Fallo la precarga de animaciones: " .. tostring(err))
end

print("Animaciones precargadas: " .. #aPrecargar)
```

- **Errores frecuentes:**
  - `PreloadAsync` bloquea el hilo hasta terminar. No lo pongas antes de algo
    urgente sin `task.spawn`.
  - Pasar IDs en texto en vez de instancias `Animation`.
  - Precargar cientos de assets a la vez: el arranque se alarga.
- **Checklist sin errores:**
  - [ ] Se pasan instancias, no cadenas de texto
  - [ ] Esta envuelto en `pcall`
  - [ ] No bloquea el arranque critico

---

### 9. Sustituir las animaciones por defecto

- **Que es:** cambiar el caminar, correr, saltar e idle del avatar.
- **Para que sirve:** que tu juego tenga su propio estilo de movimiento.
- **Dos caminos:**

| Camino | Como | Cuando usarlo |
|---|---|---|
| Editar el script `Animate` | Cambiar los `AnimationId` dentro del script que Roblox pone en el personaje | Rapido, cubre el 90 por ciento de los casos |
| Escribir tu propio controlador | Borrar `Animate` y gestionar los estados a mano | Control total, sprint, deslizamiento, capas |

- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar (camino rapido):**

```lua
local Players = game:GetService("Players")

local IDS = {
    idle = { "rbxassetid://100000001", "rbxassetid://100000002" },
    walk = { "rbxassetid://100000003" },
    run = { "rbxassetid://100000004" },
    jump = { "rbxassetid://100000005" },
    fall = { "rbxassetid://100000006" },
}

local function aplicar(personaje: Model)
    local animate = personaje:WaitForChild("Animate", 10)
    if not animate then
        return -- el jugador puede tener animaciones de paquete
    end

    for categoria, lista in IDS do
        local carpeta = animate:FindFirstChild(categoria)
        if not carpeta then
            continue
        end

        local indice = 1
        for _, hijo in carpeta:GetChildren() do
            if hijo:IsA("Animation") and lista[indice] then
                hijo.AnimationId = lista[indice]
                indice += 1
            end
        end
    end
end

Players.PlayerAdded:Connect(function(jugador)
    jugador.CharacterAppearanceLoaded:Connect(aplicar)
end)
```

- **Errores frecuentes:**
  - Aplicar en `CharacterAdded` en vez de `CharacterAppearanceLoaded`: el script
    `Animate` a veces todavia no existe y el paquete de animaciones del avatar
    sobreescribe tus IDs.
  - Animaciones R15 en un juego forzado a R6: no se ven. El rig debe coincidir
    con lo configurado en Game Settings > Avatar.
  - Cambiar los IDs desde el cliente: solo lo ve ese jugador.
- **Checklist sin errores:**
  - [ ] Se usa `CharacterAppearanceLoaded`
  - [ ] El rig del JSON coincide con el rig del juego
  - [ ] Se ejecuta en el servidor
  - [ ] Probado tras morir y reaparecer

---

### 10. Animaciones de Tool

- **Que es:** animaciones que se reproducen al equipar o usar un objeto.
- **Para que sirve:** sujetar el arma, blandirla, recargar.
- **API implicada:** `Tool.Equipped`, `Unequipped`, `Activated`,
  `Enum.AnimationPriority`.
- **Donde va:** Script dentro del Tool.
- **Codigo listo para pegar:**

```lua
local herramienta = script.Parent :: Tool

local ID_SUJETAR = "rbxassetid://100000010"
local ID_GOLPE = "rbxassetid://100000011"

local pistaSujetar: AnimationTrack? = nil
local pistaGolpe: AnimationTrack? = nil

local function crear(animator: Animator, id: string, prioridad: Enum.AnimationPriority, bucle: boolean)
    local anim = Instance.new("Animation")
    anim.AnimationId = id
    local pista = animator:LoadAnimation(anim)
    pista.Priority = prioridad
    pista.Looped = bucle
    return pista
end

herramienta.Equipped:Connect(function()
    local personaje = herramienta.Parent
    if not personaje or not personaje:IsA("Model") then
        return
    end

    local humanoid = personaje:FindFirstChildOfClass("Humanoid")
    local animator = humanoid and humanoid:FindFirstChildOfClass("Animator")
    if not animator then
        return
    end

    pistaSujetar = crear(animator, ID_SUJETAR, Enum.AnimationPriority.Idle, true)
    pistaGolpe = crear(animator, ID_GOLPE, Enum.AnimationPriority.Action, false)

    pistaSujetar:Play(0.2)
end)

herramienta.Activated:Connect(function()
    if pistaGolpe then
        pistaGolpe:Play(0.06)
    end
end)

herramienta.Unequipped:Connect(function()
    if pistaSujetar then
        pistaSujetar:Stop(0.15)
        pistaSujetar:Destroy()
        pistaSujetar = nil
    end
    if pistaGolpe then
        pistaGolpe:Stop(0.1)
        pistaGolpe:Destroy()
        pistaGolpe = nil
    end
end)
```

- **Errores frecuentes:**
  - No detener la animacion de sujetar al desequipar: el personaje sigue con la
    pose del arma con las manos vacias.
  - Cargar las pistas en cada `Equipped` sin destruir las anteriores: fuga.
  - Animacion de sujetar con prioridad `Action`: bloquea los ataques.
- **Checklist sin errores:**
  - [ ] Las pistas se detienen y destruyen en `Unequipped`
  - [ ] Sujetar va en `Idle`, golpear en `Action`
  - [ ] Probado equipando y desequipando muchas veces seguidas

---

### 11. Motor6D y agarre

- **Que es:** la union articulada entre dos partes. Es lo que permite animar.
- **Para que sirve:** unir un objeto a la mano de forma que la animacion lo
  mueva con el cuerpo.
- **API implicada:** `Motor6D`, `Part0`, `Part1`, `C0`, `C1`.
- **Donde va:** Script en `ServerScriptService`.
- **Codigo listo para pegar:**

```lua
local function agarrar(personaje: Model, objeto: BasePart)
    local mano = personaje:FindFirstChild("RightHand")   -- R15
        or personaje:FindFirstChild("Right Arm")         -- R6
    if not mano or not mano:IsA("BasePart") then
        return nil
    end

    -- limpiar un agarre previo
    local anterior = mano:FindFirstChild("AgarreMotor")
    if anterior then
        anterior:Destroy()
    end

    local motor = Instance.new("Motor6D")
    motor.Name = "AgarreMotor"
    motor.Part0 = mano
    motor.Part1 = objeto
    motor.C0 = CFrame.new(0, -1, 0) * CFrame.Angles(math.rad(-90), 0, 0)
    motor.C1 = CFrame.new()
    motor.Parent = mano

    objeto.Anchored = false
    objeto.CanCollide = false

    return motor
end

return agarrar
```

- **Errores frecuentes:**
  - El objeto sigue `Anchored`: el Motor6D no puede moverlo y el brazo se
    estira hacia el objeto.
  - `CanCollide` en true: el objeto choca con el propio personaje y todo
    tiembla.
  - Nombres de mano equivocados: en R6 es `Right Arm` con espacio, en R15 es
    `RightHand`.
  - Crear un Motor6D nuevo sin destruir el viejo: el objeto queda con dos
    padres logicos y se rompe.
- **Checklist sin errores:**
  - [ ] El objeto no esta anclado y no colisiona
  - [ ] Se comprueban los dos nombres de mano
  - [ ] Se destruye el agarre anterior

---

### 12. Animacion procedural con CFrame

- **Que es:** mover partes por codigo, sin pasar por el editor.
- **Para que sirve:** mirar hacia el raton, respiracion sutil, inclinacion al
  girar, cosas que dependen del juego y no se pueden pregrabar.
- **API implicada:** `CFrame.Angles`, `CFrame:Lerp`, `Motor6D.C0`,
  `RunService.RenderStepped`.
- **Donde va:** LocalScript en `StarterPlayerScripts`.
- **Codigo listo para pegar:**

```lua
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")

local jugador = Players.LocalPlayer

RunService.RenderStepped:Connect(function()
    local personaje = jugador.Character
    if not personaje then
        return
    end

    local cuello = personaje:FindFirstChild("Neck", true)
    if not cuello or not cuello:IsA("Motor6D") then
        return
    end

    local camara = workspace.CurrentCamera
    if not camara then
        return
    end

    -- la cabeza sigue el angulo vertical de la camara
    local _, _, _, _, _, _, _, _, m22 = camara.CFrame:GetComponents()
    local angulo = math.asin(math.clamp(camara.CFrame.LookVector.Y, -1, 1))
    local objetivo = cuello.C0 * CFrame.Angles(0, 0, 0)

    local base = CFrame.new(cuello.C0.Position)
    cuello.C0 = cuello.C0:Lerp(base * CFrame.Angles(-angulo * 0.6, 0, 0), 0.2)
end)
```

- **Errores frecuentes:**
  - Asignar `C0` sin guardar el valor original: cada frame acumula rotacion y la
    cabeza gira sin parar. Guarda el `C0` inicial y parte siempre de el.
  - Hacerlo en `Heartbeat` en vez de `RenderStepped`: se ve a saltos porque no
    esta sincronizado con el dibujado.
  - Hacerlo en el servidor: 60 actualizaciones por segundo replicadas es
    demasiado trafico.
- **Checklist sin errores:**
  - [ ] El `C0` original se guarda una vez y se usa como base
  - [ ] Se usa `RenderStepped` en el cliente
  - [ ] Se usa `Lerp` para suavizar

---

### 13. IKControl

- **Que es:** cinematica inversa nativa. Le das un objetivo y el motor calcula
  como debe doblarse la extremidad.
- **Para que sirve:** pies que se apoyan en escaleras, manos que alcanzan un
  pomo, cabeza que mira a otro jugador.
- **API implicada:** `IKControl`, `Type`, `EndEffector`, `ChainRoot`, `Target`,
  `Weight`.
- **Donde va:** Script en `ServerScriptService` o LocalScript para efectos
  locales.
- **Codigo listo para pegar:**

```lua
local function crearIKMano(personaje: Model, objetivo: BasePart)
    local humanoid = personaje:FindFirstChildOfClass("Humanoid")
    local hombro = personaje:FindFirstChild("RightUpperArm")
    local mano = personaje:FindFirstChild("RightHand")
    if not humanoid or not hombro or not mano then
        return nil -- solo funciona en R15
    end

    local ik = Instance.new("IKControl")
    ik.Name = "IKManoDerecha"
    ik.Type = Enum.IKControlType.Position
    ik.ChainRoot = hombro
    ik.EndEffector = mano
    ik.Target = objetivo
    ik.Weight = 1
    ik.Parent = humanoid

    return ik
end

-- Para desactivarlo suavemente:
-- ik.Weight = 0  (mejor que destruirlo de golpe)
return crearIKMano
```

- **Errores frecuentes:**
  - Usar IKControl en R6: no hay cadena de articulaciones suficiente. Es una
    funcion de R15.
  - El `Target` es una parte con colision que empuja al personaje. Ponle
    `CanCollide = false` y `Anchored = true`.
  - Destruir el IKControl de golpe: la extremidad salta. Baja `Weight` a 0
    primero.
- **Checklist sin errores:**
  - [ ] El rig es R15
  - [ ] El objetivo no colisiona
  - [ ] Se apaga bajando `Weight`, no destruyendo

---

### 14. Viewmodel en primera persona

- **Que es:** un modelo de brazos que solo ve el jugador local, pegado a la
  camara.
- **Para que sirve:** juegos de disparos en primera persona.
- **API implicada:** `Camera`, `Model:PivotTo`, `RunService.RenderStepped`,
  `LocalPlayer.Character` oculto.
- **Donde va:** LocalScript en `StarterPlayerScripts`.
- **Codigo listo para pegar:**

```lua
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local plantilla = ReplicatedStorage:WaitForChild("Viewmodel") :: Model
local camara = workspace.CurrentCamera

local viewmodel = plantilla:Clone()
viewmodel.Parent = camara -- dentro de la camara: solo lo ve este cliente

for _, parte in viewmodel:GetDescendants() do
    if parte:IsA("BasePart") then
        parte.CanCollide = false
        parte.CanQuery = false
        parte.CanTouch = false
        parte.Massless = true
        parte.CastShadow = false
    end
end

local DESPLAZAMIENTO = CFrame.new(0, -1.5, 0)

RunService.RenderStepped:Connect(function()
    if not camara or not viewmodel.PrimaryPart then
        return
    end
    viewmodel:PivotTo(camara.CFrame * DESPLAZAMIENTO)
end)
```

- **Errores frecuentes:**
  - Poner el viewmodel en Workspace: lo ven todos y aparece flotando.
  - No poner `CanCollide` y `CanQuery` en false: los raycast del arma chocan
    contra las propias manos.
  - Actualizarlo en `Heartbeat`: se retrasa un frame respecto a la camara y
    tiembla.
  - Falta `PrimaryPart` en el modelo: `PivotTo` no sabe que mover.
- **Checklist sin errores:**
  - [ ] El viewmodel esta dentro de `Camera`
  - [ ] Todas las partes son no colisionables y no consultables
  - [ ] Se actualiza en `RenderStepped`
  - [ ] El modelo tiene `PrimaryPart`

---

### 15. Sincronizar sonido y particulas

- **Que es:** disparar efectos en el instante exacto de la animacion.
- **Para que sirve:** pasos, impactos, casquillos, polvo.
- **API implicada:** marcadores, `Sound`, `ParticleEmitter:Emit`.
- **Donde va:** LocalScript o Script segun quien deba oirlo.
- **Codigo listo para pegar:**

```lua
local function conectarPasos(pista: AnimationTrack, personaje: Model)
    local raiz = personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
    if not raiz then
        return
    end

    local sonido = Instance.new("Sound")
    sonido.SoundId = "rbxassetid://9125644819"
    sonido.Volume = 0.35
    sonido.RollOffMaxDistance = 45
    sonido.Parent = raiz

    -- se conecta UNA vez, no en cada paso
    local conexion = pista:GetMarkerReachedSignal("Paso"):Connect(function()
        sonido.PlaybackSpeed = 0.92 + math.random() * 0.16 -- variacion
        sonido:Play()
    end)

    personaje.Destroying:Connect(function()
        conexion:Disconnect()
    end)
end

return conectarPasos
```

- **Errores frecuentes:**
  - Crear un `Sound` nuevo en cada paso: cientos de instancias por minuto.
  - Sonido sin variacion de `PlaybackSpeed`: suena a metralleta y cansa.
  - `RollOffMaxDistance` por defecto: los pasos de alguien al otro lado del mapa
    se oyen igual de fuerte.
- **Checklist sin errores:**
  - [ ] El `Sound` se crea una vez y se reutiliza
  - [ ] Hay variacion aleatoria en el tono
  - [ ] La distancia de atenuacion esta ajustada
  - [ ] La conexion se desconecta al destruir el personaje

---

### 16. Inspeccionar pistas activas

- **Que es:** listar que animaciones estan sonando ahora mismo.
- **Para que sirve:** depurar el clasico "no se por que se ve raro".
- **API implicada:** `Animator:GetPlayingAnimationTracks()`.
- **Codigo listo para pegar:**

```lua
local function inspeccionar(personaje: Model)
    local humanoid = personaje:FindFirstChildOfClass("Humanoid")
    local animator = humanoid and humanoid:FindFirstChildOfClass("Animator")
    if not animator then
        warn("Sin Animator")
        return
    end

    local pistas = animator:GetPlayingAnimationTracks()
    if #pistas == 0 then
        print("Ninguna animacion sonando")
        return
    end

    for _, pista in pistas do
        print(string.format(
            "%s | prioridad=%s | peso=%.2f | velocidad=%.2f | t=%.2f/%.2f",
            pista.Name,
            pista.Priority.Name,
            pista.WeightCurrent,
            pista.Speed,
            pista.TimePosition,
            pista.Length
        ))
    end
end

return inspeccionar
```

- **Errores frecuentes:**
  - Llamarlo en un bucle por frame y llenar la salida de mensajes.
  - Esperar que devuelva pistas cargadas pero no reproducidas: solo devuelve las
    que estan sonando.
- **Checklist sin errores:**
  - [ ] Se llama a demanda, no cada frame
  - [ ] Se revisa la prioridad y el peso, que son la causa habitual del problema

---

### 17. Animaciones en NPC

- **Que es:** animar un modelo que no pertenece a ningun jugador.
- **Para que sirve:** enemigos, aldeanos, jefes.
- **API implicada:** igual que en jugadores, pero el modelo necesita `Humanoid`,
  `HumanoidRootPart`, `Animator` y sus `Motor6D`.
- **Donde va:** Script dentro del modelo del NPC.
- **Codigo listo para pegar:**

```lua
local npc = script.Parent :: Model
local humanoid = npc:WaitForChild("Humanoid") :: Humanoid

local animator = humanoid:FindFirstChildOfClass("Animator")
if not animator then
    animator = Instance.new("Animator")
    animator.Parent = humanoid
end

local function cargar(id: string, prioridad: Enum.AnimationPriority, bucle: boolean)
    local anim = Instance.new("Animation")
    anim.AnimationId = id
    local pista = animator:LoadAnimation(anim)
    pista.Priority = prioridad
    pista.Looped = bucle
    return pista
end

local pistaIdle = cargar("rbxassetid://100000020", Enum.AnimationPriority.Idle, true)
local pistaCaminar = cargar("rbxassetid://100000021", Enum.AnimationPriority.Movement, true)

pistaIdle:Play(0.2)

humanoid.Running:Connect(function(velocidad)
    if velocidad > 0.5 then
        if not pistaCaminar.IsPlaying then
            pistaCaminar:Play(0.2)
        end
    else
        if pistaCaminar.IsPlaying then
            pistaCaminar:Stop(0.2)
        end
    end
end)
```

- **Errores frecuentes:**
  - Modelo sin `HumanoidRootPart` o sin `Motor6D`: el `Animator` carga pero nada
    se mueve. La forma segura de crear un NPC es duplicar un Dummy del Rig
    Builder.
  - NPC con `PrimaryPart` sin asignar: falla al moverlo.
  - Usar un rig R6 con animaciones R15: solo se mueve la cabeza.
- **Checklist sin errores:**
  - [ ] El NPC viene de un Dummy del Rig Builder o equivalente
  - [ ] Tiene `Humanoid`, `HumanoidRootPart`, `Animator` y `Motor6D`
  - [ ] El rig coincide con el de las animaciones

---

### 18. Detener todo al morir

- **Que es:** limpiar las animaciones y sus conexiones al morir el personaje.
- **Para que sirve:** evitar animaciones fantasma y fugas de memoria.
- **API implicada:** `Humanoid.Died`, `Animator:GetPlayingAnimationTracks`,
  `Instance.Destroying`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")

local function vigilar(personaje: Model)
    local humanoid = personaje:WaitForChild("Humanoid", 10) :: Humanoid?
    if not humanoid then
        return
    end

    local conexiones: { RBXScriptConnection } = {}

    local function limpiar()
        for _, c in conexiones do
            c:Disconnect()
        end
        table.clear(conexiones)

        local animator = humanoid:FindFirstChildOfClass("Animator")
        if animator then
            for _, pista in animator:GetPlayingAnimationTracks() do
                pista:Stop(0.1)
            end
        end
    end

    table.insert(conexiones, humanoid.Died:Connect(limpiar))
    table.insert(conexiones, personaje.Destroying:Connect(limpiar))
end

Players.PlayerAdded:Connect(function(jugador)
    jugador.CharacterAdded:Connect(vigilar)
end)
```

- **Errores frecuentes:**
  - No limpiar: cada respawn deja conexiones vivas y a los diez minutos el juego
    va a tirones.
  - Detener las pistas pero no desconectar los marcadores.
  - Guardar las pistas en una tabla global indexada por personaje y no borrar la
    entrada.
- **Checklist sin errores:**
  - [ ] Todas las conexiones se guardan y se desconectan
  - [ ] Las pistas se detienen en `Died` y en `Destroying`
  - [ ] Las tablas por personaje se vacian

---

## Por que no se reproduce mi animacion

Recorre esta lista en orden. El fallo esta casi siempre en los cuatro primeros
puntos.

| # | Comprobacion | Como se ve el fallo |
|---|---|---|
| 1 | El rig del JSON coincide con el rig del personaje | Solo se mueve la cabeza |
| 2 | La prioridad es suficiente | Se ve a medias, tembloroso, o no se ve |
| 3 | Se usa `Animator:LoadAnimation`, no `Humanoid:LoadAnimation` | Aviso de obsoleto y comportamiento raro |
| 4 | El `AnimationId` lleva `rbxassetid://` y el numero correcto | No pasa nada, sin error claro |
| 5 | La animacion la subio la misma cuenta o grupo que publica el juego | Error de carga en la salida |
| 6 | `Looped` esta como debe | Se reproduce una vez y se congela, o no para nunca |
| 7 | La pista no se recarga en cada pulsacion | La animacion se reinicia sin avanzar |
| 8 | El personaje tiene `Animator` | Nada responde |
| 9 | No hay otro script deteniendola | Arranca y se corta al instante |
| 10 | En Studio, la animacion esta publicada, no solo guardada en AnimSaves | Funciona en el editor y no en el juego |
| 11 | Si es un NPC, tiene `Motor6D` y `HumanoidRootPart` | Carga sin errores y no se mueve |
| 12 | La ultima pose del bucle es igual a la primera | Salto visible en cada ciclo |

---

## Checklist maestro de animacion

- [ ] El JSON pasa `revisar_pase.bat` sin errores
- [ ] El rig del JSON es el mismo del juego y del Dummy
- [ ] Si es bucle, primera pose igual a la ultima
- [ ] Las poses respetan los ejes de la tabla A.3
- [ ] `HumanoidRootPart` no aparece en ningun keyframe
- [ ] Las animaciones se cargan una vez y se guardan
- [ ] Las prioridades estan asignadas antes de `Play`
- [ ] Los marcadores se conectan una sola vez
- [ ] Todas las pistas se detienen al morir
- [ ] Las animaciones estan precargadas con `PreloadAsync`
- [ ] Probado en Play Solo y con dos jugadores

---

## Siguiente paso

Interfaz en `mecanicas/05-gui.md`. Combate que dispara estas animaciones en
`mecanicas/03-combate.md`. Errores concretos en
`mecanicas/09-errores-y-checklist.md`.
