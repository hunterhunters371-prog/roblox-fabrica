# Fabrica Roblox

Sistema para que cualquier IA genere **interfaces (GUI)** y **animaciones de
personaje** para Roblox, en un formato que se valida y se convierte solo.

Proyecto: *LAST DELIVERY: 60 SECONDS*

---

## Como funciona

1. Le pides a una IA que lea el prompt que corresponde:
   - Interfaces: `prompts/PROMPT-1-DISENO.md`
   - Animaciones: `prompts/PROMPT-2-ANIMACION.md`
2. La IA devuelve un **JSON**.
3. Guardas el JSON y lo arrastras sobre `herramientas/revisar_pase.bat`.
4. El .bat valida, convierte a `.rbxmx` y te deja una vista previa:
   **PNG** para interfaces, **GIF** para animaciones.
5. En Studio insertas el `.rbxmx`. Listo.

La IA nunca escribe XML de Roblox. Solo escribe JSON. Todo lo demas lo
hace el conversor, y por eso no se rompe.

---

## Pedirselo a una IA con acceso a internet

Pega esto:

> Lee este archivo y sigue sus instrucciones al pie de la letra:
> https://raw.githubusercontent.com/hunterhunters371-prog/roblox-fabrica/main/prompts/PROMPT-2-ANIMACION.md
>
> Quiero una animacion de correr para rig R6, estilo exagerado.

Para interfaces, cambia el enlace por `PROMPT-1-DISENO.md`.

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
herramientas/   los .py y el revisar_pase.bat
prompts/        los textos que le das a la IA
animaciones/    animaciones que ya funcionan (.json editable)
interfaces/     interfaces que ya funcionan (.json editable)
referencias/    medidas reales de animaciones analizadas
```

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

**R6** (6 articulaciones): Torso, Head, Left/Right Arm, Left/Right Leg.
No tiene rodillas, codos ni pies.

**R15** (15+): agrega UpperTorso, LowerTorso, brazos y piernas en dos
tramos, manos y **pies**.

Los ejes **no** son iguales en los dos rigs. La tabla esta en el
PROMPT 2 y equivocarse ahi es el error mas comun: la animacion se
inserta pero solo se mueve la cabeza.
