# Verificacion ejecutada

Este documento recoge unicamente resultados que se ejecutaron de verdad, con
el comando y la salida real. Lo que no se pudo ejecutar aparece separado en la
seccion "Lo que NO esta verificado", que es igual de importante.

Entorno de las pruebas: Linux, Python 3.13.14, sin acceso a red y sin Roblox
Studio. Por eso todo lo que es Luau se revisa de forma estatica, nunca se
ejecuta.

## Resumen

| Suite | Que revisa | Casos | Resultado |
|---|---|---|---|
| 1 | Validador de animaciones `spec_anim.py` | 37 | 37 correctas, 0 fallos |
| 2 | Generador de interfaces + linter | 99 | 99 correctas, 0 fallos |
| 3 | Auditor estatico de Luau | 7 + 16 | autotest 7/7, 16 hallazgos reales |
| 4 | Los 11 modelos de `animaciones/` | 11 | 11 pasan, 1 aviso real |
| 5 | Banco de animaciones en Roblox (.rbxmx) | - | generado y auditado |

Total: 154 casos ejecutados.

## 1. Validador de animaciones

Se ejecuto `spec_anim.py` sobre 37 casos, cada uno en un proceso nuevo porque
el validador acumula errores en una variable global de modulo. De cada caso se
comprueban cuatro cosas: el codigo de salida, el fragmento de mensaje, que el
XML sea valido cuando debe pasar y que NO se genere ningun `.rbxmx` cuando
debe fallar.

Limites confirmados en el borde exacto:

| Limite | Valor que pasa | Valor que se rechaza |
|---|---|---|
| Keyframes | 40 | 41 |
| Duracion | 30.0 s | 31.0 s |
| Angulo | 180 grados | 181 |
| Desplazamiento | 2.5 studs | 2.6 |
| Longitud del nombre | 40 caracteres | 41 |

Otros rechazos confirmados: `R7` y `r6` en minuscula, articulaciones de un rig
usadas en el otro, `"RightArm"` sin espacio en R6, animar
`HumanoidRootPart`, tiempos no crecientes, y un archivo donde ninguna
articulacion se mueve.

`Head` es la unica articulacion que existe en los dos rigs.

## 2. Interfaces

Se ejecuto el pipeline real sobre `interfaces/pase.json`:

```text
OK  el JSON es valido
instancias : 528
tamano     : 302438 bytes
premios    : 6 gratis + 6 premium
```

Auditoria independiente del XML generado: censo de 528 instancias que cuadra
exactamente, 0 referentes duplicados, 0 desplazamientos con decimales, 0
colores fuera de rango, 600 lineas de Luau embebido y 0 dobles escapados.

El linter da paso limpio:

```text
ERRORES  0   nada que rompa el motor
AVISOS   0
```

Despues se ejecutaron 99 sondas contra el generador. La tabla de limites de
tarjeta se reprodujo entera:

| Premios | Ancho | Interior | Etiqueta | Titulo | Desc | Bonus |
|---|---|---|---|---|---|---|
| 1 | 1064 | 1040 | 185 | 126 | 343 | 131 |
| 2 | 524 | 500 | 87 | 60 | 165 | 61 |
| 3 | 344 | 320 | 54 | 38 | 105 | 38 |
| 4 | 254 | 230 | 38 | 27 | 76 | 26 |
| 5 | 200 | 176 | 28 | 21 | 58 | 19 |
| 6 | 164 | 140 | 21 | 16 | 46 | 14 |

### Hallazgo: PROMPT-1 no coincide con el codigo

PROMPT-1-DISENO.md documenta limites que no son los reales.

| Campo | Dice PROMPT-1 | Limite real |
|---|---|---|
| `temporada` | 25 | 28 |
| `titulo` de cabecera | 28 | 30 |
| `subtitulo` | 80 | 81 |
| `tiempo` | 11 | 11 |

Los tres primeros son conservadores, o sea inofensivos. El peligroso es otro:
PROMPT-1 dice que el `titulo` de una tarjeta admite 20 caracteres, pero con 6
premios el limite real es 16 y el generador rechaza el archivo con el mensaje
`solo caben 16`. El `pase.json` que se envia no lo destapa porque su titulo
mas largo tiene 15 caracteres, justo uno por debajo.

Ademas `mecanicas/05-gui.md` en su Parte A repite los numeros de PROMPT-1 y se
olvida de cuatro claves obligatorias de la raiz: `niveles`, `nivel`, `xp` y
`xpPorNivel`. Se comprobo que quitando cualquiera de las cuatro el generador
falla.

### Rareza confirmada

`xp: true` se acepta como si fuera `1`, porque en Python `bool` es subclase de
`int` y la comprobacion de tipo usa `isinstance`. No rompe nada, pero conviene
saberlo.

## 3. Auditor estatico de Luau

Se extrajo el Luau que va embebido en el `.rbxmx` de la interfaz
(`PaseFuncional`, 601 lineas, 15297 bytes) y se paso por un auditor propio.

El auditor no se cree a si mismo: antes de auditar corre un autotest con
codigo cebo que contiene los 7 tipos de fallo a proposito, y aborta si no los
detecta todos. Resultado del autotest: 7 de 7 detectados, 0 falsos positivos.

Resultado sobre el codigo real: **16 hallazgos, todos de tipo `ESPERA`**. Cero
APIs obsoletas, cero llamadas de riesgo sin `pcall`, cero bucles sin espera,
cero confusiones de grados y radianes, cero fugas de conexiones.

Reglas del auditor: `OBSOLETA`, `ESPERA`, `RADIANES`, `SIN-PCALL`, `BUCLE`,
`CABECERA`, `FUGA`. La lista negra de APIs obsoletas cubre 16 casos, entre
ellos `BodyVelocity`, `SetPrimaryPartCFrame`, `FindPartOnRay`, `wait()`,
`spawn()` y `Humanoid:LoadAnimation()`.

Excepcion conocida y deliberada: la ficha 22 de `mecanicas/02-movimiento.md`
usa `cinta.Velocity` a proposito, porque en cintas transportadoras es el
comportamiento buscado.

## 4. Los 11 modelos de animaciones/

Primero se comprobo que los archivos que se probaron son los del repositorio,
comparando `git hash-object` de cada uno:

```text
los 11 modelos son byte a byte identicos al repositorio
```

Los 11 pasan el validador. Duraciones medidas:

| Modelo | Rig | Keyframes | Duracion |
|---|---|---|---|
| baile_r6 | R6 | 5 | 1.00 s |
| caminar_chulo_r6 | R6 | 9 | 1.20 s |
| caminar_r15 | R15 | 5 | 0.70 s |
| caminar_r6 | R6 | 5 | 0.70 s |
| caminar_vida_r15 | R15 | 5 | 0.90 s |
| caminar_vida_r6 | R6 | 5 | 0.90 s |
| correr_flujo_r6 | R6 | 9 | 0.60 s |
| correr_pro_r6 | R6 | 9 | 0.60 s |
| correr_ref_r6 | R6 | 9 | 0.67 s |
| salto_r6 | R6 | 7 | 1.15 s |
| saludar_r6 | R6 | 6 | 1.40 s |

### Unico defecto real

`caminar_vida_r15.json` declara `LeftLowerArm` y `RightLowerArm` en los cinco
keyframes, siempre con el mismo valor `(-12, 0, 0)`. Estan declarados pero
nunca cambian: son peso muerto en el archivo. No se corrigen automaticamente
porque inventar movimiento seria fabricar datos que nadie autorizo.

## 5. Segunda prueba: banco de animaciones en Roblox

Se construyo un juego de un solo archivo, `juego2/BancoDeAnimaciones.rbxmx`,
para ver los 11 modelos moverse en un entorno controlado. Se importa con clic
derecho en `Workspace` y despues `Insert from File`.

Estructura del paquete:

| Instancia | Clase | Tamano del codigo |
|---|---|---|
| BancoDeAnimaciones | Folder | - |
| Servidor | Script | 2522 bytes |
| Interfaz | ScreenGui | - |
| Cliente | LocalScript | 30003 bytes |
| Datos | ModuleScript | 56279 bytes |
| Rig | ModuleScript | 10121 bytes |

Auditoria del XML generado:

```text
xml bien formado            si
instancias                  6
referentes duplicados       0
fuentes que vuelven iguales 4 de 4
doble escapado              no
tamano                      100682 bytes
```

Revision estructural de los cuatro fuentes Luau, contando bloques:

| Archivo | Lineas | function | if | do | end | Veredicto |
|---|---|---|---|---|---|---|
| Servidor | 82 | 2 | 5 | 1 | 8 | OK |
| Rig | 316 | 10 | 13 | 8 | 31 | OK |
| Datos | 1282 | 0 | 0 | 0 | 0 | OK |
| Cliente | 1069 | 42 | 53 | 7 | 102 | OK |

La regla de balance que funciona es `end` igual a `function` mas `if` mas
`do`. Un `for` o un `while` ya llevan su propio `do`, y un `repeat` cierra con
`until`. Importante: no hay que restar los `elseif`, porque la expresion
`\bif\b` nunca casa dentro de `elseif`.

Los maniquies no usan `Motor6D`: todas las partes van `Anchored` y un modulo
calcula la cinematica directa con
`mundoHijo = mundoPadre * c0 * poseCF(pose) * c1:Inverse()`. Es determinista,
igual en el editor que en Play, e inmune a la deformacion por fisica.

## 6. Correccion importante: el hallazgo EN-FASE era un falso positivo

Una version anterior de este documento afirmaba que cinco modelos R6 tenian un
defecto de fase, con las dos piernas o los dos brazos moviendose a la vez.
**Esa conclusion era incorrecta y queda retractada.**

El error estaba en el metodo, no en los datos. El comparador miraba los
numeros escritos en el JSON y daba por hecho que dos valores identicos
producen el mismo movimiento. En R6 eso es falso.

### La causa

En R6 la cadera y el hombro izquierdos llevan el marco base espejado,
`euler(0, -PI/2, 0)`, frente a `euler(0, +PI/2, 0)` en el lado derecho. Ese
marco conjuga la rotacion de la pose, asi que un mismo numero produce
movimiento contrario en cada lado.

Prueba aislada, con el torso puesto a cero y la misma pose `[0, 0, 45]` en las
dos piernas de un R6:

```text
pie derecho    z = -1.4142
pie izquierdo  z = +1.4142      lados opuestos, la marcha alterna
```

Y con valores opuestos, que es lo que el comparador antiguo daba por correcto:

```text
pie derecho    z = -1.4142
pie izquierdo  z = -1.4142      mismo lado, las dos piernas van juntas
```

Esto encaja con una regla que ya estaba escrita en la documentacion del
proyecto: en R6, X eleva los brazos de lado y va siempre negativo para los dos
brazos. Esa regla solo tiene sentido si los marcos estan espejados.

### La conclusion correcta

Las dos convenciones del repositorio eran correctas, cada una para su rig:

- **R6**: los marcos estan espejados, asi que para alternar hay que poner el
  **mismo** valor en los dos lados.
- **R15**: las articulaciones estan alineadas con los ejes, asi que para
  alternar hay que poner valores **opuestos**.

El comparador antiguo aplicaba la logica de R15 a los archivos de R6.

### Medicion correcta

El analisis se rehizo con `juego2/cinematica.py`, que reconstruye la posicion
real de cada miembro y correlaciona las dos trayectorias. Una correlacion
cercana a -1 es contrafase, es decir alternancia correcta.

| Modelo | Rig | Piernas | Brazos |
|---|---|---|---|
| caminar_r6 | R6 | -1.00 | -1.00 |
| caminar_vida_r6 | R6 | -1.00 | -1.00 |
| caminar_chulo_r6 | R6 | -1.00 | -1.00 |
| correr_flujo_r6 | R6 | -1.00 | -1.00 |
| correr_pro_r6 | R6 | -0.99 | -1.00 |
| correr_ref_r6 | R6 | -0.96 | -0.92 |
| caminar_r15 | R15 | -1.00 | -0.99 |
| caminar_vida_r15 | R15 | -0.98 | -1.00 |

Los nueve ciclos de locomocion estaban bien desde el principio.

`salto_r6` mide +1.00, pero es un salto: las dos piernas deben ir juntas. La
regla se aplica ahora solo a animaciones con `loop` verdadero y prioridad
`movimiento`.

**Defectos de fase reales: 0.** El unico hallazgo valido de todo el analisis
semantico sigue siendo el de `caminar_vida_r15` de la seccion 4, que no
depende de marcos ni de convenciones porque un valor constante no se mueve en
ningun caso.

### Consecuencia practica

No hay que arreglar ninguna animacion. Aplicar la supuesta correccion, que
desplazaba medio ciclo el miembro izquierdo, **estropea** los archivos: la
simulacion mostro que dejaba los dos pies del mismo lado.

En el banco de animaciones esa variante estropeada se conserva a proposito,
como material didactico, etiquetada en rojo y con el nombre `roto`. Sirve para
ponerla al lado del dato bueno y ver la diferencia.

### Leccion metodologica

Una regla semantica sobre los numeros que alguien escribio a mano no es fiable
cuando el rig aplica transformaciones por articulacion. Hay que medir el
movimiento que sale, no el numero que entra. Este unico error produjo ocho
informes de defecto falsos y una correccion que habria dañado datos correctos.

## 7. Lo que NO esta verificado

Esta seccion es tan importante como las anteriores.

- **Ningun Luau se ha ejecutado nunca.** No hay interprete de Lua ni de Luau
  en el entorno de pruebas y no se puede instalar porque la red esta cerrada.
  Roblox Studio tampoco corre en Linux. Todo lo que se dice del Luau viene de
  revision estatica: balance de bloques, delimitadores, cadenas sin cerrar,
  APIs obsoletas y `WaitForChild` sin tiempo limite. Un error de tipo en
  tiempo de ejecucion solo aparecera al pulsar Play.
- **Ningun `.rbxmx` se ha abierto en Studio.** Se comprueba que el XML es
  valido, que los referentes no se repiten, que las clases y propiedades son
  las que el motor admite y que el codigo embebido vuelve identico al
  original. Nada de eso garantiza que Studio lo importe sin queja.
- **La animacion del banco es de cliente.** Vale para observar, pero otro
  jugador no veria moverse los maniquies.
- **La interfaz del banco se construye en tiempo de ejecucion** con
  `Instance.new`, no como instancias del XML, asi que el linter de interfaces
  no tiene nada que revisar en ese archivo. Ademas el linter no admite
  `Part`, `Script`, `SpawnLocation` ni `BillboardGui`, que el banco si usa.
- **`interfaces/temporada2.json` no se ha probado.** Solo se probo `pase.json`.
- **`GUIA-COMPLETA.md` no se ha auditado.**
- **Los nueve modulos de `mecanicas/` no se han auditado uno a uno.** El
  auditor existe y funciona, pero se ejecuto sobre el Luau de la interfaz, no
  sobre los ejemplos de la documentacion.

## 8. Como repetir las pruebas

Cada caso se lanza en un proceso nuevo, porque los validadores guardan los
errores en una variable global de modulo y reutilizar el proceso contamina el
resultado siguiente.

```text
python3 herramientas/spec_anim.py animaciones/caminar_r6.json
python3 herramientas/spec_a_rbxmx.py interfaces/pase.json
python3 herramientas/roblox_lint.py interfaces/pase.rbxmx
python3 juego2/gen_datos.py
python3 juego2/gen_rbxmx.py
```

Dos avisos practicos aprendidos a base de perder tiempo:

- Una tuberia con `head` se come el codigo de salida real. Si el codigo
  importa, hay que redirigir a un archivo y leer `$?` justo despues.
- `.text` de ElementTree ya viene sin escapar. Comparar contra la cadena
  escapada da un fallo que no existe.

## 9. Siguiente paso

Lo mas util ahora, por orden:

1. Abrir `juego2/BancoDeAnimaciones.rbxmx` en Studio y pulsar Play. Es la
   unica forma de convertir la revision estatica en verificacion real.
2. Corregir la Parte A de `mecanicas/05-gui.md`: los limites reales y las
   cuatro claves obligatorias que faltan.
3. Documentar la regla de los marcos espejados en
   `mecanicas/04-animacion.md`. Es el dato mas util que ha salido de todo
   este trabajo.
4. Probar `interfaces/temporada2.json` con el mismo pipeline que `pase.json`.
