# Flujo de trabajo por MCP con Roblox Studio

## Ciclo obligatorio para cualquier cambio

```
1. editar la fuente        /data/juego5/{Servidor,Cliente,Config}.lua
2. regenerar               python3 gen_rbxmx.py   -> exige salida=0
3. parar el modo Play      start_stop_play is_start=false
4. replicar en Studio      multi_edit (solo funciona en datamodel Edit)
5. verificar bytes         execute_luau en Edit: #Source, lineas, no ASCII
6. probar en marcha        start_stop_play is_start=true + execute_luau en Client
7. revisar consola         get_console_output
8. parar el Play           start_stop_play is_start=false
9. entregar el .rbxmx
```

Saltarse el paso 5 es la causa historica de que Studio y la fuente se separen.

## Reglas de las herramientas

- Todas exigen `studio_id`. El identificador cambia cada vez que se reabre el lugar:
  hay que llamar a `list_roblox_studios` antes de nada.
- Muchas exigen `datamodel_type`: `Edit`, `Client` o `Server`.
- `multi_edit` solo funciona en `Edit`. Con el juego en marcha falla.
- `execute_luau` en `Client` ve el HUD y el personaje; en `Edit` ve el arbol guardado.
- `search_game_tree` acepta `path`, `max_depth` (maximo 10), `head_limit`,
  `instance_type` y `keywords`. Sin `max_depth` alto no encuentra lo anidado.
- `http_get` solo admite create.roblox.com y la URL debe terminar en `.md` o ser `llms.txt`.
- `search_asset` no acepta el tipo `Animation`.

## Sondas utiles ya probadas

Medir bytes y no ASCII de los tres scripts:

```lua
local build = workspace.EntregaFinalV3
local function mide(inst)
    local src = inst.Source
    local lineas = select(2, src:gsub("\n", "\n")) + 1
    local noAscii = select(2, src:gsub("[\128-\255]", ""))
    return string.format("%s bytes=%d lineas=%d noAscii=%d", inst.Name, #src, lineas, noAscii)
end
```

Ver que animaciones suenan de verdad:

```lua
local animador = humanoide:FindFirstChildOfClass("Animator")
for _, p in ipairs(animador:GetPlayingAnimationTracks()) do
    print(p.Name, p.Speed, p.WeightCurrent, p.Priority)
end
```

Una pista con `Length == 0` significa que el asset no cargo.

## Sandbox de trabajo

Amazon Linux 2023, Python 3.13, node 24, sin acceso a internet.
Rutas: `/data/juego5/{Config.lua,Servidor.lua,Cliente.lua,gen_rbxmx.py,EntregaFinalV3.rbxmx}`.
En la terminal, encadenar con `;` y nunca con `&&`: un grep sin resultados aborta la cadena.
