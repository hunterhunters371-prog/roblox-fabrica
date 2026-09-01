# 06 - Datos persistentes y red

Modulo 6 del catalogo. Guardar el progreso, comunicar cliente y servidor, y no
perder nada cuando el servidor se cierra.

Dos reglas que resumen todo el modulo:

1. **Los datos del jugador solo existen de verdad en el servidor.** Lo que el
   cliente tiene es una copia para dibujar la interfaz.
2. **Toda llamada a DataStore puede fallar.** Siempre. Sin excepcion. Si no la
   envuelves en `pcall`, tu juego se rompera en produccion aunque funcione en
   Studio.

## Indice

| # | Mecanica | Para que |
|---|---|---|
| 1 | Activar DataStores en Studio | Requisito previo |
| 2 | Guardar y leer con seguridad | El patron base |
| 3 | Reintentos con retroceso | Sobrevivir a fallos |
| 4 | UpdateAsync frente a SetAsync | Cuando usar cada uno |
| 5 | Limites y throttling | No pasarse de cuota |
| 6 | Esquema versionado | Poder cambiar el formato |
| 7 | Bloqueo de sesion | Evitar duplicar objetos |
| 8 | Guardar al salir y al cerrar | BindToClose |
| 9 | Autoguardado | Red de seguridad |
| 10 | Gestor de datos completo | Modulo listo para usar |
| 11 | leaderstats | Estadisticas visibles |
| 12 | OrderedDataStore | Tablas de clasificacion |
| 13 | MemoryStoreService | Datos entre servidores |
| 14 | RemoteEvent | Avisos en un sentido |
| 15 | RemoteFunction | Peticiones con respuesta |
| 16 | UnreliableRemoteEvent | Datos que se pueden perder |
| 17 | BindableEvent | Comunicacion en el mismo lado |
| 18 | Validacion y limite de frecuencia | Blindar los remotes |
| 19 | Attributes replicados | Estado ligero |
| 20 | MessagingService | Hablar entre servidores |
| 21 | HttpService | Webhooks y APIs externas |
| 22 | TeleportService con datos | Pasar informacion al viajar |
| 23 | MarketplaceService | Compras y ProcessReceipt |

---

### 1. Activar DataStores en Studio

- **Que es:** un permiso que hay que activar a mano.
- **Por que importa:** sin esto, todo el codigo de guardado da error en Studio y
  parece que el codigo esta mal.

```text
En Studio:
  Inicio (Home)  >  Game Settings  >  Security
  Activa "Enable Studio Access to API Services"
  Guarda y reinicia la sesion de prueba
```

El error que ves si no lo activas:

```text
DataStore request was added to queue
... o ...
503: API Services rejected request
```

Ademas, el juego debe estar **publicado**. Un archivo local sin publicar no tiene
DataStores propios.

- **Checklist sin errores:**
  - [ ] El juego esta publicado en Roblox
  - [ ] "Enable Studio Access to API Services" activado
  - [ ] Probado tambien en un servidor real, no solo en Studio

---

### 2. Guardar y leer con seguridad

- **Que es:** el patron minimo correcto de acceso a datos.
- **API implicada:** `DataStoreService:GetDataStore`, `GetAsync`, `SetAsync`.
- **Donde va:** Script en `ServerScriptService`. **Nunca** en el cliente.
- **Codigo listo para pegar:**

```lua
local DataStoreService = game:GetService("DataStoreService")
local almacen = DataStoreService:GetDataStore("DatosJugador_v1")

local function claveDe(jugador: Player): string
    return "jugador_" .. tostring(jugador.UserId)
end

local function leer(jugador: Player)
    local ok, resultado = pcall(function()
        return almacen:GetAsync(claveDe(jugador))
    end)

    if not ok then
        warn("Fallo al leer datos de " .. jugador.Name .. ": " .. tostring(resultado))
        return nil, false -- nil de datos, false de exito
    end

    return resultado, true
end

local function escribir(jugador: Player, datos: any): boolean
    local ok, err = pcall(function()
        almacen:SetAsync(claveDe(jugador), datos)
    end)

    if not ok then
        warn("Fallo al guardar datos de " .. jugador.Name .. ": " .. tostring(err))
        return false
    end

    return true
end

return { leer = leer, escribir = escribir }
```

- **Errores frecuentes:**
  - Sin `pcall`: un fallo de red tumba el script entero y nadie guarda.
  - No distinguir "no hay datos" de "fallo la lectura". Si confundes las dos
    cosas, le das datos nuevos a un jugador veterano y **borras su progreso**.
    Este es el error mas grave posible en un juego de Roblox. Por eso `leer`
    devuelve dos valores.
  - Usar la clave del nombre del jugador: si se cambia el nombre, pierde todo.
    Usa `UserId`, que nunca cambia.
  - Guardar instancias, funciones o tablas con claves mixtas: los DataStores
    solo aceptan numeros, textos, booleanos y tablas simples.
- **Checklist sin errores:**
  - [ ] Todo acceso esta en `pcall`
  - [ ] Se distingue fallo de lectura de datos inexistentes
  - [ ] La clave usa `UserId`
  - [ ] Solo se guardan tipos simples

---

### 3. Reintentos con retroceso

- **Que es:** volver a intentarlo esperando cada vez un poco mas.
- **Para que sirve:** los fallos de DataStore suelen ser temporales. Un
  reintento salva la mayoria.
- **Codigo listo para pegar:**

```lua
local INTENTOS = 4

local function conReintentos<T>(operacion: () -> T, etiqueta: string): (boolean, T?)
    local espera = 1

    for intento = 1, INTENTOS do
        local ok, resultado = pcall(operacion)

        if ok then
            return true, resultado
        end

        warn(string.format(
            "[%s] intento %d de %d fallo: %s",
            etiqueta, intento, INTENTOS, tostring(resultado)
        ))

        if intento < INTENTOS then
            task.wait(espera)
            espera *= 2 -- 1, 2, 4 segundos
        end
    end

    return false, nil
end

return conReintentos
```

Uso:

```lua
local ok, datos = conReintentos(function()
    return almacen:GetAsync(clave)
end, "leer " .. clave)

if not ok then
    -- NO le des datos nuevos. Marca la sesion como "no guardar"
    -- y avisa al jugador de que reintente mas tarde.
    return
end
```

- **Errores frecuentes:**
  - Reintentar sin esperar: solo empeora el throttling.
  - Reintentar infinitas veces: bloquea el hilo para siempre.
  - Tras agotar los reintentos, seguir como si nada y sobrescribir con datos
    vacios.
- **Checklist sin errores:**
  - [ ] La espera crece en cada intento
  - [ ] Hay un numero maximo de intentos
  - [ ] Si falla del todo, la sesion se marca como no guardable

---

### 4. UpdateAsync frente a SetAsync

| Funcion | Que hace | Cuando usarla |
|---|---|---|
| `SetAsync` | Escribe encima sin mirar | Solo cuando eres la unica fuente |
| `UpdateAsync` | Lee, te da el valor y escribe el resultado de tu funcion | Casi siempre. Es seguro contra escrituras simultaneas |
| `IncrementAsync` | Suma a un numero | Contadores enteros |
| `RemoveAsync` | Borra la clave | Reinicios y peticiones de borrado |
| `GetAsync` | Lee | Cargar |

- **Codigo listo para pegar:**

```lua
-- Sumar monedas de forma segura aunque dos servidores lo intenten a la vez
local function sumarMonedas(clave: string, cantidad: number): (boolean, number?)
    local ok, resultado = pcall(function()
        return almacen:UpdateAsync(clave, function(actual)
            local datos = actual or { monedas = 0 }
            datos.monedas = (datos.monedas or 0) + cantidad
            return datos
        end)
    end)

    if not ok then
        warn("Fallo UpdateAsync: " .. tostring(resultado))
        return false, nil
    end

    return true, resultado and resultado.monedas
end
```

- **Errores frecuentes:**
  - Usar `SetAsync` para sumar monedas: si el jugador esta en dos servidores o
    hay un reintento, se pierden o se duplican.
  - Devolver `nil` desde la funcion de `UpdateAsync`: eso **cancela** la
    escritura. Si quieres abortar, devuelve `nil` a proposito; si no, devuelve
    siempre la tabla.
  - Hacer operaciones lentas o con `task.wait` dentro de la funcion de
    `UpdateAsync`: la transaccion se alarga y falla.
- **Checklist sin errores:**
  - [ ] Los cambios incrementales usan `UpdateAsync`
  - [ ] La funcion interna siempre devuelve la tabla completa
  - [ ] Dentro de `UpdateAsync` no hay esperas ni llamadas de red

---

### 5. Limites y throttling

- **Que es:** las cuotas que impone Roblox.
- **Por que importa:** pasarse significa que las peticiones se encolan y acaban
  fallando.

| Limite aproximado | Valor |
|---|---|
| Peticiones por minuto | 60 mas 10 por jugador en el servidor |
| Tamano maximo por clave | Del orden de 4 MB |
| Misma clave, escrituras seguidas | Deja al menos 6 segundos entre ellas |
| Longitud de la clave | Hasta 50 caracteres |

Los numeros exactos los publica Roblox y pueden cambiar. La regla practica que
no falla: **guarda poco y espaciado**. Una escritura por jugador cada 60 a 120
segundos, mas una al salir, es suficiente para casi todo.

- **Codigo listo para pegar:**

```lua
local ULTIMA_ESCRITURA: { [string]: number } = {}
local MINIMO_ENTRE_ESCRITURAS = 7

local function puedeEscribir(clave: string): boolean
    local ahora = os.clock()
    local ultima = ULTIMA_ESCRITURA[clave]
    if ultima and ahora - ultima < MINIMO_ENTRE_ESCRITURAS then
        return false
    end
    ULTIMA_ESCRITURA[clave] = ahora
    return true
end
```

- **Errores frecuentes:**
  - Guardar en cada cambio de moneda: en un minuto agotas la cuota.
  - Guardar dentro de un bucle por frame.
  - Guardar todo el inventario completo cada vez en vez de solo lo que cambia.
- **Checklist sin errores:**
  - [ ] Hay una separacion minima entre escrituras de la misma clave
  - [ ] No se guarda en cada cambio, se guarda por intervalos y al salir
  - [ ] Los datos guardados son compactos

---

### 6. Esquema versionado

- **Que es:** guardar un numero de version junto a los datos.
- **Para que sirve:** poder cambiar el formato sin romper a los jugadores
  antiguos. Si no lo haces desde el principio, cambiar el formato mas adelante
  es un problema serio.
- **Codigo listo para pegar:**

```lua
local VERSION_ACTUAL = 3

local function plantilla()
    return {
        version = VERSION_ACTUAL,
        monedas = 0,
        nivelPase = 0,
        premiosReclamados = {},
        entregasCompletadas = 0,
        mejorTiempo = 0,
        inventario = {},
    }
end

local MIGRACIONES: { [number]: (any) -> any } = {
    -- de version 1 a 2: se anadio el pase
    [1] = function(datos)
        datos.nivelPase = 0
        datos.premiosReclamados = {}
        datos.version = 2
        return datos
    end,
    -- de version 2 a 3: monedas paso de texto a numero
    [2] = function(datos)
        datos.monedas = tonumber(datos.monedas) or 0
        datos.version = 3
        return datos
    end,
}

local function migrar(datos: any)
    if type(datos) ~= "table" then
        return plantilla()
    end

    datos.version = datos.version or 1

    while datos.version < VERSION_ACTUAL do
        local paso = MIGRACIONES[datos.version]
        if not paso then
            warn("Sin migracion desde la version " .. tostring(datos.version))
            break
        end
        datos = paso(datos)
    end

    -- rellenar campos nuevos que falten
    for clave, valor in plantilla() do
        if datos[clave] == nil then
            datos[clave] = valor
        end
    end

    return datos
end

return { plantilla = plantilla, migrar = migrar, VERSION = VERSION_ACTUAL }
```

- **Errores frecuentes:**
  - No guardar version: el dia que cambies el formato tendras que adivinar.
  - Migrar de golpe de la 1 a la 5: encadena las migraciones paso a paso, es
    mas facil de mantener y de probar.
  - No rellenar los campos nuevos: `nil` donde esperabas un numero y errores por
    todo el juego.
- **Checklist sin errores:**
  - [ ] Los datos llevan `version`
  - [ ] Las migraciones son paso a paso
  - [ ] Los campos nuevos se rellenan desde la plantilla
  - [ ] Probado cargando datos de una version antigua a mano

---

### 7. Bloqueo de sesion

- **Que es:** marcar que un servidor tiene los datos abiertos.
- **Para que sirve:** evitar el duplicado clasico. El jugador entra en el
  servidor A, deja objetos, entra en el B antes de que A guarde, y al guardar A
  sobrescribe. Resultado: objetos duplicados o progreso perdido.
- **Codigo listo para pegar:**

```lua
local DataStoreService = game:GetService("DataStoreService")
local almacen = DataStoreService:GetDataStore("DatosJugador_v1")

local ID_SERVIDOR = game.JobId ~= "" and game.JobId or "studio"
local CADUCIDAD_BLOQUEO = 60 -- segundos

local function intentarBloquear(clave: string)
    local ok, resultado = pcall(function()
        return almacen:UpdateAsync(clave, function(actual)
            local datos = actual

            if datos and datos.bloqueo then
                local mismoServidor = datos.bloqueo.servidor == ID_SERVIDOR
                local caducado = os.time() - (datos.bloqueo.momento or 0) > CADUCIDAD_BLOQUEO

                if not mismoServidor and not caducado then
                    return nil -- cancelar: otro servidor lo tiene
                end
            end

            datos = datos or {}
            datos.bloqueo = { servidor = ID_SERVIDOR, momento = os.time() }
            return datos
        end)
    end)

    if not ok then
        return false, nil
    end
    if resultado == nil then
        return false, nil -- estaba bloqueado por otro
    end

    return true, resultado
end

local function liberar(clave: string, datosFinales: any)
    pcall(function()
        almacen:UpdateAsync(clave, function(actual)
            local datos = datosFinales or actual or {}
            datos.bloqueo = nil
            return datos
        end)
    end)
end

return { bloquear = intentarBloquear, liberar = liberar }
```

- **Errores frecuentes:**
  - Bloqueo sin caducidad: si el servidor se cae sin liberar, el jugador queda
    bloqueado para siempre.
  - No liberar el bloqueo al guardar la salida.
  - Reintentar el bloqueo en un bucle sin limite: el jugador se queda esperando
    en una pantalla de carga infinita. Pon un maximo de intentos y un mensaje
    claro.
  - Para un juego serio, considera usar una libreria probada como ProfileService
    en vez de escribir tu propio bloqueo.
- **Checklist sin errores:**
  - [ ] El bloqueo tiene caducidad
  - [ ] Se libera al guardar la salida
  - [ ] Hay un maximo de intentos y un mensaje al jugador

---

### 8. Guardar al salir y al cerrar

- **Que es:** los dos momentos en que **hay** que guardar.
- **Para que sirve:** que el ultimo minuto de juego no se pierda.
- **API implicada:** `Players.PlayerRemoving`, `game:BindToClose`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local cache: { [Player]: any } = {}

local function guardar(jugador: Player)
    local datos = cache[jugador]
    if not datos then
        return
    end
    -- escribir(jugador, datos)
    cache[jugador] = nil
end

Players.PlayerRemoving:Connect(guardar)

game:BindToClose(function()
    if RunService:IsStudio() then
        return -- en Studio no hace falta y solo alarga el cierre
    end

    local pendientes = 0

    for jugador in cache do
        pendientes += 1
        task.spawn(function()
            guardar(jugador)
            pendientes -= 1
        end)
    end

    -- Roblox concede unos 30 segundos. Espera con tope.
    local inicio = os.clock()
    while pendientes > 0 and os.clock() - inicio < 25 do
        task.wait(0.2)
    end
end)
```

- **Errores frecuentes:**
  - Guardar solo en `PlayerRemoving`: si el servidor se cierra con jugadores
    dentro, `PlayerRemoving` puede no llegar a completarse.
  - `BindToClose` sin esperar: la funcion termina antes de que se escriban los
    datos y se pierden.
  - Esperar mas de 30 segundos en `BindToClose`: Roblox mata el servidor y no
    guarda nada.
  - Guardar en `PlayerRemoving` con un `task.wait` largo antes: el jugador ya
    se fue y la instancia puede haber desaparecido.
- **Checklist sin errores:**
  - [ ] Se guarda en `PlayerRemoving`
  - [ ] Hay `BindToClose` con espera acotada
  - [ ] `BindToClose` se salta en Studio
  - [ ] Probado cerrando el servidor con jugadores dentro

---

### 9. Autoguardado

- **Que es:** guardar cada cierto tiempo mientras el jugador juega.
- **Para que sirve:** si el servidor se cae de golpe, se pierde un minuto y no
  una hora.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")

local INTERVALO = 120 -- segundos
local DESFASE = 3     -- separacion entre jugadores para repartir la carga

task.spawn(function()
    while true do
        task.wait(INTERVALO)

        for indice, jugador in Players:GetPlayers() do
            task.delay((indice - 1) * DESFASE, function()
                if jugador.Parent then
                    -- guardar(jugador)
                end
            end)
        end
    end
end)
```

- **Errores frecuentes:**
  - Guardar a todos los jugadores en el mismo instante: pico de peticiones y
    throttling. El desfase lo reparte.
  - Intervalos muy cortos: gasta cuota sin ganar nada.
  - No comprobar `jugador.Parent` tras la espera: el jugador puede haberse ido.
- **Checklist sin errores:**
  - [ ] El guardado esta repartido en el tiempo
  - [ ] El intervalo es de 60 segundos o mas
  - [ ] Se comprueba que el jugador sigue conectado

---

### 10. Gestor de datos completo

- **Que es:** todo lo anterior junto, en un modulo listo para usar.
- **Donde va:** ModuleScript en `ServerScriptService/Datos`.
- **Codigo listo para pegar:**

```lua
--!strict
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local almacen = DataStoreService:GetDataStore("DatosJugador_v1")

local VERSION = 1
local INTENTOS = 4
local INTERVALO_AUTOGUARDADO = 120

export type Datos = {
    version: number,
    monedas: number,
    nivelPase: number,
    entregas: number,
    mejorTiempo: number,
}

local Gestor = {}

local cache: { [Player]: Datos } = {}
local guardable: { [Player]: boolean } = {}

local function plantilla(): Datos
    return {
        version = VERSION,
        monedas = 0,
        nivelPase = 0,
        entregas = 0,
        mejorTiempo = 0,
    }
end

local function clave(jugador: Player): string
    return "jugador_" .. tostring(jugador.UserId)
end

local function conReintentos(operacion: () -> any): (boolean, any)
    local espera = 1
    for intento = 1, INTENTOS do
        local ok, resultado = pcall(operacion)
        if ok then
            return true, resultado
        end
        warn("Datos: intento " .. intento .. " fallo: " .. tostring(resultado))
        if intento < INTENTOS then
            task.wait(espera)
            espera *= 2
        end
    end
    return false, nil
end

function Gestor.cargar(jugador: Player): Datos?
    local ok, guardado = conReintentos(function()
        return almacen:GetAsync(clave(jugador))
    end)

    if not ok then
        -- CRITICO: no inventar datos nuevos. Marcar como no guardable.
        guardable[jugador] = false
        cache[jugador] = plantilla()
        warn("Datos: no se pudo cargar " .. jugador.Name .. ". Sesion en modo lectura.")
        return cache[jugador]
    end

    guardable[jugador] = true

    local datos: Datos
    if type(guardado) == "table" then
        datos = guardado :: Datos
        local base = plantilla()
        for campo, valor in base :: any do
            if (datos :: any)[campo] == nil then
                (datos :: any)[campo] = valor
            end
        end
    else
        datos = plantilla()
    end

    cache[jugador] = datos
    return datos
end

function Gestor.obtener(jugador: Player): Datos?
    return cache[jugador]
end

function Gestor.guardar(jugador: Player): boolean
    local datos = cache[jugador]
    if not datos then
        return false
    end
    if guardable[jugador] == false then
        warn("Datos: sesion no guardable, se omite " .. jugador.Name)
        return false
    end

    local ok = conReintentos(function()
        return almacen:UpdateAsync(clave(jugador), function()
            return datos
        end)
    end)

    return ok
end

function Gestor.descargar(jugador: Player)
    Gestor.guardar(jugador)
    cache[jugador] = nil
    guardable[jugador] = nil
end

Players.PlayerAdded:Connect(function(jugador)
    Gestor.cargar(jugador)
end)

Players.PlayerRemoving:Connect(function(jugador)
    Gestor.descargar(jugador)
end)

task.spawn(function()
    while true do
        task.wait(INTERVALO_AUTOGUARDADO)
        for indice, jugador in Players:GetPlayers() do
            task.delay((indice - 1) * 3, function()
                if jugador.Parent then
                    Gestor.guardar(jugador)
                end
            end)
        end
    end
end)

game:BindToClose(function()
    if RunService:IsStudio() then
        return
    end

    local pendientes = 0
    for jugador in cache do
        pendientes += 1
        task.spawn(function()
            Gestor.descargar(jugador)
            pendientes -= 1
        end)
    end

    local inicio = os.clock()
    while pendientes > 0 and os.clock() - inicio < 25 do
        task.wait(0.2)
    end
end)

return Gestor
```

- **Errores frecuentes:**
  - Que el resto del juego lea y escriba el DataStore directamente en vez de
    pasar por este modulo: se pierde el control de cuando se guarda.
  - No exponer una funcion `obtener` y hacer que cada script cargue por su
    cuenta: multiplicas las peticiones.
  - No tener el modo "no guardable": es la unica proteccion real contra borrar
    el progreso de alguien tras un fallo de lectura.
- **Checklist sin errores:**
  - [ ] Todo el juego usa este modulo, nadie toca el DataStore por su cuenta
  - [ ] Existe el modo no guardable tras un fallo de carga
  - [ ] Hay autoguardado y `BindToClose`

---

### 11. leaderstats

- **Que es:** la carpeta especial que Roblox muestra en la lista de jugadores.
- **API implicada:** carpeta llamada exactamente `leaderstats` con `IntValue`,
  `NumberValue` o `StringValue` dentro.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")

local function crearStats(jugador: Player, datos: { monedas: number, entregas: number })
    local carpeta = Instance.new("Folder")
    carpeta.Name = "leaderstats" -- el nombre debe ser exacto
    carpeta.Parent = jugador

    local monedas = Instance.new("IntValue")
    monedas.Name = "Monedas"
    monedas.Value = datos.monedas
    monedas.Parent = carpeta

    local entregas = Instance.new("IntValue")
    entregas.Name = "Entregas"
    entregas.Value = datos.entregas
    entregas.Parent = carpeta

    return carpeta
end

return crearStats
```

- **Errores frecuentes:**
  - Llamar a la carpeta `LeaderStats` o `leaderStats`: no aparece. El nombre es
    `leaderstats`, todo en minusculas.
  - Poner mas de cuatro estadisticas: la lista se corta y se ve mal.
  - Escribir los valores desde el cliente: no se replican al servidor.
  - Usar los `IntValue` como fuente de verdad: son solo para mostrar. La verdad
    esta en el gestor de datos.
- **Checklist sin errores:**
  - [ ] La carpeta se llama `leaderstats` exactamente
  - [ ] Es hija directa del `Player`
  - [ ] Solo el servidor escribe los valores
  - [ ] No es la fuente de verdad de los datos

---

### 12. OrderedDataStore

- **Que es:** un almacen que solo guarda numeros y sabe ordenarlos.
- **Para que sirve:** tablas de clasificacion globales.
- **API implicada:** `GetOrderedDataStore`, `GetSortedAsync`,
  `DataStorePages:GetCurrentPage`.
- **Codigo listo para pegar:**

```lua
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")

local tabla = DataStoreService:GetOrderedDataStore("MejoresEntregas_v1")

local function publicar(jugador: Player, puntuacion: number)
    if puntuacion ~= math.floor(puntuacion) then
        puntuacion = math.floor(puntuacion) -- solo enteros
    end

    local ok, err = pcall(function()
        tabla:SetAsync(tostring(jugador.UserId), puntuacion)
    end)

    if not ok then
        warn("No se pudo publicar la puntuacion: " .. tostring(err))
    end
end

local function leerTop(cantidad: number)
    local ok, paginas = pcall(function()
        return tabla:GetSortedAsync(false, cantidad) -- false = descendente
    end)

    if not ok then
        warn("No se pudo leer la clasificacion: " .. tostring(paginas))
        return {}
    end

    local resultado = {}
    for posicion, entrada in (paginas :: DataStorePages):GetCurrentPage() do
        local userId = tonumber(entrada.key)
        local nombre = "Desconocido"

        if userId then
            local okNombre, valor = pcall(function()
                return Players:GetNameFromUserIdAsync(userId)
            end)
            if okNombre then
                nombre = valor
            end
        end

        table.insert(resultado, {
            posicion = posicion,
            nombre = nombre,
            puntuacion = entrada.value,
        })
    end

    return resultado
end

return { publicar = publicar, leerTop = leerTop }
```

- **Errores frecuentes:**
  - Guardar valores no enteros: `OrderedDataStore` solo admite enteros.
  - Llamar a `GetSortedAsync` cada vez que alguien abre la interfaz: cachea el
    resultado y refrescalo cada minuto o dos.
  - `GetNameFromUserIdAsync` sin `pcall`: falla con cuentas borradas.
  - Guardar tambien los datos del jugador aqui: este almacen es solo para la
    puntuacion.
- **Checklist sin errores:**
  - [ ] Solo se guardan enteros
  - [ ] El resultado esta cacheado
  - [ ] La resolucion de nombres esta en `pcall`

---

### 13. MemoryStoreService

- **Que es:** almacenamiento rapido y temporal compartido entre todos los
  servidores del juego.
- **Para que sirve:** colas de emparejamiento, contadores en vivo, estado
  compartido de corta duracion.
- **API implicada:** `MemoryStoreService:GetSortedMap`, `GetQueue`,
  `SetAsync` con caducidad.
- **Codigo listo para pegar:**

```lua
local MemoryStoreService = game:GetService("MemoryStoreService")

local cola = MemoryStoreService:GetQueue("ColaEmparejamiento", 30)
local mapa = MemoryStoreService:GetSortedMap("JugadoresActivos")

local function entrarEnCola(userId: number)
    local ok, err = pcall(function()
        cola:AddAsync(userId, 120) -- caduca en 120 segundos
    end)
    if not ok then
        warn("No se pudo entrar en cola: " .. tostring(err))
    end
end

local function sacarGrupo(cantidad: number)
    local ok, valores, id = pcall(function()
        return cola:ReadAsync(cantidad, false, 30)
    end)

    if not ok or not valores then
        return nil
    end

    -- confirmar la lectura para que no vuelvan a la cola
    pcall(function()
        cola:RemoveAsync(id)
    end)

    return valores
end

local function marcarActivo(userId: number)
    pcall(function()
        mapa:SetAsync(tostring(userId), os.time(), 300) -- caduca en 5 minutos
    end)
end

return { entrar = entrarEnCola, sacar = sacarGrupo, activo = marcarActivo }
```

- **Errores frecuentes:**
  - Usarlo como almacenamiento permanente: **todo caduca**. No es un DataStore.
  - No confirmar la lectura de la cola con `RemoveAsync`: los elementos vuelven
    a aparecer pasado el tiempo de invisibilidad.
  - Olvidar la caducidad: se llena y falla.
- **Checklist sin errores:**
  - [ ] Solo datos temporales
  - [ ] Toda entrada tiene caducidad
  - [ ] Las lecturas de cola se confirman

---

### 14. RemoteEvent

- **Que es:** un aviso en un sentido entre cliente y servidor.
- **Para que sirve:** el 90 por ciento de la comunicacion.

| Direccion | Metodo | Escucha |
|---|---|---|
| Cliente a servidor | `remote:FireServer(...)` | `remote.OnServerEvent` |
| Servidor a un cliente | `remote:FireClient(jugador, ...)` | `remote.OnClientEvent` |
| Servidor a todos | `remote:FireAllClients(...)` | `remote.OnClientEvent` |

- **Donde va:** el RemoteEvent en `ReplicatedStorage/Remotes`.
- **Codigo listo para pegar:**

```lua
-- Servidor
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local carpeta = ReplicatedStorage:FindFirstChild("Remotes")
if not carpeta then
    carpeta = Instance.new("Folder")
    carpeta.Name = "Remotes"
    carpeta.Parent = ReplicatedStorage
end

local aviso = Instance.new("RemoteEvent")
aviso.Name = "AvisoRonda"
aviso.Parent = carpeta

aviso:FireAllClients("Preparacion", 10)
```

```lua
-- Cliente
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local aviso = ReplicatedStorage:WaitForChild("Remotes", 20)
    and ReplicatedStorage.Remotes:WaitForChild("AvisoRonda", 20)

if not aviso then
    warn("No se encontro AvisoRonda")
    return
end

(aviso :: RemoteEvent).OnClientEvent:Connect(function(fase: string, segundos: number)
    print("Fase: " .. fase .. " durante " .. segundos .. " s")
end)
```

- **Errores frecuentes:**
  - Crear el remote en el servidor y buscarlo en el cliente sin `WaitForChild`:
    error de nil porque el cliente arranco antes.
  - `WaitForChild` sin timeout: si el nombre esta mal escrito, el script se
    cuelga en silencio hasta que aparece el aviso de "Infinite yield possible".
  - Un remote por cada accion: acabas con cincuenta remotes. Agrupa por sistema
    y pasa un identificador de accion.
  - Enviar tablas enormes cada frame: saturas la red.
- **Checklist sin errores:**
  - [ ] Todos los `WaitForChild` de remotes tienen timeout
  - [ ] Los remotes viven en una carpeta conocida de `ReplicatedStorage`
  - [ ] No se envian datos cada frame

---

### 15. RemoteFunction

- **Que es:** una llamada que espera respuesta.
- **Para que sirve:** "puedo comprar esto", "dame mis datos".
- **Cuidado:** el cliente que llama se **bloquea** hasta recibir respuesta.
- **Codigo listo para pegar:**

```lua
-- Servidor
local funcion = Instance.new("RemoteFunction")
funcion.Name = "PedirDatos"
funcion.Parent = ReplicatedStorage.Remotes

funcion.OnServerInvoke = function(jugador: Player)
    local datos = Gestor.obtener(jugador)
    if not datos then
        return { ok = false }
    end

    -- devolver solo lo que el cliente necesita ver
    return {
        ok = true,
        monedas = datos.monedas,
        nivelPase = datos.nivelPase,
        entregas = datos.entregas,
    }
end
```

```lua
-- Cliente
local ok, respuesta = pcall(function()
    return funcion:InvokeServer()
end)

if not ok then
    warn("El servidor no respondio: " .. tostring(respuesta))
    return
end

if respuesta and respuesta.ok then
    print("Monedas: " .. respuesta.monedas)
end
```

- **Errores frecuentes:**
  - **Nunca uses `InvokeClient` desde el servidor.** Si el cliente se
    desconecta o no responde, el hilo del servidor se queda colgado. Usa
    `FireClient` con un `RemoteEvent` de vuelta.
  - `InvokeServer` sin `pcall`: si `OnServerInvoke` lanza un error, el cliente
    recibe la excepcion.
  - Devolver toda la tabla de datos: expones informacion interna. Devuelve solo
    lo necesario.
  - Olvidar que `OnServerInvoke` solo admite una funcion: la segunda asignacion
    sustituye a la primera sin avisar.
- **Checklist sin errores:**
  - [ ] No se usa `InvokeClient`
  - [ ] `InvokeServer` esta en `pcall`
  - [ ] Se devuelve solo lo que el cliente debe ver
  - [ ] Hay una unica asignacion de `OnServerInvoke`

---

### 16. UnreliableRemoteEvent

- **Que es:** un RemoteEvent que puede perder mensajes pero es mas barato.
- **Para que sirve:** datos que se reemplazan constantemente: posicion de un
  cursor, rotacion de una torreta, efectos visuales.
- **Codigo listo para pegar:**

```lua
local rapido = Instance.new("UnreliableRemoteEvent")
rapido.Name = "PosicionMira"
rapido.Parent = ReplicatedStorage.Remotes

-- Cliente: manda su direccion de mira varias veces por segundo
local acumulado = 0
game:GetService("RunService").Heartbeat:Connect(function(dt)
    acumulado += dt
    if acumulado < 0.1 then -- 10 veces por segundo basta
        return
    end
    acumulado = 0

    local camara = workspace.CurrentCamera
    if camara then
        rapido:FireServer(camara.CFrame.LookVector)
    end
end)
```

- **Errores frecuentes:**
  - Usarlo para algo importante: si el mensaje se pierde, no hay reintento.
    Nunca lo uses para dano, compras ni guardado.
  - Enviar cada frame: sigue costando. Limita a 10 o 20 veces por segundo.
  - Suponer que llegan en orden: no esta garantizado.
- **Checklist sin errores:**
  - [ ] Solo se usa para datos que se reemplazan
  - [ ] La frecuencia esta limitada
  - [ ] Nada critico depende de el

---

### 17. BindableEvent

- **Que es:** comunicacion entre scripts del **mismo lado**.
- **Para que sirve:** que dos scripts del servidor hablen sin acoplarse.
- **Importante:** no cruza la frontera cliente-servidor. Para eso son los
  Remote.
- **Codigo listo para pegar:**

```lua
-- ModuleScript: Senales
local Senales = {}

local function crear(nombre: string)
    local evento = Instance.new("BindableEvent")
    evento.Name = nombre
    Senales[nombre] = evento
    return evento
end

crear("RondaEmpezo")
crear("RondaTermino")
crear("EntregaCompletada")

return Senales
```

```lua
-- Un script emite
local Senales = require(game.ServerScriptService.Modulos.Senales)
Senales.EntregaCompletada:Fire(jugador, 42)

-- Otro script escucha, sin conocer al primero
Senales.EntregaCompletada.Event:Connect(function(jugador, segundos)
    print(jugador.Name .. " entrego en " .. segundos .. " s")
end)
```

- **Errores frecuentes:**
  - Intentar usarlo entre cliente y servidor: no funciona.
  - Pasar tablas y modificarlas despues: `BindableEvent` **copia** las tablas al
    pasarlas, asi que el receptor no ve tus cambios posteriores. Y las
    instancias dentro de la tabla si se pasan por referencia. Es una fuente
    clasica de confusion.
  - No desconectar las conexiones de objetos que se destruyen.
- **Checklist sin errores:**
  - [ ] Solo se usa dentro del mismo lado
  - [ ] No se depende de mutar tablas despues de enviarlas
  - [ ] Las conexiones se desconectan

---

### 18. Validacion y limite de frecuencia

- **Que es:** la puerta de seguridad de todos los remotes.
- **Para que sirve:** que un cliente modificado no rompa el juego.
- **Codigo listo para pegar:**

```lua
--!strict
local Players = game:GetService("Players")

local Guardia = {}

local contadores: { [Player]: { [string]: { veces: number, ventana: number } } } = {}

-- Limite: cuantas veces por segundo se permite cada accion
function Guardia.permitido(jugador: Player, accion: string, porSegundo: number): boolean
    local ahora = os.clock()
    contadores[jugador] = contadores[jugador] or {}
    local registro = contadores[jugador][accion]

    if not registro or ahora - registro.ventana >= 1 then
        contadores[jugador][accion] = { veces = 1, ventana = ahora }
        return true
    end

    if registro.veces >= porSegundo then
        return false
    end

    registro.veces += 1
    return true
end

-- Validadores reutilizables
function Guardia.esEnteroEnRango(valor: any, minimo: number, maximo: number): boolean
    if typeof(valor) ~= "number" then
        return false
    end
    if valor ~= valor then -- nan
        return false
    end
    if valor ~= math.floor(valor) then
        return false
    end
    return valor >= minimo and valor <= maximo
end

function Guardia.esTextoCorto(valor: any, maximo: number): boolean
    return typeof(valor) == "string" and #valor > 0 and #valor <= maximo
end

function Guardia.esOpcion(valor: any, permitidos: { [string]: boolean }): boolean
    return typeof(valor) == "string" and permitidos[valor] == true
end

function Guardia.esInstanciaDe(valor: any, clase: string): boolean
    return typeof(valor) == "Instance" and valor:IsA(clase)
end

Players.PlayerRemoving:Connect(function(jugador)
    contadores[jugador] = nil
end)

return Guardia
```

Uso completo:

```lua
local TIPOS_VALIDOS = { gratis = true, premium = true }

remote.OnServerEvent:Connect(function(jugador, nivel, tipo)
    if not Guardia.permitido(jugador, "Reclamar", 3) then
        return
    end
    if not Guardia.esEnteroEnRango(nivel, 1, 20) then
        return
    end
    if not Guardia.esOpcion(tipo, TIPOS_VALIDOS) then
        return
    end

    -- ahora si, la logica
end)
```

- **Errores frecuentes:**
  - Confiar en `tonumber(valor)`: un cliente puede enviar el texto `"1e400"` o
    `nan`. Comprueba tipo, rango y que sea entero.
  - No limitar la frecuencia: un cliente modificado envia mil peticiones por
    segundo y hunde el servidor.
  - Validar en el cliente y no en el servidor. La validacion del cliente es
    comodidad para el jugador honesto, no seguridad.
  - No limpiar los contadores al salir el jugador.
- **Checklist sin errores:**
  - [ ] Todo remote valida tipo y rango de cada argumento
  - [ ] Todo remote tiene limite de frecuencia
  - [ ] Los contadores se limpian en `PlayerRemoving`
  - [ ] Probado enviando argumentos absurdos desde la consola del cliente

---

### 19. Attributes replicados

- **Que es:** valores con nombre pegados a cualquier instancia, que se replican
  del servidor al cliente automaticamente.
- **Para que sirve:** estado ligero sin crear `IntValue` ni remotes.
- **API implicada:** `SetAttribute`, `GetAttribute`,
  `GetAttributeChangedSignal`, `GetAttributes`.

| Aspecto | Attributes | ValueObjects (IntValue, etc.) |
|---|---|---|
| Instancias creadas | Ninguna | Una por valor |
| Replicacion | Automatica del servidor al cliente | Automatica |
| Tipos soportados | Muchos, incluido Vector3 y Color3 | Uno por clase |
| Aparecen en leaderstats | No | Si |

- **Codigo listo para pegar:**

```lua
-- Servidor: escribe
jugador:SetAttribute("Monedas", 250)
jugador:SetAttribute("NivelPase", 4)
jugador:SetAttribute("TienePremium", false)

-- Cliente: lee y reacciona
local jugador = game:GetService("Players").LocalPlayer

local function refrescar()
    local monedas = jugador:GetAttribute("Monedas") or 0
    print("Monedas: " .. monedas)
end

refrescar()
jugador:GetAttributeChangedSignal("Monedas"):Connect(refrescar)
```

- **Errores frecuentes:**
  - Escribir un atributo desde el cliente y esperar que el servidor lo vea: los
    cambios del cliente **no** se replican al servidor.
  - Guardar tablas en atributos: no se admiten. Solo tipos simples y algunos
    tipos de Roblox.
  - Usar atributos como fuente de verdad de los datos guardados: el gestor de
    datos es la fuente, los atributos son el reflejo para la interfaz.
- **Checklist sin errores:**
  - [ ] Solo el servidor escribe
  - [ ] No se guardan tablas
  - [ ] Son un reflejo, no la fuente de verdad

---

### 20. MessagingService

- **Que es:** mensajes entre los distintos servidores del mismo juego.
- **Para que sirve:** anuncios globales, expulsiones, eventos que afectan a
  todos.
- **API implicada:** `PublishAsync`, `SubscribeAsync`.
- **Codigo listo para pegar:**

```lua
local MessagingService = game:GetService("MessagingService")
local Players = game:GetService("Players")

local TEMA = "AnuncioGlobal"

-- Escuchar
local ok, conexion = pcall(function()
    return MessagingService:SubscribeAsync(TEMA, function(mensaje)
        local datos = mensaje.Data
        if typeof(datos) ~= "table" or typeof(datos.texto) ~= "string" then
            return
        end
        -- avisar a todos los clientes de este servidor
        -- remotes.Anuncio:FireAllClients(datos.texto)
        print("Anuncio global: " .. datos.texto)
    end)
end)

if not ok then
    warn("No se pudo suscribir a " .. TEMA .. ": " .. tostring(conexion))
end

-- Publicar
local function anunciar(texto: string)
    if #texto > 500 then
        texto = string.sub(texto, 1, 500)
    end

    local okEnvio, err = pcall(function()
        MessagingService:PublishAsync(TEMA, { texto = texto, momento = os.time() })
    end)

    if not okEnvio then
        warn("No se pudo publicar: " .. tostring(err))
    end
end

return anunciar
```

- **Errores frecuentes:**
  - No validar el contenido recibido: cualquier servidor de tu juego puede
    publicar, y un exploit en uno afecta a todos.
  - Publicar en bucle: hay limite de mensajes por minuto.
  - Esperar que llegue al instante: puede tardar unos segundos.
  - No envolver `SubscribeAsync` en `pcall`: falla en Studio si no hay acceso a
    API Services.
- **Checklist sin errores:**
  - [ ] `PublishAsync` y `SubscribeAsync` en `pcall`
  - [ ] El contenido recibido se valida
  - [ ] La frecuencia de publicacion es baja

---

### 21. HttpService

- **Que es:** peticiones a servicios externos.
- **Para que sirve:** webhooks de Discord, paneles de administracion, APIs
  propias.
- **API implicada:** `HttpService:RequestAsync`, `JSONEncode`, `JSONDecode`,
  `GenerateGUID`.
- **Requisito:** activar "Allow HTTP Requests" en Game Settings > Security.
- **Codigo listo para pegar:**

```lua
local HttpService = game:GetService("HttpService")

local function enviarWebhook(url: string, contenido: string): boolean
    local cuerpo = HttpService:JSONEncode({
        content = contenido,
    })

    local ok, respuesta = pcall(function()
        return HttpService:RequestAsync({
            Url = url,
            Method = "POST",
            Headers = { ["Content-Type"] = "application/json" },
            Body = cuerpo,
        })
    end)

    if not ok then
        warn("Fallo la peticion HTTP: " .. tostring(respuesta))
        return false
    end

    local r = respuesta :: any
    if not r.Success then
        warn(string.format("HTTP %d %s", r.StatusCode, tostring(r.StatusMessage)))
        return false
    end

    return true
end

local function leerJson(url: string)
    local ok, respuesta = pcall(function()
        return HttpService:RequestAsync({ Url = url, Method = "GET" })
    end)

    if not ok then
        return nil
    end

    local r = respuesta :: any
    if not r.Success then
        return nil
    end

    local okJson, datos = pcall(function()
        return HttpService:JSONDecode(r.Body)
    end)

    if not okJson then
        warn("Respuesta no es JSON valido")
        return nil
    end

    return datos
end

return { webhook = enviarWebhook, leer = leerJson }
```

- **Errores frecuentes:**
  - No se puede llamar a `roblox.com` ni a sus subdominios desde `HttpService`.
    Esta bloqueado a proposito.
  - `JSONDecode` sin `pcall`: si la respuesta no es JSON, el script muere.
  - Poner la URL del webhook en un script del cliente o en `ReplicatedStorage`:
    cualquiera puede leerla y usarla. Los secretos van en `ServerScriptService`
    o mejor en `ServerStorage`.
  - Hacer peticiones en un bucle rapido: hay un limite de unas 500 por minuto.
  - Bloquear el hilo principal esperando la respuesta: usa `task.spawn`.
- **Checklist sin errores:**
  - [ ] "Allow HTTP Requests" activado
  - [ ] Todo en `pcall`, incluido `JSONDecode`
  - [ ] Las URLs con secretos solo existen en el servidor
  - [ ] Las peticiones no bloquean la logica del juego

---

### 22. TeleportService con datos

- **Que es:** mover jugadores entre lugares del mismo juego pasando informacion.
- **Para que sirve:** lobby y partida en lugares separados, mazmorras privadas.
- **API implicada:** `TeleportService:TeleportAsync`,
  `ReserveServerAccessCode`, `GetLocalPlayerTeleportData`,
  `TeleportOptions`, `SetTeleportData`.
- **Codigo listo para pegar:**

```lua
local TeleportService = game:GetService("TeleportService")
local Players = game:GetService("Players")

local ID_LUGAR_PARTIDA = 0 -- pon aqui el PlaceId real

local function enviarAPartida(jugadores: { Player }, datosRonda: any)
    if ID_LUGAR_PARTIDA == 0 then
        warn("Configura ID_LUGAR_PARTIDA")
        return
    end

    local opciones = Instance.new("TeleportOptions")
    opciones.ShouldReserveServer = true
    opciones:SetTeleportData({
        ronda = datosRonda,
        momento = os.time(),
    })

    local ok, err = pcall(function()
        TeleportService:TeleportAsync(ID_LUGAR_PARTIDA, jugadores, opciones)
    end)

    if not ok then
        warn("Fallo el teletransporte: " .. tostring(err))
        -- reintentar una vez tras una pausa
        task.delay(3, function()
            pcall(function()
                TeleportService:TeleportAsync(ID_LUGAR_PARTIDA, jugadores, opciones)
            end)
        end)
    end
end

-- En el lugar de destino, servidor:
Players.PlayerAdded:Connect(function(jugador)
    local datos = jugador:GetJoinData().TeleportData
    if typeof(datos) == "table" then
        print("Llego con datos de ronda")
    end
end)
```

- **Errores frecuentes:**
  - Confiar en los datos de teletransporte para cosas importantes: el cliente
    puede manipularlos en algunos flujos. Para datos sensibles, usa DataStore o
    MemoryStore y pasa solo un identificador.
  - No manejar el fallo: los teletransportes fallan a veces y el jugador se
    queda atascado. Siempre reintenta.
  - Usar `TeleportPartyAsync`, que esta obsoleto. Usa `TeleportAsync` con una
    lista de jugadores.
  - Teletransportar a un `PlaceId` que no pertenece al mismo juego sin
    configurarlo: falla.
- **Checklist sin errores:**
  - [ ] `TeleportAsync` en `pcall` con reintento
  - [ ] Los datos sensibles no viajan en `TeleportData`
  - [ ] Se comprueba el tipo de los datos al llegar

---

### 23. MarketplaceService

- **Que es:** compras de productos y pases dentro del juego.
- **Para que sirve:** monetizar. Y aqui un error significa cobrar sin entregar.
- **API implicada:** `PromptProductPurchase`, `ProcessReceipt`,
  `UserOwnsGamePassAsync`, `PromptGamePassPurchase`.
- **Donde va:** Script en `ServerScriptService`. **Solo uno** en todo el juego
  puede definir `ProcessReceipt`.
- **Codigo listo para pegar:**

```lua
local MarketplaceService = game:GetService("MarketplaceService")
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")

local recibos = DataStoreService:GetDataStore("RecibosProcesados_v1")

local PRODUCTOS: { [number]: (Player) -> boolean } = {
    [111111111] = function(jugador)
        -- entregar 500 monedas
        local datos = Gestor.obtener(jugador)
        if not datos then
            return false
        end
        datos.monedas += 500
        jugador:SetAttribute("Monedas", datos.monedas)
        return true
    end,
}

MarketplaceService.ProcessReceipt = function(info)
    local jugador = Players:GetPlayerByUserId(info.PlayerId)
    if not jugador then
        -- el jugador se fue. NO marcar como procesado:
        -- Roblox lo reintentara cuando vuelva.
        return Enum.ProductPurchaseDecision.NotProcessedYet
    end

    local claveRecibo = "recibo_" .. info.PurchaseId

    -- 1. idempotencia: si ya se proceso, confirmar sin entregar otra vez
    local okLectura, yaProcesado = pcall(function()
        return recibos:GetAsync(claveRecibo)
    end)

    if not okLectura then
        return Enum.ProductPurchaseDecision.NotProcessedYet
    end
    if yaProcesado then
        return Enum.ProductPurchaseDecision.PurchaseGranted
    end

    -- 2. entregar
    local entregar = PRODUCTOS[info.ProductId]
    if not entregar then
        warn("Producto desconocido: " .. tostring(info.ProductId))
        return Enum.ProductPurchaseDecision.NotProcessedYet
    end

    local okEntrega, entregado = pcall(entregar, jugador)
    if not okEntrega or not entregado then
        return Enum.ProductPurchaseDecision.NotProcessedYet
    end

    -- 3. marcar como procesado SOLO si la entrega funciono
    local okMarca = pcall(function()
        recibos:SetAsync(claveRecibo, os.time())
    end)

    if not okMarca then
        -- se entrego pero no se pudo marcar. Aun asi confirmamos:
        -- es mejor una entrega doble improbable que cobrar sin dar nada.
        warn("No se pudo marcar el recibo " .. claveRecibo)
    end

    return Enum.ProductPurchaseDecision.PurchaseGranted
end

-- Pases: se comprueban, no se procesan por recibo
local function tienePase(jugador: Player, idPase: number): boolean
    local ok, resultado = pcall(function()
        return MarketplaceService:UserOwnsGamePassAsync(jugador.UserId, idPase)
    end)
    return ok and resultado == true
end

return { tienePase = tienePase }
```

- **Errores frecuentes:**
  - **Devolver `PurchaseGranted` sin comprobar el `PurchaseId`.** Roblox puede
    reintentar el mismo recibo, y sin la comprobacion entregas dos veces. Esta
    comprobacion de idempotencia no es opcional.
  - Devolver `PurchaseGranted` cuando la entrega fallo: cobras y no das nada.
  - Dos scripts asignando `ProcessReceipt`: solo vale el ultimo, y las compras
    del otro sistema se pierden.
  - Guardar el recibo antes de entregar: si la entrega falla, queda marcado como
    hecho y el jugador nunca lo recibe.
  - Comprobar la compra desde el cliente.
- **Checklist sin errores:**
  - [ ] Hay un unico `ProcessReceipt` en todo el juego
  - [ ] Se comprueba el `PurchaseId` antes de entregar
  - [ ] Solo se devuelve `PurchaseGranted` si la entrega tuvo exito
  - [ ] El recibo se marca despues de entregar
  - [ ] Probado con la compra de prueba de Studio

---

## Tabla resumen: que usar para cada cosa

| Necesito | Uso |
|---|---|
| Guardar el progreso del jugador | `DataStore` con el gestor del punto 10 |
| Mostrar una estadistica en la lista | `leaderstats` |
| Tabla de clasificacion global | `OrderedDataStore` |
| Cola de emparejamiento entre servidores | `MemoryStoreService` |
| El cliente pide algo al servidor | `RemoteEvent` |
| El cliente necesita una respuesta | `RemoteFunction` con `InvokeServer` |
| Datos que se reemplazan constantemente | `UnreliableRemoteEvent` |
| Dos scripts del servidor se comunican | `BindableEvent` |
| Estado ligero visible en el cliente | Attributes |
| Anuncio a todos los servidores | `MessagingService` |
| Hablar con un servicio externo | `HttpService` |
| Mover jugadores entre lugares | `TeleportService` |
| Vender algo | `MarketplaceService` con `ProcessReceipt` |

---

## Checklist maestro de datos y red

- [ ] "Enable Studio Access to API Services" activado y el juego publicado
- [ ] Todo acceso a DataStore esta en `pcall` con reintentos
- [ ] Se distingue "fallo la lectura" de "jugador nuevo"
- [ ] Tras un fallo de carga, la sesion queda en modo no guardable
- [ ] Las claves usan `UserId`, nunca el nombre
- [ ] Los datos llevan `version` y hay migraciones
- [ ] Se guarda en `PlayerRemoving` y en `BindToClose`
- [ ] `BindToClose` espera menos de 30 segundos
- [ ] Hay autoguardado repartido en el tiempo
- [ ] Los cambios incrementales usan `UpdateAsync`
- [ ] Todo remote valida tipo, rango y frecuencia
- [ ] No se usa `InvokeClient` en ningun sitio
- [ ] `ProcessReceipt` es unico y comprueba `PurchaseId`
- [ ] Ningun secreto ni URL privada esta en `ReplicatedStorage`
- [ ] Probado con dos jugadores y cerrando el servidor a mitad

---

## Siguiente paso

Los sistemas que consumen estos datos en `mecanicas/08-sistemas.md`. La interfaz
que los muestra en `mecanicas/05-gui.md`. Errores concretos en
`mecanicas/09-errores-y-checklist.md`.
