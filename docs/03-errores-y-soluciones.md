# Errores sufridos y su solucion

## 1. Caracter no ASCII en un identificador de Luau

Error literal en la consola de Studio:

```
Players.BosneSUS_V2.PlayerGui.Interfaz.Cliente:201: Expected identifier when parsing expression, got Unicode character U+f1
```

Causa: la variable se llamaba `ladosVinneta` con ene espanola. Luau no admite
no ASCII en identificadores y el LocalScript entero no arranca, por lo que el
juego se ve sin HUD y parece que no hay codigo.

Solucion: renombrar y anadir al generador un guardia que rechaza cualquier
caracter no ASCII fuera de cadenas. Probado con una insercion deliberada:

```
- caracter no ASCII fuera de cadenas: 'n con virgulilla' en lineas [5]
```

## 2. Propiedad inexistente en StarterPlayer

```
HumanoidRigType is not a valid member of StarterPlayer "StarterPlayer"
```

Causa: `game.StarterPlayer.HumanoidRigType` no existe.
Solucion: leer el tipo de esqueleto del humanoide en marcha con `humanoide.RigType`.

## 3. La animacion propia no sonaba

Sintoma: `GetPlayingAnimationTracks()` solo devolvia `WalkAnim` y `FallAnim`,
las dos de prioridad `Core`, aunque la carpeta de animaciones existia y el
registro manual funcionaba (`registro=true`, `carga=true`, `longitud=0.67`).

Causa real: la carpeta `Animaciones` replica al cliente DESPUES de que aparece
el personaje, y la carga se intentaba una sola vez al conectar el personaje.

Solucion: reintentos. Ver `06-animaciones-propias.md`.

## 4. Falso positivo del generador con elseif

```
- bloques descuadrados: function 28 + if 47 + do 12 = 87, end 89
```

Causa: el patron `\bif\b` casaba dentro de `elseif`, que no abre bloque nuevo.
Solucion: contar solo `if` que no vengan de `elseif`.

## 5. Cadena de comandos abortada en la terminal

Un `grep` sin coincidencias devuelve codigo 1 y mata la cadena `&&`.
Solucion: separar con `;` y usar `grep -n` amplio mas `sed -n` para el tramo exacto.

## 6. Sandbox sin internet

```
curl: (6) Could not resolve host: raw.githubusercontent.com
```

Solucion: escribir los archivos desde el propio agente, no descargarlos.

## 7. La conexion MCP con Studio se cae

Sintomas: `Failed to connect to MCP server` o `{"studios":[]}`.
Al reabrir el lugar cambia el `studio_id`.
Solucion: `list_roblox_studios` de nuevo y comprobar el estado con una sonda
antes de replicar, porque los scripts vivos pueden haber vuelto atras si no se
guardo el lugar. Guardar con Ctrl+S despues de cada replica.

## 8. Limite real de las animaciones sin publicar

`KeyframeSequenceProvider:RegisterKeyframeSequence` devuelve un id temporal
`hash://` que solo vale dentro de Studio. En un juego publicado hay que subir la
animacion y usar `Animation.AnimationId`.
