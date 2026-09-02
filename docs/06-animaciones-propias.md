# Animaciones propias

## Que hay integrado

Las animaciones del usuario que estaban sueltas en el Workspace se copiaron a
`Workspace.EntregaFinalV3.Animaciones`, sin borrar ni mover los originales:

| Ruta | Origen | Marcos | Duracion |
| --- | --- | --- | --- |
| `Animaciones/R6/Correr` | `animacion de correr actualizado` / `Untitled` | 41 | 0.67 s |
| `Animaciones/R6/Caminar` | `Animacion Caminar` / `R6 Caminar` | 50 | 0.82 s |
| `Animaciones/R15/Caminar` | `Personaje R15` / `R15 Caminar` | 40 | 0.67 s |

Otras disponibles y no usadas, todas R6, en `RestosAntiguos.Rig.AnimSaves`:
`CaminarEpico` 0.70 s / 5 marcos, `CorrerPro` 0.60 s / 9, `CorrerSprint` 0.56 s / 9,
`CorrerFlujo` 0.60 s / 9.

El avatar de prueba es R6, por lo que la rama que se usa es `Animaciones/R6`.

## Como funciona el cargador

1. `carpetaDeAnimaciones` busca la carpeta primero en `ReplicatedStorage` y
   despues en `workspace`, de forma recursiva, usando `Config.CARPETA_ANIMACIONES`.
2. La rama se elige por `humanoide.RigType`: `R6` o `R15`.
3. `animacionDe(rama, nombre)` recorre `rama:GetChildren()` y PREFIERE un objeto
   `Animation` con `AnimationId` no vacio; si no lo hay, usa la `KeyframeSequence`
   del mismo nombre registrandola con `KeyframeSequenceProvider`.
4. `cargarPropias` carga las pistas de `Config.PISTAS_PROPIAS` con
   `Animator:LoadAnimation` y las guarda en `propias`.
5. `ajustarAnimaciones` elige `Deslizada`, `Correr` o `Caminar` segun el estado,
   mezcla con `Config.MEZCLA_ANIMACION` y, si no hay pista propia, cae al respaldo
   de `AdjustSpeed` sobre la animacion por defecto.

## El detalle que costo encontrar

La carpeta replica al cliente despues de que aparece el personaje, asi que un
unico intento de carga fallaba en silencio. La solucion son reintentos:

```lua
local function pedirPropias(humanoide)
    task.spawn(function()
        for _ = 1, 20 do
            if not humanoide.Parent then
                return
            end
            cargarPropias(humanoide)
            if next(propias) ~= nil then
                return
            end
            task.wait(0.5)
        end
    end)
end
```

`pedirPropias(humanoide)` se llama dentro de `conectarPersonaje`.

## Prueba que confirma que suenan

```
ANDANDO    vel=10.2   WalkAnim v=0.69 Core  ;  Caminar v=1.00 peso=1.0 Action
CORRIENDO  vel=23.2   WalkAnim v=1.55 Core  ;  Correr  v=1.30 peso=1.0 Action
```

La pista propia manda por prioridad `Action`. La `WalkAnim` de Roblox sigue
sonando por debajo en `Core` y no se ve. Una pista con `Length == 0` indica que
el asset no cargo.

## Para el juego publicado

El id que devuelve `RegisterKeyframeSequence` es temporal y solo vale en Studio.
Pasos para produccion:

1. Clic derecho en la `KeyframeSequence` y `Save to Roblox` o `Publish to Roblox`.
2. Copiar el id publicado.
3. Crear en `Animaciones/R6` un objeto `Animation` llamado `Correr` o `Caminar`
   con ese `AnimationId`.
4. No hay que tocar codigo: `animacionDe` prefiere ese `Animation` sobre la
   `KeyframeSequence` del mismo nombre.
