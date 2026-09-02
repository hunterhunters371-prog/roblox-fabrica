# Como hacer que otras IAs generen mecanicas de juego sin errores

Antes de usar este prompt: **mira primero en `mecanicas/00-INDICE.md`**. El
catalogo tiene mas de 170 mecanicas ya escritas, probadas y con su lista de
comprobacion. Si lo que necesitas ya esta ahi, no pidas nada a ninguna IA.

Este prompt es para lo que **no** esta en el catalogo.

## La diferencia con los otros dos prompts

| Prompt | La IA devuelve | Quien la corrige |
|---|---|---|
| PROMPT-1 | Un plan en texto | Tu, leyendolo |
| PROMPT-2 | JSON de animacion | `spec_anim.py`, que valida todo |
| PROMPT-3 | **Codigo Luau** | **Nadie** |

Esa ultima fila es la razon de ser de este documento.

Con las animaciones y las interfaces hay una red de seguridad: la IA escribe
JSON, y un programa comprueba cada campo antes de generar nada. Si la IA se
equivoca, el validador lo caza.

Con las mecanicas no hay red. La IA escribe Luau y ese Luau va directo a tu
juego. Por eso aqui la seguridad no viene de un validador, sino de **tres cosas
que el prompt obliga a la IA a hacer**:

1. Decir siempre **donde va** cada script y de que tipo es.
2. Entregar el script **completo**, nunca un fragmento.
3. Pasar por una **lista negra** de APIs que ya no existen.

---

## El flujo

```text
   1. Buscar en mecanicas/00-INDICE.md
            |
      esta? --- SI --> usar esa ficha. Fin.
            |
            NO
            |
            v
   2. Copiar EL PROMPT de mas abajo
            |
            v
   3. Pegarlo en la IA y describir la mecanica
            |
            v
   4. La IA devuelve uno o varios scripts,
      cada uno con su ruta exacta en la cabecera
            |
            v
   5. Crear esos scripts en Studio, en la ruta indicada
            |
            v
   6. Probar en Play Solo
            |
            v
   7. Probar en Test > Clients and Servers > 2 Players
            |
            v
   8. Recorrer la checklist I.3 de
      mecanicas/09-errores-y-checklist.md
            |
            v
   9. Si falla: pegar el error a la IA con el
      formato de la Parte J del modulo 09
```

El paso 7 no es opcional. **La mitad de los fallos de Roblox solo aparecen con
dos jugadores.** Todo lo que funciona en Play Solo y se rompe en el juego real
es, casi siempre, codigo de cliente haciendo algo que le toca al servidor.

---

## Por que las IAs fallan con Luau, y como lo cortamos

Cada fila de esta tabla es un fallo real y repetido. La tercera columna es lo
que el prompt obliga a hacer para que no ocurra.

| Fallo tipico de la IA | Que provoca | Como lo corta el prompt |
|---|---|---|
| Mezcla codigo de cliente y de servidor en un archivo | Nada funciona y no da error claro | Obliga a declarar tipo y contenedor en la cabecera |
| Usa APIs de hace anos | Avisos, o silencio total | Lista negra explicita en el prompt |
| Confia en lo que manda el cliente | El juego se rompe en cuanto alguien lo mira | Obliga a validar todo en el servidor |
| Escribe `game.Workspace.Parte` de algo que aun no existe | `attempt to index nil` | Obliga a `WaitForChild` con tiempo maximo |
| Conecta eventos y nunca los desconecta | Fuga de memoria, servidor lento | Obliga a limpiar en `PlayerRemoving` y `Destroying` |
| Inventa propiedades que no existen | `Unable to assign property` | Obliga a usar solo clases y propiedades reales |
| Devuelve fragmentos sueltos | No sabes donde pegarlos | Obliga a entregar el script entero |
| No dice donde va el script | Lo pones mal y no corre | Cabecera obligatoria con la ruta |
| Pone bucles sin espera | El servidor se cuelga | Obliga a `task.wait()` en todo bucle |
| Usa grados donde van radianes | El objeto gira al azar | Obliga a `math.rad` en CFrame |

---

## EL PROMPT (copia desde aqui)

```text
Eres un programador experto en Roblox Studio y Luau. Vas a escribir una
mecanica de juego para un proyecto real.

REGLAS QUE NO PUEDES ROMPER

1. UBICACION OBLIGATORIA
   Cada script que entregues empieza con un comentario de dos lineas:
       -- TIPO: Script | LocalScript | ModuleScript
       -- RUTA: la ruta exacta, por ejemplo
                ServerScriptService > Sistemas > Economia
   Sin esas dos lineas el script no sirve.

2. SCRIPT COMPLETO
   Entrega el archivo entero, desde la primera linea hasta la ultima.
   Nunca escribas "aqui va tu logica", "..." ni fragmentos sueltos.
   Si hacen falta tres scripts, entrega los tres completos.

3. EL SERVIDOR DECIDE
   El cliente solo puede pedir y dibujar. Nunca decide.
   Todo lo que afecte a vida, dinero, objetos, puntuacion o progreso
   se calcula y se comprueba en el servidor.
   Todo RemoteEvent y RemoteFunction valida, en este orden:
       a) frecuencia: cuantas veces por segundo puede llamarlo un jugador
       b) tipo de cada argumento
       c) rango de cada valor numerico
       d) que el jugador tenga derecho a hacer eso
   Si algo no cuadra, la funcion termina sin hacer nada.

4. NADA DE APIS OBSOLETAS
   Prohibido usar:
       BodyVelocity, BodyPosition, BodyGyro, BodyAngularVelocity
       Model:SetPrimaryPartCFrame, Model:GetPrimaryPartCFrame
       workspace:FindPartOnRay, workspace:FindPartsInRegion3
       part.Velocity, part.RotVelocity
       wait(), spawn(), delay()
       Player.Chatted
       TeleportService:TeleportPartyAsync
       Humanoid:LoadAnimation
   Usa en su lugar:
       LinearVelocity, AlignPosition, AlignOrientation, AngularVelocity
       Model:PivotTo, Model:GetPivot
       workspace:Raycast, workspace:GetPartBoundsInBox
       part.AssemblyLinearVelocity, part.AssemblyAngularVelocity
       task.wait(), task.spawn(), task.delay()
       TextChatService con TextChatCommand
       TeleportService:TeleportAsync
       Animator:LoadAnimation

5. NADA PUEDE SER NULO POR SORPRESA
   Todo WaitForChild lleva tiempo maximo:
       local x = padre:WaitForChild("Hijo", 10)
       if not x then return end
   Nunca encadenes rutas tipo game.Workspace.Mapa.Puerta.
   Comprueba cada objeto antes de usarlo.

6. LIMPIEZA
   Guarda las conexiones que crees y desconectalas cuando toque.
   Todo estado guardado por jugador se borra en PlayerRemoving.
   Todo bucle infinito lleva task.wait() y una condicion de salida.

7. PROPIEDADES REALES
   Solo puedes usar clases, propiedades, metodos y eventos que existan
   de verdad en Roblox. Si no estas seguro de que algo existe, no lo uses
   y dilo abiertamente en las notas del final.

8. ANGULOS
   Los angulos de CFrame.Angles van en radianes. Usa siempre math.rad.

9. LO QUE PUEDE FALLAR VA EN PCALL
   DataStore, MarketplaceService, BadgeService, TeleportService,
   HttpService y PathfindingService van siempre dentro de pcall.

10. ESTILO
    Comentarios en espanol sin acentos.
    Indentacion de cuatro espacios.
    Nombres de variables en espanol y descriptivos.
    Comenta solo donde hay una trampa, no lo evidente.

FORMATO DE TU RESPUESTA

Primero, una frase diciendo que hace la mecanica.

Despues, cada script en su propio bloque de codigo, con sus dos lineas de
cabecera.

Despues, una seccion titulada COMO INSTALARLO con los pasos numerados de
que crear en Studio y donde.

Despues, una seccion titulada QUE COMPROBAR con casillas, incluyendo
siempre estas tres:
    - [ ] Funciona en Play Solo
    - [ ] Funciona con Test > 2 Players
    - [ ] Funciona despues de morir y reaparecer

Por ultimo, una seccion titulada AVISOS donde digas con honestidad que
partes no has podido verificar, que suposiciones has hecho sobre la
estructura del juego, y que puede fallar.

No escribas nada mas fuera de esas secciones.

LA MECANICA QUE QUIERO ES:
[describe aqui lo que quieres, con el mayor detalle que puedas]
```

---

## Como describir bien lo que quieres

La ultima linea del prompt es la que decide la calidad del resultado. Compara:

**Mal:**

```text
quiero un sistema de dash
```

**Bien:**

```text
Quiero un dash: el jugador pulsa Q y sale disparado hacia donde mira,
unos 40 studs, en medio segundo. No puede volver a usarlo hasta pasados
3 segundos. Durante el dash no recibe dano. Si esta en el aire no puede
usarlo. Debe funcionar tambien en movil con un boton en pantalla.
El enfriamiento tiene que verse en la interfaz.
```

Lo que conviene decir siempre:

| Dato | Ejemplo |
|---|---|
| Que tecla o boton lo activa | Q, clic derecho, boton tactil |
| Numeros concretos | 40 studs, 3 segundos, 25 de dano |
| Cuando **no** debe funcionar | en el aire, sin municion, si esta aturdido |
| Que debe ver el jugador | efecto, sonido, cambio en la interfaz |
| Si es para uno o para todos | solo quien lo usa, o lo ven los demas |
| Si hay que guardarlo | se pierde al salir, o persiste |

---

## Si el juego devuelve errores

No arregles el codigo a mano si no sabes exactamente que estas tocando. Pega el
error a la IA con este formato, que es el mismo de la Parte J del modulo 09:

```text
El script da este error en Studio:

[pega el mensaje exacto de la Output, con el nombre del script y la linea]

El script esta en: [ruta exacta]
Es un: [Script | LocalScript | ModuleScript]

Esto es lo que hice justo antes: [que pasaba en el juego]

Devuelve el script COMPLETO corregido, no solo la linea. Manten las dos
lineas de cabecera con TIPO y RUTA.
```

La frase final importa. Sin ella, la IA devuelve un parche de tres lineas y tu
tienes que adivinar donde encaja, que es como se introducen errores nuevos.

### Los errores que veras mas veces

| Mensaje | Casi siempre significa |
|---|---|
| `attempt to index nil with X` | El objeto no existe todavia o el nombre esta mal escrito |
| `Infinite yield possible on WaitForChild` | Ese hijo no existe, o esta en otro contenedor |
| `attempt to call a nil value` | La funcion no existe o el modulo no la devuelve |
| `Unable to assign property X` | Tipo equivocado, o la propiedad no existe en esa clase |
| `Requested module experienced an error` | El ModuleScript falla, o hay dependencias en circulo |
| El script no hace nada y no da error | Es un LocalScript en un sitio donde no corre |

El catalogo completo, con 60 errores y sus causas reales, esta en
`mecanicas/09-errores-y-checklist.md`.

---

## Comprobacion rapida antes de dar por buena una mecanica

Antes de aceptar lo que te ha dado la IA, mira estas diez cosas. Se tarda dos
minutos y ahorra tardes enteras.

- [ ] Cada script tiene sus dos lineas de cabecera con TIPO y RUTA
- [ ] Ningun LocalScript esta en `ServerScriptService` ni en `Workspace`
- [ ] No aparece ninguna API de la lista negra
- [ ] Todos los `WaitForChild` tienen tiempo maximo
- [ ] Los remotes validan tipo y rango de cada argumento
- [ ] Nada importante lo decide el cliente
- [ ] Los bucles llevan `task.wait()`
- [ ] Las llamadas a DataStore y similares van en `pcall`
- [ ] Hay limpieza en `PlayerRemoving`
- [ ] Los angulos de CFrame usan `math.rad`

Si falla alguna, devuelvesela a la IA senalando cual y pidiendo el script
completo otra vez.

---

## Nota sobre el alcance

Este prompt reduce mucho los errores, pero no los elimina. Ninguna IA conoce la
estructura concreta de tu juego: no sabe como se llaman tus carpetas, ni tus
partes, ni tus remotes.

Por eso el prompt obliga a la seccion AVISOS. Ahi es donde la IA debe decir que
ha supuesto. Lee esa seccion **antes** que el codigo: casi siempre explica por
adelantado por que algo no va a funcionar a la primera en tu proyecto.

Y el consejo mas util de todos: **pide una mecanica cada vez**. Un prompt que
pide inventario, tienda, misiones y NPC a la vez devuelve cuatro sistemas a
medias que no encajan entre si. Cuatro prompts separados devuelven cuatro
sistemas que funcionan.

---

## Vuelta al catalogo

- `mecanicas/00-INDICE.md` para buscar entre las mecanicas ya escritas
- `mecanicas/09-errores-y-checklist.md` cuando algo falle
- `prompts/PROMPT-2-ANIMACION.md` si lo que necesitas es una animacion
- `prompts/PROMPT-1-DISENO.md` si aun estas planificando el juego
