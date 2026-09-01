# Como hacer que otras IAs generen animaciones sin errores

La idea clave: **la IA no escribe el `.rbxmx` ni Luau.** Escribir el XML de
un KeyframeSequence a mano es donde se equivocan siempre. La IA escribe un
JSON pequeno (tiempos y angulos por articulacion), y el conversor lo vuelve
`.rbxmx` con el arbol de poses completo y la jerarquia correcta.

## El flujo

```
  1. Le pegas el prompt de abajo a DeepSeek / Qwen / ChatGPT / Gemini
  2. Te devuelve un JSON  ->  lo guardas como  baile.json
  3. python spec_anim.py baile.json
        si hay errores -> te los lista -> se los pegas a la IA -> vuelve al 2
        si esta bien    -> genera baile.rbxmx
  3b. python ver_anim.py baile.json   ->  baile.gif (vista previa del
        movimiento sin abrir Studio: maniqui de bloques aproximado)
     (el revisar_pase.bat hace los dos pasos solo: detecta la clave "rig")
  4. Studio: inserta un Dummy (Avatar -> Rig Builder -> R15 o R6)
        -> abre Animation Editor sobre el Dummy
        -> arrastra el .rbxmx a la carpeta AnimSaves del Dummy
           (o clic derecho en AnimSaves -> Insert from File...)
  5. En el Animation Editor la ves y la pruebas. Para usarla en el juego:
        Menu ... -> Export to Roblox -> te da el Animation ID
```

Lo importante del paso 3: **la IA no puede cometer los errores tipicos**,
porque ya no toca las partes donde se cometen.

| Error que cometian | Por que ya no puede pasar |
|---|---|
| articulacion inventada o mal escrita | solo puede elegir de la lista del rig |
| XML de KeyframeSequence escrito a mano | la IA no escribe XML |
| tiempos desordenados | el conversor exige orden creciente |
| angulos absurdos (400 grados) | acotados a +/-180 |
| easing o prioridad inventados | listas cerradas |
| jerarquia de poses rota | el conversor genera el arbol entero |
| animacion que no mueve nada | el conversor lo detecta y lo rechaza |

El movimiento entre keyframes lo interpola el motor de Roblox: la IA solo
define las poses clave, nunca los frames intermedios.

---

## EL PROMPT (copia desde aqui)

```text
Necesito que escribas UNICAMENTE un archivo JSON. No escribas codigo Lua, ni
XML, ni .rbxmx, ni explicaciones. Solo el bloque JSON.

Es para una animacion de personaje de Roblox (por ejemplo: un baile, un idle
respirando, o saludar con la mano).

Copia esta estructura exacta y cambia solo los valores:

{
  "rig": "R15",
  "nombre": "BaileVictoria",
  "loop": true,
  "prioridad": "accion",
  "easing": "suave",
  "keyframes": [
    { "t": 0.0,  "poses": { "RightUpperArm": [0, 0, 70],  "LeftUpperArm": [0, 0, -70],  "Head": [0, 0, 0] } },
    { "t": 0.25, "poses": { "RightUpperArm": [0, 0, 110], "LeftUpperArm": [0, 0, -40],  "Head": [0, 12, 0] } },
    { "t": 0.5,  "poses": { "RightUpperArm": [0, 0, 40],  "LeftUpperArm": [0, 0, -110], "Head": [0, -12, 0] } },
    { "t": 0.75, "poses": { "RightUpperArm": [0, 0, 110], "LeftUpperArm": [0, 0, -40],  "Head": [0, 12, 0] } },
    { "t": 1.0,  "poses": { "RightUpperArm": [0, 0, 70],  "LeftUpperArm": [0, 0, -70],  "Head": [0, 0, 0] } }
  ]
}

Que significa cada cosa:
- "keyframes": la lista de momentos. Cada uno tiene "t" (segundo exacto) y
  "poses" (que articulaciones se mueven y cuanto).
- Cada pose es [x, y, z] = rotacion en grados sobre cada eje.
  [0, 0, 0] = la articulacion en reposo. No hace falta poner las que no
  se mueven.
- El motor interpola entre keyframes: con 4-6 keyframes por segundo el
  movimiento ya se ve fluido.

REGLAS. Si rompes una, el archivo se rechaza y tendras que corregirlo:

1. "rig" solo puede ser "R15" (avatares modernos, 15 partes) o "R6"
   (avatares clasicos, 6 partes).

2. Los nombres de articulaciones deben ser EXACTAMENTE de esta lista,
   en ingles y con estas mayusculas:
   R15: LowerTorso, UpperTorso, Head,
        LeftUpperArm, LeftLowerArm, LeftHand,
        RightUpperArm, RightLowerArm, RightHand,
        LeftUpperLeg, LeftLowerLeg, LeftFoot,
        RightUpperLeg, RightLowerLeg, RightFoot
   R6:  Torso, Head, Left Arm, Right Arm, Left Leg, Right Leg
   Nunca animes "HumanoidRootPart": es la raiz y va quieta.

3. Cada pose es una lista de 3 numeros [x, y, z] en grados, entre -180
   y 180. OJO: los ejes CAMBIAN segun el rig, porque las articulaciones
   de R6 vienen rotadas 90 grados de fabrica y las de R15 no:

   R15: el eje Z sube los brazos a los lados (Z POSITIVO sube el brazo
        DERECHO, Z NEGATIVO sube el IZQUIERDO); el eje X mueve brazos y
        piernas adelante y atras (X POSITIVO = adelante, ambos lados);
        en la cabeza, Y la gira como diciendo "no" y X como "si".

   R6:  el eje X sube los brazos a los lados y SIEMPRE con signo
        NEGATIVO (los dos brazos); el eje Z mueve brazos y piernas
        adelante y atras (Z POSITIVO = adelante el lado DERECHO,
        Z NEGATIVO = adelante el lado IZQUIERDO); el eje Y es el giro
        o torsion de cada extremidad.

   Si un giro sale al reves, cambia el signo.

4. "t" son segundos desde el inicio, en orden estrictamente creciente.
   El primer keyframe casi siempre en t = 0.

5. Entre 2 y 40 keyframes, y la animacion completa no puede pasar de
   30 segundos.

6. "easing" solo uno de: suave, lineal, rebote, elastica, instantaneo.

7. "prioridad" solo una de: accion, core, idle, movimiento.
   Para bailes y saludos usa "accion"; para un idle de reposo, "idle".

8. "loop" es true o false sin comillas. true para bailes e idles;
   false para saludos o gestos de una vez.

9. "nombre" sin los caracteres < > &, maximo 40 caracteres.

10. La animacion tiene que mover algo de verdad: si todas las poses son
    [0, 0, 0], el conversor la rechaza. Y si el loop es true, la ultima
    pose debe coincidir con la primera para que no haga un salto feo.

11. Opcional: una pose puede llevar 6 numeros [x, y, z, px, py, pz], donde
    px/py/pz es un DESPLAZAMIENTO en studs (maximo +/-2.5). Con valores
    chicos (0.05 a 0.3) sirve para el rebote vertical al caminar: ponlo
    en LowerTorso (R15) o Torso (R6) con py negativo cuando el cuerpo
    baja y positivo cuando sube. Si no lo necesitas, usa 3 numeros.

12. TECNICA DE FLUJO VISUAL (deformacion a proposito). Los desplazamientos
    grandes (0.8 a 1.5 studs) separan la extremidad del cuerpo. Se ve
    imposible pero da mucha sensacion de movimiento; es lo que usan
    muchas animaciones populares de la toolbox. Las reglas del truco,
    medidas de un asset real:

    - PIERNAS en CONTRA-FASE: el desplazamiento va al reves que el giro.
      Si la pierna gira adelante (z positivo), su px es NEGATIVO. Eso
      estira visualmente la zancada mas alla de lo que el rig permite.
      Acoplalos proporcionalmente, por ejemplo z = 50 con px = -1.2.
    - BRAZOS en FASE: el desplazamiento acompana al giro (z positivo con
      px positivo), mas chico que el de las piernas (0.3 a 0.5).
    - Las extremidades suben un poco (py entre 0.2 y 0.3) en el pico del
      paso, y los brazos bajan (py entre -0.1 y -0.2) para descolgarse.
    - El TORSO casi no se desplaza (menos de 0.3) pero lleva el rebote
      vertical y una inclinacion constante hacia adelante.
    - La RAIZ (HumanoidRootPart) nunca se toca: se queda en cero.

    Usa esta tecnica solo cuando pidan un estilo llamativo o exagerado.
    Para algo realista, quedate con desplazamientos menores a 0.3.

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

Los errores dicen la ruta exacta (`raiz.keyframes[1].poses.RightUpperArm`),
el problema, y cuando aplica, la lista de valores validos.

## Comprobacion rapida antes de abrir Studio

```
python spec_anim.py baile.json     ->  OK  el JSON es valido
python ver_anim.py baile.json      ->  baile.gif (vista previa)
```

El GIF usa un maniqui de bloques y una interpolacion aproximada: sirve
para revisar el movimiento y los signos de los ejes. La animacion final,
con el modelo real, se verifica en el Animation Editor de Studio.
El lint y el render PNG son solo para interfaces (GUI).

## Nota sobre alcance

Esto cubre animaciones SIMPLES de personaje (idle, baile, saludar, gestos):
rotaciones de articulaciones por keyframes. No cubre caminar con desplazamiento
real, IK, ni animacion de camara. Para eso esta el Animation Editor completo.
