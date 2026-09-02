# GUIA COMPLETA — Fabrica Roblox

Proyecto: **LAST DELIVERY: 60 SECONDS**

Esta guia recopila todo el conocimiento del repositorio en un solo lugar:
las mecanicas y sus usos, como ejecutar el sistema sin errores, los modelos
JSON de animacion e interfaz, y el flujo de trabajo multiagente.

> **Verificada contra el codigo fuente.** Todos los limites y reglas de este
> documento se comprobaron leyendo `herramientas/spec_anim.py`,
> `spec_a_rbxmx.py` y `roblox_lint.py`, no la documentacion. Cuando el codigo
> y un prompt no coinciden, aqui manda el codigo y se dice cual es cual.
> El detalle de la auditoria esta en [VERIFICACION.md](VERIFICACION.md).

---

## 1. Que es este repositorio

Un sistema para que cualquier IA genere **interfaces (GUI)** y **animaciones
de personaje** para Roblox en un formato que se valida y se convierte solo.

La regla de oro: **la IA nunca escribe XML de Roblox ni codigo Lua.** Solo
escribe un **JSON**. Un conversor (Python) traduce ese JSON a `.rbxmx` y lo
valida. Por eso no se rompe.

### Estructura

```
herramientas/   los .py y el revisar_pase.bat (el pipeline)
prompts/        los textos que le das a la IA (PROMPT 1 y 2)
animaciones/    animaciones que ya funcionan (.json editable)
interfaces/     interfaces que ya funcionan (.json editable)
referencias/    medidas reales de animaciones analizadas
mecanicas/      catalogo completo de mecanicas (9 modulos)
```

---

## 2. Como ejecutar el sistema sin errores

### 2.1 Requisitos del entorno

| Requisito | Comprobacion | Si falta |
|---|---|---|
| Python 3 en el PATH | `python --version` | El .bat dice "no encuentro Python" |
| Pillow | `pip install pillow` | Falla el render PNG y el GIF |
| lz4 | `pip install lz4` | Falla `leer_anim.py` con `.rbxm` |

Los `.py` deben estar junto al `.bat` o en la subcarpeta `herramientas\`.

### 2.2 El flujo de revisar_pase.bat (v6.0)

El `.bat` es el unico punto de entrada. **Arrastra siempre el archivo encima
del .bat.** Con doble clic coge el `.json` mas reciente de la carpeta, que a
menudo no es el que querias.

```
        ARRASTRAS UN ARCHIVO SOBRE revisar_pase.bat
                          |
                          v
               Que extension tiene?
     +---------------+--------+--------+----------------+
   .json           .rbxmx            .rbxm         (nada valido)
     |               |                 |                |
     v               v                 v                v
 Contiene       Contiene          leer_anim.py       ERROR:
 la clave       KeyframeSequence?  MIDE la animacion  no hay .json
 "rig"?              |             -> _medida.txt    .rbxmx ni .rbxm
     |          +----+----+             |
  +--+--+      SI        NO             v
  |     |       |         |        <nombre>_medida.txt
 SI     NO      v         v        y se abre en Notepad
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

**Todo lo que sale por pantalla queda guardado en `ultimo_resultado.txt`.**
Si algo falla, ese archivo es lo que hay que copiar y pegar.

### 2.3 Como decide si es animacion o interfaz

El `.bat` busca literalmente el texto `"rig"` dentro del JSON con `findstr`:

| Encuentra `"rig"` | Conversor | Vista previa |
|---|---|---|
| Si | `spec_anim.py` | GIF con `ver_anim.py` |
| No | `spec_a_rbxmx.py` | PNG con `render_rbxmx.py` |

Un JSON de interfaz **nunca** debe contener la palabra `"rig"`, ni siquiera
dentro de un texto, o se procesara como animacion.

### 2.4 De JSON a Studio — Animaciones

```
1. La IA devuelve un bloque JSON y nada mas
2. Guardas el archivo en animaciones/  (por ejemplo mi_correr.json)
3. Arrastras el archivo encima de herramientas/revisar_pase.bat
   - detecta la clave "rig" y sabe que es una animacion
   - valida campos, limites y articulaciones
   - si falla, imprime la ruta exacta del error
   - si pasa, genera mi_correr.rbxmx
4. Opcional: python ver_anim.py mi_correr.json  ->  mi_correr.gif
   (maniqui de bloques para revisar el movimiento sin abrir Studio)
5. En Studio:
   - Modelo > Rig Builder > R6 o R15  (el MISMO rig del JSON)
   - Avatar > Animation Editor, selecciona el Dummy
   - arrastra mi_correr.rbxmx dentro de la carpeta AnimSaves del Dummy
     (o clic derecho en AnimSaves > Insert from File...)
   - en el editor, menu de tres puntos > Export to Roblox
   - copia el Asset ID que te da
6. Ese ID va en la propiedad AnimationId de un objeto Animation
```

### 2.5 De JSON a Studio — Interfaces

```
1. La IA devuelve un bloque JSON y nada mas
2. Guardas el archivo en interfaces/  (por ejemplo temporada3.json)
3. Arrastras el archivo encima de herramientas/revisar_pase.bat
   - no encuentra la clave "rig", asi que lo trata como interfaz
   - spec_a_rbxmx.py valida y genera temporada3.rbxmx
   - roblox_lint.py revisa el .rbxmx (debe decir ERRORES 0)
   - render_rbxmx.py genera una vista previa PNG
4. Miras el PNG. Si el texto se corta o el color no encaja, corriges el JSON
   y repites. No toques el PNG ni el rbxmx a mano
5. En Studio:
   - clic derecho en StarterGui  >  Insert from File...
   - eliges temporada3.rbxmx
   - aparece un ScreenGui completo con todos los marcos
6. No hay que programar nada para probarlo: el .rbxmx ya trae dentro un
   LocalScript llamado PaseFuncional con la logica lista (ver 5.6)
```

### 2.6 Medir una animacion que te guste (copiar estilo)

1. En Studio, clic derecho en el modelo que tiene la animacion ->
   **Save to File**. Te da un `.rbxm`
2. Arrastra ese `.rbxm` sobre `revisar_pase.bat`
3. Se abre un `.txt` con los angulos y desplazamientos reales de cada
   articulacion, keyframe por keyframe
4. Le pegas ese texto a la IA: *"replica este estilo en una animacion de
   [lo que quieras]"*

En `referencias/` ya hay dos medidas hechas.

---

## 3. Catalogo de mecanicas (funciones y usos)

Resumen de los 9 modulos de `mecanicas/`. Cada uno tiene codigo listo para
pegar, errores frecuentes y checklist. La regla que sostiene todo:

> **El servidor decide. El cliente pide y dibuja.**

### Modulo 01 — Fundamentos y ejecucion sin errores

| # | Mecanica | Para que sirve |
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

**Mapa de contenedores (donde poner cada script):**

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

### Modulo 02 — Movimiento, control y camara

| # | Mecanica | Para que sirve |
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

Regla general: **el movimiento se siente en el cliente y se valida en el
servidor.**

### Modulo 03 — Combate, dano y habilidades

| # | Mecanica | Para que sirve |
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

Regla de oro: **el cliente pide, el servidor decide.** El cliente manda a
QUIEN golpea, nunca CUANTO.

### Modulo 04 — Animacion

**Parte A (modelos JSON):** el formato que genera la IA y como se convierte.
**Parte B (tiempo de ejecucion):** el Luau que reproduce y mezcla animaciones.

| # | Mecanica (Parte B) | Para que sirve |
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

### Modulo 05 — Interfaz de usuario

**Parte A (modelos JSON):** el formato del pase de batalla.
**Parte B (tiempo de ejecucion):** el Luau que construye y anima la GUI.

| # | Mecanica (Parte B) | Para que sirve |
|---|---|---|
| 1 | ScreenGui y sus propiedades | La base de todo |
| 2 | UDim2, Scale y Offset | Que se vea igual en todas las pantallas |
| 3 | AnchorPoint | Centrar de verdad |
| 4 | Restricciones UI | Layouts sin calcular a mano |
| 5 | Area segura y muescas | Que no se tape en movil |
| 6 | Texto que se adapta | TextScaled y RichText |
| 7 | ScrollingFrame automatico | Listas largas |
| 8 | Tweens en interfaz | Animar sin animaciones |
| 9 | Botones con antirrebote | Evitar dobles clics |
| 10 | Barra de vida y de progreso | El widget mas comun |
| 11 | Enfriamiento circular | Indicador de habilidad |
| 12 | Cola de notificaciones | Avisos sin solaparse |
| 13 | Efecto maquina de escribir | Dialogos |
| 14 | Ventana modal | Confirmaciones |
| 15 | Pestanas | Menus con secciones |
| 16 | Arrastrar y soltar | Inventario |
| 17 | Cuadricula de inventario | Rejilla de objetos |
| 18 | Navegacion con mando | Consola y accesibilidad |
| 19 | ViewportFrame | Modelos 3D dentro de la interfaz |
| 20 | BillboardGui y SurfaceGui | Interfaz en el mundo |
| 21 | Ocultar la interfaz de Roblox | Pantalla limpia |
| 22 | Conectar la interfaz al servidor | Reclamar premios del pase |
| 23 | Reaccionar a datos sin sondear | Attributes y leaderstats |

> **Aviso de compatibilidad.** El linter solo acepta estas clases en un
> `.rbxmx` generado: ScreenGui, Frame, ScrollingFrame, CanvasGroup,
> TextLabel, TextButton, TextBox, ImageLabel, ImageButton, ViewportFrame,
> UICorner, UIStroke, UIPadding, UIListLayout, UIAspectRatioConstraint,
> UISizeConstraint, UIGradient, LocalScript, ModuleScript y Folder.
> `UIGridLayout`, `UIScale` y `UITextSizeConstraint` **no** estan en la lista:
> uselos en Luau escrito a mano (el linter no mira tu codigo), pero no en un
> `.rbxmx` generado, o dara ERROR de lint.

### Modulo 06 — Datos persistentes y red

| # | Mecanica | Para que sirve |
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

Dos reglas: **los datos del jugador solo existen de verdad en el servidor** y
**toda llamada a DataStore puede fallar** (siempre en `pcall`).

### Modulo 07 — Fisica, CFrame y modelos

| # | Mecanica | Para que sirve |
|---|---|---|
| 1 | Propiedades de BasePart | La base de todo objeto |
| 2 | CFrame explicado | Posicion y rotacion juntas |
| 3 | PivotTo y GetPivot | Mover modelos enteros |
| 4 | PrimaryPart | Que parte manda |
| 5 | Soldaduras | Que las piezas no se separen |
| 6 | Motor6D y articulaciones | Lo que permite animar |
| 7 | Restricciones de movimiento | Mover con fisica |
| 8 | Grupos de colision | Que atraviesa que |
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

Idea central: hay **dos formas de mover algo** y mezclarlas causa problemas.
Cinematica (escribir CFrame/PivotTo) para lo anclado; dinamica (restricciones
y velocidades) para lo que debe respetar la fisica.

### Modulo 08 — Sistemas de juego

| # | Sistema | Para que sirve |
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

### Modulo 09 — Errores y checklist

El modulo al que se viene **cuando algo falla**. Contiene:

- **A.** El flujo completo paso a paso
- **B.** Requisitos del entorno
- **C.** Reglas exactas del validador de animacion
- **D.** Reglas exactas del validador de interfaz
- **E.** Reglas exactas del lint del .rbxmx
- **F.** Catalogo de errores del pipeline (22 errores)
- **G.** Catalogo de errores de Luau en Studio (42 errores)
- **H.** Catalogo de errores de rig y animacion (60 errores)
- **I.** Listas de comprobacion
- **J.** Como reportar un error al asistente

---

## 4. Modelos de animacion (JSON)

### 4.1 Campos del JSON

Solo tres campos son obligatorios. Los demas tienen valor por defecto.

| Campo | Nivel | Tipo | Obligatorio | Limites y defecto |
|---|---|---|---|---|
| `rig` | raiz | texto | **si** | Solo `R6` o `R15` |
| `nombre` | raiz | texto | **si** | Hasta 40 caracteres, sin `<` `>` `&` |
| `keyframes` | raiz | lista | **si** | Entre 2 y 40 elementos |
| `loop` | raiz | booleano | no | Defecto `true` |
| `prioridad` | raiz | texto | no | `core`, `idle`, `movimiento`, `accion`. Defecto `accion` |
| `easing` | raiz | texto | no | `suave`, `lineal`, `rebote`, `elastica`, `instantaneo`. Defecto `suave` |
| `keyframes[].t` | keyframe | numero | **si** | Segundos, estrictamente creciente, no negativo, total 30 s maximo |
| `keyframes[].poses` | keyframe | objeto | **si** | Nombre de articulacion como clave. No puede estar vacio |

**`easing` es un campo de la raiz, no de cada keyframe.** Se aplica a toda la
animacion. Si lo pones dentro de un keyframe, el conversor lo ignora sin
avisar. Equivalencias que aplica:

| `easing` | EasingStyle | EasingDirection |
|---|---|---|
| `suave` | Linear | InOut |
| `lineal` | Linear | Out |
| `rebote` | Bounce | Out |
| `elastica` | Elastic | Out |
| `instantaneo` | Constant | Out |

**El indice de keyframes empieza en 0.** Las rutas de error tienen la forma
`raiz.keyframes[0].poses.RightUpperArm`.

### 4.2 Formato de una pose

Cada pose acepta **3 valores** (solo rotacion) o **6 valores** (rotacion mas
desplazamiento). Cuatro o cinco valores dan error.

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

### 4.3 Articulaciones por rig

**Nunca mezcles los dos.** Solo `Head` existe en ambos, asi que si te
equivocas de rig lo unico que se movera es la cabeza.

- **R6 (6 animables):** `Torso`, `Head`, `Left Arm`, `Right Arm`, `Left Leg`,
  `Right Leg`. Ojo: `Left Arm` lleva **un espacio**; `LeftArm` es un error.
- **R15 (15 animables):** `LowerTorso`, `UpperTorso`, `Head`, `LeftUpperArm`,
  `LeftLowerArm`, `LeftHand`, `RightUpperArm`, `RightLowerArm`, `RightHand`,
  `LeftUpperLeg`, `LeftLowerLeg`, `LeftFoot`, `RightUpperLeg`,
  `RightLowerLeg`, `RightFoot`.
- `HumanoidRootPart` existe en el arbol pero **nunca** se anima. Si necesitas
  que el cuerpo suba o baje, usa el desplazamiento del torso.

### 4.4 Ejes y signos: la parte que mas errores causa

El conversor **no aplica ningun espejo**: escribe tus angulos tal cual. El
espejo lo pone el rig, y ahi esta la trampa, porque **R6 y R15 se comportan
al contrario**.

**Que eje levanta un brazo de lado:**

- **R15:** el eje **Z**. Z+ sube el derecho, Z- sube el izquierdo.
- **R6:** el eje **X**, y **siempre en negativo** en los dos brazos.

**Que eje mueve adelante y atras:**

- **R15:** el eje **X**. X+ = adelante, igual en los dos lados.
- **R6:** el eje **Z**. Z+ adelanta el lado **derecho**, Z- adelanta el
  **izquierdo**.

**La consecuencia, que es lo que casi todo el mundo escribe mal:**

| Quieres | En R6 | En R15 |
|---|---|---|
| Contrafase (una pierna adelante, la otra atras) | **el mismo valor** en las dos | **signos opuestos** |
| Pose simetrica (las dos extremidades igual) | **signos opuestos** | el mismo valor en el eje de avance |
| Brazos contralaterales a las piernas | signo **opuesto** al de las piernas | contrario al de su pierna del mismo lado |

Esto no es teoria: es lo que hacen los modelos que funcionan.

```
caminar_r6.json, t=0        ->  Right Leg [0,0,45]   Left Leg [0,0,45]
                                Right Arm [-15,0,-35] Left Arm [-15,0,-35]
   piernas identicas  = contrafase
   brazos con el signo contrario al de las piernas = contralateral

caminar_r15.json, t=0      ->  RightUpperLeg [45,0,0]  LeftUpperLeg [-45,0,0]
   signos opuestos = contrafase

salto_r6.json, t=0.18      ->  Left Arm [-15,0,50]  Right Arm [-15,0,-50]
   signos opuestos en R6 = pose simetrica (los dos brazos abiertos igual)
```

Si un giro sale al reves, cambia el signo.

### 4.5 Reglas de oro del diseno

1. **Si es bucle, la ultima pose debe ser identica a la primera.** Si no, hay
   un salto visible en cada repeticion.
2. **Piernas en contrafase.** En R6 eso se escribe con el **mismo** valor en
   las dos piernas; en R15, con signos opuestos (ver 4.4).
3. **Brazos contralaterales:** el brazo acompana a la pierna del lado
   opuesto. En R6 eso significa darles el signo contrario al de las piernas.
   Si van del mismo lado, se ve como un zombi.
4. **Nada perfectamente simetrico ni perfectamente quieto.** Dos o tres
   grados de diferencia entre lados dan vida.
5. **El torso siempre hace algo:** balanceo vertical de 0.1 a 0.3 studs y una
   inclinacion constante hacia adelante al correr.
6. **Amplitudes realistas.** Caminar mueve las piernas unos 25 a 40 grados;
   correr, 45 a 70. Mas de 90 parece una caricatura.
7. **Algo tiene que moverse.** La comprobacion es global para toda la
   animacion, no por keyframe: por eso `salto_r6.json` es valido aunque su
   primer y ultimo keyframe sean todo ceros. Lo que si falla es un keyframe
   con `poses` vacio.
8. **R6 no tiene rodillas.** Se finge con el desplazamiento vertical de la
   pierna: sube cuando deberia doblarse, baja cuando deberia extenderse.

### 4.6 Truco de flujo (deformacion a proposito)

Desplazamientos grandes separan la extremidad del cuerpo. Se ve imposible
pero da mucha sensacion de movimiento. Valores medidos de
`correr_flujo_r6.json`:

| Elemento | Valor real en el modelo | Motivo |
|---|---|---|
| Piernas, giro | `z` de +-48 (mismo valor en las dos) | Zancada amplia en contrafase |
| Piernas, desplazamiento | `px` de -+1.0, **signo contrario al del giro** | Estira la zancada mas alla del rig |
| Brazos, giro | `z` de -+52, signo contrario al de las piernas | Contralateral |
| Brazos, desplazamiento | `px` **en fase** con su giro, y de 0.3 a 0.5 del de las piernas (0.42 frente a 1.0) | Acompana sin exagerar |
| Extremidades en el punto alto | `py` de +0.1 a +0.3 | El paso despega |
| Brazos | `py` de -0.1 a -0.2 | Los hombros caen al correr |
| Torso | Desplazamiento menor a 0.3, inclinacion X constante de 8 a 12 | Balanceo, no teletransporte |
| Root | Siempre cero | Nunca se toca |

Lo que se escala a 0.3-0.5 es el **desplazamiento** del brazo, no su giro.
El giro del brazo puede ser incluso mayor que el de la pierna.

Usa esta tecnica solo para estilos llamativos. Para algo realista, quedate
con desplazamientos menores a 0.3.

### 4.7 Los modelos que ya existen

| Archivo | Rig | Loop | Prioridad | Que resuelve |
|---|---|---|---|---|
| `caminar_r6.json` | R6 | si | movimiento | Ciclo base de caminar, punto de partida limpio |
| `caminar_vida_r6.json` | R6 | si | movimiento | Caminar con balanceo de torso y asimetria |
| `caminar_chulo_r6.json` | R6 | si | movimiento | Caminar con actitud, hombros marcados |
| `caminar_r15.json` | R15 | si | movimiento | El mismo ciclo traducido a R15 |
| `caminar_vida_r15.json` | R15 | si | movimiento | Version con vida en R15 |
| `correr_ref_r6.json` | R6 | si | movimiento | Carrera de referencia, medida en `referencias/` |
| `correr_pro_r6.json` | R6 | si | movimiento | Carrera pulida, la mejor plantilla de correr |
| `correr_flujo_r6.json` | R6 | si | movimiento | Carrera con el truco de flujo |
| `salto_r6.json` | R6 | **no** | accion | Salto completo, empieza y acaba en reposo |
| `saludar_r6.json` | R6 | **no** | accion | Gesto de un solo brazo |
| `baile_r6.json` | R6 | si | accion | Animacion larga de cuerpo completo |

Para aprender el formato abre `correr_pro_r6.json` y `caminar_vida_r6.json`.
Para entender la diferencia de ejes y signos, compara `caminar_r6.json` con
`caminar_r15.json`: es la misma animacion escrita para dos rigs distintos.

---

## 5. Modelos de interfaz (JSON)

### 5.1 Campos de la cabecera

| Campo | Tipo | Obligatorio | Limite duro (codigo) | Recomendado |
|---|---|---|---|---|
| `temporada` | texto | **si** | 28 caracteres | 25 |
| `titulo` | texto | **si** | 30 caracteres | 28 |
| `subtitulo` | texto | **si** | 81 caracteres | 80 |
| `tiempo` | texto | **si** | 11 caracteres | 11 |
| `resaltado` | texto | no | Debe aparecer literalmente dentro de `titulo` | — |
| `textoAbrirTodos` | texto | no | Defecto `Abrir todos` | — |
| `textoPremium` | texto | no | Defecto `Mejorar` | — |

Los limites no son fijos: se calculan con
`limite = ancho_de_la_caja / (tamano_de_letra * 0.55)`. La columna
"recomendado" son los valores conservadores del prompt, que siempre pasan.

Ningun texto puede contener `<`, `>` ni `&`: romperian el XML del `.rbxmx`.
Escribe "y" en lugar de `&`.

### 5.2 Campos numericos (los que mas se olvidan)

| Campo | Tipo | Obligatorio | Regla exacta |
|---|---|---|---|
| `niveles` | **numero entero** | **si** | Entre 2 y 20 |
| `nivel` | numero entero | **si** | Entre 1 y `niveles` |
| `xp` | numero entero | **si** | Entre 0 y `xpPorNivel - 1` |
| `xpPorNivel` | numero entero | **si** | 1 o mas |
| `xpPorPremio` | numero entero | no | Defecto 100 |
| `xpPorPremioPremium` | numero entero | no | Defecto 150 |

**`niveles` es un numero, no una lista.** Es la cantidad de puntos del camino
de progreso que se dibuja arriba. Las listas son `gratis` y `premium`. Por
eso `pase.json` puede tener `niveles: 20` con solo 6 + 6 premios.

### 5.3 Las dos pistas y los premios

`gratis` y `premium` son listas obligatorias de **1 a 6 premios** cada una.
Cada premio lleva:

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `etiqueta` | texto | **si** | En mayusculas por convencion (no lo valida el codigo) |
| `color` | texto | **si** | Solo: azul, cian, dorado, morado, naranja, rojo, rosa, verde |
| `icono` | texto | **si** | Un emoji por convencion (no lo valida el codigo) |
| `titulo` | texto | **si** | Ver tabla 5.4 |
| `desc` | texto | **si** | Ver tabla 5.4 |
| `bonus` | texto | no | Defecto vacio |
| `nuevo` | booleano | no | Defecto `false`. Sin comillas |

La paleta de ocho colores es cerrada: son los unicos nombres que el conversor
sabe traducir a un `Color3`. Un hexadecimal se rechaza.

### 5.4 Los limites de texto dependen de cuantos premios pongas

Este es el punto que mas confunde. El ancho disponible se reparte entre las
cartas, asi que **cuantos mas premios, menos texto cabe en cada uno**.

| Premios en la pista | Ancho carta | `etiqueta` | `titulo` | `desc` | `bonus` |
|---|---|---|---|---|---|
| 1 | 1064 px | 185 | 126 | 343 | 131 |
| 2 | 524 px | 87 | 60 | 165 | 61 |
| 3 | 344 px | 54 | 38 | 105 | 38 |
| 4 | 254 px | 38 | 27 | 76 | 26 |
| 5 | 200 px | 28 | 21 | 58 | 19 |
| 6 | 164 px | 21 | 16 | 46 | 14 |

**Anadir un premio puede invalidar textos que antes pasaban.** Quitarlo nunca
rompe nada. Si quieres textos que valgan siempre, escribe para la fila de 6:
etiqueta 21, titulo 16, desc 46, bonus 14.

### 5.5 Los modelos que ya existen

| Archivo | Que resuelve |
|---|---|
| `interfaces/pase.json` | El pase de referencia: 20 niveles, 6 premios gratis + 6 premium. La plantilla a copiar |
| `interfaces/temporada2.json` | Segunda temporada: 10 niveles, 4 + 3 premios |

Antes de pedir una pantalla nueva, abre `pase.json`. Es mas rapido copiar su
estructura y cambiar los textos que describir todo desde cero.

### 5.6 El pase generado ya viene funcionando

No hace falta programar nada para probarlo. El conversor inyecta en el
`.rbxmx` un `LocalScript` llamado **PaseFuncional** con la logica hecha:

- Reclamar premios con animacion, confeti y `+XP` flotante
- Subida de nivel con aviso emergente y barra de progreso animada
- El camino de puntos se repinta segun el nivel
- Desbloqueo de la pista premium
- Hover de tarjetas, pulsacion de botones, cerrar y reabrir el pase

Lo que **no** trae es nada de servidor: el estado vive en una tabla local del
cliente. Sirve como demo jugable, no como sistema seguro. Para produccion hay
que mover la autoridad al servidor siguiendo
`mecanicas/08-sistemas.md` (seccion 10, pase de batalla) y
`mecanicas/05-gui.md` (Parte B, mecanica 22).

---

## 6. Flujo de trabajo multiagente

El sistema esta disenado para repartir el trabajo entre varias IAs:

| IA | Para que |
|---|---|
| DeepSeek, Qwen | escribir el JSON (solo texto, es lo que mejor hacen) |
| Gemini | revisar capturas de Studio, porque ve imagenes |
| ChatGPT, Meta | Figma, si vuelves a la parte de diseno |
| Notion AI | el conversor, el linter y la logica en Luau |

### 6.1 Flujo recomendado (interfaces)

```
1. Pegas PROMPT-1-DISENO.md + tu idea  ->  la IA devuelve el plan
2. Lo revisas y pides cambios ("mas niveles", "otro color"...)
3. Confirmas el plan y pegas PROMPT-IAS.md  ->  la IA genera el JSON
4. Guardas el JSON y lo ARRASTRAS sobre revisar_pase.bat
5. Si hay errores: se los pegas a la IA y vuelves al paso 3.
   Si no hay: ves el PNG y, si te gusta, lo importas a Studio.
```

### 6.2 Flujo recomendado (animaciones)

```
1. Le pegas PROMPT-2-ANIMACION.md a DeepSeek / Qwen / ChatGPT / Gemini
2. Te devuelve un JSON  ->  lo guardas como  baile.json
3. python spec_anim.py baile.json
   - si hay errores -> se los pegas a la IA -> vuelve al 2
   - si esta bien  -> genera baile.rbxmx
3b. python ver_anim.py baile.json  ->  baile.gif (vista previa)
4. Studio: Dummy del rig correcto -> Animation Editor -> AnimSaves ->
   Insert from File -> Export to Roblox -> Animation ID
```

### 6.3 Como pedirle a una IA con acceso a internet

> Lee este archivo y sigue sus instrucciones al pie de la letra:
> https://raw.githubusercontent.com/hunterhunters371-prog/roblox-fabrica/main/prompts/PROMPT-2-ANIMACION.md
>
> Quiero una animacion de correr para rig R6, estilo exagerado.

Para interfaces, cambia el enlace por `PROMPT-1-DISENO.md`.

### 6.4 Cuando el validador devuelve errores

**No arregles el JSON a mano.** Copia la lista tal cual y pegasela a la IA
con esta linea delante:

```text
Corrige el JSON. El validador devolvio estos errores:

[pega aqui la lista completa]

Devuelve el JSON completo ya corregido, sin explicaciones.
```

Exige el JSON **completo**, nunca un fragmento. Los errores dicen la ruta
exacta, con el indice de keyframe empezando en 0.

---

## 7. Checklist de ejecucion sin errores

### Antes de dar por bueno un JSON de animacion

- [ ] Tiene `rig` con valor `R6` o `R15`
- [ ] Tiene `nombre` (40 caracteres o menos, sin `<`, `>` ni `&`)
- [ ] Tiene `keyframes` con entre 2 y 40 elementos
- [ ] `easing` esta en la raiz, **no** dentro de los keyframes
- [ ] Todos los nombres de articulacion son del rig elegido
- [ ] `Left Arm` y `Right Arm` llevan su espacio, si es R6
- [ ] Ninguna pose es de `HumanoidRootPart`
- [ ] Cada pose tiene exactamente 3 o 6 valores
- [ ] Los `t` crecen estrictamente y ninguno es negativo
- [ ] El ultimo `t` no pasa de 30
- [ ] Ningun angulo pasa de +-180
- [ ] Ningun desplazamiento pasa de +-2.5
- [ ] Ningun keyframe tiene `poses` vacio
- [ ] Al menos una articulacion se mueve en toda la animacion
- [ ] Si `loop` es true, la ultima pose es identica a la primera
- [ ] **Los signos siguen la convencion del rig** (4.4): en R6 contrafase con
      el mismo valor, en R15 con signos opuestos
- [ ] `prioridad` es uno de: accion, core, idle, movimiento
- [ ] `easing` es uno de: elastica, instantaneo, lineal, rebote, suave
- [ ] Se paso por `revisar_pase.bat` y el GIF se ve razonable

### Antes de dar por bueno un JSON de interfaz

- [ ] **No** contiene en ningun sitio la palabra `"rig"`
- [ ] Estan los cuatro textos de cabecera: `temporada`, `titulo`,
      `subtitulo`, `tiempo`
- [ ] Estan los cuatro numeros: `niveles`, `nivel`, `xp`, `xpPorNivel`
- [ ] `niveles` es un **numero** entre 2 y 20, no una lista
- [ ] `nivel` entre 1 y `niveles`; `xp` menor que `xpPorNivel`
- [ ] `resaltado`, si existe, aparece literalmente dentro de `titulo`
- [ ] `gratis` y `premium` tienen entre 1 y 6 premios cada una
- [ ] Cada premio tiene `etiqueta`, `color`, `icono`, `titulo` y `desc`
- [ ] `color` es uno de los ocho nombres de la paleta
- [ ] `nuevo` es `true` o `false` sin comillas
- [ ] Ningun texto tiene `<`, `>` ni `&`
- [ ] Los textos caben **para el numero de premios que tiene la pista** (5.4)
- [ ] Se paso por `revisar_pase.bat`, el lint dice ERRORES 0 y el PNG se ve
      bien

### Entorno

- [ ] Python 3 en el PATH
- [ ] `pip install pillow lz4`
- [ ] Para DataStores: juego publicado + "Enable Studio Access to API
      Services"

---

## 8. Catalogo rapido de errores

### Los mas comunes del pipeline

| Sintoma | Causa real | Solucion |
|---|---|---|
| "no encuentro Python" | Python no esta en el PATH | Reinstala marcando "Add to PATH" |
| "EL JSON NO ES VALIDO, linea N" | Coma de mas, comilla sin cerrar | Pide el JSON entero corregido a la IA |
| Un JSON de interfaz se procesa como animacion | Contiene `"rig"` en algun sitio | Quita esa palabra |
| Procesa un archivo que no querias | Se hizo doble clic; coge el .json mas reciente | Arrastra el archivo concreto |
| "No pude leer ese .rbxm" | Falta lz4 | `pip install lz4` |
| El render falla o no crea el PNG | Falta Pillow | `pip install pillow` |
| "la clase X no esta en la lista permitida" | El .rbxmx usa una clase fuera de `CLASES` | No la uses o anadela a `roblox_lint.py` |
| "UDim.Offset es entero..." | Offset con decimales | Redondea a entero |
| "debe estar entre 0 y 1 (no 0..255)" | Color3 en formato 0-255 | Divide entre 255 |
| El texto se ve cortado en el PNG | Aviso R7 ignorado | Acorta el texto o reduce premios |

### Los mas comunes en Studio (Luau)

| Mensaje | Causa real | Solucion |
|---|---|---|
| `attempt to index nil with 'X'` | El objeto no existe o el nombre esta mal | `WaitForChild` con timeout |
| `Infinite yield possible...` | El hijo nunca aparece | Pon timeout y comprueba el nombre |
| `Script timeout` | Bucle sin `task.wait()` | Anade `task.wait()` |
| `Requested module experienced an error` | Error en el modulo o `require` circular | Abre el modulo y rompe el ciclo |
| `Animation failed to load` | ID no existe, no es publico o no es tuyo | Publica desde tu cuenta |
| `PlayerGui... is not a valid member` | Buscaste en `StarterGui` en vez de `PlayerGui` | En ejecucion vive en `PlayerGui` |
| LocalScript no hace nada y no da error | Esta donde no corre en cliente | Mueve a StarterPlayerScripts o StarterGui |
| `Studio Access to API Services is not enabled` | Falta el permiso | Game Settings > Security |

### Los mas comunes de rig y animacion

| Sintoma | Causa real | Solucion |
|---|---|---|
| Solo se mueve la cabeza | Se mezclaron R6 y R15 | Elige un rig y usa solo sus nombres |
| El personaje camina como un zombi | Brazos y piernas del mismo lado | En R6, dales el signo contrario (4.4) |
| Las piernas se mueven juntas en vez de alternarse | Se usaron signos opuestos en R6 creyendo que era contrafase | En R6 la contrafase es el **mismo** valor |
| El bucle da un salto visible | La ultima pose no coincide con la primera | Copiala del primer keyframe |
| La animacion no se reproduce, otra la tapa | Prioridad insuficiente | Sube a `accion` |
| El easing no cambia nada | Se puso dentro de un keyframe | Va en la raiz del JSON |
| Los brazos suben al lado equivocado (R6) | En R6 el eje X sube brazos y es siempre negativo | Pon valores negativos en X |
| Los brazos suben al lado equivocado (R15) | En R15 el eje Z sube brazos | Invierte el signo del brazo afectado |
| El personaje se estira raro | Se abuso del desplazamiento de 6 valores | Baja `px`, `py`, `pz` o quitalos |
| El GIF se ve bien pero en Studio no | El Dummy es del otro rig | Inserta un Dummy del rig del JSON |
| El .rbxmx no aparece en el editor | Se solto fuera de `AnimSaves` | Debe ir dentro de AnimSaves |

---

## 9. Referencias

- [VERIFICACION.md](VERIFICACION.md) — auditoria de esta guia contra el codigo
- `mecanicas/01-fundamentos.md` a `09-errores-y-checklist.md` — el catalogo
  completo
- `prompts/PROMPT-1-DISENO.md` — plan de diseno de interfaces
- `prompts/PROMPT-2-ANIMACION.md` — generacion de animaciones
- `prompts/PROMPT-IAS.md` — generacion del pase de batalla
- `herramientas/revisar_pase.bat` — el pipeline (unico punto de entrada)
- `herramientas/spec_anim.py` — validador y conversor de animaciones
- `herramientas/spec_a_rbxmx.py` — validador y conversor de interfaces
- `herramientas/roblox_lint.py` — las 10 reglas del linter
- `referencias/*.txt` — medidas reales de animaciones de la toolbox
