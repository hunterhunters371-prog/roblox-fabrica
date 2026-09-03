# Catalogo de mecanicas de Roblox

Guia practica de mecanicas de juego para Roblox Studio, escrita en Luau y
pensada para el proyecto **LAST DELIVERY: 60 SECONDS**.

Diez modulos, mas de 180 mecanicas, cada una con su codigo listo para pegar,
sus errores tipicos y su lista de comprobacion.

## Como se usa este catalogo

1. Busca lo que necesitas en la **tabla de busqueda rapida** de mas abajo.
2. Abre el modulo y ve a la ficha. Cada ficha te dice **donde va el script**.
3. Pega el codigo, cambia los nombres a los de tu juego.
4. Recorre la casilla de verificacion de la ficha.
5. Si algo falla, ve a `09-errores-y-checklist.md`.

Si lo que quieres no esta en el catalogo, usa `prompts/PROMPT-3-MECANICAS.md`
para pedirselo a otra IA con un formato que evita los fallos habituales.

---

## Los diez modulos

| Modulo | Tema | Fichas | De que trata |
|---|---|---|---|
| [01](01-fundamentos.md) | Fundamentos | 18 | Lo que hay que saber antes de escribir nada |
| [02](02-movimiento.md) | Movimiento y camara | 23 | Correr, saltar, escalar, vehiculos, camara |
| [03](03-combate.md) | Combate y dano | 22 | Golpear, disparar, curar, morir |
| [04](04-animacion.md) | Animacion | 9 + 18 | El formato JSON del repositorio y como reproducir animaciones |
| [05](05-gui.md) | Interfaz | 9 + 23 | El formato JSON del repositorio y como construir GUI |
| [06](06-datos-red.md) | Datos y red | 23 | Guardar partidas, remotes, validacion, compras |
| [07](07-fisica-modelos.md) | Fisica y modelos | 24 | CFrame, soldaduras, restricciones, puertas, terreno |
| [08](08-sistemas.md) | Sistemas de juego | 22 | Economia, inventario, rondas, NPC, misiones |
| [09](09-errores-y-checklist.md) | Errores y checklists | 60 errores | El catalogo de fallos con causas reales |
| [10](10-mejoras.md) | Mejoras del juego real | 12 | Las mecanicas que ya funcionan en el Place, con sus numeros |

Los modulos 04 y 05 tienen dos partes: una **Parte A** que documenta el formato
JSON de este repositorio con los limites exactos del validador, y una **Parte B**
con las mecanicas de Luau.

El modulo 10 no es como los demas. Los nueve primeros explican mecanicas de
Roblox en general; el 10 recoge las que **ya estan probadas** en el Place de
Studio del proyecto, con los valores que quedaron despues de jugarlas. Amplia
las fichas 02.07, 08.02 y 08.22 con el blindaje que hizo falta de verdad.

---

## Busqueda rapida

### Quiero que el jugador se mueva

| Necesito | Modulo | Ficha |
|---|---|---|
| Cambiar velocidad o altura de salto | 02 | 1 |
| Correr con barra de estamina | 02 | 3 |
| Dash o impulso rapido | 02 | 4 |
| Doble salto | 02 | 5 |
| Agacharse | 02 | 6 |
| Deslizarse | 02 | 7, y 10.6 |
| Correr por la pared | 02 | 8 |
| Agarrarse a un borde | 02 | 9 |
| Escaleras | 02 | 10 |
| Nadar | 02 | 11 |
| Detectar teclas | 02 | 12 |
| Botones para movil | 02 | 13 |
| Primera persona o shift-lock | 02 | 14 |
| Sacudir la camara | 02 | 15 |
| Coches y vehiculos | 02 | 16 |
| Teletransportar dentro del mapa | 02 | 17 |
| Donde nace el jugador | 02 | 18 |
| Ragdoll al morir | 02 | 19 |
| Dano por caida | 02 | 20 |
| Empujar al jugador | 02 | 21 |
| Plataformas moviles | 02 | 22, y 07 |
| Zonas que cambian la velocidad | 02 | 23 |
| Que llevar cosas encima pese | 10 | 10.7 |
| Camara que reacciona al estado | 10 | 10.11 |

### Quiero que haya combate

| Necesito | Modulo | Ficha |
|---|---|---|
| Hitbox de un golpe | 03 | 1 |
| Disparar un rayo | 03 | 2, y 07 |
| Hitbox con volumen | 03 | 3 |
| Tiempo de espera entre golpes | 03 | 4 |
| Quitar vida correctamente | 03 | 5 |
| Remote de ataque seguro | 03 | 6 |
| Proyectiles | 03 | 7 |
| Combos | 03 | 8, y 10.9 |
| Invulnerabilidad temporal | 03 | 9 |
| Aturdir | 03 | 10 |
| Empujar al golpear | 03 | 11 |
| Fuego amigo | 03 | 12 |
| Golpes criticos | 03 | 13 |
| Veneno o quemadura | 03 | 14 |
| Curarse | 03 | 15 |
| Escudos y armadura | 03 | 16 |
| Congelar el golpe un instante | 03 | 17 |
| Muerte, respawn y aviso de baja | 03 | 18 |
| Armas como Tool | 03 | 19 |
| Municion y recarga | 03 | 20 |
| Explosiones | 03 | 21 |
| Estados alterados | 03 | 22 |

### Quiero animaciones

| Necesito | Modulo | Ficha |
|---|---|---|
| Escribir el JSON de animacion del repositorio | 04 | Parte A |
| Los ejes de R6 y R15 | 04 | A.3 |
| Las articulaciones de cada rig | 04 | A.2, y 09 C.4 |
| Los limites exactos del validador | 09 | Parte C |
| Reproducir una animacion | 04 | 1 |
| Fundido de entrada y salida | 04 | 2 |
| Prioridades entre animaciones | 04 | 3 |
| Ajustar velocidad al caminar | 04 | 4, y 10.11 |
| Mezclar dos animaciones | 04 | 5 |
| Saltar a un momento concreto | 04 | 6 |
| Disparar algo a mitad de la animacion | 04 | 7 |
| Precargar para que no falle | 04 | 8 |
| Sustituir las animaciones por defecto | 04 | 9, y 10.11 |
| Animar una herramienta | 04 | 10 |
| Sujetar objetos en la mano | 04 | 11, y 07 |
| Animar sin Animation Editor | 04 | 12 |
| Que mire hacia un punto | 04 | 13 |
| Brazos en primera persona | 04 | 14 |
| Sonido sincronizado | 04 | 15 |
| Animar NPC | 04 | 17 |
| Mi animacion no se reproduce | 04 | tabla final, y 09 Parte H |

### Quiero interfaz

| Necesito | Modulo | Ficha |
|---|---|---|
| Escribir el JSON de interfaz del repositorio | 05 | Parte A |
| Los limites exactos de cada texto | 09 | Parte D |
| Escala frente a pixeles | 05 | 2, y 10 trampas |
| Centrar bien las cosas | 05 | 3 |
| Que se vea igual en movil | 05 | 4, 5 |
| Texto que se ajusta | 05 | 6 |
| Listas con barra de desplazamiento | 05 | 7 |
| Animar la interfaz | 05 | 8 |
| Botones que responden bien | 05 | 9 |
| Barra de vida | 05 | 10 |
| Enfriamiento circular | 05 | 11 |
| Avisos que aparecen y se van | 05 | 12 |
| Texto que se escribe solo | 05 | 13 |
| Ventana emergente | 05 | 14 |
| Pestanas | 05 | 15 |
| Arrastrar y soltar | 05 | 16 |
| Cuadricula de inventario | 05 | 17 |
| Navegar con mando | 05 | 18 |
| Ver un modelo 3D en la interfaz | 05 | 19 |
| Texto flotando sobre un objeto | 05 | 20 |
| Ocultar la interfaz de Roblox | 05 | 21 |
| Boton que llama al servidor | 05 | 22 |
| Mostrar monedas y nivel | 05 | 23 |
| Una barra que no vaya a saltos | 10 | 10.2 |
| Vinetas que no dejen franjas negras | 10 | trampas |
| Mi GUI no aparece | 05 | tabla final |

### Quiero guardar datos y comunicar cliente y servidor

| Necesito | Modulo | Ficha |
|---|---|---|
| Activar DataStore en Studio | 06 | 1 |
| Guardar y cargar una partida | 06 | 2 |
| Reintentar cuando falla | 06 | 3 |
| Cual usar: SetAsync, UpdateAsync | 06 | 4 |
| Cuotas y limites reales | 06 | 5 |
| Cambiar el formato sin perder datos | 06 | 6 |
| Evitar duplicados entre servidores | 06 | 7 |
| Guardar al salir el jugador | 06 | 8, y 10.12 |
| Guardado automatico | 06 | 9, y 10.12 |
| Un gestor de datos completo | 06 | 10 |
| Mostrar puntos en la lista de jugadores | 06 | 11, y 10.5 |
| Ranking global | 06 | 12, y 08 |
| Datos temporales entre servidores | 06 | 13 |
| Mandar algo del cliente al servidor | 06 | 14 |
| Pedir algo y esperar respuesta | 06 | 15 |
| Comunicar dos scripts del mismo lado | 06 | 17 |
| Validar lo que manda el cliente | 06 | 18, y 10.10 |
| Compartir un valor con todos | 06 | 19 |
| Hablar entre servidores | 06 | 20 |
| Llamar a una web externa | 06 | 21 |
| Mover jugadores a otro lugar | 06 | 22 |
| Vender productos y pases | 06 | 23 |
| Replicar un valor que cambia cada frame | 10 | 10.2 |

### Quiero construir el mundo

| Necesito | Modulo | Ficha |
|---|---|---|
| Propiedades de las partes | 07 | 1 |
| Entender CFrame de una vez | 07 | 2 |
| Mover un modelo entero | 07 | 3 |
| Unir partes entre si | 07 | 5 |
| Que un objeto siga la mano | 07 | 6, y 04 |
| Restricciones de movimiento | 07 | 7 |
| Que dos cosas no choquen | 07 | 8 |
| Detectar que algo toca algo | 07 | 9 |
| Buscar lo que hay en una zona | 07 | 10 |
| Lanzar un rayo | 07 | 11, y 03 |
| Medir un modelo | 07 | 12 |
| Cambiar el tamano de un modelo | 07 | 13 |
| Que la fisica vaya suave | 07 | 14 |
| Crear objetos desde el servidor | 07 | 15 |
| Borrar cosas automaticamente | 07 | 16 |
| Puertas | 07 | 17, y 08 |
| Plataformas y ascensores | 07 | 18, 19 |
| Cintas transportadoras | 07 | 20 |
| Cosas que se rompen | 07 | 21 |
| Terreno por codigo | 07 | 22 |
| Mapas muy grandes | 07 | 23 |
| Configurar cada objeto por atributos | 10 | 10.4 |
| Mi modelo se desarma | 07 | 24 |

### Quiero sistemas completos

| Necesito | Modulo | Ficha |
|---|---|---|
| Organizar todos mis sistemas | 08 | 1 |
| Monedas | 08 | 2, y 10.5 |
| Inventario | 08 | 3 |
| Equipar objetos | 08 | 4 |
| Tienda | 08 | 5, y 10.12 |
| Monedas por el mapa | 08 | 6 |
| Misiones | 08 | 7 |
| Logros e insignias | 08 | 8 |
| Premio diario | 08 | 9 |
| Pase de batalla funcional | 08 | 10 |
| Partidas por rondas | 08 | 11, y 10.8 |
| Cuenta atras que no se desincroniza | 08 | 12, y 10.3 |
| Equipos | 08 | 13 |
| El bucle de entregas del juego | 08 | 14, y 10.9 |
| Puntos de control y llaves | 08 | 15 |
| NPC que caminan por el mapa | 08 | 16 |
| NPC con comportamiento | 08 | 17 |
| Oleadas de enemigos | 08 | 18 |
| Cartel con el top | 08 | 19 |
| Comandos en el chat | 08 | 20 |
| Comandos de administrador | 08 | 21 |
| Anticheat | 08 | 22, y 10.10 |
| Power-ups guiados por tabla | 10 | 10.12 |

### Quiero las mecanicas que ya funcionan en el juego

Estas doce salen del Place de Studio, no de la teoria. Cada una trae los valores
reales con los que se juega hoy.

| Necesito | Ficha |
|---|---|
| Un medidor que sube al pulsar y baja solo | 10.1 |
| Replicar un valor que cambia cada frame sin inundar la red | 10.2 |
| Cerrar un temporizador sin que se dispare sobre la partida siguiente | 10.3 |
| Configurar cada objeto del mapa sin tocar el script | 10.4 |
| Que nadie pueda duplicar monedas | 10.5 |
| Una deslizada que rompa el techo de velocidad | 10.6 |
| Que llevar cosas encima pese de verdad | 10.7 |
| Que la dificultad suba dentro de la misma ronda | 10.8 |
| Pedidos urgentes y combo con ventana | 10.9 |
| Anticheat que no castigue al que tiene lag | 10.10 |
| Camara y animacion que reaccionan al estado | 10.11 |
| Power-ups sin escribir un `if` por cada uno | 10.12 |
| Todos los numeros del equilibrio en una tabla | 10, Resumen de constantes |

### Necesito arreglar algo

| Necesito | Modulo |
|---|---|
| El flujo completo de la herramienta | 09, Parte A |
| Que instalar para que funcione | 09, Parte B |
| Limites del validador de animacion | 09, Parte C |
| Limites del validador de interfaz | 09, Parte D |
| Las reglas R1 a R10 del lint | 09, Parte E |
| Errores del conversor | 09, Parte F |
| Errores de Luau en Studio | 09, Parte G |
| Errores de rig y animacion | 09, Parte H |
| Listas de comprobacion | 09, Parte I |
| Como reportar un fallo | 09, Parte J |

---

## Las diez reglas del catalogo

Si solo te llevas diez cosas de aqui, que sean estas.

| # | Regla | Donde se explica |
|---|---|---|
| 1 | El servidor decide, el cliente pide y dibuja | 01, 06, 08 |
| 2 | Todo remote valida frecuencia, tipo y rango | 06, ficha 18, y 10.10 |
| 3 | `WaitForChild` siempre con tiempo maximo | 01, ficha 6 |
| 4 | Toda llamada que puede fallar va en `pcall` | 01, ficha 9 |
| 5 | Las conexiones se desconectan al terminar | 01, ficha 13 |
| 6 | Los angulos de CFrame pasan por `math.rad` | 07, ficha 2 |
| 7 | Las restricciones no funcionan sobre partes ancladas | 07, ficha 7 |
| 8 | R6 y R15 no comparten articulaciones salvo `Head` | 04, 09 |
| 9 | Los temporizadores guardan el instante de fin, no el contador | 08, ficha 12, y 10.3 |
| 10 | Nunca uses `BodyVelocity`, `BodyPosition` ni `SetPrimaryPartCFrame` | 01, 07 |

Dos reglas mas que salieron del juego real y que estan en el modulo 10:

| # | Regla | Donde se explica |
|---|---|---|
| 11 | Un valor que cambia cada frame se publica con cuentagotas | 10.2 |
| 12 | Comprobar y descontar van juntos, sin esperas en medio | 10.5 |

---

## APIs obsoletas y su sustituto

La causa mas comun de codigo que "funciona pero da avisos" o que directamente
no funciona: una IA que aprendio con tutoriales de hace anos.

| No uses | Usa |
|---|---|
| `BodyVelocity` | `LinearVelocity` |
| `BodyPosition` | `AlignPosition` |
| `BodyGyro` | `AlignOrientation` |
| `BodyAngularVelocity` | `AngularVelocity` |
| `Model:SetPrimaryPartCFrame()` | `Model:PivotTo()` |
| `Model:GetPrimaryPartCFrame()` | `Model:GetPivot()` |
| `workspace:FindPartOnRay()` | `workspace:Raycast()` |
| `part.Velocity` | `part.AssemblyLinearVelocity` |
| `part.RotVelocity` | `part.AssemblyAngularVelocity` |
| `wait()` | `task.wait()` |
| `spawn()` | `task.spawn()` |
| `delay()` | `task.delay()` |
| `Player.Chatted` | `TextChatService` con `TextChatCommand` |
| `TeleportService:TeleportPartyAsync()` | `TeleportService:TeleportAsync()` |
| `Humanoid:LoadAnimation()` | `Animator:LoadAnimation()` |
| `workspace:FindPartsInRegion3()` | `workspace:GetPartBoundsInBox()` |

---

## Donde va cada script

La mitad de los errores de Roblox son un script correcto en el sitio
equivocado. Esta tabla resuelve la duda.

| Contenedor | Que corre ahi | Para que |
|---|---|---|
| `ServerScriptService` | Script | Toda la logica del juego |
| `ServerStorage` | Nada, es almacen | Plantillas que el cliente no debe ver |
| `ReplicatedStorage` | ModuleScript compartido | Remotes, modulos comunes, plantillas visibles |
| `StarterPlayerScripts` | LocalScript | Entrada de teclado, camara, cliente general |
| `StarterCharacterScripts` | LocalScript | Lo que depende del personaje |
| `StarterGui` | LocalScript | Interfaz |
| `ReplicatedFirst` | LocalScript | Pantalla de carga, corre antes que nada |
| `Workspace` | Script | Objetos concretos del mundo |

Un LocalScript en `ServerScriptService` o en `Workspace` **no se ejecuta**. Es
el fallo silencioso mas comun del motor.

Y un aviso que cuesta caro: un ModuleScript de constantes en `ReplicatedStorage`
requerido por los dos lados da **dos instancias distintas**, no estado
compartido. Esta explicado en el modulo 10, seccion de trampas transversales.

---

## Como se conecta con el resto del repositorio

```text
   prompts/PROMPT-1-DISENO.md     -> planificar el juego
   prompts/PROMPT-2-ANIMACION.md  -> pedir animaciones en JSON
   prompts/PROMPT-3-MECANICAS.md  -> pedir mecanicas en Luau
                |
                v
   mecanicas/  (este catalogo)    -> como funciona cada cosa
                |
                v
   herramientas/revisar_pase.bat  -> validar y convertir el JSON
                |
                v
   Roblox Studio                  -> insertar y probar
                |
                +--> mecanicas/10-mejoras.md         <- lo que sobrevivio a la partida
                |
                v
   mecanicas/09-errores-y-checklist.md  -> cuando algo falla
```

El modulo 10 cierra el circulo: lo que se prueba en Studio y funciona vuelve al
catalogo con sus numeros reales, para no volver a ajustarlo a ciegas.

Diferencia importante entre los prompts:

| Prompt | La IA devuelve | Hay validador |
|---|---|---|
| PROMPT-1 | Un plan en texto | No hace falta |
| PROMPT-2 | JSON de animacion | Si, `spec_anim.py` |
| PROMPT-3 | Codigo Luau | **No.** Por eso el formato es tan estricto |

---

## Convenciones de escritura

Todo el repositorio sigue las mismas reglas, y este catalogo tambien:

- Espanol sin acentos ni letra ene con virgulilla, para que ningun archivo se
  rompa al abrirlo con una codificacion distinta.
- Sin emojis en la documentacion. Los emojis solo aparecen dentro del campo
  `icono` de los JSON de interfaz.
- Cada ficha tiene siempre las mismas siete secciones: que es, para que sirve,
  API implicada, donde va, codigo, errores frecuentes y checklist.
- El codigo lleva comentarios donde hay una trampa, no donde es obvio.
- Indentacion de cuatro espacios en todo el Luau.

---

## Estado del catalogo

| Archivo | Tamano |
|---|---|
| `01-fundamentos.md` | 30 KB |
| `02-movimiento.md` | 43 KB |
| `03-combate.md` | 44 KB |
| `04-animacion.md` | 41 KB |
| `05-gui.md` | 61 KB |
| `06-datos-red.md` | 50 KB |
| `07-fisica-modelos.md` | 51 KB |
| `08-sistemas.md` | 70 KB |
| `09-errores-y-checklist.md` | 29 KB |
| `10-mejoras.md` | 42 KB |

Todos los numeros de los validadores que aparecen en el modulo 09 estan sacados
leyendo el codigo de `herramientas/`, no de memoria.

Todos los valores de equilibrio que aparecen en el modulo 10 estan sacados
leyendo los scripts del Place en Studio, no de memoria.
