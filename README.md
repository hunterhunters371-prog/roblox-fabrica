# Fabrica Roblox

Sistema para que cualquier IA genere **interfaces (GUI)**, **animaciones de
personaje** y **mecanicas de juego** para Roblox, en un formato que se valida y
se convierte solo.

Proyecto: *LAST DELIVERY: 60 SECONDS*

---

## Catalogo de mecanicas

Mas de 170 mecanicas de Roblox documentadas, cada una con su codigo Luau listo
para pegar, sus errores tipicos y su lista de comprobacion.

**Empieza aqui: [mecanicas/00-INDICE.md](mecanicas/00-INDICE.md)**

| Modulo | Tema |
|---|---|
| [01](mecanicas/01-fundamentos.md) | Fundamentos: servicios, scripts, eventos, limpieza |
| [02](mecanicas/02-movimiento.md) | Movimiento y camara |
| [03](mecanicas/03-combate.md) | Combate y dano |
| [04](mecanicas/04-animacion.md) | Animacion: el formato JSON y como reproducirla |
| [05](mecanicas/05-gui.md) | Interfaz: el formato JSON y como construirla |
| [06](mecanicas/06-datos-red.md) | Datos, DataStore y remotes |
| [07](mecanicas/07-fisica-modelos.md) | Fisica, CFrame y modelos |
| [08](mecanicas/08-sistemas.md) | Sistemas: economia, inventario, rondas, NPC |
| [09](mecanicas/09-errores-y-checklist.md) | Catalogo de errores y checklists |

El modulo 09 contiene los limites exactos de los validadores, sacados leyendo
el codigo de `herramientas/`, y 60 errores con su causa real y su solucion.

---

## Como funciona

1. Le pides a una IA que lea el prompt que corresponde:
   - Planificar el juego: `prompts/PROMPT-1-DISENO.md`
   - Animaciones: `prompts/PROMPT-2-ANIMACION.md`
   - Mecanicas en Luau: `prompts/PROMPT-3-MECANICAS.md`
2. Para animaciones e interfaces, la IA devuelve un **JSON**.
3. Guardas el JSON y lo arrastras sobre `herramientas/revisar_pase.bat`.
4. El .bat valida, convierte a `.rbxmx` y te deja una vista previa:
   **PNG** para interfaces, **GIF** para animaciones.
5. En Studio insertas el `.rbxmx`. Listo.

La IA nunca escribe XML de Roblox. Solo escribe JSON. Todo lo demas lo
hace el conversor, y por eso no se rompe.

**Las mecanicas son la excepcion:** ahi la IA si escribe Luau y no hay
validador que la corrija. Por eso `PROMPT-3-MECANICAS.md` es mucho mas
estricto, y por eso conviene buscar antes en el catalogo de `mecanicas/`.

---

## Pedirselo a una IA con acceso a internet

Pega esto:

> Lee este archivo y sigue sus instrucciones al pie de la letra:
> https://raw.githubusercontent.com/hunterhunters371-prog/roblox-fabrica/main/prompts/PROMPT-2-ANIMACION.md
>
> Quiero una animacion de correr para rig R6, estilo exagerado.

Para interfaces, cambia el enlace por `PROMPT-1-DISENO.md`.
Para mecanicas, por `PROMPT-3-MECANICAS.md`.

Si la IA no tiene acceso a internet, abres el archivo y le pegas el
texto completo. Funciona igual.

---

## Requisitos

- Python 3 instalado y en el PATH
- Librerias: `pip install pillow lz4`
  - `pillow` para las vistas previas PNG y GIF
  - `lz4` para poder **medir** animaciones `.rbxm` de la toolbox

---

## Estructura

```
herramientas/     los .py y el revisar_pase.bat
prompts/          los textos que le das a la IA
mecanicas/        catalogo de mecanicas (10 archivos)
animaciones/      animaciones que ya funcionan (.json editable)
interfaces/       interfaces que ya funcionan (.json editable)
referencias/      medidas reales de animaciones analizadas
GUIA-COMPLETA.md  resumen de todo el repositorio
VERIFICACION.md   comprobaciones del pipeline
```

---

## Los limites que mas se olvidan

Estan todos en `mecanicas/09-errores-y-checklist.md`, pero estos cuatro son los
que mas veces rompen un JSON:

| Cosa | Limite real |
|---|---|
| Keyframes de una animacion | Entre 2 y 40 |
| Duracion de una animacion | Maximo 30 segundos |
| Angulo por eje | Maximo mas o menos 180 grados |
| Premios por pista del pase | Entre 1 y 6 |

Y el limite de texto de las tarjetas del pase **depende de cuantos premios
pongas**: con 6 premios cada tarjeta es estrecha y el titulo solo admite 16
caracteres. La tabla completa esta en el modulo 09, Parte D.

---

## Medir una animacion que te guste

Esto sirve para copiar el estilo de cualquier animacion de la toolbox.

1. En Studio, clic derecho en el modelo que tiene la animacion ->
   **Save to File**. Te da un `.rbxm`
2. Arrastra ese `.rbxm` sobre `revisar_pase.bat`
3. Se abre un `.txt` con los angulos y desplazamientos reales de cada
   articulacion, keyframe por keyframe
4. Le pegas ese texto a la IA: *"replica este estilo en una animacion
   de [lo que quieras]"*

En `referencias/` ya hay dos medidas hechas, por si quieres ver como se
ven los datos antes de probar.

---

## Rigs

**R6** (6 articulaciones): Torso, Head, Left Arm, Right Arm, Left Leg,
Right Leg. No tiene rodillas, codos ni pies.

**R15** (15 animables): agrega UpperTorso, LowerTorso, brazos y piernas en dos
tramos, manos y **pies**.

Los ejes **no** son iguales en los dos rigs. La tabla esta en el PROMPT 2 y en
`mecanicas/04-animacion.md`. Equivocarse ahi es el error mas comun: la
animacion se inserta pero **solo se mueve la cabeza**, porque `Head` es la
unica articulacion que existe con el mismo nombre en los dos rigs.
