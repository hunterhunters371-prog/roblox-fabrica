# Modulo 10: Mejoras extraidas del juego en produccion

Este modulo es distinto a los nueve anteriores. Los modulos 01 a 09 explican
mecanicas de Roblox en general. Este recoge **doce mecanicas que ya estan
funcionando** en el Place de Studio del proyecto, con los numeros reales que
quedaron despues de probarlas y corregirlas.

No son ideas. Son ajustes que sobrevivieron a la partida.

## De donde sale cada ficha

| Origen en Studio | Que aporta |
|---|---|
| `Workspace.EntregaFinalV3` (juego4) | Rondas, carga, deslizada, combo, camara, limites de servidor |
| `ServerScriptService.Reto67` | Ratio de accion, publicacion con cuentagotas, cierre por latido |
| `ServerScriptService.Economia` | Saldo blindado, cobro atomico, registro auditable |
| `Workspace.CoinRush` y su tienda | Power-ups guiados por tabla, fichas persistentes |

Cada ficha sigue el formato del catalogo: que es, para que sirve, API
implicada, donde va, codigo, errores frecuentes y checklist.

---

## Tabla de busqueda rapida

| Necesito | Ficha |
|---|---|
| Un medidor que sube al pulsar y baja solo | 10.1 |
| Replicar un valor que cambia cada frame sin inundar la red | 10.2 |
| Cerrar un temporizador sin que se dispare sobre la partida siguiente | 10.3 |
| Configurar cada objeto del mapa sin tocar el script | 10.4 |
| Que nadie pueda duplicar monedas | 10.5 |
| Una deslizada que rompa el techo de velocidad | 10.6 |
| Que llevar cosas encima pese de verdad | 10.7 |
| Que la dificultad suba dentro de la misma ronda | 10.8 |
| Pedidos urgentes y combo con ventana | 10.9 |
| Anticheat que no castigue al que tiene lag | 10.10 |
| Camara y animacion que reaccionan al estado | 10.11 |
| Power-ups sin escribir un `if` por cada uno | 10.12 |

---

## Ficha 10.1: Ratio de accion, el medidor que se desinfla

### Que es

Un valor de 0 a 1 que **sube un poco con cada pulsacion** y **baja solo con el
tiempo**. La nota final no es cuantas veces pulsaste, es la media de ese valor
sostenida durante todo el reto.

### Para que sirve

Un contador de pulsaciones premia una rafaga al final. Un ratio que se desinfla
premia mantener el ritmo, que es lo que de verdad se siente como esfuerzo. Ademas
se apaga solo si el jugador se detiene, sin necesidad de detectar el hueco entre
pulsaciones.

Numeros que quedaron tras probar:

| Constante | Valor | Que hace |
|---|---|---|
| `SUBIDA_POR_PAREJA` | 0.13 | Cuanto empuja cada pulsacion |
| `BAJADA_POR_SEGUNDO` | 0.55 | Cuanto se desinfla por segundo |
| `MEDIA_MINIMA` | 0.15 | Media que hay que sostener para cobrar |

Con esos dos primeros valores el equilibrio queda en unas cuatro pulsaciones por
segundo para mantenerse arriba. Si subes `BAJADA_POR_SEGUNDO` el reto se vuelve
agotador muy rapido.

### API implicada

`RunService.Heartbeat`, `Instance:SetAttribute`, `math.min`, `math.max`,
`math.clamp`, `workspace:GetServerTimeNow`

### Donde va

`ServerScriptService`, en un ModuleScript. El servidor decide, regla 1 del
catalogo. El cliente solo avisa de la pulsacion y dibuja la barra.

### Codigo

```lua
local ServicioEjecucion = game:GetService("RunService")

local SUBIDA_POR_PAREJA = 0.13
local BAJADA_POR_SEGUNDO = 0.55
local MEDIA_MINIMA = 0.15

local activos = {}

-- El cliente pulsa: solo empujamos el medidor hacia arriba.
local function alPulsar(jugador)
    local estado = activos[jugador]
    if not estado then
        return
    end
    estado.intensidad = math.min(estado.intensidad + SUBIDA_POR_PAREJA, 1)
end

ServicioEjecucion.Heartbeat:Connect(function(dt)
    for jugador, estado in activos do
        -- Si nadie pulsa, esto lo lleva a cero solo. No hace falta medir huecos.
        estado.intensidad = math.max(estado.intensidad - BAJADA_POR_SEGUNDO * dt, 0)

        -- La nota es la media sostenida, no el pico.
        estado.suma += estado.intensidad
        estado.muestras += 1
    end
end)

local function nota(estado)
    if estado.muestras == 0 then
        return 0, false
    end
    local media = estado.suma / estado.muestras
    return media, media >= MEDIA_MINIMA
end
```

El premio se escala con la media, no se paga entero:

```lua
local premio = math.floor(estado.premio * math.min(media, 1) + 0.5)
```

### Errores frecuentes

| Error | Causa | Solucion |
|---|---|---|
| El medidor se queda clavado en 1 | Falta el `math.min(..., 1)` en la subida | Acotar siempre arriba |
| La media sale altisima | Se suman muestras solo cuando el jugador pulsa | Sumar en el latido, tambien cuando esta a cero |
| Division por cero al terminar | El reto acaba en el mismo frame que empieza | Comprobar `muestras > 0` antes de dividir |
| Se puede cobrar con una rafaga final | Se guarda el pico en vez de la media | Guardar `suma` y `muestras`, nunca el maximo |

### Checklist

- [ ] La subida esta acotada a 1 con `math.min`
- [ ] La bajada esta acotada a 0 con `math.max`
- [ ] La bajada se multiplica por `dt`, no por un numero fijo
- [ ] Las muestras se acumulan en el latido, no en la pulsacion
- [ ] Se comprueba `muestras > 0` antes de dividir
- [ ] El premio se escala con la media

---

## Ficha 10.2: Publicacion con cuentagotas

### Que es

Un valor que cambia cada frame no se replica cada frame. Se publica solo si ha
cambiado lo suficiente **y** ha pasado un hueco minimo desde la ultima vez.

### Para que sirve

Un atributo que se escribe en el latido son sesenta replicaciones por segundo y
por jugador. Con ocho jugadores son casi quinientas. El cliente no necesita esa
resolucion porque ya interpola entre avisos.

| Constante | Valor | Que hace |
|---|---|---|
| `HUECO_PUBLICACION` | 0.08 s | Como maximo 12 avisos por segundo |
| `CAMBIO_MINIMO` | 0.02 | Por debajo de esto no merece la pena avisar |

Las dos condiciones tienen que cumplirse a la vez. Solo con el hueco, un valor
quieto sigue replicando. Solo con el cambio minimo, un valor nervioso replica en
cada frame.

### API implicada

`Instance:SetAttribute`, `workspace:GetServerTimeNow`, `math.abs`

### Donde va

En el mismo Script de servidor que calcula el valor.

### Codigo

```lua
local HUECO_PUBLICACION = 0.08
local CAMBIO_MINIMO = 0.02

local function publicar(jugador, personaje, estado, ahora)
    local salto = math.abs(estado.intensidad - estado.publicada)

    -- Las dos condiciones a la vez. Con una sola no sirve.
    if salto < CAMBIO_MINIMO then
        return
    end
    if ahora - estado.publicadaEn < HUECO_PUBLICACION then
        return
    end

    estado.publicada = estado.intensidad
    estado.publicadaEn = ahora

    personaje:SetAttribute("Intensidad", estado.intensidad)
    jugador:SetAttribute("Intensidad", estado.intensidad)
end
```

El estado arranca con `publicada = -1` a proposito, para que el primer valor
siempre supere `CAMBIO_MINIMO` y se publique sin esperar.

En el cliente, la barra se mueve suave aunque lleguen 12 avisos por segundo:

```lua
local ServicioEjecucion = game:GetService("RunService")

local mostrada = 0

ServicioEjecucion.RenderStepped:Connect(function(dt)
    local objetivo = jugador:GetAttribute("Intensidad") or 0
    -- Interpolacion exponencial: independiente de los FPS.
    mostrada += (objetivo - mostrada) * math.min(dt * 12, 1)
    barra.Size = UDim2.fromScale(mostrada, 1)
end)
```

### Errores frecuentes

| Error | Causa | Solucion |
|---|---|---|
| La barra va a saltos | El cliente lee el atributo sin interpolar | Interpolar en `RenderStepped` |
| El primer valor tarda en aparecer | `publicada` arranca en 0 igual que el valor | Arrancar en -1 |
| Sigue replicando con el valor quieto | Solo se comprueba el hueco de tiempo | Comprobar tambien el cambio minimo |
| El valor final no llega | Se cierra sin publicar el ultimo | Publicar siempre al terminar, sin condiciones |

### Checklist

- [ ] Se comprueban cambio minimo y hueco de tiempo a la vez
- [ ] `publicada` arranca en un valor imposible, como -1
- [ ] Al cerrar se publica el valor final sin condiciones
- [ ] El cliente interpola con `dt`, no asigna directamente
- [ ] La interpolacion esta acotada con `math.min(dt * k, 1)`

---

## Ficha 10.3: Cerrar por latido, nunca por task.delay

### Que es

Un reto o una ronda con duracion fija se cierra comprobando el reloj en el
latido, no programando un `task.delay` a los diez segundos.

### Para que sirve

Un `task.delay` no se puede cancelar. Si el jugador empieza un reto, lo
abandona y empieza otro, el delay del primero se dispara **encima del segundo** y
lo cierra antes de tiempo. Es un fallo que solo aparece cuando alguien juega
rapido, o sea en cuanto lo publicas.

### API implicada

`RunService.Heartbeat`, `workspace:GetServerTimeNow`, `Players.PlayerRemoving`

### Donde va

`ServerScriptService`.

### Codigo

```lua
local ServicioEjecucion = game:GetService("RunService")
local Jugadores = game:GetService("Players")

local activos = {}

local function iniciar(jugador, segundos)
    -- Regla 9 del catalogo: se guarda el instante de fin, no un contador.
    -- GetServerTimeNow esta sincronizado entre servidor y clientes.
    activos[jugador] = {
        fin = workspace:GetServerTimeNow() + segundos,
        personaje = jugador.Character,
    }
    jugador:SetAttribute("Fin", activos[jugador].fin)
end

ServicioEjecucion.Heartbeat:Connect(function()
    local ahora = workspace:GetServerTimeNow()

    for jugador, estado in activos do
        local personaje = jugador.Character
        local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")

        if not jugador.Parent then
            -- Se fue: limpiar sin pagar.
            activos[jugador] = nil
        elseif personaje ~= estado.personaje or not humanoide or humanoide.Health <= 0 then
            -- Murio o reaparecio: el reto se cae con el personaje.
            terminar(jugador)
        elseif ahora >= estado.fin then
            terminar(jugador)
        end
    end
end)

Jugadores.PlayerRemoving:Connect(function(jugador)
    activos[jugador] = nil
end)
```

Guardar `estado.personaje` y compararlo con `jugador.Character` es lo que detecta
el respawn. Sin esa comparacion, el reto sigue vivo sobre un personaje que ya no
existe.

### Errores frecuentes

| Error | Causa | Solucion |
|---|---|---|
| Un reto se cierra solo antes de tiempo | El `task.delay` del reto anterior | Cerrar en el latido |
| El contador se desincroniza | Se resta `dt` a un contador local | Guardar el instante de fin |
| El reto sigue tras morir | No se compara el personaje guardado | Comparar `personaje ~= estado.personaje` |
| Fuga de memoria | No se limpia al salir el jugador | Limpiar en `PlayerRemoving` |
| El cliente y el servidor no coinciden | Se usa `os.time` o `tick` | Usar `workspace:GetServerTimeNow` |

### Checklist

- [ ] No hay ningun `task.delay` gobernando el cierre
- [ ] Se guarda el instante de fin, no un contador
- [ ] El instante viene de `workspace:GetServerTimeNow()`
- [ ] Se compara el personaje guardado con el actual
- [ ] Se limpia en `PlayerRemoving`

---

## Ficha 10.4: Atributos por instancia con defecto y tope

### Que es

Cada objeto del mapa lleva su propia configuracion en atributos. El script tiene
valores por defecto y **acota** lo que lee, para que un atributo mal puesto no
rompa la partida.

### Para que sirve

Asi pones veinte puertas con premios distintos sin duplicar el script ni tocar
codigo. Y como el atributo lo puede editar cualquiera en Studio, el script no se
lo puede creer.

### API implicada

`Instance:GetAttribute`, `typeof`, `math.clamp`, `math.floor`

### Donde va

En el Script de servidor que gobierna esos objetos.

### Codigo

```lua
-- Lee un atributo numerico con valor por defecto y tope. El chequeo
-- valor ~= valor es el que caza los nan: un nan se cuela por cualquier
-- comparacion sin quejarse y luego contamina todas las cuentas.
local function numeroDe(instancia, nombre, defecto, minimo, maximo)
    if not instancia then
        return defecto
    end

    local valor = instancia:GetAttribute(nombre)
    if typeof(valor) ~= "number" or valor ~= valor then
        return defecto
    end

    return math.clamp(valor, minimo, maximo)
end

-- Uso: cada puerta puede traer TiempoReto y PremioReto en sus atributos.
local tiempo = numeroDe(modelo, "TiempoReto", 10, 2, 60)
local premio = math.floor(numeroDe(modelo, "PremioReto", 150, 0, 100000))
```

### Errores frecuentes

| Error | Causa | Solucion |
|---|---|---|
| El premio sale astronomico | Se confia en el atributo tal cual | Acotar con `math.clamp` |
| Todas las cuentas dan `nan` | Un atributo trae `nan` | Comprobar `valor ~= valor` |
| Error al comparar | El atributo es texto | Comprobar `typeof(valor) ~= "number"` |
| Premios con decimales | Falta redondear | `math.floor` en los enteros |
| El atributo no existe y todo falla | No hay valor por defecto | Devolver `defecto` si es `nil` |

### Checklist

- [ ] Hay valor por defecto para cada atributo
- [ ] Se comprueba el tipo con `typeof`
- [ ] Se cazan los `nan` con `valor ~= valor`
- [ ] Se acota con `math.clamp`
- [ ] Los valores enteros pasan por `math.floor`

---

## Ficha 10.5: Economia blindada, cobro atomico y registro auditable

### Que es

Un unico modulo es la puerta de entrada para tocar el saldo. La verdad vive en
una tabla del servidor; `leaderstats` y el atributo son solo un **reflejo** para
que la lista de jugadores y la interfaz puedan leerlos.

### Para que sirve

Si quince scripts suman monedas por su cuenta no se puede auditar nada, y en
cuanto uno se equivoca no hay forma de saber cual fue. Ademas el cobro tiene que
comprobar y descontar **sin esperas en medio**, o dos peticiones seguidas gastan
el mismo dinero dos veces.

Esto amplia la ficha 08.02 del catalogo con el blindaje que hizo falta de verdad.

### API implicada

`Players.PlayerAdded`, `Players.PlayerRemoving`, `Instance:SetAttribute`,
`IntValue`, `math.floor`, `math.min`, `os.time`

### Donde va

`ServerScriptService`, en un ModuleScript. Nunca en `ReplicatedStorage`: el
cliente no debe poder leerlo.

### Codigo

```lua
local Jugadores = game:GetService("Players")

local Economia = {}

local MAXIMO = 1000000000
local MAXIMO_REGISTRO = 200

local saldos = {}
local registro = {}

-- leaderstats es un REFLEJO. La verdad vive en saldos.
local function reflejar(jugador, saldo)
    jugador:SetAttribute("Monedas", saldo)

    local stats = jugador:FindFirstChild("leaderstats")
    local valor = stats and stats:FindFirstChild("Monedas")
    if valor and valor:IsA("IntValue") then
        valor.Value = saldo
    end
end

local function anotar(jugador, cambio, motivo)
    table.insert(registro, {
        jugador = jugador.Name,
        cambio = cambio,
        motivo = motivo,
        momento = os.time(),
    })

    -- Sin tope, una partida larga se come la memoria en historial.
    while #registro > MAXIMO_REGISTRO do
        table.remove(registro, 1)
    end
end

-- Ni texto, ni nan, ni infinito, ni cero, ni negativo.
local function cantidadValida(cantidad)
    if typeof(cantidad) ~= "number" then
        return false
    end
    if cantidad ~= cantidad then
        return false
    end
    if cantidad == math.huge or cantidad == -math.huge then
        return false
    end
    return cantidad > 0
end

-- Comprobar y descontar pasan aqui juntos y sin esperas en medio. Separados,
-- dos peticiones seguidas gastan el mismo dinero dos veces.
function Economia.cobrar(jugador, cantidad, motivo)
    if not cantidadValida(cantidad) then
        return false
    end

    local coste = math.floor(cantidad)
    local actual = saldos[jugador] or 0
    if actual < coste then
        return false
    end

    saldos[jugador] = actual - coste
    reflejar(jugador, saldos[jugador])
    anotar(jugador, -coste, motivo or "sin motivo")
    return true
end

function Economia.anadir(jugador, cantidad, motivo)
    if not cantidadValida(cantidad) then
        warn("Economia: cantidad invalida al anadir: " .. tostring(cantidad))
        return false
    end

    local suma = math.floor(cantidad)
    saldos[jugador] = math.min((saldos[jugador] or 0) + suma, MAXIMO)
    reflejar(jugador, saldos[jugador])
    anotar(jugador, suma, motivo or "sin motivo")
    return true
end

return Economia
```

Detalle que se olvida: el modulo puede cargarse **despues** de que alguien ya
haya entrado, asi que no basta con conectar `PlayerAdded`.

```lua
Jugadores.PlayerAdded:Connect(preparar)

for _, jugador in Jugadores:GetPlayers() do
    task.spawn(preparar, jugador)
end
```

### Errores frecuentes

| Error | Causa | Solucion |
|---|---|---|
| Se gasta el mismo dinero dos veces | Hay un `task.wait` entre comprobar y descontar | Todo dentro de la misma funcion sin esperas |
| El saldo se puede editar desde el cliente | La verdad esta en `leaderstats` | La verdad en una tabla del servidor |
| El saldo se vuelve `nan` | No se valida la cantidad | `cantidadValida` con el chequeo de `nan` |
| Se puede sumar en negativo para robar | Solo se comprueba el tipo | Exigir `cantidad > 0` |
| El servidor se queda sin memoria | El registro crece sin tope | `MAXIMO_REGISTRO` y `table.remove` |
| El primer jugador no tiene saldo | Solo se conecta `PlayerAdded` | Recorrer `GetPlayers` al cargar |

### Checklist

- [ ] Un solo modulo toca el saldo
- [ ] El modulo vive en `ServerScriptService`
- [ ] `leaderstats` es reflejo, no fuente de verdad
- [ ] `cobrar` comprueba y descuenta sin esperas en medio
- [ ] Se rechaza texto, `nan`, infinito, cero y negativo
- [ ] El registro tiene tope
- [ ] Se recorre `GetPlayers` al cargar el modulo

---

## Ficha 10.6: Deslizada que rompe el techo de velocidad y cuesta aire

### Que es

Una rafaga corta que va **por encima** de la velocidad de carrera, cuesta
resistencia de golpe y tiene enfriamiento propio.

### Para que sirve

Si la deslizada va a la misma velocidad que correr, nadie la usa. Si es gratis,
nadie deja de usarla. El coste fijo mas el enfriamiento la convierten en una
decision.

Numeros que quedaron:

| Constante | Valor |
|---|---|
| `VELOCIDAD_BASE` | 18 |
| `VELOCIDAD_CARRERA` | 31 |
| `VELOCIDAD_DESLIZADA` | 44 |
| `SEGUNDOS_DESLIZADA` | 0.75 |
| `COSTE_DESLIZADA` | 22 |
| `ENFRIAMIENTO_DESLIZADA` | 1.6 |
| `RESISTENCIA_MAXIMA` | 100 |
| `GASTO_CARRERA` | 27 por segundo |
| `RECUPERACION` | 19 por segundo |
| `MINIMO_PARA_CORRER` | 12 |

El coste de 22 sobre 100 permite cuatro deslizadas seguidas como maximo, y el
enfriamiento de 1.6 s las separa lo justo para que no sean una forma de volar.

`MINIMO_PARA_CORRER` mayor que cero evita el tartamudeo clasico: sin ese umbral,
el jugador alterna correr y andar cada frame al quedarse sin aire.

### API implicada

`Humanoid.WalkSpeed`, `Humanoid.JumpPower`, `RunService.Heartbeat`, `os.clock`

### Donde va

El estado y la velocidad los aplica el **servidor**. El cliente solo pide
`deslizar`.

### Codigo

```lua
local function pedirDeslizada(estado, ahora)
    if estado.deslizando then
        return false
    end
    if ahora - estado.ultimaDeslizada < ENFRIAMIENTO_DESLIZADA then
        return false
    end
    if estado.resistencia < COSTE_DESLIZADA then
        return false
    end

    estado.resistencia -= COSTE_DESLIZADA
    estado.deslizando = true
    estado.finDeslizada = ahora + SEGUNDOS_DESLIZADA
    estado.ultimaDeslizada = ahora
    return true
end

local function velocidadDe(estado)
    if estado.deslizando then
        return VELOCIDAD_DESLIZADA
    end
    if estado.corriendo and estado.resistencia > MINIMO_PARA_CORRER then
        return VELOCIDAD_CARRERA
    end
    return VELOCIDAD_BASE
end
```

### Errores frecuentes

| Error | Causa | Solucion |
|---|---|---|
| Deslizada infinita | El enfriamiento se mide desde el fin, no desde el inicio | Guardar `ultimaDeslizada` al iniciar |
| El jugador tartamudea entre correr y andar | No hay umbral minimo | `MINIMO_PARA_CORRER` mayor que cero |
| La deslizada no se nota | Va a la misma velocidad que correr | Que supere la carrera de forma clara |
| Se puede deslizar en el aire sin parar | No se comprueba el estado | Exigir suelo antes de conceder |
| Se cuela por el remote | El cliente aplica su propia velocidad | Solo el servidor escribe `WalkSpeed` |

### Checklist

- [ ] La velocidad de deslizada supera claramente la de carrera
- [ ] El coste se descuenta al iniciar, no al terminar
- [ ] El enfriamiento se mide desde el inicio
- [ ] Hay umbral minimo de resistencia para correr
- [ ] Solo el servidor escribe `WalkSpeed`

---

## Ficha 10.7: Penalizacion por carga, el inventario pesa

### Que es

Cada objeto que el jugador lleva encima le resta velocidad y altura de salto.

### Para que sirve

Convierte "llevo tres cajas" en una decision de riesgo. Sin esto, siempre
conviene llevar el maximo, y el maximo deja de significar nada.

| Constante | Valor |
|---|---|
| `CAJAS_MAXIMAS` | 3 |
| `PENALIZACION_POR_CAJA` | 2.6 de velocidad |
| `PENALIZACION_SALTO` | 4 de `JumpPower` |
| `SALTO_BASE` | 50 |
| `PUNTOS_POR_CAJA` | 60 |
| `BONUS_LOTE` | 45 por entregar el lote completo |

Con tres cajas la velocidad baja 7.8 y el salto 12. El `BONUS_LOTE` es lo que
hace que valga la pena arriesgarse a ir cargado.

### API implicada

`Humanoid.WalkSpeed`, `Humanoid.JumpPower`, `math.max`

### Donde va

`ServerScriptService` o el Script de servidor del juego.

### Codigo

```lua
local function aplicarCarga(humanoide, estado)
    local carga = math.clamp(estado.cajas, 0, CAJAS_MAXIMAS)

    -- El math.max evita que una carga grande deje al jugador clavado en el sitio.
    humanoide.WalkSpeed = math.max(velocidadDe(estado) - PENALIZACION_POR_CAJA * carga, 6)
    humanoide.JumpPower = math.max(SALTO_BASE - PENALIZACION_SALTO * carga, 12)
end
```

### Errores frecuentes

| Error | Causa | Solucion |
|---|---|---|
| El jugador se queda inmovil | La penalizacion supera la velocidad base | Suelo con `math.max` |
| No puede saltar nada | Mismo problema con `JumpPower` | Suelo tambien en el salto |
| Se acumulan mas cajas que el maximo | No se acota al recoger | `math.clamp` con `CAJAS_MAXIMAS` |
| La penalizacion no se quita al entregar | Solo se aplica al recoger | Recalcular en cada cambio de carga |
| `JumpPower` no hace nada | `UseJumpPower` esta en falso | Poner `humanoide.UseJumpPower = true` |

### Checklist

- [ ] La carga esta acotada con `math.clamp`
- [ ] Velocidad y salto tienen suelo con `math.max`
- [ ] Se recalcula al recoger y al entregar
- [ ] `UseJumpPower` esta activo si se toca `JumpPower`
- [ ] Hay bonus por lote completo que compense el riesgo

---

## Ficha 10.8: Ritmo de ronda, la dificultad sube dentro de la partida

### Que es

Cada cierto tiempo dentro de la misma ronda, los objetivos **valen mas** y
**duran menos**.

### Para que sirve

Una ronda de 90 segundos con dificultad constante se siente igual al principio
que al final. Con el ritmo, los ultimos veinte segundos son los que deciden la
puntuacion.

| Constante | Valor |
|---|---|
| `SEGUNDOS_RONDA` | 90 |
| `SEGUNDOS_DESCANSO` | 12 |
| `SEGUNDOS_INTRO` | 7 |
| `SEGUNDOS_RITMO` | 20 |
| `SUBIDA_RITMO` | 0.18 |
| `RECORTE_RITMO` | 4 segundos |

En una ronda de 90 s con paso de 20 s hay cuatro escalones. Al ultimo, los
pedidos valen un 72 por ciento mas y duran 16 segundos menos.

### API implicada

`workspace:GetServerTimeNow`, `math.floor`, `math.max`

### Donde va

`ServerScriptService`.

### Codigo

```lua
local function escalonActual(inicioRonda, ahora)
    return math.floor((ahora - inicioRonda) / SEGUNDOS_RITMO)
end

local function valorDelPedido(base, escalon)
    return math.floor(base * (1 + SUBIDA_RITMO * escalon) + 0.5)
end

local function duracionDelPedido(base, escalon)
    -- El suelo es obligatorio: sin el, a los 100 segundos la duracion es negativa
    -- y el pedido caduca en el mismo frame en que nace.
    return math.max(base - RECORTE_RITMO * escalon, 6)
end
```

### Errores frecuentes

| Error | Causa | Solucion |
|---|---|---|
| Los pedidos caducan al nacer | La duracion llega a cero o negativa | Suelo con `math.max` |
| La puntuacion se dispara | La subida es multiplicativa por escalon | Subida lineal sobre la base |
| El escalon salta al reaparecer | Se guarda el escalon en vez de calcularlo | Calcularlo desde el inicio de ronda |
| Cada jugador ve un escalon distinto | Se usa el reloj del cliente | `workspace:GetServerTimeNow` |

### Checklist

- [ ] El escalon se calcula, no se guarda
- [ ] La duracion tiene suelo
- [ ] La subida de valor es lineal sobre la base
- [ ] El reloj es el del servidor
- [ ] Hay descanso e intro entre rondas

---

## Ficha 10.9: Pedidos urgentes y combo con ventana

### Que es

Dos multiplicadores distintos que se combinan: el **urgente** es un pedido que
vale el triple pero dura casi la mitad, y el **combo** premia entregar seguido.

### Para que sirve

El urgente crea picos de tension puntuales. El combo premia la constancia. Los
dos juntos hacen que la partida tenga ritmo propio sin tocar la dificultad base.

| Constante | Valor |
|---|---|
| `PEDIDOS_ACTIVOS` | 3 |
| `SEGUNDOS_PEDIDO` | 27 |
| `SEGUNDOS_PEDIDO_URGENTE` | 15 |
| `PROBABILIDAD_URGENTE` | 0.24 |
| `MULTIPLICADOR_URGENTE` | 3 |
| `SEGUNDOS_COMBO` | 12 |
| `COMBO_MAXIMO` | 6 |
| `BONUS_COMBO` | 0.25 por escalon |

Con `COMBO_MAXIMO` 6 y `BONUS_COMBO` 0.25, el techo del combo es un 125 por
ciento extra. El tope existe para que una racha no rompa la tabla de records.

### API implicada

`Random.new`, `workspace:GetServerTimeNow`, `math.min`, `math.floor`

### Donde va

`ServerScriptService`.

### Codigo

```lua
-- Un solo Random por servidor. math.random global comparte estado con
-- cualquier otro script que lo use y se vuelve impredecible de depurar.
local azar = Random.new()

local function crearPedido(escalon)
    local urgente = azar:NextNumber() < PROBABILIDAD_URGENTE
    local base = urgente and SEGUNDOS_PEDIDO_URGENTE or SEGUNDOS_PEDIDO

    return {
        urgente = urgente,
        multiplicador = urgente and MULTIPLICADOR_URGENTE or 1,
        caduca = workspace:GetServerTimeNow() + duracionDelPedido(base, escalon),
    }
end

local function registrarEntrega(estado, ahora)
    -- La ventana se mide desde la ultima entrega, no desde el inicio del combo.
    if ahora - estado.ultimaEntrega <= SEGUNDOS_COMBO then
        estado.combo = math.min(estado.combo + 1, COMBO_MAXIMO)
    else
        estado.combo = 1
    end
    estado.ultimaEntrega = ahora
end

local function puntosDe(pedido, estado, escalon)
    local base = valorDelPedido(PUNTOS_ENTREGA, escalon)
    local factorCombo = 1 + BONUS_COMBO * (estado.combo - 1)
    return math.floor(base * pedido.multiplicador * factorCombo + 0.5)
end
```

### Errores frecuentes

| Error | Causa | Solucion |
|---|---|---|
| El combo nunca se rompe | La ventana se mide desde el inicio del combo | Medir desde la ultima entrega |
| El combo empieza en cero y no suma | El primer escalon es 1, no 0 | `estado.combo = 1` en la primera entrega |
| Puntuaciones absurdas | El combo no tiene tope | `math.min` con `COMBO_MAXIMO` |
| Salen todos urgentes | Se compara mal la probabilidad | `NextNumber() < PROBABILIDAD_URGENTE` |
| La aleatoriedad se repite | `math.random` global sin semilla propia | Un `Random.new()` por sistema |

### Checklist

- [ ] La ventana del combo se mide desde la ultima entrega
- [ ] El combo tiene tope
- [ ] El primer escalon del combo vale 1
- [ ] Hay un `Random.new()` propio
- [ ] El urgente dura menos y vale mas, las dos cosas

---

## Ficha 10.10: Anticheat con avisos antes de corregir

### Que es

El servidor vigila velocidad y frecuencia de llamadas, pero **no corrige al
primer aviso**. Acumula unos cuantos antes de actuar. Y solo acepta acciones que
esten en una lista blanca.

### Para que sirve

Un anticheat que corrige al primer frame raro castiga al jugador con lag, que es
la mayoria. Los avisos acumulados distinguen una conexion mala de un cliente
tocado.

| Constante | Valor | Que hace |
|---|---|---|
| `ENFRIAMIENTO_TOQUE` | 0.3 s | Minimo entre dos toques del mismo jugador |
| `LLAMADAS_POR_SEGUNDO` | 6 | Techo del remote |
| `MARGEN_VELOCIDAD` | 1.7 | Cuanto se tolera sobre la velocidad legal |
| `AVISOS_ANTES_DE_CORREGIR` | 3 | Avisos acumulados antes de actuar |

Esto amplia la ficha 08.22 del catalogo.

### API implicada

`os.clock`, `RemoteEvent.OnServerEvent`, `Humanoid.WalkSpeed`,
`Model:PivotTo`, `Players.PlayerRemoving`

### Donde va

`ServerScriptService`.

### Codigo

Limite de frecuencia por ventana de un segundo:

```lua
local contadores = {}

local function permitido(jugador, porSegundo)
    local ahora = os.clock()
    local registro = contadores[jugador]

    if not registro or ahora - registro.ventana >= 1 then
        contadores[jugador] = { veces = 1, ventana = ahora }
        return true
    end

    if registro.veces >= porSegundo then
        return false
    end

    registro.veces += 1
    return true
end
```

Lista blanca de acciones. Cualquier cosa que no este aqui se descarta sin
responder:

```lua
local ACCIONES = {
    empezar = true,
    soltar = true,
    correr = true,
    andar = true,
    deslizar = true,
}

aviso.OnServerEvent:Connect(function(jugador, accion)
    if not permitido(jugador, LLAMADAS_POR_SEGUNDO) then
        return
    end
    -- typeof primero: una tabla como indice tambien indexa sin error.
    if typeof(accion) ~= "string" or not ACCIONES[accion] then
        return
    end

    atender(jugador, accion)
end)
```

Avisos acumulados antes de corregir la posicion:

```lua
local function vigilarVelocidad(estado, humanoide, raiz, dt)
    local legal = velocidadDe(estado) * MARGEN_VELOCIDAD
    local real = raiz.AssemblyLinearVelocity.Magnitude

    if real <= legal then
        estado.avisos = 0
        estado.ultimaBuena = raiz.CFrame
        return
    end

    estado.avisos += 1
    if estado.avisos < AVISOS_ANTES_DE_CORREGIR then
        return
    end

    estado.avisos = 0
    if estado.ultimaBuena then
        raiz.CFrame = estado.ultimaBuena
    end
end
```

### Errores frecuentes

| Error | Causa | Solucion |
|---|---|---|
| Los jugadores con lag se teletransportan atras | Se corrige al primer aviso | Acumular avisos |
| El anticheat no detecta nada | El margen es demasiado alto | Bajar `MARGEN_VELOCIDAD` hacia 1.5 |
| Error al indexar la lista blanca | Llega una tabla en vez de texto | `typeof` antes de indexar |
| Se usa `part.Velocity` y da aviso | API obsoleta | `AssemblyLinearVelocity` |
| Fuga de memoria en los contadores | No se limpian al salir | Limpiar en `PlayerRemoving` |
| El contador nunca se reinicia | La ventana no se compara con 1 segundo | Reiniciar cuando la ventana caduca |

### Checklist

- [ ] Hay lista blanca de acciones
- [ ] Se comprueba `typeof` antes de indexar la lista
- [ ] Hay limite de frecuencia por ventana
- [ ] Se acumulan avisos antes de corregir
- [ ] Se guarda la ultima posicion buena
- [ ] Se usa `AssemblyLinearVelocity`, no `Velocity`
- [ ] Los contadores se limpian en `PlayerRemoving`

---

## Ficha 10.11: Camara y animacion que reaccionan al estado

### Que es

El campo de vision, el cabeceo, el ladeo, la inclinacion del cuerpo y la
velocidad de las animaciones cambian segun lo que este haciendo el jugador.

### Para que sirve

Es lo que hace que correr **se sienta** rapido sin cambiar la velocidad real.
Es la mejora con mejor relacion entre esfuerzo y resultado de toda la lista.

| Constante | Valor |
|---|---|
| `CAMPO_VISION` | 70 |
| `CAMPO_VISION_CARRERA` | 87 |
| `CAMPO_VISION_DESLIZADA` | 97 |
| `CABECEO` | 0.85 |
| `LADEO_MAXIMO` | 4.5 grados |
| `LADEO_DESLIZADA` | 7 grados |
| `INCLINACION_CUERPO` | -9 grados |
| `VELOCIDAD_ANIMACION_CARRERA` | 1.3 |
| `VELOCIDAD_ANIMACION_DESLIZADA` | 1.6 |
| `MEZCLA_ANIMACION` | 0.15 s |

El signo de `INCLINACION_CUERPO` depende del rig. Si el personaje se echa hacia
atras en vez de hacia delante, cambia el signo.

### API implicada

`Camera.FieldOfView`, `RunService.RenderStepped`, `AnimationTrack:AdjustSpeed`,
`AnimationTrack:Play`, `CFrame.Angles`, `math.rad`

### Donde va

`StarterPlayerScripts`, en un LocalScript. Todo esto lo aplica **el cliente**
sobre su propia camara: no es informacion que el servidor deba gobernar.

### Codigo

```lua
local ServicioEjecucion = game:GetService("RunService")
local camara = workspace.CurrentCamera

local fovMostrado = CAMPO_VISION

local function fovObjetivo(estado)
    if estado.deslizando then
        return CAMPO_VISION_DESLIZADA
    end
    if estado.corriendo then
        return CAMPO_VISION_CARRERA
    end
    return CAMPO_VISION
end

ServicioEjecucion.RenderStepped:Connect(function(dt)
    -- Interpolar, nunca asignar de golpe: un salto de FOV marea.
    local objetivo = fovObjetivo(estado)
    fovMostrado += (objetivo - fovMostrado) * math.min(dt * 6, 1)
    camara.FieldOfView = fovMostrado
end)
```

Las pistas propias se identifican por nombre para no pisar las animaciones por
defecto de Roblox:

```lua
local PISTAS_PROPIAS = { "Caminar", "Correr", "Deslizada" }

local function esPistaPropia(nombre)
    for _, propia in PISTAS_PROPIAS do
        if nombre == propia then
            return true
        end
    end
    return false
end

-- Animator:LoadAnimation, no Humanoid:LoadAnimation. La segunda esta obsoleta.
local pista = animador:LoadAnimation(animacion)
pista:Play(MEZCLA_ANIMACION)
pista:AdjustSpeed(VELOCIDAD_ANIMACION_CARRERA)
```

### Errores frecuentes

| Error | Causa | Solucion |
|---|---|---|
| El FOV pega saltos y marea | Se asigna de golpe | Interpolar con `dt` |
| El personaje se echa hacia atras al correr | El signo de la inclinacion depende del rig | Cambiar el signo |
| La animacion no se reproduce | Se usa `Humanoid:LoadAnimation` | `Animator:LoadAnimation` |
| Se pisan las animaciones por defecto | No se filtran las pistas propias | Filtrar por nombre |
| El ladeo se acumula y gira el mundo | Se suma al `CFrame` en vez de recomponerlo | Recomponer desde el angulo objetivo |
| Los angulos no hacen nada | Falta `math.rad` | Regla 6 del catalogo |

### Checklist

- [ ] El FOV se interpola, no se asigna
- [ ] La interpolacion esta acotada con `math.min(dt * k, 1)`
- [ ] Los angulos pasan por `math.rad`
- [ ] Se usa `Animator:LoadAnimation`
- [ ] Las pistas propias se filtran por nombre
- [ ] Todo esto corre en el cliente

---

## Ficha 10.12: Power-ups guiados por tabla con inventario persistente

### Que es

Los power-ups no son doce `if`. Son una **tabla de datos** donde el orden define
la tecla y la posicion en la barra. Anadir uno nuevo es anadir una fila.

### Para que sirve

El cliente y el servidor leen la misma tabla desde `ReplicatedStorage`, asi que
la barra de la interfaz, las teclas, los costes y los efectos no se pueden
desincronizar.

| Constante | Valor | Que hace |
|---|---|---|
| `FichasPorMonedas` | 50 | Monedas recogidas para ganar 1 ficha |
| `FichasPorVictoria` | 5 | Fichas extra por ganar la ronda |
| `MaxInventario` | 5 | Tope de cada power-up guardado |
| `RadioIman` | 14 studs | Radio del campo del iman |
| `SuperSaltoPower` | 100 | `JumpPower` durante el efecto |
| `SaltoNormal` | 50 | Valor al que hay que volver |
| `AutoguardadoSegundos` | 120 | Intervalo de guardado |

### API implicada

`ReplicatedStorage`, `Enum.KeyCode`, `UserInputService.InputBegan`,
`DataStoreService`, `task.delay`

### Donde va

La tabla en `ReplicatedStorage`, en un ModuleScript. El efecto en
`ServerScriptService`. Las teclas en `StarterPlayerScripts`.

### Codigo

La tabla compartida:

```lua
local Config = {}

Config.FichasPorMonedas = 50
Config.MaxInventario = 5
Config.RadioIman = 14
Config.SuperSaltoPower = 100
Config.SaltoNormal = 50

-- El orden define la tecla y la posicion en la barra.
Config.Items = {
    {
        Id = "Iman",
        Nombre = "Iman",
        Descripcion = "Atrae las monedas cercanas durante 12 s",
        Costo = 3,
        Duracion = 12,
        Color = Color3.fromRGB(80, 220, 255),
        Tecla = Enum.KeyCode.One,
    },
    {
        Id = "Doble",
        Nombre = "Doble Monedas",
        Descripcion = "Duplica cada moneda recogida durante 15 s",
        Costo = 5,
        Duracion = 15,
        Color = Color3.fromRGB(255, 215, 0),
        Tecla = Enum.KeyCode.Two,
    },
    {
        Id = "SuperSalto",
        Nombre = "Super Salto",
        Descripcion = "Salta mucho mas alto durante 20 s",
        Costo = 2,
        Duracion = 20,
        Color = Color3.fromRGB(120, 255, 120),
        Tecla = Enum.KeyCode.Three,
    },
}

return Config
```

La barra y las teclas se construyen recorriendo la tabla:

```lua
for indice, item in Config.Items do
    crearRanura(indice, item.Nombre, item.Color, item.Tecla)
end
```

El efecto temporal se apaga comparando un identificador, no con un `task.delay`
suelto:

```lua
local function activar(jugador, item)
    local estado = efectos[jugador]
    estado.turno += 1
    local turno = estado.turno

    aplicar(jugador, item.Id, true)

    task.delay(item.Duracion, function()
        -- Si el jugador volvio a activarlo, este turno ya no manda.
        if efectos[jugador] and efectos[jugador].turno == turno then
            aplicar(jugador, item.Id, false)
        end
    end)
end
```

### Errores frecuentes

| Error | Causa | Solucion |
|---|---|---|
| El `JumpPower` se queda en 100 para siempre | Se apago un efecto que ya se habia renovado | Comparar el turno antes de apagar |
| Se acumulan power-ups sin limite | No se aplica `MaxInventario` | Acotar al comprar |
| La tecla no coincide con la barra | Se escriben las teclas a mano | Sacarlas del orden de la tabla |
| El iman atrae todo el mapa | El radio se mide mal | Comparar `Magnitude` con `RadioIman` |
| Se pierde el inventario al salir | Solo hay autoguardado | Guardar tambien en `PlayerRemoving` |
| El cliente decide si tiene el item | La comprobacion esta en el LocalScript | El servidor comprueba y descuenta |

### Checklist

- [ ] La tabla vive en `ReplicatedStorage` y la leen los dos lados
- [ ] El orden de la tabla define tecla y posicion
- [ ] El inventario esta acotado con `MaxInventario`
- [ ] Los efectos temporales comparan turno antes de apagarse
- [ ] El servidor comprueba y descuenta, el cliente solo pide
- [ ] Se guarda en `PlayerRemoving`, no solo en el autoguardado

---

## Trampas transversales

Tres cosas que aparecieron al integrar todo esto y que no encajan en una sola
ficha.

### Un ModuleScript de constantes requerido dos veces son dos instancias

Si el servidor y el cliente hacen `require` del mismo modulo de configuracion,
cada lado recibe **su propia copia**. Sirve para constantes. No sirve como estado
compartido: escribir un valor en el cliente no lo cambia en el servidor.

Si necesitas estado compartido, usa atributos o remotes, nunca un modulo.

### Sonidos del cliente de Roblox, nada subido

Todos los sonidos del juego salen de `rbxasset://sounds/`, que ya viene con el
cliente. No hay que subir nada, no hay que esperar moderacion y no fallan en
Studio.

| Uso | Recurso |
|---|---|
| Recoger | `rbxasset://sounds/switch3.wav` |
| Entrega | `rbxasset://sounds/electronicpingshort.wav` |
| Urgente | `rbxasset://sounds/clickfast.wav` |
| Inicio | `rbxasset://sounds/unsheath.wav` |
| Fin | `rbxasset://sounds/bass.wav` |
| Deslizada | `rbxasset://sounds/switch.wav` |

### Las vinetas de la interfaz van en escala, no en pixeles

Una franja lateral definida en pixeles fijos deja franjas negras con corte duro
en pantallas anchas. En escala se adapta sola.

```lua
-- Mal: 260 pixeles fijos a cada lado.
UDim2.new(0, 260, 1, 0)

-- Bien: 13 por ciento del ancho.
UDim2.fromScale(0.13, 1)
```

Y el degradado necesita un punto intermedio para que el corte no se vea:

```lua
degradado.Transparency = NumberSequence.new({
    NumberSequenceKeypoint.new(0, 0),
    NumberSequenceKeypoint.new(0.45, 0.65),
    NumberSequenceKeypoint.new(1, 1),
})
```

Rotaciones de `UIGradient`, comprobadas: 0 deja opaco el lado izquierdo, 90
arriba, 180 la derecha, 270 abajo.

---

## Resumen de constantes

Todo en una tabla, por si solo quieres los numeros.

| Sistema | Constante | Valor |
|---|---|---|
| Ronda | Duracion | 90 s |
| Ronda | Descanso | 12 s |
| Ronda | Intro | 7 s |
| Ritmo | Paso | 20 s |
| Ritmo | Subida de valor | 0.18 |
| Ritmo | Recorte de duracion | 4 s |
| Movimiento | Base | 18 |
| Movimiento | Carrera | 31 |
| Movimiento | Deslizada | 44 |
| Movimiento | Salto base | 50 |
| Deslizada | Duracion | 0.75 s |
| Deslizada | Coste | 22 |
| Deslizada | Enfriamiento | 1.6 s |
| Resistencia | Maxima | 100 |
| Resistencia | Gasto al correr | 27 por s |
| Resistencia | Recuperacion | 19 por s |
| Resistencia | Minimo para correr | 12 |
| Carga | Cajas maximas | 3 |
| Carga | Penalizacion velocidad | 2.6 por caja |
| Carga | Penalizacion salto | 4 por caja |
| Carga | Puntos por caja | 60 |
| Carga | Bonus de lote | 45 |
| Pedidos | Activos | 3 |
| Pedidos | Duracion normal | 27 s |
| Pedidos | Duracion urgente | 15 s |
| Pedidos | Probabilidad urgente | 0.24 |
| Pedidos | Multiplicador urgente | 3 |
| Combo | Ventana | 12 s |
| Combo | Maximo | 6 |
| Combo | Bonus por escalon | 0.25 |
| Camara | FOV base | 70 |
| Camara | FOV carrera | 87 |
| Camara | FOV deslizada | 97 |
| Camara | Cabeceo | 0.85 |
| Camara | Ladeo maximo | 4.5 grados |
| Camara | Inclinacion del cuerpo | -9 grados |
| Animacion | Velocidad al correr | 1.3 |
| Animacion | Velocidad al deslizar | 1.6 |
| Animacion | Mezcla | 0.15 s |
| Anticheat | Enfriamiento de toque | 0.3 s |
| Anticheat | Llamadas por segundo | 6 |
| Anticheat | Margen de velocidad | 1.7 |
| Anticheat | Avisos antes de corregir | 3 |
| Ratio de accion | Subida por pulsacion | 0.13 |
| Ratio de accion | Bajada por segundo | 0.55 |
| Ratio de accion | Media minima | 0.15 |
| Ratio de accion | Hueco de publicacion | 0.08 s |
| Ratio de accion | Cambio minimo | 0.02 |
| Tienda | Monedas por ficha | 50 |
| Tienda | Fichas por victoria | 5 |
| Tienda | Tope de inventario | 5 |
| Tienda | Radio del iman | 14 studs |
| Tienda | Super salto | 100 |
| Tienda | Autoguardado | 120 s |
| Arena | Radio | 110 studs |

---

## Que falta por extraer

Cosas que estan en el Place y que todavia no tienen ficha aqui:

| Sistema en Studio | Por que interesa |
|---|---|
| `ServerScriptService.SistemaPuertas` | Puertas con estado compartido entre varios modelos |
| `Workspace.PuertaFuncional.ControlPuerta` | Apertura por proximidad con `PivotTo` |
| `Workspace.ModernDoor.ProceduralGeneration` | Modelo procedural con atributos editables |
| `ServerStorage.ZeroScript.Memory` | Notas de UI nativa y `TweenService` |

Cuando alguna de estas se estabilice, se anade como ficha 10.13 y siguientes.
