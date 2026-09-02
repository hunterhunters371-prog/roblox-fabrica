# juego3 - ENTREGA FINAL: 60 SEGUNDOS

Tercer juego del proyecto y primer bucle **jugable de principio a fin**: rondas
de 60 segundos, recoger cajas en el almacen y llevarlas al punto que se
ilumina. juego2 es una cinematica; este es el juego.

Todo cabe en un solo archivo `.rbxmx` que se arrastra a `Workspace`. No hace
falta subir ningun asset, no usa imagenes y no depende de juego2.

## Como se abre

1. `python juego3/gen_rbxmx.py`
2. Se crea `juego3/EntregaFinal.rbxmx`.
3. En Roblox Studio: clic derecho en `Workspace` > **Insert from File** >
   elegir `EntregaFinal.rbxmx`.
4. Pulsar Play. La arena se construye sola al arrancar el servidor.

Requisitos: Python 3 y nada mas. Este generador no usa `pillow`, `lz4` ni
`numpy`.

## Que aparece dentro

```
Workspace
  EntregaFinal              Folder
    Servidor                Script          decide todo
    Interfaz                ScreenGui       plantilla inerte
      Cliente               LocalScript     dibuja y pide
      Config                ModuleScript    solo constantes
    Arena                   Folder          se crea en ejecucion
      Suelo, Almacen, Punto1..Punto6, Aparicion
```

En `ReplicatedStorage` el servidor crea `EntregaFinalRemotos` con dos
`RemoteEvent`: `Estado` (servidor -> cliente) y `Acciones` (cliente ->
servidor).

Un `LocalScript` dentro de `Workspace` no se ejecuta: la `ScreenGui` de la
carpeta es una plantilla. El servidor la clona al `PlayerGui` de cada jugador
y es esa copia la que corre, igual que en juego2.

## Como se juega

| Accion | Teclado | Movil |
| --- | --- | --- |
| Empezar la ronda sin esperar el descanso | `E` | boton EMPEZAR |
| Soltar la caja (la racha vuelve a cero) | `Q` | boton SOLTAR |
| Recoger caja | pisar el bloque ambar del centro | igual |
| Entregar | pisar el punto verde | igual |

Puntuacion: 100 puntos por entrega mas 25 por cada eslabon de racha, hasta x8.
Morir o soltar la caja rompe la racha. Al acabar la ronda se guarda el mejor
resultado del jugador con `DataStore` dentro de `pcall`.

## Que decide el servidor

Todo lo que da puntos. El cliente **nunca** manda puntuaciones ni posiciones,
solo dos peticiones de texto que el servidor filtra en cuatro pasos:

1. **frecuencia**: maximo 4 peticiones por segundo y jugador.
2. **tipo**: se descarta lo que no sea `string`.
3. **rango**: solo las claves declaradas en `Config.ACCIONES`.
4. **derecho**: `empezar` solo si no hay ronda; `soltar` solo si lleva caja.

Los toques del almacen y de los puntos se verifican en el servidor
(`Humanoid` vivo, jugador real, enfriamiento de 0.35 s para que `Touched` no
dispare veinte veces por pisada).

La cuenta atras no viaja como numero que baja: el servidor manda el instante
de fin y el cliente lo resta contra `workspace:GetServerTimeNow()`. Es la
ficha 12 del bloque 08 del catalogo y evita que el reloj se desincronice.

## Como se reconstruye

`gen_rbxmx.py` hace tres cosas y en este orden: revisa el Luau, escribe el
XML y vuelve a leer el XML que acaba de escribir. Si la revision encuentra
algo, **no** escribe el archivo.

Lo que revisa: cabecera `-- TIPO:` y `-- RUTA:`, APIs retiradas, `wait()`,
`spawn()` y `delay()` globales, `WaitForChild` sin tiempo maximo, `CFrame` con
angulos sin `math.rad`, recuento de bloques `function`/`if`/`do` contra `end`,
`repeat`/`until`, y parentesis, corchetes y llaves por parejas.

Lo que audita despues: que el XML se pueda releer, que no haya referentes
repetidos, que no haya doble escapado y que cada fuente vuelva **byte a byte**
igual que salio.

Es una version corregida del generador de juego2. Los siete arreglos y el
resto de fallos que se encontraron en el entorno estan en
[HALLAZGOS.md](HALLAZGOS.md).

## Limites

- **El Luau no se ha ejecutado.** Aqui no hay Studio ni interprete de Luau,
  asi que todo lo verificado es estatico: sintaxis por recuento, APIs y
  cabeceras. El primer Play en Studio sigue siendo la prueba de verdad.
- El recuento de bloques es una heuristica. Un `function` de una linea o un
  `if ... then ... end` en la misma linea cuadran igual, pero codigo raro
  puede dar un falso aviso; el mensaje dice los cuatro numeros para poder
  descartarlo a mano.
- `roblox_lint.py` no sirve todavia para este archivo: no conoce `Part`,
  `Script`, `SpawnLocation`, `BillboardGui`, `WeldConstraint` ni `RemoteEvent`
  y los marca como clase no permitida. Ver hallazgo 8.
- `DataStore` solo guarda de verdad en un servidor publicado o con
  **Studio Access to API Services** activado. Sin eso, el `pcall` falla, el
  mejor resultado se queda en 0 y el juego sigue funcionando.
- Sin animaciones: los personajes usan las de Roblox. Enganchar el banco de
  `animaciones/` es el paso siguiente.
- La caja va soldada con `WeldConstraint` y `Massless = true`. Si se sube
  mucho el tamano en `Config`, el personaje empieza a tropezar con su propia
  caja.

## Checklist de PROMPT-3

- [x] El servidor decide, el cliente pide.
- [x] `WaitForChild` con tiempo maximo en todas las esperas y comprobacion de
      `nil` despues.
- [x] `task.wait`, `task.spawn` y `task.delay`; ni un `wait()` global.
- [x] Ninguna API de la lista de retiradas.
- [x] Conexiones guardadas y cortadas en `PlayerRemoving` y en `Destroying`.
- [x] `DataStore` siempre dentro de `pcall`.
- [x] Bucle infinito con `task.wait(1)` y condicion de salida (`ejecutando`).
- [x] Cabecera de dos lineas en los tres scripts.
- [x] Comentarios en espanol sin acentos, sangria de 4 espacios.
- [x] Se puede jugar en movil: las dos acciones tienen boton.

## Siguiente paso

1. Play en Studio y anotar lo que salga en la consola.
2. Modo mundo en `roblox_lint.py` (hallazgo 8) para poder lintar este archivo.
3. Enganchar `animaciones/` al llevar y soltar la caja.
4. Tabla de puntuaciones compartida con `OrderedDataStore`.
