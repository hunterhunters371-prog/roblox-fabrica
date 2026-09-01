# Instrucciones para IAs

Este repositorio produce dos cosas para Roblox: **interfaces (GUI)** y
**animaciones de personaje**.

Regla base: tu unica salida es un **JSON**. Nunca escribas XML de
Roblox, ni `.rbxmx`, ni codigo Lua, salvo que te lo pidan aparte. Un
conversor traduce tu JSON y lo valida.

---

## Routing

| Te piden | Lee |
|---|---|
| Interfaz, menu, HUD, pase de batalla, tienda, popup | `prompts/PROMPT-1-DISENO.md` |
| Animacion de personaje (caminar, correr, baile, saludo, idle) | `prompts/PROMPT-2-ANIMACION.md` |
| Copiar el estilo de una animacion existente | `referencias/*.txt` + regla 12 del PROMPT 2 |

---

## Reglas que no se negocian

1. Devuelve **solo** el bloque JSON. Sin explicaciones alrededor, sin
   texto antes ni despues.
2. Respeta los limites del validador. Cada prompt los lista.
3. **R6 y R15 tienen articulaciones y ejes distintos.** No los mezcles.
   Si pones nombres de R15 en un rig R6, la animacion se inserta pero
   solo se movera la cabeza, porque `Head` es el unico nombre que
   comparten. La tabla de ejes esta en el PROMPT 2.
4. Si el usuario te pega errores del validador, corrige y devuelve el
   JSON **completo** otra vez, no un fragmento.
5. Si una animacion hace loop, la ultima pose debe coincidir con la
   primera.

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
