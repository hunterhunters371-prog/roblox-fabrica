# Como hacer que otras IAs generen el pase sin errores

La idea clave: **la IA no escribe el `.rbxmx`.** Escribir XML de Roblox a mano
es donde se equivocan siempre. La IA escribe un JSON pequeno, y el conversor
lo vuelve `.rbxmx` con las posiciones ya calculadas.

## El flujo

```
  1. Le pegas el prompt de abajo a DeepSeek / Qwen / ChatGPT / Gemini
  2. Te devuelve un JSON  ->  lo guardas como  pase.json
  3. python spec_a_rbxmx.py pase.json
        si hay errores -> te los lista -> se los pegas a la IA -> vuelve al 2
        si esta bien    -> genera pase.rbxmx
  4. python roblox_lint.py pase.rbxmx        (debe decir ERRORES 0)
  5. Studio -> clic derecho en StarterGui -> Insert from File...
```

Lo importante del paso 3: **la IA no puede cometer los errores tipicos**,
porque ya no toca las partes donde se cometen.

| Error que cometian | Por que ya no puede pasar |
|---|---|
| decimal en `UDim.Offset` | la IA no escribe posiciones, las calcula el conversor |
| doble escapado de RichText | la IA no escribe etiquetas, el conversor las pone |
| colores fuera de paleta | solo puede elegir entre 8 nombres |
| texto que se sale de la caja | el conversor lo mide y lo rechaza |
| clase o propiedad inventada | la IA no elige clases |
| elementos solapados | las posiciones son calculadas, no escritas |

---

## EL PROMPT (copia desde aqui)

```text
Necesito que escribas UNICAMENTE un archivo JSON. No escribas codigo Lua, ni
XML, ni .rbxmx, ni HTML, ni explicaciones. Solo el bloque JSON.

Es para el pase de batalla de un juego de Roblox llamado
"LAST DELIVERY: 60 SECONDS": el jugador es un repartidor que tiene 60
segundos para entregar un paquete. Los premios son skins de paquete que
cambian como se entrega, y cada una da un multiplicador de pago.

Copia esta estructura exacta y cambia solo los valores:

{
  "temporada": "TEMPORADA 1 - REPARTIDOR",
  "titulo": "PASE DE BATALLA",
  "resaltado": "BATALLA",
  "subtitulo": "Abre paquetes y consigue skins.",
  "tiempo": "12d 08:42",

  "niveles": 10,
  "nivel": 7,
  "xp": 2400,
  "xpPorNivel": 3000,
  "xpPorPremio": 100,
  "xpPorPremioPremium": 150,

  "textoAbrirTodos": "Abrir todos",
  "textoPremium": "Mejorar - 400 Robux",

  "gratis": [
    {
      "etiqueta": "FRAGIL",
      "color": "azul",
      "icono": "[emoji]",
      "titulo": "Skin Fragil",
      "desc": "Se rompe si te golpean",
      "bonus": "x1.5",
      "nuevo": false
    },
    {
      "etiqueta": "PESADO",
      "color": "naranja",
      "icono": "[emoji]",
      "titulo": "Skin Pesado",
      "desc": "Caminas lento pero pagan mas",
      "bonus": "x1.7",
      "nuevo": true
    }
  ],

  "premium": [
    {
      "etiqueta": "VALIOSO",
      "color": "dorado",
      "icono": "[emoji]",
      "titulo": "Skin Valioso",
      "desc": "Todos ven donde estas",
      "bonus": "x3.0",
      "nuevo": false
    }
  ]
}

Pon 5 premios en "gratis" y 5 en "premium". Sustituye [emoji] por un emoji
real que encaje con el premio.

REGLAS. Si rompes una, el archivo se rechaza y tendras que corregirlo:

1. "color" solo puede ser uno de estos ocho nombres, en minusculas:
   azul, cian, dorado, morado, naranja, rojo, rosa, verde
   No inventes colores ni uses codigos hex ni RGB.

2. Prohibidos los caracteres < > & en CUALQUIER texto. Nada de etiquetas
   HTML ni de <font color=...>. Los colores del texto los pone el programa.

3. "resaltado" tiene que ser una palabra que aparezca literalmente dentro
   de "titulo".

4. "niveles" entre 2 y 20. "nivel" entre 1 y "niveles".

5. "xp" tiene que ser menor que "xpPorNivel".

6. "gratis" y "premium" llevan entre 1 y 6 premios cada una.

7. Limites de caracteres con 5 premios por pista:
      etiqueta   maximo 10
      titulo     maximo 22
      desc       maximo 58
      bonus      maximo 8
   Cuenta los caracteres antes de entregar.

8. "icono" es un solo emoji.

9. "nuevo" es true o false sin comillas. Marca solo 2 o 3 en total.

10. Los premios van de menos a mas valiosos: el nivel 1 es el mas humilde
    y el ultimo es el mejor del pase. Los multiplicadores suben en ese
    mismo orden.

Entrega: solo el bloque JSON, nada mas.
```

## Si el conversor devuelve errores

No los arregles tu. Copia la lista tal cual y pegasela a la IA con esta
linea delante:

```text
Corrige el JSON. El validador devolvio estos errores:

[pega aqui la lista completa]

Devuelve el JSON completo ya corregido, sin explicaciones.
```

Los errores estan escritos para que la IA los entienda sola: dicen la ruta
exacta (`raiz.gratis[2].titulo`), el problema, y cuando aplica, la lista de
valores validos.

## Reparto de IAs

| IA | Para que |
|---|---|
| DeepSeek, Qwen | escribir el JSON (solo texto, es lo que mejor hacen) |
| Gemini | revisar capturas de Studio, porque ve imagenes |
| ChatGPT, Meta | Figma, si vuelves a la parte de diseno |
| Notion AI | el conversor, el linter y la logica en Luau |

## Comprobacion rapida antes de importar

```
python spec_a_rbxmx.py pase.json     ->  OK  el JSON es valido
python roblox_lint.py pase.rbxmx     ->  ERRORES  0
```

Si las dos lineas salen limpias, el archivo abre bien en Studio. El linter
revisa 10 reglas del motor: clases, propiedades, offsets enteros, tokens de
enum, rango de colores, RichText, textos que no caben, hijos desbordados,
ZIndex y Frames con nombre de boton.
