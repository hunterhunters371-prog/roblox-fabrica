# 09 - Errores y listas de comprobacion

Modulo 9 y ultimo. Este es el modulo al que se viene **cuando algo falla**.

Todos los numeros de este documento estan sacados leyendo el codigo real de
`herramientas/`, no de memoria. Donde una regla no esta en el codigo, se dice
expresamente.

## Indice

| Parte | Contenido |
|---|---|
| A | El flujo completo, paso a paso |
| B | Requisitos del entorno |
| C | Reglas exactas del validador de animacion |
| D | Reglas exactas del validador de interfaz |
| E | Reglas exactas del lint del .rbxmx |
| F | Catalogo de errores del pipeline |
| G | Catalogo de errores de Luau en Studio |
| H | Catalogo de errores de rig y animacion |
| I | Listas de comprobacion |
| J | Como reportar un error al asistente |

---

# PARTE A - El flujo completo

`herramientas/revisar_pase.bat` es el unico punto de entrada. Version 6.0.

```text
            ARRASTRAS UN ARCHIVO SOBRE revisar_pase.bat
                              |
                  (o doble clic: coge el .json mas
                   reciente de la carpeta)
                              |
                              v
                   Que extension tiene?
                              |
     +---------------+--------+--------+----------------+
     |               |                 |                |
   .json           .rbxmx            .rbxm         (nada valido)
     |               |                 |                |
     v               v                 v                v
 Contiene       Contiene          leer_anim.py       ERROR:
 la clave       KeyframeSequence?  MIDE la           no hay .json
 "rig"?              |             animacion         .rbxmx ni
     |          +----+----+             |             .rbxm aqui
     |          |         |             v
  +--+--+      SI        NO       <nombre>_medida.txt
  |     |       |         |        y se abre en Notepad
 SI     NO      v         v
  |     |    Aviso:    lint +
  v     v    va al     render
  |     |    Animation
  |     |    Editor
  |     |
  |     +--> [1/3] spec_a_rbxmx.py  --> genera .rbxmx
  |          [2/3] roblox_lint.py   --> revisa el .rbxmx
  |          [3/3] render_rbxmx.py  --> genera .png y lo abre
  |
  +--------> [1/3] spec_anim.py     --> genera .rbxmx
             [2/3] ver_anim.py      --> genera .gif y lo abre
```

**Todo lo que sale por pantalla queda guardado en `ultimo_resultado.txt`**, en
la misma carpeta del `.bat`. Si algo falla, ese archivo es lo que hay que
copiar y pegar.

## A.1 Como decide si es animacion o interfaz

El `.bat` busca literalmente el texto `"rig"` dentro del JSON:

```text
findstr /c:"\"rig\"" archivo.json
```

| Encuentra `"rig"` | Conversor | Vista previa |
|---|---|---|
| Si | `spec_anim.py` | GIF con `ver_anim.py` |
| No | `spec_a_rbxmx.py` | PNG con `render_rbxmx.py` |

Consecuencia practica: **un JSON de interfaz nunca debe contener la palabra
`"rig"`**, ni siquiera dentro de un texto, o se procesara como animacion.

## A.2 Que hace cada script

| Script | Entrada | Salida |
|---|---|---|
| `spec_anim.py` | JSON con `rig` | `.rbxmx` KeyframeSequence |
| `spec_a_rbxmx.py` | JSON de interfaz | `.rbxmx` ScreenGui completo con su LocalScript |
| `roblox_lint.py` | `.rbxmx` de interfaz | Lista de ERRORES y AVISOS |
| `render_rbxmx.py` | `.rbxmx` de interfaz | `.png` de vista previa |
| `ver_anim.py` | JSON con `rig` | `.gif` con un maniqui de bloques |
| `leer_anim.py` | `.rbxm` binario | `<nombre>_medida.txt` con la animacion medida |

## A.3 Como buscar el archivo si haces doble clic

Si no arrastras nada, el `.bat` busca en este orden y coge el mas reciente:

1. `*.json` en la carpeta del `.bat`
2. `*.json` en subcarpetas, recursivo
3. `*.rbxmx` en la carpeta del `.bat`
4. `*.rbxm` en la carpeta del `.bat`

Por eso conviene arrastrar el archivo concreto: con doble clic puede coger uno
que no querias.

## A.4 De .rbxmx a Studio

| Tipo | Donde se inserta |
|---|---|
| Interfaz | Clic derecho en `StarterGui` > Insert from File... |
| Animacion | Dummy del rig correcto > carpeta `AnimSaves` > Insert from File... |

Para la animacion: Avatar > Rig Builder > R6 o R15, abre el Animation Editor con
el Dummy seleccionado, y arrastra el `.rbxmx` a su carpeta `AnimSaves`. Luego
Menu de los tres puntos > Export to Roblox para obtener el Animation ID.

---

# PARTE B - Requisitos del entorno

| Requisito | Como comprobarlo | Si falta |
|---|---|---|
| Python 3 en el PATH | `python --version` en la consola | El `.bat` dice "no encuentro Python en este equipo" |
| Pillow | `pip install pillow` | Falla el render PNG y el GIF |
| lz4 | `pip install lz4` | Falla `leer_anim.py` con `.rbxm` |

Los `.py` pueden estar junto al `.bat` **o** dentro de la subcarpeta
`herramientas\`. El `.bat` detecta las dos ubicaciones:

```bat
set "PY=%~dp0"
if not exist "%PY%spec_anim.py" (
    if exist "%~dp0herramientas\spec_anim.py" set "PY=%~dp0herramientas\"
)
```

Si mueves los `.py` a cualquier otra carpeta, el `.bat` deja de encontrarlos.

---

# PARTE C - Reglas exactas del validador de animacion

Todo lo de esta parte sale de `herramientas/spec_anim.py`.

## C.1 Limites numericos, textuales

```python
MAX_KEYFRAMES = 40
MAX_DURACION = 30.0
MAX_ANGULO = 180.0
MAX_DESPLAZAMIENTO = 2.5
```

| Regla | Valor exacto |
|---|---|
| Keyframes | Minimo 2, maximo 40 |
| Duracion total | Maximo 30.0 segundos |
| Angulo por eje | Maximo mas o menos 180.0 grados |
| Desplazamiento por eje | Maximo mas o menos 2.5 studs |
| Longitud de `nombre` | Maximo 40 caracteres |

## C.2 Campos de la raiz

| Campo | Obligatorio | Tipo | Valor por defecto |
|---|---|---|---|
| `rig` | Si | texto | - |
| `nombre` | Si | texto | - |
| `keyframes` | Si | lista | - |
| `loop` | No | booleano | `true` |
| `prioridad` | No | texto | `"accion"` |
| `easing` | No | texto | `"suave"` |

**Dato importante:** `easing` es un campo **de la raiz**, no de cada keyframe.
Se aplica a toda la animacion.

## C.3 Valores cerrados

```text
rig         : R15, R6
prioridad   : accion, core, idle, movimiento
easing      : elastica, instantaneo, lineal, rebote, suave
```

Equivalencias reales que aplica el conversor:

| `easing` | EasingStyle | EasingDirection |
|---|---|---|
| `suave` | Linear (0) | InOut (2) |
| `lineal` | Linear (0) | Out (1) |
| `rebote` | Bounce (4) | Out (1) |
| `elastica` | Elastic (2) | Out (1) |
| `instantaneo` | Constant (1) | Out (1) |

| `prioridad` | Token |
|---|---|
| `core` | 0 |
| `idle` | 1 |
| `movimiento` | 2 |
| `accion` | 3 |

## C.4 Articulaciones exactas por rig

**R6** (6 articulaciones, 5 animables):

```text
HumanoidRootPart        <- existe pero NO se anima
  Torso
    Head
    Left Arm
    Right Arm
    Left Leg
    Right Leg
```

Animables: `Torso`, `Head`, `Left Arm`, `Right Arm`, `Left Leg`, `Right Leg`.

Fijate en que `Left Arm` lleva **un espacio**. `LeftArm` sin espacio es un error.

**R15** (16 articulaciones, 15 animables):

```text
HumanoidRootPart        <- existe pero NO se anima
  LowerTorso
    LeftUpperLeg
      LeftLowerLeg
        LeftFoot
    RightUpperLeg
      RightLowerLeg
        RightFoot
    UpperTorso
      Head
      LeftUpperArm
        LeftLowerArm
          LeftHand
      RightUpperArm
        RightLowerArm
          RightHand
```

En R15 no existen `Torso`, `Left Arm` ni `Right Arm`. En R6 no existe ninguno de
los nombres de R15. **El unico nombre comun a los dos rigs es `Head`.** Por eso,
si mezclas rigs, lo unico que se mueve es la cabeza.

## C.5 Reglas de las poses

| Regla | Comportamiento |
|---|---|
| `t` debe ser numero | Un texto da error |
| `t` no puede ser negativo | Da error |
| `t` debe crecer estrictamente | Dos tiempos iguales dan error |
| `poses` debe existir y ser objeto | Si falta, error |
| `poses` no puede estar vacio | "Al menos una articulacion debe moverse" |
| No se puede animar `HumanoidRootPart` | Error explicito |
| Cada pose es `[x,y,z]` o `[x,y,z,px,py,pz]` | 4 o 5 valores dan error |
| Al menos una articulacion debe moverse | Si todo es `[0,0,0]`, error |

## C.6 Formato de los mensajes de error

La ruta que imprime el validador tiene esta forma exacta:

```text
raiz.keyframes[0].poses.RightUpperArm tiene 200 grados. Maximo +/-180.
raiz.keyframes[3].t = 1.2. Los tiempos deben ir en orden creciente (el anterior era 1.5).
raiz.nombre tiene 47 caracteres y solo caben 40.
raiz.rig = "R12" no existe. Rigs validos: R15, R6
```

**El indice de `keyframes` empieza en 0**, no en 1. El primer keyframe es
`raiz.keyframes[0]`.

Cuando hay errores, el validador imprime la lista y **no genera ningun `.rbxmx`**.

---

# PARTE D - Reglas exactas del validador de interfaz

Todo lo de esta parte sale de `herramientas/spec_a_rbxmx.py`.

## D.1 Como se calculan los limites de texto

Aqui esta la clave que casi nadie entiende. Los limites **no son fijos**: se
calculan con esta funcion.

```python
ANCHO_CHAR = 0.55

def cabe(texto, ancho_px, text_size, donde):
    limite = int(ancho_px / (text_size * ANCHO_CHAR))
    if len(texto) > limite:
        err("%s tiene %d caracteres y solo caben %d. Acortalo.")
```

Es decir: **limite = ancho de la caja en pixeles / (tamano de letra x 0.55)**.

## D.2 Campos de la cabecera y sus limites reales

| Campo | Obligatorio | Ancho | Letra | Limite real |
|---|---|---|---|---|
| `temporada` | Si | 190 px | 12 | **28 caracteres** |
| `titulo` | Si | 630 px | 38 | **30 caracteres** |
| `subtitulo` | Si | 630 px | 14 | **81 caracteres** |
| `tiempo` | Si | 150 px | 24 | **11 caracteres** |

El prompt `prompts/PROMPT-1-DISENO.md` pide margenes mas estrechos (25, 28, 80,
11). Eso es a proposito: son valores conservadores que siempre pasan. Los de
arriba son los limites duros del codigo.

## D.3 Campos numericos

| Campo | Obligatorio | Tipo | Regla exacta |
|---|---|---|---|
| `niveles` | Si | entero | Entre 2 y 20 |
| `nivel` | Si | entero | Entre 1 y `niveles` |
| `xp` | Si | entero | Entre 0 y `xpPorNivel - 1` |
| `xpPorNivel` | Si | entero | 1 o mas |
| `xpPorPremio` | No | entero | Por defecto 100 |
| `xpPorPremioPremium` | No | entero | Por defecto 150 |

Estos cuatro campos obligatorios se olvidan constantemente. Un JSON de pase sin
`nivel`, `xp` y `xpPorNivel` **no compila**.

## D.4 Campos de texto opcionales

| Campo | Por defecto | Regla |
|---|---|---|
| `resaltado` | `""` | Debe aparecer **dentro** de `titulo` |
| `textoAbrirTodos` | `"Abrir todos"` | Sin `< > &` |
| `textoPremium` | `"Mejorar"` | Sin `< > &` |

`resaltado` pinta esa parte del titulo en cian. Si el texto de `resaltado` no
aparece literalmente dentro de `titulo`, el validador da error.

## D.5 Las dos pistas

| Campo | Obligatorio | Regla |
|---|---|---|
| `gratis` | Si | Lista de 1 a 6 premios |
| `premium` | Si | Lista de 1 a 6 premios |

## D.6 Campos de un premio

| Campo | Obligatorio | Tipo |
|---|---|---|
| `etiqueta` | Si | texto |
| `color` | Si | texto de la paleta |
| `icono` | Si | texto, un emoji |
| `titulo` | Si | texto |
| `desc` | Si | texto |
| `bonus` | No | texto, por defecto `""` |
| `nuevo` | No | booleano, por defecto `false` |

Paleta cerrada de ocho colores:

```text
azul, cian, dorado, morado, naranja, rojo, rosa, verde
```

## D.7 Los limites de las cartas dependen de cuantas hay

Este es el punto que mas confunde. El ancho de cada carta se reparte asi:

```python
CONTENT_W = 1064
GAP = 16
cw = (CONTENT_W - GAP * (n - 1)) // n
interior = cw - 24
```

**Cuantos mas premios pongas en una pista, mas estrecha es cada carta y menos
texto cabe.** Tabla calculada con las formulas reales del codigo:

| Premios en la pista | Ancho carta | Interior | `etiqueta` | `titulo` | `desc` | `bonus` |
|---|---|---|---|---|---|---|
| 1 | 1064 px | 1040 px | 185 | 126 | 343 | 131 |
| 2 | 524 px | 500 px | 87 | 60 | 165 | 61 |
| 3 | 344 px | 320 px | 54 | 38 | 105 | 38 |
| 4 | 254 px | 230 px | 38 | 27 | 76 | 26 |
| 5 | 200 px | 176 px | 28 | 21 | 58 | 19 |
| 6 | 164 px | 140 px | 21 | 16 | 46 | 14 |

Los numeros son el maximo de caracteres. Si escribes para 6 premios y luego
quitas dos, tus textos siguen siendo validos. Al reves no: **anadir un premio
puede invalidar textos que antes pasaban**.

Si quieres textos que valgan siempre, usa la fila de 6 premios como referencia:
etiqueta 21, titulo 16, desc 46, bonus 14.

## D.8 Caracteres prohibidos

Ni `<`, ni `>`, ni `&` en ningun campo de texto, ni en la animacion ni en la
interfaz. El conversor escapa el XML exactamente una vez y esos tres caracteres
lo romperian.

Escribe "y" en lugar de `&`. Para comillas no hay problema.

---

# PARTE E - Reglas exactas del lint del .rbxmx

Todo lo de esta parte sale de `herramientas/roblox_lint.py`. Este script **no
revisa el JSON**: revisa el `.rbxmx` ya generado, imitando lo que haria Roblox
Studio.

Devuelve codigo de salida 1 si hay algun ERROR. Los AVISOS no detienen el flujo.

## E.1 Las diez reglas

| Codigo | Nivel | Que comprueba |
|---|---|---|
| `XML` | ERROR | El archivo es XML valido |
| `REF` | ERROR | No hay atributos `referent` repetidos |
| `R1-CLASE` | ERROR | La clase esta en la lista permitida |
| `R2-PROP` | ERROR | La propiedad existe en esa clase |
| `R3-OFFSET` | ERROR | Los `Offset` de UDim y UDim2 son enteros |
| `R4-ENUM` | ERROR | El token del enum esta dentro de rango |
| `R5-COLOR` | ERROR | Los componentes Color3 estan entre 0 y 1 |
| `R6-RICHTEXT` | ERROR | Coherencia entre el texto y `RichText` |
| `R7-TEXTO` | AVISO | El texto cabe en su caja |
| `R8-DESBORDE` | AVISO | El hijo no se sale del padre |
| `R9-ZINDEX` | AVISO | `ZIndexBehavior` es Global |
| `R10-CLIC` | AVISO | Un Frame no se llama como un boton |

## E.2 Clases permitidas (R1)

```text
ScreenGui, Frame, ScrollingFrame, CanvasGroup,
TextLabel, TextButton, TextBox,
ImageLabel, ImageButton, ViewportFrame,
UICorner, UIStroke, UIPadding, UIListLayout,
UIAspectRatioConstraint, UISizeConstraint, UIGradient,
LocalScript, ModuleScript, Folder
```

Cualquier otra clase en el `.rbxmx` es un ERROR. Fijate en que **no** estan
permitidas `UIGridLayout`, `UIScale`, `UITextSizeConstraint`, `VideoFrame` ni
`BillboardGui`. Si necesitas alguna, hay que anadirla al conjunto `CLASES` de
`roblox_lint.py`.

## E.3 Rangos de enum (R4)

| Propiedad | Token maximo valido |
|---|---|
| `Font` | 60 |
| `TextXAlignment` | 2 |
| `TextYAlignment` | 2 |
| `ZIndexBehavior` | 1 |
| `ApplyStrokeMode` | 1 |
| `ScrollingDirection` | 4 |
| `AutomaticSize` | 3 |
| `SortOrder` | 2 |
| `FillDirection` | 1 |
| `ScaleType` | 3 |
| `LineJoinMode` | 2 |
| `ElasticBehavior` | 2 |

## E.4 Las tres reglas que mas se disparan

**R3-OFFSET.** `UDim.Offset` es un entero de 32 bits en el motor. Si el XML
lleva `<XO>12.5</XO>`, Studio lo convierte en **0**, no en 12 ni en 13. El
elemento salta a la esquina. Por eso `spec_a_rbxmx.py` redondea con:

```python
def ent(v):
    return int(round(float(v)))
```

**R5-COLOR.** Los `Color3` del XML van de 0 a 1, no de 0 a 255. Un `<R>255</R>`
es un ERROR. El conversor divide entre 255.0 al escribir.

**R6-RICHTEXT.** Tiene tres comprobaciones distintas:

| Situacion | Mensaje |
|---|---|
| El texto contiene `&lt;` o `&amp;` | Se escapo dos veces, se vera el markup crudo |
| `RichText` true y las etiquetas no cuadran | "etiquetas sin cerrar: N abren, M cierran" |
| `RichText` false y hay etiquetas `font`, `b`, `i`, `u`, `s`, `stroke`, `br` | Se veran como caracteres |

## E.5 Los avisos, explicados

**R7-TEXTO** usa la misma constante `ANCHO_CHAR = 0.55`. Si el texto no esta
envuelto y su ancho estimado supera el de la caja por mas de un 18 por ciento,
avisa. Si esta envuelto, calcula cuantas lineas necesita y compara con el alto.

**R8-DESBORDE** solo se comprueba cuando el padre **no** tiene
`ClipsDescendants`. Tiene en cuenta el `AnchorPoint`.

**R9-ZINDEX** avisa una sola vez si ningun `ScreenGui` tiene
`ZIndexBehavior = 1` (Global). Con sombras duras y comportamiento Sibling, la
sombra de una tarjeta puede taparse con la vecina.

**R10-CLIC** avisa si un `Frame` tiene en el nombre `btn`, `button` o `boton`,
porque un Frame no dispara `MouseButton1Click`. Los nombres que contienen
`shadow` o `sombra` estan excluidos a proposito: la sombra dura de un boton **si**
debe ser un Frame.

---

# PARTE F - Catalogo de errores del pipeline

| # | Sintoma | Causa real | Solucion |
|---|---|---|---|
| 1 | "no encuentro Python en este equipo" | Python no esta en el PATH | Reinstala Python marcando "Add to PATH" |
| 2 | "EL JSON NO ES VALIDO, linea N, columna M" | Coma de mas, comilla sin cerrar, llave suelta | Pega el mensaje completo a la IA y pide el JSON entero corregido |
| 3 | "No encontre ningun .json, .rbxmx ni .rbxm" | El `.bat` esta en otra carpeta que el archivo | Arrastra el archivo encima del `.bat` en vez de hacer doble clic |
| 4 | Procesa un archivo que no querias | Doble clic coge el `.json` mas reciente | Arrastra siempre el archivo concreto |
| 5 | Un JSON de interfaz se procesa como animacion | Contiene el texto `"rig"` en algun sitio | Quita esa palabra de todos los campos |
| 6 | "No pude leer ese .rbxm" | Falta la libreria lz4 | `pip install lz4` |
| 7 | El render falla o no crea el PNG | Falta Pillow | `pip install pillow` |
| 8 | "la clase X no esta en la lista permitida" | El `.rbxmx` usa una clase fuera de `CLASES` | Anade la clase a `roblox_lint.py` o no la uses |
| 9 | "X no es una propiedad valida de Y" | Propiedad mal escrita o inexistente | Revisa `PROPS` en `roblox_lint.py` |
| 10 | "UDim.Offset es entero, un decimal se convierte en 0" | Offset con decimales en el XML | Redondea a entero |
| 11 | "debe estar entre 0 y 1 (no 0..255)" | Color3 en formato 0-255 | Divide entre 255 |
| 12 | "se escapo dos veces y se vera el markup crudo" | El texto llevaba `<` o `&` desde el JSON | Quita esos caracteres del JSON |
| 13 | "etiquetas sin cerrar: N abren, M cierran" | RichText con markup incompleto | Cierra todas las etiquetas |
| 14 | "hay referentes repetidos" | Dos `Item` con el mismo `referent` | Regenera el `.rbxmx`, no lo edites a mano |
| 15 | "tiene N caracteres y solo caben M" | Texto mas largo que su caja | Acorta el texto, no toques el codigo |
| 16 | "raiz.nivel = N. Debe estar entre 1 y raiz.niveles" | `nivel` fuera de rango | Ajusta `nivel` o sube `niveles` |
| 17 | "raiz.xp = N. Debe estar entre 0 y xpPorNivel - 1" | `xp` mayor o igual que `xpPorNivel` | Baja `xp` |
| 18 | "raiz.resaltado no aparece dentro de raiz.titulo" | El texto resaltado no esta en el titulo | Copia el fragmento exacto del titulo |
| 19 | "no existe. Colores validos: ..." | Color fuera de la paleta de ocho | Usa uno de los ocho nombres |
| 20 | "tiene N premios. Debe tener entre 1 y 6" | Lista `gratis` o `premium` fuera de rango | Ajusta la cantidad |
| 21 | Todo pasa pero el texto se ve cortado en el PNG | Aviso R7 ignorado | Acorta el texto o reduce el numero de premios |
| 22 | El PNG se ve bien pero en Studio no | El `.rbxmx` se edito a mano tras el lint | Vuelve a generar desde el JSON |

---

# PARTE G - Catalogo de errores de Luau en Studio

Estos ya no vienen del pipeline: son los errores del codigo que escribes o que
te da una IA.

| # | Mensaje de Studio | Causa real | Solucion |
|---|---|---|---|
| 23 | `attempt to index nil with 'X'` | El objeto no existe todavia o el nombre esta mal | `WaitForChild` con timeout, y comprobar que no es `nil` |
| 24 | `attempt to call a nil value` | La funcion no existe o el modulo no la exporta | Revisa el nombre y que el modulo la devuelva |
| 25 | `attempt to perform arithmetic (add) on nil` | Una variable esperada no llego | Da valor por defecto: `local n = valor or 0` |
| 26 | `Infinite yield possible on 'X:WaitForChild("Y")'` | El hijo nunca aparece: nombre mal escrito, o esta en otro contenedor | Pon timeout: `WaitForChild("Y", 10)` y comprueba el resultado |
| 27 | `Unable to cast value to Object` | Se paso un texto donde se esperaba una instancia | Revisa los argumentos de la funcion |
| 28 | `Unable to assign property X. Y expected` | Tipo equivocado, por ejemplo `Vector3` en `Position` de una GUI | Usa `UDim2` en interfaz y `Vector3` en el mundo |
| 29 | `Unable to assign property Parent. Instance expected` | Se asigno `nil` como padre | Comprueba que el contenedor existe |
| 30 | `invalid argument #1 to 'CFrame.new'` | Se paso `nil` o un tipo raro | Comprueba la variable antes |
| 31 | `Requested module experienced an error while loading` | El ModuleScript tiene un error, o hay un ciclo de `require` | Abre ese modulo, mira su error real, y rompe el ciclo |
| 32 | `Maximum event re-entrancy depth exceeded` | Un evento se dispara a si mismo en cadena | Anade una bandera o desconecta antes de reasignar |
| 33 | `Script timeout: exhausted allowed execution time` | Bucle sin `task.wait()` | Anade `task.wait()` dentro del bucle |
| 34 | `Studio Access to API Services is not enabled` | No esta activado en Game Settings | Game Settings > Security > Enable Studio Access to API Services |
| 35 | `502: API Services rejected request` o peticion encolada | Throttling de DataStore | Espacia las escrituras y usa reintentos con espera creciente |
| 36 | `Http requests are not enabled` | HttpService desactivado | Game Settings > Security > Allow HTTP Requests |
| 37 | `Animation failed to load` | El Animation ID no existe, no es publico, o no es tuyo | Publica la animacion desde tu cuenta y usa ese ID |
| 38 | `RemoteEvent is not a valid member of ...` | El cliente busco el remote antes de que existiera | `WaitForChild` con timeout en el cliente |
| 39 | `Players.X.PlayerGui... is not a valid member` | Se busco en `StarterGui` en vez de `PlayerGui` | En ejecucion la interfaz vive en `PlayerGui` |
| 40 | El LocalScript no hace nada y no da error | Esta en un sitio donde no corre en cliente | LocalScript solo corre en `StarterPlayerScripts`, `StarterCharacterScripts`, `StarterGui`, `ReplicatedFirst` o dentro de una Tool |
| 41 | `SetNetworkOwner: cannot be called on an anchored part` | La parte esta anclada | Comprueba `Anchored` antes de llamar |
| 42 | Todo funciona en Studio pero no en el juego publicado | Se dependia de algo solo de Studio | Prueba siempre en un servidor real con 2 jugadores |

---

# PARTE H - Catalogo de errores de rig y animacion

| # | Sintoma | Causa real | Solucion |
|---|---|---|---|
| 43 | Solo se mueve la cabeza | Se mezclaron R6 y R15. `Head` es el unico nombre comun | Elige un rig y usa solo sus nombres |
| 44 | "no existe en el rig R6" | Se usaron nombres de R15 en un JSON R6 | Consulta la Parte C.4 |
| 45 | "Left Arm no existe" en R15 | R15 no tiene `Left Arm`, tiene `LeftUpperArm` | Cambia el nombre |
| 46 | El bucle da un salton visible | La ultima pose no coincide con la primera | Copia la pose del primer keyframe al ultimo |
| 47 | La animacion no se reproduce, otra la tapa | Prioridad insuficiente | Sube a `accion`, que es el token 3 |
| 48 | La animacion se ve pero el personaje sigue caminando | La animacion de caminar tiene la misma prioridad | Usa `accion` para lo que debe tapar al movimiento |
| 49 | El personaje se estira de forma rara | Se abuso del desplazamiento de 6 valores | Baja los valores `px`, `py`, `pz`, o quitalos |
| 50 | "desplaza N studs. Maximo +/-2.5" | Desplazamiento fuera de rango | Reduce el valor |
| 51 | "tiene N grados. Maximo +/-180" | Angulo fuera de rango | Un giro de 200 grados es lo mismo que uno de -160 |
| 52 | "los tiempos deben ir en orden creciente" | Dos `t` iguales o desordenados | Ordena y separa los tiempos |
| 53 | "ninguna articulacion se mueve" | Todas las poses son `[0,0,0]` | Al menos un valor distinto de cero |
| 54 | "no se anima la raiz" | Hay una pose para `HumanoidRootPart` | Quitala. El desplazamiento del cuerpo va en el torso |
| 55 | El GIF se ve bien pero en Studio no | El Dummy es del otro rig | Inserta un Dummy del rig que dice el JSON |
| 56 | El `.rbxmx` no aparece en el Animation Editor | Se solto fuera de `AnimSaves` | Debe ir dentro de la carpeta `AnimSaves` del Dummy |
| 57 | Los brazos suben hacia el lado equivocado en R6 | En R6 el eje X sube los brazos y es **siempre negativo** en los dos brazos | Pon valores negativos en X para ambos brazos |
| 58 | Los brazos suben hacia el lado equivocado en R15 | En R15 el eje Z sube los brazos: Z positivo el derecho, Z negativo el izquierdo | Invierte el signo del brazo afectado |
| 59 | La animacion dura menos de lo esperado | `t` es en segundos, no en frames | Ajusta los tiempos en segundos |
| 60 | "la animacion dura Ns. Maximo 30s" | El ultimo `t` pasa de 30 | Acorta o divide en dos animaciones |

---

# PARTE I - Listas de comprobacion

## I.1 Antes de dar por bueno un JSON de animacion

- [ ] Tiene la clave `rig` con valor `R6` o `R15`
- [ ] `nombre` tiene 40 caracteres o menos, sin `<`, `>` ni `&`
- [ ] Todos los nombres de articulacion son del rig elegido
- [ ] `Left Arm` y `Right Arm` llevan su espacio, si es R6
- [ ] Ninguna pose es de `HumanoidRootPart`
- [ ] Hay entre 2 y 40 keyframes
- [ ] Los `t` crecen estrictamente y ninguno es negativo
- [ ] El ultimo `t` no pasa de 30
- [ ] Ningun angulo pasa de mas o menos 180
- [ ] Ningun desplazamiento pasa de mas o menos 2.5
- [ ] Al menos una articulacion se mueve
- [ ] Si `loop` es true, la ultima pose es igual a la primera
- [ ] `prioridad` es uno de: accion, core, idle, movimiento
- [ ] `easing` es uno de: elastica, instantaneo, lineal, rebote, suave
- [ ] Se paso por `revisar_pase.bat` y el GIF se ve razonable

## I.2 Antes de dar por bueno un JSON de interfaz

- [ ] **No** contiene en ningun sitio la palabra `"rig"`
- [ ] Estan los cuatro textos de cabecera: `temporada`, `titulo`, `subtitulo`, `tiempo`
- [ ] Estan los cuatro numeros: `niveles`, `nivel`, `xp`, `xpPorNivel`
- [ ] `niveles` esta entre 2 y 20
- [ ] `nivel` esta entre 1 y `niveles`
- [ ] `xp` es menor que `xpPorNivel`
- [ ] `gratis` y `premium` tienen entre 1 y 6 premios cada una
- [ ] Cada premio tiene `etiqueta`, `color`, `icono`, `titulo` y `desc`
- [ ] Todos los colores estan en la paleta de ocho
- [ ] Si hay `resaltado`, aparece literalmente dentro de `titulo`
- [ ] Ningun texto contiene `<`, `>` ni `&`
- [ ] Los textos respetan la fila de la tabla D.7 que corresponde al numero de premios
- [ ] Se paso por `revisar_pase.bat` y el PNG se ve correcto
- [ ] El lint no dio ningun ERROR

## I.3 Antes de dar por buena una mecanica en Luau

- [ ] El script dice en su cabecera de que tipo es y en que contenedor va
- [ ] Es Script, LocalScript o ModuleScript, y esta en el sitio correcto
- [ ] Los servicios se obtienen con `game:GetService("...")`
- [ ] Todos los `WaitForChild` tienen timeout
- [ ] Se comprueba que cada objeto buscado no es `nil`
- [ ] Toda llamada que puede fallar esta en `pcall`
- [ ] Los datos importantes se validan en el servidor, no en el cliente
- [ ] Cada remote valida tipo, rango y frecuencia de sus argumentos
- [ ] No se usa ninguna API obsoleta: `BodyPosition`, `BodyVelocity`, `BodyGyro`, `FindPartOnRay`, `SetPrimaryPartCFrame`, `Velocity`, `TeleportPartyAsync`
- [ ] Las conexiones se desconectan al destruir o al salir el jugador
- [ ] El estado por jugador se limpia en `PlayerRemoving`
- [ ] Los bucles tienen `task.wait()` y condicion de salida
- [ ] Los angulos de CFrame pasan por `math.rad`
- [ ] Probado en Play Solo
- [ ] Probado con Test > 2 Players
- [ ] Probado muriendo y reapareciendo

## I.4 Antes de insertar un .rbxmx en Studio

- [ ] El validador dijo "OK el JSON es valido"
- [ ] El lint dio 0 ERRORES
- [ ] El PNG o el GIF se ve como esperabas
- [ ] Si es interfaz, va en `StarterGui`
- [ ] Si es animacion, va en `AnimSaves` de un Dummy del rig correcto
- [ ] No se edito el `.rbxmx` a mano despues de generarlo

---

# PARTE J - Como reportar un error al asistente

Cuando algo falle, manda **estas cuatro cosas**. Con menos, la respuesta sera
una suposicion.

```text
1. El archivo ultimo_resultado.txt completo, o el texto exacto del error.
   No lo resumas ni lo recortes.

2. El JSON completo que estabas procesando.

3. Si es animacion: el rig (R6 o R15).

4. Que esperabas que pasara.
```

Y la frase que hay que poner delante, tal como la sugiere el propio `.bat`:

```text
Corrige el JSON. El validador devolvio estos errores:
[pega aqui la lista]
Devuelve el JSON completo, sin explicaciones.
```

## J.1 Por que el JSON completo y no un fragmento

Porque parchear un JSON a mano casi siempre introduce un error nuevo: una coma
que sobra, una llave que falta, una comilla sin cerrar. La regla del repositorio
es que **la IA devuelve siempre el archivo entero** y tu lo sustituyes de golpe.

## J.2 Si el error es de Luau y no del pipeline

```text
1. El mensaje exacto de la Output de Studio, con el nombre del script
   y el numero de linea.

2. El script completo, no solo la linea que falla.

3. Donde esta ese script exactamente
   (por ejemplo: ServerScriptService > Sistemas > Economia).

4. Si es Script, LocalScript o ModuleScript.

5. Que hiciste justo antes de que fallara.
```

El punto 3 es el que mas se olvida y el que mas veces explica el fallo por si
solo: la mitad de los errores de Luau en Roblox son un script correcto en el
contenedor equivocado.

---

## Resumen de los diez fallos mas repetidos

| # | Fallo | Recordatorio |
|---|---|---|
| 1 | Mezclar R6 y R15 | Solo `Head` es comun a los dos |
| 2 | Olvidar `nivel`, `xp` y `xpPorNivel` | Son obligatorios en el JSON de interfaz |
| 3 | Textos demasiado largos | El limite depende de cuantos premios hay |
| 4 | Usar `<`, `>` o `&` | Rompen el XML |
| 5 | `ResetOnSpawn` en true | La interfaz se reinicia al morir |
| 6 | Buscar la interfaz en `StarterGui` | En ejecucion vive en `PlayerGui` |
| 7 | `WaitForChild` sin timeout | Cuelga el script en silencio |
| 8 | Confiar en el cliente | El servidor decide siempre |
| 9 | Restriccion sobre una parte anclada | No hace absolutamente nada |
| 10 | Angulos en grados donde van radianes | Usa `math.rad` |

---

## Vuelta al catalogo

`mecanicas/00-INDICE.md` para el indice completo. Para pedir mecanicas nuevas a
otra IA, `prompts/PROMPT-3-MECANICAS.md`.
