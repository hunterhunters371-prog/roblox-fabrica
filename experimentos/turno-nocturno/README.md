# Turno Nocturno - experimental

La propuesta completa esta en `PROPUESTA.md`. Este kit mejora Entrega Final V3 con
contratos por turno, medallas, reputacion temporal y comprobaciones de entregas.
No se ha instalado ni probado en Roblox Studio durante esta entrega.

## Archivos

- `base/EntregaFinalV3.rbxmx`: respaldo sin modificar (en el ZIP de esta entrega).
- `generado/EntregaFinalV4-Experimental.rbxmx`: copia experimental importable.
- `generado/{Servidor,Cliente,Config,Turnos}.lua`: fuentes completas extraidas.
- `Turnos.lua`: reglas puras del servidor, sin dependencias de Roblox.
- `Turnos.spec.lua`: 15 pruebas de reglas de contratos.
- `construir.py`: 41 cambios controlados sobre la base; rechaza otra version por SHA256.
- `probar.py`: sintaxis Lua 5.4, reglas puras, 10 pruebas con servicios simulados,
  fuentes del XML y firmas SHA256. Lua 5.4 NO sustituye al compilador Luau.
- `VALIDACION.md` y `pruebas.txt`: alcance y salida real de las pruebas.

## Reconstruir

Con Python 3 y los archivos de este kit juntos:

```sh
python3 construir.py base/EntregaFinalV3.rbxmx
python3 probar.py
```

La segunda orden necesita una biblioteca Lua 5.4 local. Si no la encuentra,
termina con error y NO declara pruebas superadas. El generador solo necesita Python.

Base exacta, SHA256:
`bc7b1cfbfb010a16346a2b99c18c69446bf65ae5a5940ea9769f3c1b1cf57e77`

El kit de fuentes en GitHub requiere aportar ese `.rbxmx` base. El ZIP descargable
incluye la base y las fuentes completas; no depende de rutas temporales del chat.
Si tu Studio tiene cambios posteriores, NO reemplazarlos: comparar primero con las
fuentes de la copia y aplicar solo los cambios que correspondan.

## Probar en Studio sin perder la version actual

1. Guarda una copia local de tu lugar y trabaja en ella, con Play detenido.
2. Mueve el contenedor anterior `EntregaFinalV3` a `ServerStorage`; no lo borres.
3. Importa `EntregaFinalV4-Experimental.rbxmx` dentro de Workspace. Debe quedar una
   sola version ejecutable. El juego experimental intenta detectar duplicados.
4. Si quieres las animaciones propias, COPIA `Animaciones` del contenedor anterior
   al nuevo. Este paquete no incluye esas KeyframeSequence del Studio.
5. Comprueba los SpawnLocation existentes: ninguno debe colocar al personaje dentro
   del almacen o fuera de la arena. La aparicion del juego se llama `Aparicion`.
6. Prueba elegir contrato durante el descanso y arrancar con E. Prueba por separado
   CARGA (1), RUTA (2) y EXPRESS (3). Revisa la consola y la lista de VALIDACION.
7. Para volver a V3: detiene Play, mueve V4 a ServerStorage y devuelve V3 a Workspace.

No se cambiaron archivos en main ni el lugar de Studio. No se mezclan los records
V3 con el espacio de datos de la version experimental. No se han publicado assets.

## Limites

Reputacion temporal, sin tienda, sin guardado de titulos, sin mapa nuevo. Balance,
renderizado, rendimiento, multijugador y animaciones requieren pruebas reales.
El resultado es un prototipo de la propuesta, no una version certificada para publicar.
