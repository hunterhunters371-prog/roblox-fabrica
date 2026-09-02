# GUÍA COMPLETA — Fábrica Roblox

Proyecto: **LAST DELIVERY: 60 SECONDS**

Esta guía recopila todo el conocimiento del repositorio en un solo lugar:
las mecánicas y sus usos, cómo ejecutar el sistema sin errores, los modelos
JSON de animación e interfaz, y el flujo de trabajo multiagente.

---

## 1. Qué es este repositorio

Un sistema para que **cualquier IA genere interfaces (GUI) y animaciones de
personaje para Roblox** en un formato que se valida y se convierte solo.

La regla de oro: **la IA nunca escribe XML de Roblox ni código Lua.** Solo
escribe un **JSON**. Un conversor (Python) traduce ese JSON a `.rbxmx` y lo
valida. Por eso no se rompe.

### Estructura

```
herramientas/   los .py y el revisar_pase.bat (el pipeline)
prompts/        los textos que le das a la IA (PROMPT 1 y 2)
animaciones/    animaciones que ya funcionan (.json editable)
interfaces/     interfaces que ya funcionan (.json editable)
referencias/    medidas reales de animaciones analizadas
mecanicas/      catálogo completo de mecánicas (9 módulos)
```

---

## 2. Cómo ejecutar el sistema sin errores

### 2.1 Requisitos del entorno

| Requisito | Comprobación | Si falta |
|---|---|---|
| Python 3 en el PATH | `python --version` | El .bat dice "no encuentro Python" |
| Pillow | `pip install pillow` | Falla el render PNG y el GIF |
| lz4 | `pip install lz4` | Falla `leer_anim.py` con `.rbxm` |

Los `.py` deben estar junto al `.bat` o en la subcarpeta `herramientas\`.

### 2.2 El flujo de revisar_pase.bat (v6.0)

El `.bat` es el único punto de entrada. **Arrastra el archivo encima del .bat**
(si haces doble clic, coge el `.json` más reciente, que puede no ser el que
quieres).

```
        ARRASTRAS UN ARCHIVO SOBRE revisar_pase.bat
                          |
                          v
               Qué extensión tiene?
     +---------------+--------+--------+----------------+
   .json           .rbxmx            .rbxm         (nada válido)
     |               |                 |                |
     v               v                 v                v
 Contiene       Contiene          leer_anim.py       ERROR:
 la clave       KeyframeSequence?  MIDE la animación  no hay .json
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

### 2.3 Cómo decide si es animación o interfaz

El `.bat` busca literalmente el texto `"rig"` dentro del JSON:

| Encuentra `"rig"` | Conversor | Vista previa |
|---|---|---|
| Sí | `spec_anim.py` | GIF con `ver_anim.py` |
| No | `spec_a_rbxmx.py` | PNG con `render_rbxmx.py` |

⚠️ **Un JSON de interfaz nunca debe contener la palabra `"rig"`**, ni siquiera
dentro de un texto, o se procesará como animación.

### 2.4 De JSON a Studio — Animaciones

```
1. La IA devuelve un bloque JSON y nada más
2. Guardas el archivo en animaciones/  (ej: mi_correr.json)
3. Arrastras el archivo encima de herramientas/revisar_pase.bat
   - detecta la clave "rig" y sabe que es una animación
   - valida campos, límites y articulaciones
   - si falla, imprime la ruta exacta del error
   - si pasa, genera mi_correr.rbxmx
4. Opcional: python ver_anim.py mi_correr.json  ->  mi_correr.gif
   (maniquí de bloques para revisar el movimiento sin abrir Studio)
5. En Studio:
   - Modelo > Rig Builder > R6 o R15  (el MISMO rig del JSON)
   - Avatar > Animation Editor, selecciona el Dummy
   - arrastra mi_correr.rbxmx dentro de la carpeta AnimSaves del Dummy
     (o clic derecho en AnimSaves > Insert from File...)
   - en el editor, menú de tres puntos > Export to Roblox
   - copia el Asset ID que te da
6. Ese ID va en la propiedad AnimationId de un objeto Animation
```

### 2.5 De JSON a Studio — Interfaces

```
1. La IA devuelve un bloque JSON y nada más
2. Guardas el archivo en interfaces/  (ej: temporada3.json)
3. Arrastras el archivo encima de herramientas/revisar_pase.bat
   - no encuentra la clave "rig", así que lo trata como interfaz
   - roblox_lint.py revisa longitudes, colores y caracteres prohibidos
   - spec_a_rbxmx.py genera temporada3.rbxmx
   - se genera también una vista previa PNG
4. Miras el PNG. Si el texto se corta o el color no encaja, corriges el JSON
   y repites. No toques el PNG ni el rbxmx a mano
5. En Studio:
   - clic derecho en StarterGui  >  Insert from File...
   - eliges temporada3.rbxmx
   - aparece un ScreenGui completo con todos los marcos
6. Conectas los botones con el código de la Parte B (mecanicas/05-gui.md)
```

### 2.6 Medir una animación que te guste (copiar estilo)

1. En Studio, clic derecho en el modelo que tiene la animación ->
   **Save to File**. Te da un `.rbxm`
2. Arrastra ese `.rbxm` sobre `revisar_pase.bat`
3. Se abre un `.txt` con los ángulos y desplazamientos reales de cada
   articulación, keyframe por keyframe
4. Le pegas ese texto a la IA: *"replica este estilo en una animación de
   [lo que quieras]"*

En `referencias/` ya hay dos medidas hechas.

---

## 3. Catálogo de mecánicas (funciones y usos)

Resumen de los 9 módulos de `mecanicas/`. Cada uno tiene código listo para
pegar, errores frecuentes y checklist. La regla que sostiene todo:

> **El servidor decide. El cliente pide y dibuja.**

### Módulo 01 — Fundamentos y ejecución sin errores

| # | Mecánica | Para qué sirve |
|---|---|---|
| 1 | Obtener servicios con GetService | Acceso fiable a la API |
| 2 | Script, LocalScript y ModuleScript | Elegir dónde corre el código |
| 3 | Módulo reutilizable con require | No repetir código |
| 4 | Ciclo de vida del jugador | Entrada y salida de jugadores |
| 5 | Ciclo de vida del personaje | Respawn sin romper nada |
| 6 | Esperar instancias sin colgarse | Evitar el infinite yield |
| 7 | Bucle por frame con RunService | Lógica continua |
| 8 | Librería task | Esperas y tareas paralelas |
| 9 | pcall y xpcall | Que un fallo no tumbe el script |
| 10 | Tipado Luau estricto | Cazar errores antes de ejecutar |
| 11 | Attributes como estado replicado | Compartir datos sin remotes |
| 12 | CollectionService y tags | Comportamiento por etiqueta |
| 13 | Limpieza de conexiones (Trove) | Evitar fugas de memoria |
| 14 | Debris y destrucción diferida | Limpiar efectos temporales |
| 15 | Frontera cliente-servidor | Saber qué se replica |
| 16 | Arranque ordenado y precarga | Evitar carreras de inicio |
| 17 | Diagnóstico: mi script no corre | Checklist de arranque |
| 18 | APIs obsoletas y sus reemplazos | No heredar código roto |

**Mapa de contenedores (dónde poner cada script):**

| Contenedor | Qué corre ahí | Visible para el cliente |
|---|---|---|
| `ServerScriptService` | Script de servidor | No |
| `ServerStorage` | Modelos y módulos solo de servidor | No |
| `ReplicatedStorage` | Módulos y remotes compartidos | Sí |
| `StarterPlayer/StarterPlayerScripts` | LocalScript del jugador | Sí |
| `StarterPlayer/StarterCharacterScripts` | LocalScript que revive con el personaje | Sí |
| `StarterGui` | ScreenGui y LocalScript de interfaz | Sí |
| `StarterPack` | Tools que recibe el jugador al aparecer | Sí |
| `Workspace` | Partes y modelos del mundo | Sí |

Regla corta: **lógica que decide, en el servidor. Lógica que muestra, en el
cliente.**

### Módulo 02 — Movimiento, control y cámara

| # | Mecánica | Para qué sirve |
|---|---|---|
| 1 | Velocidad y salto del Humanoid | Ajuste base del personaje |
| 2 | Estados del Humanoid | Controlar saltar, caer, nadar |
| 3 | Sprint con resistencia | Correr con coste |
| 4 | Dash con LinearVelocity | Impulso corto direccional |
| 5 | Doble salto | Salto extra en el aire |
| 6 | Agacharse | Reducir altura y velocidad |
| 7 | Deslizamiento | Slide con fricción |
| 8 | Correr por la pared | Wall run con raycast |
| 9 | Agarre de borde | Ledge grab |
| 10 | Escalada con TrussPart | Trepar escaleras |
| 11 | Nadar y zonas de agua | Estado Swimming |
| 12 | UserInputService y ContextActionService | Capturar entrada |
| 13 | Botones táctiles para móvil | Soporte de teléfono |
| 14 | Primera persona y bloqueo de hombro | Modos de cámara |
| 15 | Sacudida de cámara | Impacto y peso |
| 16 | Asientos y VehicleSeat | Vehículos |
| 17 | Teletransporte con PivotTo | Mover al personaje |
| 18 | Puntos de aparición | SpawnLocation y equipos |
| 19 | Ragdoll al morir | Muerte con física |
| 20 | Daño por caída | Castigo por altura |
| 21 | Empuje | Knockback |
| 22 | Plataformas móviles | Sin jitter |
| 23 | Zonas que cambian la velocidad | Barro, hielo, turbo |

Regla general: **el movimiento se siente en el cliente y se valida en el
servidor.**

### Módulo 03 — Combate, daño y habilidades

| # | Mecánica | Para qué sirve |
|---|---|---|
| 1 | Hitbox por volumen | Detectar a quién alcanza el golpe |
| 2 | Raycast y RaycastParams | Disparos instantáneos |
| 3 | Shapecast | Proyectiles con grosor |
| 4 | Enfriamiento con os.clock | Limitar la cadencia |
| 5 | Aplicar daño correctamente | TakeDamage y no Health |
| 6 | Remote de ataque validado | La frontera de seguridad |
| 7 | Proyectil con predicción | Se siente instantáneo y es justo |
| 8 | Combos encadenados | Golpes M1 con ventana |
| 9 | Fotogramas de invulnerabilidad | Esquivas que perdonan |
| 10 | Aturdimiento | Bloquear acciones un instante |
| 11 | Empuje al golpear | Peso del impacto |
| 12 | Equipos y fuego amigo | No matar a los tuyos |
| 13 | Críticos y variación de daño | Que no sea plano |
| 14 | Daño en el tiempo | Veneno y quemadura |
| 15 | Curación y regeneración | Recuperar vida |
| 16 | Escudos y armadura | Capa antes de la vida |
| 17 | Hitstop y retroalimentación | Que el golpe se sienta |
| 18 | Muerte, respawn y killfeed | Cerrar el ciclo |
| 19 | Tool como arma | Equipar y usar |
| 20 | Munición y recarga | Gestión de recursos |
| 21 | Daño en área | Explosiones |
| 22 | Gestor de estados alterados | Un solo sitio para todo |

Regla de oro: **el cliente pide, el servidor decide.** El cliente manda a
QUIÉN golpea, nunca CUÁNTO.

### Módulo 04 — Animación

**Parte A (modelos JSON):** el formato que genera la IA y cómo se convierte.
**Parte B (tiempo de ejecución):** el Luau que reproduce y mezcla animaciones.

| # | Mecánica (Parte B) | Para qué sirve |
|---|---|---|
| 1 | Animator y LoadAnimation | La forma correcta de cargar |
| 2 | Play y Stop con fundido | Transiciones limpias |
| 3 | Prioridades | Qué animación gana |
| 4 | Bucle y velocidad | Ajustar el ritmo |
| 5 | Peso y mezcla | Combinar dos animaciones |
| 6 | TimePosition | Saltar a un instante |
| 7 | Marcadores | Sincronizar con eventos |
| 8 | Precarga | Que no se vea el tirón |
| 9 | Sustituir las animaciones por defecto | Caminar propio |
| 10 | Animaciones de Tool | Armas y objetos |
| 11 | Motor6D y agarre | Sujetar objetos |
| 12 | Animación procedural con CFrame | Sin editor |
| 13 | IKControl | Pies y manos que se adaptan |
| 14 | Viewmodel en primera persona | Manos propias |
| 15 | Sincronizar sonido y partículas | Impacto |
| 16 | Inspeccionar pistas activas | Depurar |
| 17 | Animaciones en NPC | Sin Player |
| 18 | Detener todo al morir | Limpieza |

### Módulo 05 — Interfaz de usuario

**Parte A (modelos JSON):** el formato del pase de batalla.
**Parte B (tiempo de ejecución):** el Luau que construye y anima la GUI.

| # | Mecánica (Parte B) | Para qué sirve |
|---|---|---|
| 1 | ScreenGui y sus propiedades | La base de todo |
| 2 | UDim2, Scale y Offset | Que se vea igual en todas las pantallas |
| 3 | AnchorPoint | Centrar de verdad |
| 4 | Restricciones UI | Layouts sin calcular a mano |
| 5 | Área segura y muescas | Que no se tape en móvil |
| 6 | Texto que se adapta | TextScaled y RichText |
| 7 | ScrollingFrame automático | Listas largas |
| 8 | Tweens en interfaz | Animar sin animaciones |
| 9 | Botones con antirrebote | Evitar dobles clics |
| 10 | Barra de vida y de progreso | El widget más común |
| 11 | Enfriamiento circular | Indicador de habilidad |
| 12 | Cola de notificaciones | Avisos sin solaparse |
| 13 | Efecto máquina de escribir | Diálogos |
| 14 | Ventana modal | Confirmaciones |
| 15 | Pestañas | Menús con secciones |
| 16 | Arrastrar y soltar | Inventario |
| 17 | Cuadrícula de inventario | Rejilla de objetos |
| 18 | Navegación con mando | Consola y accesibilidad |
| 19 | ViewportFrame | Modelos 3D dentro de la interfaz |
| 20 | BillboardGui y SurfaceGui | Interfaz en el mundo |
| 21 | Ocultar la interfaz de Roblox | Pantalla limpia |
| 22 | Conectar la interfaz al servidor | Reclamar premios del pase |
| 23 | Reaccionar a datos sin sondear | Attributes y leaderstats |

### Módulo 06 — Datos persistentes y red

| # | Mecánica | Para qué sirve |
|---|---|---|
| 1 | Activar DataStores en Studio | Requisito previo |
| 2 | Guardar y leer con seguridad | El patrón base |
| 3 | Reintentos con retroceso | Sobrevivir a fallos |
| 4 | UpdateAsync frente a SetAsync | Cuándo usar cada uno |
| 5 | Límites y throttling | No pasarse de cuota |
| 6 | Esquema versionado | Poder cambiar el formato |
| 7 | Bloqueo de sesión | Evitar duplicar objetos |
| 8 | Guardar al salir y al cerrar | BindToClose |
| 9 | Autoguardado | Red de seguridad |
| 10 | Gestor de datos completo | Módulo listo para usar |
| 11 | leaderstats | Estadísticas visibles |
| 12 | OrderedDataStore | Tablas de clasificación |
| 13 | MemoryStoreService | Datos entre servidores |
| 14 | RemoteEvent | Avisos en un sentido |
| 15 | RemoteFunction | Peticiones con respuesta |
| 16 | UnreliableRemoteEvent | Datos que se pueden perder |
| 17 | BindableEvent | Comunicación en el mismo lado |
| 18 | Validación y límite de frecuencia | Blindar los remotes |
| 19 | Attributes replicados | Estado ligero |
| 20 | MessagingService | Hablar entre servidores |
| 21 | HttpService | Webhooks y APIs externas |
| 22 | TeleportService con datos | Pasar información al viajar |
| 23 | MarketplaceService | Compras y ProcessReceipt |

Dos reglas: **los datos del jugador solo existen de verdad en el servidor** y
**toda llamada a DataStore puede fallar** (siempre en `pcall`).

### Módulo 07 — Física, CFrame y modelos

| # | Mecánica | Para qué sirve |
|---|---|---|
| 1 | Propiedades de BasePart | La base de todo objeto |
| 2 | CFrame explicado | Posición y rotación juntas |
| 3 | PivotTo y GetPivot | Mover modelos enteros |
| 4 | PrimaryPart | Qué parte manda |
| 5 | Soldaduras | Que las piezas no se separen |
| 6 | Motor6D y articulaciones | Lo que permite animar |
| 7 | Restricciones de movimiento | Mover con física |
| 8 | Grupos de colisión | Qué atraviesa qué |
| 9 | Touched con antirrebote | Detección simple |
| 10 | Consultas espaciales | Detección fiable |
| 11 | Raycast | La línea de visión |
| 12 | Tamaño y límites de un modelo | Medir sin adivinar |
| 13 | Escalar un modelo | ScaleTo |
| 14 | Propiedad de red | Quién simula qué |
| 15 | Clonar desde almacenamiento | El patrón correcto |
| 16 | Debris y limpieza | No dejar basura |
| 17 | Puertas | Cinemática bien hecha |
| 18 | Plataformas móviles | Sin tirar al jugador |
| 19 | Ascensores | Movimiento vertical |
| 20 | Cintas transportadoras | Empuje continuo |
| 21 | Partes destructibles | Romper cosas |
| 22 | Terreno por código | Generar el mundo |
| 23 | StreamingEnabled | Mundos grandes |
| 24 | Por qué mi modelo se desarma | Diagnóstico |

Idea central: hay **dos formas de mover algo** y mezclarlas causa problemas.
Cinemática (escribir CFrame/PivotTo) para lo anclado; dinámica (restricciones
y velocidades) para lo que debe respetar la física.

### Módulo 08 — Sistemas de juego

| # | Sistema | Para qué sirve |
|---|---|---|
| 1 | Módulo base reutilizable | El patrón de todos los demás |
| 2 | Economía y moneda | La base de todo progreso |
| 3 | Inventario con autoridad de servidor | Objetos que no se duplican |
| 4 | Barra rápida | Equipar desde el inventario |
| 5 | Tienda | Comprar sin exploits |
| 6 | Recogibles | Monedas y objetos en el mundo |
| 7 | Misiones con progreso | Objetivos con seguimiento |
| 8 | Logros | Hitos permanentes |
| 9 | Recompensas diarias | Retención |
| 10 | Pase de batalla | Ligado a interfaces/pase.json |
| 11 | Máquina de estados de ronda | El corazón de una partida |
| 12 | Temporizador sincronizado | El reloj de 60 segundos |
| 13 | Equipos | Teams y reaparición |
| 14 | Entregas contra reloj | El bucle de LAST DELIVERY |
| 15 | Checkpoints y puertas con llave | Progresión espacial |
| 16 | NPC con pathfinding | Que se muevan por el mapa |
| 17 | Máquina de estados de NPC | Que se comporten |
| 18 | Oleadas de enemigos | Dificultad creciente |
| 19 | Tabla de clasificación | Competición |
| 20 | Comandos de chat | Herramientas rápidas |
| 21 | Comandos de administrador | Con lista blanca |
| 22 | Anticheat básico | Lo mínimo razonable |

### Módulo 09 — Errores y checklist

El módulo al que se viene **cuando algo falla**. Contiene:

- **A.** El flujo completo paso a paso
- **B.** Requisitos del entorno
- **C.** Reglas exactas del validador de animación
- **D.** Reglas exactas del validador de interfaz
- **E.** Reglas exactas del lint del .rbxmx
- **F.** Catálogo de errores del pipeline (22 errores)
- **G.** Catálogo de errores de Luau en Studio (42 errores)
- **H.** Catálogo de errores de rig y animación (60 errores)
- **I.** Listas de comprobación
- **J.** Cómo reportar un error al asistente

---

## 4. Modelos de animación (JSON)

### 4.1 Campos del JSON

| Campo | Tipo | Obligatorio | Límites |
|---|---|---|---|
| `nombre` | texto | sí | Hasta 40 caracteres, sin `<` `>` `&` |
| `rig` | texto | sí | Solo `R6` o `R15` |
| `loop` | booleano | sí | `true` o `false` |
| `prioridad` | texto | sí | `core`, `idle`, `movimiento`, `accion` |
| `keyframes` | lista | sí | Entre 2 y 40 elementos |
| `keyframes[].t` | número | sí | Segundos, estrictamente creciente, total 30 s máx |
| `keyframes[].easing` | texto | no | `suave`, `lineal`, `rebote`, `elastica`, `instantaneo` |
| `keyframes[].poses` | objeto | sí | Nombre de articulación como clave |

### 4.2 Formato de una pose

Cada pose acepta **3 valores** (solo rotación) o **6 valores** (rotación más
desplazamiento):

```json
{
  "Right Arm": [-70, 0, 20],
  "Torso": [4, 0, 0, 0, 0.15, 0]
}
```

| Posición | Significado | Límite |
|---|---|---|
| 1, 2, 3 | Rotación X, Y, Z en grados | -180 a 180 |
| 4, 5, 6 | Desplazamiento X, Y, Z en studs | -2.5 a 2.5 |

### 4.3 Articulaciones por rig

**Nunca mezcles los dos.** Solo `Head` existe en ambos; si te equivocas de rig
lo único que se mueve es la cabeza.

**R6 (6 articulaciones):** `Torso, Head, Left Arm, Right Arm, Left Leg, Right Leg`
(nota: `Left Arm` lleva un espacio).

**R15 (15 articulaciones):** `LowerTorso, UpperTorso, Head, LeftUpperArm,
LeftLowerArm, LeftHand, RightUpperArm, RightLowerArm, RightHand,
LeftUpperLeg, LeftLowerLeg, LeftFoot, RightUpperLeg, RightLowerLeg, RightFoot`

`HumanoidRootPart` **nunca** se anima.

### 4.4 Ejes: la parte que más errores causa

Memoriza estas dos frases:

- **En R15, para levantar un brazo de lado se usa Z.** (Z+ sube el derecho,
  Z- sube el izquierdo; X mueve adelante/atrás en ambos lados)
- **En R6, para levantar un brazo de lado se usa X y siempre en negativo.**
  (Z mueve adelante/atrás: Z+ adelanta el lado derecho, Z- el izquierdo)

### 4.5 Reglas de oro del diseño

1. Si es bucle, la última pose debe ser igual a la primera.
2. Piernas en contrafase (una adelante, otra atrás).
3. Brazos en fase con la pierna opuesta (contralaterales).
4. Nada perfectamente simétrico: 2-3 grados de diferencia dan vida.
5. El torso siempre hace algo (balanceo vertical 0.1-0.3 studs).
6. Amplitudes realistas: caminar 25-40 grados, correr 45-70.
7. Algo tiene que moverse (el validador rechaza todo a cero).

### 4.6 Truco de flujo (deformación a propósito)

| Elemento | Valor típico | Motivo |
|---|---|---|
| Piernas | `z` de +50 y -50 en contrafase | Zancada amplia |
| Pierna adelantada | `px` de -1.2 | La pierna se separa del eje |
| Brazos | `z` de 0.3 a 0.5 del valor de las piernas | Acompañan sin exagerar |
| Extremidades en el punto alto | `py` de +0.2 o +0.3 | El paso despega |
| Brazos | `py` de -0.1 o -0.2 | Los hombros caen al correr |
| Torso | Desplazamiento menor a 0.3 | Balanceo, no teletransporte |
| Root | Siempre cero | Nunca se toca |

### 4.7 Los modelos que ya existen

| Archivo | Rig | Qué resuelve |
|---|---|---|
| `caminar_r6.json` | R6 | Ciclo base de caminar, punto de partida limpio |
| `caminar_vida_r6.json` | R6 | Caminar con balanceo de torso y asimetría |
| `caminar_chulo_r6.json` | R6 | Caminar con actitud, hombros marcados |
| `caminar_r15.json` | R15 | El mismo ciclo traducido a R15 |
| `caminar_vida_r15.json` | R15 | Versión con vida en R15 |
| `correr_ref_r6.json` | R6 | Carrera de referencia, medida en `referencias/` |
| `correr_pro_r6.json` | R6 | Carrera pulida, la mejor plantilla de correr |
| `correr_flujo_r6.json` | R6 | Carrera con el truco de flujo |
| `salto_r6.json` | R6 | Salto, no es bucle |
| `saludar_r6.json` | R6 | Gesto de brazo, prioridad de acción |
| `baile_r6.json` | R6 | Animación larga de cuerpo completo |

Para aprender el formato abre `correr_pro_r6.json` y `caminar_vida_r6.json`.
Para entender la diferencia de ejes, compara `caminar_r6.json` con
`caminar_r15.json`.

---

## 5. Modelos de interfaz (JSON)

### 5.1 Campos de la cabecera

| Campo | Tipo | Límite exacto |
|---|---|---|
| `temporada` | texto | Hasta 25 caracteres |
| `titulo` | texto | Hasta 28 caracteres |
| `subtitulo` | texto | Hasta 80 caracteres |
| `tiempo` | texto | Hasta 11 caracteres |
| `niveles` | lista | Entre 2 y 20 elementos |

Ningún texto puede contener `<`, `>` ni `&` (rompen el XML del .rbxmx).

### 5.2 Campos de un premio

| Campo | Tipo | Límite exacto |
|---|---|---|
| `etiqueta` | texto | Hasta 18 caracteres, en MAYÚSCULAS |
| `color` | texto | Solo: azul, cian, dorado, morado, naranja, rojo, rosa, verde |
| `icono` | texto | Un solo emoji |
| `titulo` | texto | Hasta 20 caracteres |
| `desc` | texto | Hasta 55 caracteres |
| `bonus` | texto | Hasta 16 caracteres |
| `nuevo` | booleano | `true` o `false` |

La paleta de ocho colores es cerrada: son los únicos nombres que el conversor
sabe traducir a un `Color3`.

### 5.3 Campos numéricos obligatorios (fáciles de olvidar)

| Campo | Regla exacta |
|---|---|
| `niveles` | Entre 2 y 20 |
| `nivel` | Entre 1 y `niveles` |
| `xp` | Entre 0 y `xpPorNivel - 1` |
| `xpPorNivel` | 1 o más |
| `xpPorPremio` | Por defecto 100 |
| `xpPorPremioPremium` | Por defecto 150 |
| `resaltado` | Debe aparecer literalmente dentro de `titulo` |

### 5.4 Los límites dependen de cuántos premios pongas

Cuantos más premios en una pista, más estrecha es cada carta y menos texto
cabe. Si quieres textos que valgan siempre, usa la fila de 6 premios:
`etiqueta` 21, `titulo` 16, `desc` 46, `bonus` 14 caracteres.

### 5.5 Los modelos que ya existen

| Archivo | Qué resuelve |
|---|---|
| `interfaces/pase.json` | El pase de batalla de referencia (20 niveles, 6+6 premios). Plantilla a copiar |
| `interfaces/temporada2.json` | Segunda temporada, misma estructura con otros premios |

---

## 6. Flujo de trabajo multiagente

El sistema está diseñado para repartir el trabajo entre varias IAs:

| IA | Para qué |
|---|---|
| DeepSeek, Qwen | escribir el JSON (solo texto, es lo que mejor hacen) |
| Gemini | revisar capturas de Studio, porque ve imágenes |
| ChatGPT, Meta | Figma, si vuelves a la parte de diseño |
| Notion AI | el conversor, el linter y la lógica en Luau |

### 6.1 Flujo recomendado (interfaces)

```
1. Pegas PROMPT-1-DISENO.md + tu idea  ->  la IA devuelve el plan
2. Lo revisas y pides cambios ("más niveles", "otro color"...)
3. Confirmas el plan y pegas PROMPT-IAS.md  ->  la IA genera el JSON
4. Guardas el JSON en la carpeta  ->  doble clic a revisar_pase.bat
5. Si hay errores: se los pegas a la IA y vuelves al paso 3.
   Si no hay: ves el PNG y, si te gusta, lo importas a Studio.
```

### 6.2 Flujo recomendado (animaciones)

```
1. Le pegas PROMPT-2-ANIMACION.md a DeepSeek / Qwen / ChatGPT / Gemini
2. Te devuelve un JSON  ->  lo guardas como  baile.json
3. python spec_anim.py baile.json
   - si hay errores -> se los pegas a la IA -> vuelve al 2
   - si está bien  -> genera baile.rbxmx
3b. python ver_anim.py baile.json  ->  baile.gif (vista previa)
4. Studio: Dummy del rig correcto -> Animation Editor -> AnimSaves ->
   Insert from File -> Export to Roblox -> Animation ID
```

### 6.3 Cómo pedirle a una IA con acceso a internet

> Lee este archivo y sigue sus instrucciones al pie de la letra:
> https://raw.githubusercontent.com/hunterhunters371-prog/roblox-fabrica/main/prompts/PROMPT-2-ANIMACION.md
>
> Quiero una animación de correr para rig R6, estilo exagerado.

Para interfaces, cambia el enlace por `PROMPT-1-DISENO.md`.

### 6.4 Cuando el validador devuelve errores

**No arregles el JSON a mano.** Copia la lista tal cual y pégasela a la IA con
esta línea delante:

```text
Corrige el JSON. El validador devolvió estos errores:

[pega aquí la lista completa]

Devuelve el JSON completo ya corregido, sin explicaciones.
```

Exige el JSON **completo**, nunca un fragmento.

---

## 7. Checklist de ejecución sin errores

### Antes de dar por bueno un JSON de animación

- [ ] Tiene la clave `rig` con valor `R6` o `R15`
- [ ] `nombre` tiene 40 caracteres o menos, sin `<`, `>` ni `&`
- [ ] Todos los nombres de articulación son del rig elegido
- [ ] `Left Arm` y `Right Arm` llevan su espacio, si es R6
- [ ] Ninguna pose es de `HumanoidRootPart`
- [ ] Hay entre 2 y 40 keyframes
- [ ] Los `t` crecen estrictamente y ninguno es negativo
- [ ] El último `t` no pasa de 30
- [ ] Ningún ángulo pasa de ±180
- [ ] Ningún desplazamiento pasa de ±2.5
- [ ] Al menos una articulación se mueve
- [ ] Si `loop` es true, la última pose es igual a la primera
- [ ] `prioridad` es uno de: accion, core, idle, movimiento
- [ ] `easing` es uno de: elastica, instantaneo, lineal, rebote, suave
- [ ] Se pasó por `revisar_pase.bat` y el GIF se ve razonable

### Antes de dar por bueno un JSON de interfaz

- [ ] **No** contiene en ningún sitio la palabra `"rig"`
- [ ] Están los cuatro textos de cabecera: `temporada`, `titulo`, `subtitulo`, `tiempo`
- [ ] `resaltado` aparece dentro de `titulo`
- [ ] `niveles` entre 2 y 20; `nivel` entre 1 y `niveles`; `xp` menor que `xpPorNivel`
- [ ] `gratis` y `premium` tienen entre 1 y 6 premios cada una
- [ ] Cada premio tiene `etiqueta`, `color`, `icono`, `titulo`, `desc`
- [ ] `color` es uno de los ocho nombres de la paleta
- [ ] `icono` es un solo emoji
- [ ] `nuevo` es `true` o `false` sin comillas
- [ ] Ningún texto tiene `<`, `>` ni `&`
- [ ] Los textos caben según el número de premios por pista
- [ ] Se pasó por `revisar_pase.bat`, el lint dice ERRORES 0 y el PNG se ve bien

### Entorno

- [ ] Python 3 en el PATH
- [ ] `pip install pillow lz4`
- [ ] Para DataStores: juego publicado + "Enable Studio Access to API Services"

---

## 8. Catálogo rápido de errores

### Los más comunes del pipeline

| Síntoma | Causa real | Solución |
|---|---|---|
| "no encuentro Python" | Python no está en el PATH | Reinstala marcando "Add to PATH" |
| "EL JSON NO ES VÁLIDO" | Coma de más, comilla sin cerrar | Pide el JSON entero corregido a la IA |
| Un JSON de interfaz se procesa como animación | Contiene `"rig"` | Quita esa palabra |
| "No pude leer ese .rbxm" | Falta lz4 | `pip install lz4` |
| El render falla | Falta Pillow | `pip install pillow` |
| El texto se ve cortado en el PNG | Aviso R7 ignorado | Acorta el texto o reduce premios |

### Los más comunes en Studio (Luau)

| Mensaje | Causa real | Solución |
|---|---|---|
| `attempt to index nil with 'X'` | El objeto no existe o el nombre está mal | `WaitForChild` con timeout |
| `Infinite yield possible...` | El hijo nunca aparece | Pon timeout y comprueba el nombre |
| `Script timeout` | Bucle sin `task.wait()` | Añade `task.wait()` |
| `Animation failed to load` | ID no existe, no es público o no es tuyo | Publica desde tu cuenta |
| `PlayerGui... is not a valid member` | Buscaste en `StarterGui` en vez de `PlayerGui` | En ejecución vive en `PlayerGui` |
| LocalScript no hace nada | Está en un sitio donde no corre en cliente | Mueve a StarterPlayerScripts/StarterGui |

### Los más comunes de rig y animación

| Síntoma | Causa real | Solución |
|---|---|---|
| Solo se mueve la cabeza | Se mezclaron R6 y R15 | Elige un rig y usa solo sus nombres |
| El bucle da un salto visible | La última pose no coincide con la primera | Cópiala del primer keyframe |
| La animación no se reproduce | Prioridad insuficiente | Sube a `accion` |
| Los brazos suben al lado equivocado (R6) | En R6 el eje X sube brazos y es siempre negativo | Pon valores negativos en X |
| Los brazos suben al lado equivocado (R15) | En R15 el eje Z sube brazos | Invierte el signo del brazo afectado |
| El GIF se ve bien pero en Studio no | El Dummy es del otro rig | Inserta un Dummy del rig del JSON |
| El .rbxmx no aparece en el editor | Se soltó fuera de `AnimSaves` | Debe ir dentro de AnimSaves |

---

## 9. Referencias

- `mecanicas/01-fundamentos.md` a `09-errores-y-checklist.md` — el catálogo completo
- `prompts/PROMPT-1-DISENO.md` — plan de diseño de interfaces
- `prompts/PROMPT-2-ANIMACION.md` — generación de animaciones
- `prompts/PROMPT-IAS.md` — generación del pase de batalla
- `herramientas/revisar_pase.bat` — el pipeline (único punto de entrada)
- `referencias/*.txt` — medidas reales de animaciones de la toolbox
