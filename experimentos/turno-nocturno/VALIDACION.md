# Validacion - 2026-09-04

## Ejecutado

- 15 casos de contratos en Lua 5.4: elecciones, bloqueo de cambios, metas, destinos
  unicos, urgentes, entregas duplicadas, cierre repetido, rondas viejas, AFK, transicion,
  aislamiento entre jugadores, numeros invalidos, rangos y 1000 eventos con duplicados.
- 10 casos de integracion SIMULADA ejecutando las funciones reales de recogida y
  entrega contra servicios sustitutos. No se simula el motor de Roblox.
- Los cuatro scripts son aceptados por el parser Lua 5.4 y contienen solo ASCII.
- XML generado valido: se recuperan los cuatro scripts exactamente como se escribieron.
- SHA256 de todos los scripts y del modelo generado.

La salida completa esta en `pruebas.txt`.

## No ejecutado: barrera para publicar

- [ ] Compilacion con Luau y ejecucion en Play Solo.
- [ ] Dos clientes: pedidos compartidos y premios por jugador.
- [ ] Entrada durante una ronda y desconexion durante el cierre.
- [ ] Muerte y reaparicion sin perder reputacion de la sesion.
- [ ] R6/R15, animaciones y camara.
- [ ] HUD sin texto cortado ni solapes, en PC y movil.
- [ ] Controles de contrato con teclado, tactil y mando.
- [ ] Guardado del record experimental, fallos de DataStore y cierre del servidor.
- [ ] Rendimiento y equilibrio con personas reales.

No hay conexion a Roblox Studio disponible en esta conversacion al preparar el kit.
Una prueba de sintaxis no verifica clases, propiedades, replicacion ni renderizado.

## Aclaraciones de la base

Las puertas V3 son visuales, no barreras de colision. El registro antiguo que decia
198 piezas contaba todos los descendientes: por su codigo hay 162 Part decorativas,
mas modelos y luces. Eso no fue una medicion nueva en esta entrega.

Coincidir en bytes y numero de lineas no demuestra igualdad de fuentes. En este kit
se comparan textos del XML y se generan firmas SHA256. No se afirma coincidencia
con el Studio actual, al que no se pudo acceder.
