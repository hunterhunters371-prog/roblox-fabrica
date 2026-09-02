# Informe de verificacion

Auditoria de `GUIA-COMPLETA.md` y de la documentacion de `mecanicas/`
contra el **codigo fuente real** del repositorio.

**Fuentes de verdad usadas:** `herramientas/spec_anim.py`,
`herramientas/spec_a_rbxmx.py`, `herramientas/roblox_lint.py`,
`herramientas/revisar_pase.bat`, y como evidencia cruzada los modelos
`caminar_r6.json`, `caminar_r15.json`, `caminar_vida_r6.json`,
`correr_pro_r6.json`, `correr_flujo_r6.json`, `salto_r6.json`,
`saludar_r6.json`, `interfaces/pase.json`.

Metodo: cuatro frentes en paralelo (pipeline, validador de animacion,
validador de interfaz + linter, modelos JSON), y contraste de cada regla
documentada contra la linea de codigo que la implementa.

---

## A. Errores corregidos en GUIA-COMPLETA.md

### A1. `easing` es campo de raiz, no de keyframe

**Estaba mal:** la tabla listaba `keyframes[].easing`.

**Codigo (`spec_anim.py`):**

```python
easing_nom = spec.get("easing", "suave")   # <- nivel raiz
...
cuerpo.append(keyframe_xml(k["t"], k["poses"], arbol, easing))
```

El easing se lee **una vez** de la raiz y se aplica a **todas** las poses de
**todos** los keyframes. Un `easing` dentro de un keyframe se ignora en
silencio.

> Nota: `mecanicas/04-animacion.md` (tabla A.1) tiene el mismo error.

### A2. `loop`, `prioridad` y `easing` son opcionales

**Estaba mal:** `loop` y `prioridad` marcados como obligatorios.

**Codigo:** solo tres campos pasan por `pide()`, que es lo que exige la
clave:

```python
rig    = pide(spec, "rig", str, "raiz")
nombre = pide(spec, "nombre", str, "raiz")
kfs    = pide(spec, "keyframes", list, "raiz")
loop        = spec.get("loop", True)        # opcional, default true
prioridad   = spec.get("prioridad", "accion")
easing_nom  = spec.get("easing", "suave")
```

### A3. Contrafase en R6: se usa el MISMO valor en los dos lados

Este es el error mas importante del informe, porque invierte el signo de
media animacion.

**Estaba mal (y en `mecanicas/04-animacion.md` A.5 esta escrito al reves):**
"En R6 la contrafase es un `z` positivo en una pierna y negativo en la otra."

**Por que es falso:** `spec_anim.py` **no aplica ningun espejo**. Cada
articulacion recibe sus angulos tal cual:

```python
vals = rotaciones.get(nombre, (0.0, 0.0, 0.0))
rx, ry, rz = vals[:3]
m = rotacion_matriz(rx, ry, rz)
```

El espejo lo pone el **rig**: en R6 las articulaciones vienen rotadas 90
grados de fabrica y en sentido opuesto entre lado izquierdo y derecho. Por
eso `PROMPT-2-ANIMACION.md` dice: *"Z POSITIVO = adelante el lado DERECHO,
Z NEGATIVO = adelante el IZQUIERDO"*.

**Evidencia en los tres modelos R6 que funcionan** (piernas identicas):

| Archivo | Right Leg | Left Leg |
|---|---|---|
| `caminar_r6.json` t=0 | `[0, 0, 45]` | `[0, 0, 45]` |
| `caminar_vida_r6.json` t=0 | `[0, 0, 32, 0, 0.05, 0]` | `[0, 0, 32, 0, 0.05, 0]` |
| `correr_flujo_r6.json` t=0 | `[0, 0, 48, -1.0, 0.12, 0]` | `[0, 0, 48, -1.0, 0.12, 0]` |

**Y al contrario, `salto_r6.json`** (pose simetrica, las dos piernas abiertas
igual) usa signos **opuestos**: `Left Leg [0,0,-25,...]` /
`Right Leg [0,0,25,...]`.

**Contraste con R15** (`caminar_r15.json`), donde si hacen falta signos
opuestos para la contrafase: `RightUpperLeg [45,0,0]` /
`LeftUpperLeg [-45,0,0]`.

**Regla correcta:**

| Quieres | R6 | R15 |
|---|---|---|
| Contrafase (una extremidad adelante, la otra atras) | **mismo valor** en ambos lados | **signos opuestos** |
| Pose simetrica / espejada (las dos igual) | **signos opuestos** | **mismo valor** en el eje de avance |
| Brazos contralaterales a las piernas | signo **opuesto** al de las piernas | mismo criterio que las piernas, invertido |

Comprobacion final en `caminar_r6.json` t=0: piernas `+45` (derecha
adelante), brazos `-35` (izquierdo adelante) -> pierna derecha con brazo
izquierdo. Contralateral correcto.

### A4. El truco de flujo: lo que va a 0.3-0.5 es el desplazamiento, no el giro

**Estaba mal:** "Brazos: `z` de 0.3 a 0.5 del valor de las piernas".

**Evidencia (`correr_flujo_r6.json` t=0):**

```
Right Leg : [0, 0,  48, -1.00,  0.12, 0]
Right Arm : [0, 0, -52, -0.42, -0.18, 0]
```

El giro `z` del brazo (52) es **mayor** que el de la pierna (48). Lo que si
esta en la proporcion 0.3-0.5 es el **desplazamiento**: `0.42 / 1.00 = 0.42`.
Coincide con `PROMPT-2-ANIMACION.md`: *"BRAZOS en FASE: el desplazamiento
acompana al giro... mas chico que el de las piernas (0.3 a 0.5)"*.

Ademas se corrigieron dos valores: el `px` de la pierna en el modelo real es
`-1.0` (no `-1.2`) y el `py` de las piernas va de `0.12`
(`correr_flujo_r6.json`) a `0.25-0.30` (`correr_pro_r6.json`).

### A5. `niveles` es un numero entero, no una lista

**Estaba mal:** "`niveles` | lista | Entre 2 y 20 elementos".

**Codigo (`spec_a_rbxmx.py`):**

```python
niveles = pide(spec, "niveles", int, "raiz")
if isinstance(niveles, int) and not (2 <= niveles <= 20):
    err("raiz.niveles = %d. Debe estar entre 2 y 20." % niveles)
```

`niveles` es la **cantidad de niveles del camino de puntos**. Las listas son
`gratis` y `premium` (1 a 6 premios cada una). Por eso `pase.json` tiene
`niveles: 20` con solo 6 + 6 premios, y es valido.

> Nota: `mecanicas/05-gui.md` (tabla A.2) tiene el mismo error.

### A6. Los limites de la cabecera no eran los del codigo

**Estaba mal:** temporada 25, titulo 28, subtitulo 80 presentados como
"limite exacto". Esos son los valores **conservadores del prompt**.

**Codigo:** el limite se calcula, no es fijo.

```python
ANCHO_CHAR = 0.55
def cabe(texto, ancho_px, text_size, donde):
    limite = int(ancho_px / (text_size * ANCHO_CHAR))
```

| Campo | Llamada real | Limite duro | Recomendado |
|---|---|---|---|
| `temporada` | `cabe(t, 190, 12)` | **28** | 25 |
| `titulo` | `cabe(t, 630, 38)` | **30** | 28 |
| `subtitulo` | `cabe(t, 630, 14)` | **81** | 80 |
| `tiempo` | `cabe(t, 150, 24)` | **11** | 11 |

### A7. Los limites de un premio son calculados, no fijos

**Estaba mal:** etiqueta 18 / titulo 20 / desc 55 / bonus 16 como "limite
exacto".

**Codigo:**

```python
CONTENT_W, GAP = 1064, 16
cw = (CONTENT_W - GAP * (n - 1)) // n
interior = cw - 24
cabe(etiqueta, interior - 20, 10)
cabe(titulo,   interior,      15)
cabe(desc,     interior * 2,  11)   # se envuelve en 2 lineas
cabe(bonus,    interior - 26, 14)
```

Tabla recalculada desde las formulas (verificada premio a premio):

| Premios en la pista | Ancho carta | Interior | etiqueta | titulo | desc | bonus |
|---|---|---|---|---|---|---|
| 1 | 1064 | 1040 | 185 | 126 | 343 | 131 |
| 2 | 524 | 500 | 87 | 60 | 165 | 61 |
| 3 | 344 | 320 | 54 | 38 | 105 | 38 |
| 4 | 254 | 230 | 38 | 27 | 76 | 26 |
| 5 | 200 | 176 | 28 | 21 | 58 | 19 |
| 6 | 164 | 140 | 21 | 16 | 46 | 14 |

Consecuencia practica: **anadir un premio puede invalidar textos que antes
pasaban**. Quitarlo nunca rompe nada.

### A8. El pase generado ya viene funcionando

**Estaba mal:** "Conectas los botones con el codigo de la Parte B".

**Codigo:** `spec_a_rbxmx.py` inyecta un `LocalScript` llamado
`PaseFuncional` dentro del `.rbxmx`, con la logica completa ya escrita:

```python
cfg = "local CFG = {...}"        # sale del JSON
lua = cfg + LOGICA               # ~450 lineas de Luau fijo
"LocalScript": {"Name": "PaseFuncional", "Source": ("protected", lua)}
```

Lo que ya trae hecho: reclamar premios, confeti, `+XP` flotante, subida de
nivel con aviso, barra de progreso animada, camino de puntos que se repinta,
desbloqueo premium, hover de tarjetas, cerrar y reabrir el pase.

Lo que **no** trae: nada de servidor. El estado vive en una tabla local
(`estado.reclamados`), asi que es una demo jugable, no un sistema seguro.
Para produccion hay que mover la autoridad al servidor
(`mecanicas/08-sistemas.md`, seccion 10).

### A9. Etiquetas en mayusculas e icono de un emoji son estilo, no validacion

El codigo solo comprueba longitud y ausencia de `< > &`. Nada obliga a que
`etiqueta` este en mayusculas ni a que `icono` tenga exactamente un emoji.
Son convenciones de diseno, utiles pero no forzadas.

### A10. El indice de keyframes empieza en 0

Las rutas de error son `raiz.keyframes[0]`, `raiz.keyframes[1]`... El primer
keyframe es el `[0]`. Faltaba decirlo.

### A11. La regla de "algo tiene que moverse" es global

`se_mueve_algo` es una sola bandera para toda la animacion:

```python
if any(a != 0 for a in ang):
    se_mueve_algo = True
```

Por eso `salto_r6.json` es valido aunque su primer y ultimo keyframe sean
todo ceros. Lo que si falla es `poses: {}` vacio en un keyframe, que tiene su
propio error. Ademas la bandera cuenta tambien los desplazamientos, no solo
los angulos.

### A12. Incoherencia interna: doble clic vs arrastrar

La seccion 2.2 decia "arrastra el archivo" y la 6.1 "doble clic". El `.bat`
admite las dos, pero con doble clic coge el `.json` **mas reciente** de la
carpeta, que a menudo no es el que quieres. Unificado a "arrastrar".

---

## B. Comprobado y correcto (sin cambios)

Todo esto se verifico linea por linea y **coincide** con lo que decia la guia:

- **Limites de animacion:** `MAX_KEYFRAMES = 40`, `MAX_DURACION = 30.0`,
  `MAX_ANGULO = 180.0`, `MAX_DESPLAZAMIENTO = 2.5`, `nombre` 40 caracteres.
- **Keyframes:** minimo 2, `t` no negativo y estrictamente creciente.
- **Poses:** 3 o 6 valores; 4 o 5 dan error; `HumanoidRootPart` prohibido.
- **Listas cerradas:** rigs `R6`/`R15`; prioridades `core`/`idle`/
  `movimiento`/`accion` con tokens 0/1/2/3; easings `suave` (Linear/InOut),
  `lineal` (Linear/Out), `rebote` (Bounce/Out), `elastica` (Elastic/Out),
  `instantaneo` (Constant/Out).
- **Articulaciones:** R6 tiene 6 animables (`Torso`, `Head`, `Left Arm`,
  `Right Arm`, `Left Leg`, `Right Leg`, con el espacio en los nombres);
  R15 tiene 15. `Head` es el unico nombre comun.
- **Enrutado del pipeline:** el `.bat` v6.0 busca literalmente `"rig"` con
  `findstr` para decidir si es animacion o interfaz; `.rbxm` va a
  `leer_anim.py`; todo se registra en `ultimo_resultado.txt`.
- **Interfaz:** paleta cerrada de 8 colores; `resaltado` debe estar dentro de
  `titulo`; `nivel` entre 1 y `niveles`; `xp` entre 0 y `xpPorNivel - 1`;
  `xpPorNivel >= 1`; `gratis` y `premium` de 1 a 6; `nuevo` booleano;
  `bonus` texto; prohibidos `< > &` en todo texto.
- **Linter:** las 10 reglas (XML, REF, R1-CLASE, R2-PROP, R3-OFFSET,
  R4-ENUM, R5-COLOR, R6-RICHTEXT, R7-TEXTO, R8-DESBORDE, R9-ZINDEX,
  R10-CLIC), la lista de clases permitidas, los rangos de token de enum y el
  hecho de que solo los ERROR devuelven codigo de salida 1.
- **Cierre de bucle:** los cuatro modelos con `loop: true` que revise
  (`caminar_r6`, `caminar_vida_r6`, `correr_pro_r6`, `correr_flujo_r6`,
  `caminar_r15`) tienen el ultimo keyframe identico al primero.
- **Modelos sin bucle:** `salto_r6.json` y `saludar_r6.json` tienen
  `loop: false` y `prioridad: accion`, como decia la guia.

---

## C. Trampa detectada entre modulos

El linter **rechaza** clases que el modulo 05 recomienda en su Parte B:
`UIGridLayout`, `UIScale` y `UITextSizeConstraint` **no** estan en el
conjunto `CLASES` de `roblox_lint.py`.

No es una contradiccion, pero conviene saberlo:

- En **Luau escrito a mano** puedes usar esas clases sin problema. El linter
  no mira tu codigo.
- En un **`.rbxmx` generado** por el conversor, cualquier clase fuera de la
  lista es un ERROR de lint. Si algun dia hace falta, hay que anadirla al
  conjunto `CLASES`.

---

## D. Pendiente en la documentacion del repositorio

Dos errores de esta lista **vienen de los propios modulos** y siguen ahi.
Se corrigieron en `GUIA-COMPLETA.md`, pero conviene arreglarlos en origen:

| Archivo | Seccion | Que dice mal | Que deberia decir |
|---|---|---|---|
| `mecanicas/04-animacion.md` | A.1 | `easing` como campo de keyframe | Campo de raiz |
| `mecanicas/04-animacion.md` | A.5 regla 2 | En R6 la contrafase es un `z` positivo en una pierna y negativo en la otra | En R6 la contrafase es el **mismo** valor en las dos; signos opuestos dan una pose simetrica |
| `mecanicas/04-animacion.md` | A.1 | `loop` y `prioridad` obligatorios | Opcionales, con defaults `true` y `accion` |
| `mecanicas/05-gui.md` | A.2 | `niveles` como lista | Numero entero de 2 a 20 |
| `mecanicas/09-errores-y-checklist.md` | C.4 | R6 tiene "5 animables" | 6 animables |

El resto de `mecanicas/09-errores-y-checklist.md` se verifico numero por
numero (incluida la tabla D.7 de limites por cantidad de premios) y es
exacto.
