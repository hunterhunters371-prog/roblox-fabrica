# Notas de apoyo: Entrega Final (Roblox)

Documentacion de respaldo del juego `EntregaFinalV3`, escrita el 2 de septiembre de 2026.
Sirve para retomar el trabajo sin volver a investigar nada.

## Indice

| Archivo | Para que sirve |
| --- | --- |
| `01-estado-verificado.md` | Que existe hoy, con tamanos y rutas exactas |
| `02-flujo-mcp-studio.md` | Como editar el juego por MCP sin romperlo |
| `03-errores-y-soluciones.md` | Fallos ya sufridos y su arreglo, con el error literal |
| `04-config-referencia.md` | Todas las claves de `Config.lua` y su valor |
| `05-puertas-animadas.md` | Sistema de puertas: diseno, medidas y codigo completo |
| `06-animaciones-propias.md` | Integrar animaciones propias y publicarlas |
| `07-interfaz-medidas.md` | Medidas del HUD, fallos corregidos y falsos positivos |
| `08-reglas-generador.md` | Reglas que impone `gen_rbxmx.py` y APIs prohibidas |
| `09-studio-barra-plugins.md` | Recuperar la barra de plugins o de herramientas en Studio |

## Reglas de oro

1. La fuente de verdad son los tres `.lua` del sandbox, no el script vivo de Studio.
2. Nunca se edita solo en Studio: se edita la fuente, se regenera y se replica.
3. Ninguna entrega sale sin `salida=0` en el generador y sin comparar bytes.
4. Toda mejora visual es aditiva: no cambia velocidades, puntos ni tiempos.
