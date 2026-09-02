# Instrucciones para IAs

Este repositorio produce tres cosas para Roblox: **interfaces (GUI)**,
**animaciones de personaje** y **mecanicas de juego**.

Regla base para interfaces y animaciones: tu unica salida es un **JSON**.
Nunca escribas XML de Roblox ni `.rbxmx`. Un conversor traduce tu JSON y lo
valida.

**Las mecanicas son la excepcion.** Ahi si escribes Luau, y no hay ningun
validador que te corrija. Por eso las reglas de `prompts/PROMPT-3-MECANICAS.md`
son obligatorias y mucho mas estrictas.

---

## Routing

| Te piden | Lee |
|---|---|
| Interfaz, menu, HUD, pase de batalla, tienda, popup | `prompts/PROMPT-1-DISENO.md` |
| Animacion de personaje (caminar, correr, baile, saludo, idle) | `prompts/PROMPT-2-ANIMACION.md` |
| Copiar el estilo de una animacion existente | `referencias/*.txt` + regla 12 del PROMPT 2 |
| Mecanica de juego, sistema, script en Luau | `mecanicas/00-INDICE.md` primero, y si no esta, `prompts/PROMPT-3-MECANICAS.md` |
| Un error del validador, del conversor o de Studio | `mecanicas/09-errores-y-checklist.md` |
| Los limites exactos de cualquier campo del JSON | `mecanicas/09-errores-y-checklist.md`, partes C y D |

Antes de escribir una mecanica desde cero, **busca en
`mecanicas/00-INDICE.md`**. Hay mas de 170 mecanicas ya resueltas, con codigo,
errores tipicos y checklist. Reutilizar una ficha del catalogo siempre es mejor
que improvisar.

---

## Reglas que no se negocian

1. Para JSON: devuelve **solo** el bloque JSON. Sin explicaciones alrededor,
   sin texto antes ni despues.
2. Respeta los limites del validador. Cada prompt los lista, y el modulo 09
   tiene los numeros exactos sacados del codigo.
3. **R6 y R15 tienen articulaciones y ejes distintos.** No los mezcles.
   Si pones nombres de R15 en un rig R6, la animacion se inserta pero
   solo se movera la cabeza, porque `Head` es el unico nombre que
   comparten. La tabla de ejes esta en el PROMPT 2.
4. Si el usuario te pega errores del validador, corrige y devuelve el
   JSON **completo** otra vez, no un fragmento.
5. Si una animacion hace loop, la ultima pose debe coincidir con la
   primera.
6. Para Luau: cada script empieza con dos lineas de cabecera indicando
   **TIPO** (Script, LocalScript o ModuleScript) y **RUTA** exacta en Studio.
   Sin eso, el usuario no sabe donde ponerlo y no funcionara.
7. Para Luau: el servidor decide, el cliente pide y dibuja. Todo lo que afecte
   a vida, dinero, objetos o progreso se valida en el servidor.

---

## Un JSON de interfaz nunca lleva la clave "rig"

`revisar_pase.bat` decide que conversor usar buscando literalmente el texto
`"rig"` dentro del archivo. Si aparece en un JSON de interfaz, aunque sea
dentro de un texto, el archivo se procesara como animacion y fallara.

---

## Como se disena una animacion decente

No inventes angulos sueltos. Primero define la **coreografia por
fases** y despues traduce cada fase a poses. Para una carrera en R6:

| Fase | Que pasa |
|---|---|
| Contacto | el pie delantero toca, pierna estirada hacia abajo |
| Amortiguacion | punto mas bajo del cuerpo, pierna de atras se pliega |
| Impulso | pierna de apoyo empuja hacia atras, cuerpo sube |
| Vuelo | ambos pies en el aire, punto mas alto |

Despues se repite espejado para el otro lado.

Dos cosas que casi siempre se olvidan:

- **Brazos contralaterales**: pierna derecha adelante va con brazo
  izquierdo adelante. Si van del mismo lado, se ve como un zombi.
- **R6 no tiene rodillas.** La rodilla se finge con el desplazamiento
  vertical de la pierna: sube cuando deberia doblarse, baja cuando
  deberia extenderse. Sin eso la carrera se ve tiesa.

---

## Ejemplos que ya funcionan

| Archivo | Que es |
|---|---|
| `animaciones/correr_pro_r6.json` | carrera disenada por fases, con rodilla fingida |
| `animaciones/caminar_vida_r6.json` | caminar realista con rebote |
| `animaciones/baile_r6.json` | baile |
| `animaciones/saludar_r6.json` | saludo |
| `interfaces/pase.json` | pase de batalla, 20 niveles |

Si dudas del formato, abre uno de estos y copia su estructura.

---

## Convenciones de escritura del repositorio

- Espanol **sin acentos** y sin la letra ene con virgulilla, en todos los
  archivos de documentacion y en los comentarios del codigo.
- **Sin emojis** en la documentacion. Los emojis solo van dentro del campo
  `icono` de los JSON de interfaz.
- Indentacion de cuatro espacios en todo el Luau.
- Comenta solo donde hay una trampa, no lo evidente.
