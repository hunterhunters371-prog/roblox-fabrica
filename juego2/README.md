# Banco de animaciones

Segundo juego del proyecto. Es un banco de pruebas para ver los 11 modelos de
`animaciones/` moviendose de verdad, en un entorno controlado, sin tener que
importar cada uno a mano en el editor de animaciones.

Todo cabe en un solo archivo `.rbxmx` que se inserta en `Workspace`.

## Como se abre

1. Roblox Studio, plantilla Baseplate.
2. Clic derecho en **`Workspace`**, opcion **Insert from File**.
3. Elegir `BancoDeAnimaciones.rbxmx`.
4. Pulsar **F5**.

El `Script` del servidor monta suelo, punto de aparicion y luz, y copia la
interfaz al `PlayerGui` de cada jugador que entra. Eso ultimo hace falta
porque un `LocalScript` dentro de `Workspace` no se ejecuta.

## Que aparece dentro

```text
Workspace
└── BancoDeAnimaciones          Folder
    ├── Servidor                Script         suelo, aparicion, luz
    └── Interfaz                ScreenGui      plantilla, ResetOnSpawn false
        ├── Cliente             LocalScript    interfaz, camara, reto
        ├── Datos               ModuleScript   los 11 modelos (generado)
        └── Rig                 ModuleScript   maniquies R6 y R15
```

## Modo visor

A la izquierda, la lista de los 11 modelos. Al elegir uno se levantan dos
maniquies sobre dos pedestales:

- **Verde, a la izquierda**: el dato tal cual esta en `animaciones/*.json`.
- **Rojo, a la derecha**: la misma animacion con el eje de vaiven del miembro
  izquierdo negado.

El maniqui rojo **no es una correccion**. Es el error tipico al portar una
animacion de un rig al otro, puesto ahi a proposito para poder comparar. Ver
la seccion de la convencion mas abajo.

Abajo: pausa, reiniciar, bucle, velocidad (0.25x, 0.5x, 1x, 2x), comparar, y
una pista de tiempo que se puede arrastrar, con una marca por keyframe.

A la derecha: la correlacion de fase medida para cada par de miembros, y la
convencion del rig al que pertenece la animacion.

Camara orbital. Clic derecho arrastrando gira, la rueda acerca y aleja. Si no
se toca, orbita despacio sola.

Teclas: `Espacio` pausa, `R` reinicia, flechas arriba y abajo cambian de
modelo.

## Modo reto de fase

Mecanica de 60 segundos, igual de duracion que el juego principal del
proyecto.

Sale **un solo maniqui**, siempre en azul neutro para que el color no delate
la respuesta, y la mitad de las veces es la variante rota. Hay que decidir si
los miembros **alternan bien** o **van en fase**. Puntos con bonus por racha,
y al terminar aciertos, precision y mejor racha.

Solo entran los ocho ciclos que tienen variante de contraste, asi que no vale
memorizar la lista.

## La convencion que hay que entender

Es el dato mas util que salio de construir esto.

| Rig | Marcos de las articulaciones | Para que una marcha alterne |
|---|---|---|
| R6 | La cadera y el hombro izquierdos van espejados, `euler(0,-90,0)` frente a `euler(0,+90,0)` | Hay que poner el **mismo** valor en los dos lados |
| R15 | Alineadas con los ejes | Hay que poner valores **opuestos** |

En R6 el marco espejado conjuga la rotacion de la pose, asi que un mismo
numero produce movimiento contrario en cada lado. Prueba aislada, torso a
cero, pose `[0, 0, 45]` en las dos piernas:

```text
pie derecho    z = -1.4142
pie izquierdo  z = +1.4142      lados opuestos, alterna
```

Y con valores opuestos, que es lo que parece correcto a primera vista:

```text
pie derecho    z = -1.4142
pie izquierdo  z = -1.4142      mismo lado, van juntas
```

Esto encaja con la regla que ya estaba escrita en `mecanicas/04-animacion.md`:
en R6, X eleva los brazos de lado y va siempre negativo para los dos brazos.
Solo tiene sentido si los marcos estan espejados.

Consecuencia: **no hay que arreglar ninguna animacion del repositorio.** Los
nueve ciclos alternan correctamente, cada uno con la convencion de su rig. El
detalle completo esta en `VERIFICACION.md`, seccion 6.

## Como se reconstruye

Dos archivos del banco son generados y no se guardan en el repositorio,
porque se reproducen exactamente con estos dos comandos:

```text
cd juego2
python3 gen_datos.py      # lee ../animaciones/*.json  ->  Datos.lua
python3 gen_rbxmx.py      # empaqueta los 4 .lua       ->  BancoDeAnimaciones.rbxmx
```

`gen_datos.py` necesita `numpy`, porque el analisis de fase pasa por
`cinematica.py`.

`gen_rbxmx.py` no solo empaqueta: antes revisa los cuatro fuentes Luau
(balance de bloques, delimitadores, cadenas sin cerrar, APIs obsoletas,
`WaitForChild` sin tiempo limite) y despues audita el XML que acaba de
escribir (XML bien formado, referentes sin repetir, y que el codigo embebido
vuelva byte a byte igual al original). Si algo no cuadra, aborta.

## Archivos

| Archivo | Que es |
|---|---|
| `cinematica.py` | Cinematica directa de R6 y R15, y analisis de fase medido en el mundo |
| `gen_datos.py` | Convierte los 11 JSON en `Datos.lua` |
| `gen_rbxmx.py` | Revisa los 4 fuentes Luau y los empaqueta en el `.rbxmx` |
| `Rig.lua` | Construye los maniquies y evalua las poses |
| `Cliente.lua` | Interfaz, camara y el reto |
| `Servidor.lua` | Suelo, aparicion, luz y copia de la interfaz |
| `Datos.lua` | Generado por `gen_datos.py` |
| `BancoDeAnimaciones.rbxmx` | Generado por `gen_rbxmx.py` |

## Decisiones de diseno

- **Cinematica directa, no `Motor6D`.** Todas las partes van `Anchored` y con
  `CanCollide` en falso. `Rig.lua` calcula
  `mundoHijo = mundoPadre * c0 * poseCF(pose) * c1:Inverse()` recorriendo las
  partes en orden topologico. Es determinista, se ve igual en el editor y en
  Play, y no se deforma con la fisica.
- **Los `c0` y `c1` de R6 llevan las rotaciones reales del rig de Roblox.** Se
  cancelan en la pose de reposo, pero conjugan la rotacion de la pose. Eso es
  precisamente lo que produce el efecto del marco espejado.
- **La interfaz se construye en tiempo de ejecucion** con `Instance.new`, no
  como instancias del XML. Mucho menos fragil que emitir cientos de nodos a
  mano, pero significa que `herramientas/roblox_lint.py` no tiene nada que
  revisar aqui. Ese linter tampoco admite `Part`, `Script`, `SpawnLocation`
  ni `BillboardGui`, que este archivo si usa.

## Limites

- **El Luau nunca se ha ejecutado.** No habia interprete de Lua ni de Luau en
  el entorno donde se construyo, y Studio no corre en Linux. Todo lo que se
  afirma del codigo viene de revision estatica. Un error de tipo en tiempo de
  ejecucion solo aparecera al pulsar Play.
- **La animacion es de cliente.** Vale para observar, pero otro jugador no
  veria moverse los maniquies. Para un banco de un solo jugador da igual.
- **Los maniquies no son avatares.** Son partes movidas por calculo, no
  personajes con `Humanoid`.

## Siguiente paso

Abrirlo en Studio y pulsar Play. Es la unica forma de convertir la revision
estatica en verificacion de verdad.
