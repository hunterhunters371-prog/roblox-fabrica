# Hallazgos del entorno

Lista de fallos y mejoras encontrados al usar las herramientas del repositorio
para construir juego3. Cada punto dice donde esta, que pasa, por que pasa y el
arreglo. Los que llevan **arreglado en juego3** ya estan escritos como codigo
en `juego3/gen_rbxmx.py`; el resto sigue abierto en el resto del repositorio.

## 1. WaitForChild con parentesis anidados da falso positivo

**Donde**: `juego2/gen_rbxmx.py`, `revisar_lua`.

La busqueda es `WaitForChild\(([^)]*)\)`. La clase `[^)]*` para en el primer
parentesis de cierre, asi que en
`carpeta:WaitForChild(tostring(i), 5)` captura `tostring(i`, no ve la coma y
avisa de "WaitForChild sin timeout" en una linea que si lo tiene. Al contrario
tambien falla: `WaitForChild(nombres[1])` captura `nombres[1]` sin coma y
acierta por casualidad, pero `WaitForChild(pack(a, b))` pasaria como correcto
sin llevar tiempo maximo.

**Arreglo**: leer los argumentos contando parentesis y buscar la coma solo en
el primer nivel. **Arreglado en juego3** (`argumentos_de` y
`hay_coma_de_primer_nivel`).

## 2. La lista negra rechaza Animator:LoadAnimation

**Donde**: `juego2/gen_rbxmx.py`, lista de APIs obsoletas.

El patron es `LoadAnimation` a secas. `PROMPT-3` regla 4 obliga a usar
`Animator:LoadAnimation` en lugar de `Humanoid:LoadAnimation`, asi que
cualquier script que cumpla la regla es rechazado por el empaquetador. La
herramienta y la norma se contradicen.

**Arreglo**: marcar solo `Humanoid:LoadAnimation`. **Arreglado en juego3**.

## 3. El numero de fuentes esta escrito a mano

**Donde**: `juego2/gen_rbxmx.py`, `main`: `return 0 if ok_src == 4 else 1`.

El 4 no sale de la lista de fuentes. Al anadir un quinto script el generador
devuelve 1 aunque todo este bien, y si se quita uno devuelve 0 con una fuente
sin verificar. Un `.bat` o un CI que mire el codigo de salida se cree lo
contrario de lo que pasa.

**Arreglo**: comparar contra `len(FUENTES)` y declarar el arbol como dato.
**Arreglado en juego3** (`FUENTES`, `TIPO_ESPERADO`, `ARBOL`).

## 4. esc() no se aplica a los nombres

**Donde**: `juego2/gen_rbxmx.py`, construccion del XML.

`esc()` se usa en las fuentes pero los `Name` y los valores de propiedad se
meten tal cual. Hoy no rompe porque ningun nombre lleva `&`, `<` o `>`, pero
el dia que un nombre los lleve el fallo aparece tarde y disfrazado: el
generador escribe el archivo y es `ET.parse` de la auditoria quien avisa de un
XML mal formado, sin decir que el problema es el nombre.

**Arreglo**: pasar por `esc()` todo lo que entra al XML. **Arreglado en
juego3** (`escribir_nodo`).

## 5. despojar() no conoce las cadenas con acento grave

**Donde**: `juego2/gen_rbxmx.py`, `despojar`.

Entiende `"`, `'`, `[[ ]]` y los comentarios, pero no las cadenas
interpoladas de Luau. Su contenido llega intacto al recuento de bloques, asi
que una palabra como `if` o `end` dentro del texto descuadra la cuenta y el
aviso apunta a un fallo de sintaxis que no existe.

**Arreglo**: tratar el acento grave como delimitador de cadena. **Arreglado
en juego3**.

## 6. El recuento de bloques no descontaba elseif

**Donde**: `juego2/gen_rbxmx.py`, `revisar_lua`.

El propio comentario del archivo reconoce que la cuenta daba `end` de mas.
La causa es que `elseif` entra en el recuento de `if` sin abrir bloque nuevo:
cada `elseif` pide un `end` que nunca existe.

**Arreglo**: `n_if = contar(if) - contar(elseif)`, y sacar `repeat`/`until` a
su propia comprobacion. **Arreglado en juego3**, con el mensaje de error
mostrando los cuatro numeros para poder descartar un falso aviso a mano.

## 7. Falta comprobar la cabecera obligatoria

**Donde**: `AGENTS.md` (regla de las dos lineas) frente a los generadores.

`AGENTS.md` obliga a que todo script empiece con `-- TIPO:` y `-- RUTA:`,
pero ninguna herramienta lo comprueba: es una regla que solo existe en la
documentacion. Y cuando la cabecera miente (dice `Script` y el generador lo
monta como `LocalScript`) el error solo se ve al probar en Studio.

**Arreglo**: `revisar_cabecera` compara la cabecera con la clase real del
arbol. **Arreglado en juego3**.

## 8. roblox_lint.py solo entiende interfaces

**Donde**: `herramientas/roblox_lint.py`, tablas `CLASES` y `PROPS`.

No estan `Part`, `Script`, `LocalScript`, `ModuleScript`, `SpawnLocation`,
`BillboardGui`, `WeldConstraint` ni `RemoteEvent`. Cualquier `.rbxmx` de juego
completo, incluidos juego2 y juego3, se llena de `R1-CLASE` y `R2-PROP`
falsos. `juego2/README.md` ya lo daba por conocido; sigue abierto y es lo que
impide meter los juegos en la verificacion automatica.

**Arreglo**: un modo mundo (`--mundo`) que amplie las clases permitidas y
salte las reglas de GUI, o separar las tablas en dos perfiles.

## 9. R6-RICHTEXT falla con las etiquetas que se cierran solas

**Donde**: `herramientas/roblox_lint.py`, regla de RichText.

Cuenta aperturas con `<\s*(\w+)` y cierres con `<\s*/\s*\w+`. Un `<br/>`
legitimo suma apertura y no suma cierre, asi que da error de etiqueta sin
cerrar en texto correcto. Ademas la condicion exterior es
`if abre != cierra * 2 - cierra:`, que es exactamente `abre != cierra`, con lo
que el `if abre != cierra:` de dentro nunca decide nada: parece que compara
dos cosas distintas y compara la misma dos veces.

**Arreglo**: descontar las etiquetas que terminan en `/>` y dejar una sola
condicion legible.

## 10. Clases permitidas sin tabla de propiedades

**Donde**: `herramientas/roblox_lint.py`, `PROPS.get(cls)`.

`ViewportFrame`, `UIAspectRatioConstraint` y `UISizeConstraint` estan en
`CLASES` pero no en `PROPS`. `PROPS.get` devuelve `None` y la regla `R2-PROP`
se salta en silencio: en esas clases se puede escribir cualquier propiedad,
incluso mal escrita, y el lint dice que todo esta bien. Un agujero silencioso
es peor que un error.

**Arreglo**: si una clase esta en `CLASES` y no en `PROPS`, avisar de que no
hay tabla en lugar de aprobar.

## 11. R9 tiene codigo que no hace nada

**Donde**: `herramientas/roblox_lint.py`, regla de sombras.

El comentario dice que cada sombra se valida contra sus hermanos, pero la
lista de hermanos se crea vacia y no se usa, y el marcado `_shadowz` que se
escribe en el arbol no lo lee nadie despues. La comprobacion por elemento
nunca se dispara: solo queda el aviso global del final.

**Arreglo**: quitar el codigo muerto o terminar la comprobacion. Tal como
esta, quien lea el archivo cree que hay una validacion que no existe.

## 12. es_entero acepta el vacio como entero

**Donde**: `herramientas/roblox_lint.py`, `es_entero`.

Con cadena vacia o `None` devuelve `True`. Un desplazamiento que falta pasa
como valido en vez de avisar de que falta.

**Arreglo**: separar "no hay valor" de "el valor es entero" y decidir cual de
las dos cosas quiere la regla.

## 13. revisar_pase.bat elige conversor por una palabra

**Donde**: `herramientas/revisar_pase.bat`, documentado en `AGENTS.md`.

Elige entre conversor de animacion y de interfaz buscando el texto literal
`rig` dentro del JSON. Un JSON de interfaz que contenga esa palabra en
cualquier sitio, aunque sea el nombre de un boton, se procesa con el conversor
equivocado. El aviso esta en la documentacion, pero es una trampa que se
puede quitar.

**Arreglo**: decidir por una clave de primer nivel explicita, por ejemplo
`"tipo": "animacion"` o `"tipo": "interfaz"`, y fallar con un mensaje claro
si no esta.

## 14. Requisitos de Python incompletos

**Donde**: `README.md` raiz frente a `juego2/gen_datos.py`.

El README pide `pillow` y `lz4`. `juego2/gen_datos.py` importa `numpy`, que no
se menciona en ningun sitio: quien clone el repositorio y siga el README se
encuentra un `ImportError` al reconstruir juego2.

**Arreglo**: anadir `numpy` a la lista, o mejor un `requirements.txt` que sea
la unica fuente de verdad. Aparte, `juego2/Datos.lua` y
`juego2/BancoDeAnimaciones.rbxmx` no estan en el repositorio porque se
generan; conviene decirlo en el README de juego2 junto al comando que los crea.

## 15. AGENTS.md no encamina "quiero un juego"

**Donde**: tabla de rutas de `AGENTS.md`.

Hay ruta para interfaces, animaciones y mecanicas, pero no para "quiero un
juego completo". El patron existe (juego2 y ahora juego3: un solo `.rbxmx`
autocontenido, servidor mas plantilla de interfaz, generador con revision y
auditoria) y no esta escrito en la tabla, asi que hay que descubrirlo leyendo
los archivos.

**Arreglo**: una fila mas que apunte a `juego3/README.md` como patron de juego
completo.
