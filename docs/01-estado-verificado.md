# Estado verificado

Ultima verificacion: 2 de septiembre de 2026, prueba en marcha superada y juego parado.

## Tamanos exactos (fuente y script vivo coinciden byte a byte)

| Archivo | Bytes | Lineas | No ASCII |
| --- | --- | --- | --- |
| `Servidor.lua` | 28446 | 929 | 0 |
| `Cliente.lua` | 63966 | 1885 | 0 |
| `Config.lua` | 3966 | 132 | 0 |
| `EntregaFinalV3.rbxmx` | 97981 | 2979 | 0 |

## Arbol del paquete .rbxmx

```
Folder EntregaFinalV3
  Script Servidor
  ScreenGui Interfaz   (Enabled=true, ResetOnSpawn=false, IgnoreGuiInset=true, ZIndexBehavior=1)
    LocalScript Cliente
    ModuleScript Config
```

Cabecera XML `version="4"` mas `<Meta name="ExplicitAutoJoints">true</Meta>`.
El campo `Source` se escribe como `ProtectedString` y los referentes son `RBX%d`.

El `.rbxmx` NO incluye la carpeta `Animaciones`: el codigo tolera su ausencia y
en ese caso usa las animaciones por defecto de Roblox.

## Rutas en el Studio del usuario

```
game.Workspace.EntregaFinalV3.Servidor
game.Workspace.EntregaFinalV3.Interfaz.Cliente
game.Workspace.EntregaFinalV3.Interfaz.Config
game.Workspace.EntregaFinalV3.Arena              (39 piezas, la crea el servidor)
game.Workspace.EntregaFinalV3.Animaciones        (R6/Correr, R6/Caminar, R15/Caminar)
game.Workspace.RestosAntiguos                    (restos del usuario, desactivados)
game.ReplicatedStorage.EntregaFinalRemotos       (Estado, Acciones)
game.Workspace.PuertasCliente                    (solo en marcha, la crea el cliente)
PlayerGui.Interfaz                               (14 hijos)
```

## Nombres que crea el servidor en marcha

`Folder Arena`, `Part Suelo`, `Part Muro{0,90,180,270}`, `Part Almacen`,
`Part BalizaAlmacen`, `Part Punto{1..8}` con `PointLight Baliza`, `Part Carril{i}`,
`Part Farola{i}`, `Part Foco{i}`, `SpawnLocation Aparicion`, `Folder Carga` con `Caja{k}`.

## Campos del estado que viaja al cliente

`activa, finaliza, ritmo, puntos, combo, comboVence, mejor, entregas, cajas,`
`cajasMaximas, resistencia, corriendo, deslizando, deslizaLibre, almacen, pedidos, tabla`

Cada pedido: `posicion, vence, valor, urgente`.
Efectos posibles: `entrega, recoger, soltar, deslizar, urgente, inicio, fin`.

## Estado del repositorio

- Rama por defecto: `main`, base `889bf444583ad732373c8471686fd0d1b723af6e`.
- Rama `juego3-entrega-final`, HEAD `3900f58e6937ea8d6a38ef21cd13d3994f9081a7`, PR #1 abierto.
- Issue #2 con 15 hallazgos de auditoria; los puntos 1 a 7 estan arreglados.
- Rama `apoyo-documentacion`: esta documentacion.
