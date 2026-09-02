# Reglas de gen_rbxmx.py

El generador construye `EntregaFinalV3.rbxmx` a partir de los tres `.lua` y se
niega a escribir el paquete si detecta un solo aviso. Salida esperada:

```
revision estatica de Luau
  Servidor: limpio (929 lineas)
  Cliente: limpio (1885 lineas)
  Config: limpio (132 lineas)
auditoria del XML
  XML valido, 3 de 3 fuentes verificadas byte a byte
salida=0
```

## Comprobaciones que aplica

1. Cabecera obligatoria de dos lineas: `-- TIPO:` y `-- RUTA:`.
2. Todo `WaitForChild` debe llevar coma de primer nivel, es decir, tiempo de espera.
3. Prohibido `wait(`, `spawn(` y `delay(` globales. Se usa `task.wait`, `task.spawn`, `task.delay`.
4. Prohibido `.Velocity` y `.RotVelocity`. Se usa `AssemblyLinearVelocity`.
5. `CFrame.Angles` siempre con `math.rad`.
6. Prohibido `Humanoid:LoadAnimation`. Se usa `Animator:LoadAnimation`.
7. Prohibido `Player.Chatted`. Se usa `TextChatService`.
8. Balance de bloques: `function + if + do == end`. `elseif` y `else` no cuentan.
9. Ningun caracter no ASCII fuera de cadenas. Este guardia evita el fallo que
   dejaba el LocalScript entero sin arrancar.

## APIs prohibidas y su sustituto

| Prohibido | Sustituto |
| --- | --- |
| `BodyVelocity` | `LinearVelocity` |
| `BodyPosition` | `AlignPosition` |
| `BodyGyro` | `AlignOrientation` |
| `BodyAngularVelocity` | `AngularVelocity` |
| `SetPrimaryPartCFrame` | `PivotTo` |
| `FindPartOnRay` | `Raycast` |
| `FindPartsInRegion3` | `GetPartBoundsInBox` |
| `part.Velocity` | `AssemblyLinearVelocity` |
| `wait` `spawn` `delay` | `task.wait` `task.spawn` `task.delay` |
| `Player.Chatted` | `TextChatService` |

## Estructura interna

Funciones: `despojar`, `contar`, `argumentos_de`, `hay_coma_de_primer_nivel`,
`esc`, `revisar_cabecera`, `revisar_lua`, `escribir_nodo`, `construir`,
`auditar`, `main`.
Constantes: `AQUI`, `SALIDA`, `FUENTES`, `TIPO_ESPERADO`, `ARBOL`, `CAB`, `OBSOLETAS`.

`despojar` quita comentarios y cadenas antes de contar bloques, por eso el
guardia de no ASCII se aplica sobre el texto ya despojado.
