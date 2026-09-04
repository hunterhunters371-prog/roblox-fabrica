# Entrega Final: Turno Nocturno

Propuesta y primer corte experimental. Fecha: 2026-09-04.

## La promesa

Un repartidor de una central nocturna tiene 90 segundos para cumplir su contrato.
No gana simplemente quien corre mas: gana quien decide bien que cargar, que puerta
visitar y cuando gastar su ultimo impulso. Cada turno termina con un resultado
legible, una medalla posible y un objetivo para la siguiente partida.

Frase de presentacion: **Tu contrato. Tu ruta. Un ultimo turno.**

## Diagnostico

La V3 ya tiene carrera, resistencia, carga visible, deslizada, pedidos urgentes,
combo, camara reactiva y puertas animadas. El problema principal no es la falta de
efectos: casi todas las partidas piden hacer lo mismo, y el cierre muestra numeros
sin explicar que dominaste ni que intentar despues.

Decision de diseno: conservar ese movimiento y construir objetivos encima antes
de meter mas mecanicas, una tienda o un mapa enorme. La nueva version es una copia,
no una sustitucion del juego guardado en Studio.

## Primer corte implementado en el paquete experimental

### 1. Elegir como jugar

Durante el descanso puedes elegir por botones o teclas 1, 2 y 3. La eleccion se
bloquea cuando empieza la ronda. No requiere compras, nivel previo ni Robux.

| Contrato | Decision que provoca | Bronce | Plata | Oro |
| --- | --- | --- | --- | --- |
| CARGA | Hacer viajes cargados o salir antes para mantener velocidad | 3 cajas | 9 cajas | 18 cajas |
| RUTA | Salir del circuito comodo y planear destinos diferentes | 2 destinos | 4 destinos | 6 destinos |
| EXPRESS | Priorizar pedidos urgentes en lugar del destino mas cercano | 1 urgente | 3 urgentes | 5 urgentes |

CARGA cuenta cajas aceptadas. RUTA cuenta puertas distintas; volver a la misma no
avanza el contrato. EXPRESS cuenta pedidos urgentes completados, no cajas. Todos
pueden entregar cualquier pedido: el contrato orienta, no prohibe jugar.

Se mantienen 3 cajas como capacidad maxima y las velocidades de V3. No se prometen
clases con estadisticas diferentes. Los umbrales son un punto de partida de diseno,
NO un equilibrio validado con jugadores.

### 2. Un turno con principio y final

- Preparacion: 20 segundos para elegir. No se puede adelantar con E antes de los
  primeros 8 segundos. E no debe iniciar desde la pantalla de introduccion.
- Partida: 90 segundos, con el ritmo y combo existentes.
- Primer exito: una entrega de 3 cajas ya puede dar bronce en CARGA.
- Cierre: medalla, reputacion ganada, rango de la sesion y sugerencia de probar
  otro contrato. Se mantiene la puntuacion y el top de la ronda.

En multijugador los pedidos siguen siendo compartidos como en V3. Esto es
competencia ligera; NO se ha implementado un cooperativo con objetivos de equipo.
La ronda puede iniciarse con E tras el tiempo minimo: no hay sistema de votos.

### 3. Progreso honesto

Premio del turno = 30/70/120 REP segun la mejor medalla, mas 2 REP por caja
entregada, con un maximo de 30 REP extra. No se suman los premios de las tres
medallas. Maximo por turno: 150 REP. Si no entregas, ganas cero.

Rangos: APRENDIZ (0), REPARTIDOR (120), ESPECIALISTA (360), LEYENDA (720).
Son titulos internos del juego, NO insignias oficiales de Roblox.

**En este prototipo la reputacion solo dura durante la conexion al servidor.**
Sobrevive entre turnos y a la muerte del personaje, pero se pierde al salir. No
hay tienda ni cosmeticos desbloqueados todavia. El record de puntos usa un espacio
de datos experimental separado del de V3; su guardado requiere verificacion real.

### 4. Interfaz que ayuda a decidir

El panel derecho existente pasa a mostrar el contrato, sus tres botones, progreso
a oro, medalla actual y el top 3 de la ronda. No se apilan cinco paneles nuevos.
La brujula prioriza puertas no visitadas para RUTA y urgentes para EXPRESS; sigue
siendo una recomendacion por distancia, no un calculador exacto de rutas.

La introduccion explica el orden de las acciones: cargar en el almacen, entregar
en puertas activas, correr o deslizar y elegir un contrato. Las puertas, sonidos
y camara anteriores se conservan.

### 5. Integridad de las reglas

- Contadores y reputacion calculados solo en el servidor.
- Identificador de ronda y de entrega: un toque repetido no duplica avance.
- Cierre idempotente: no puede pagar la recompensa dos veces.
- Entregas vencidas y rondas terminadas se rechazan en el instante exacto.
- Se comprueban vida y distancia a la zona de recogida/entrega.
- El generador de pedidos intenta mantener al menos un urgente disponible.
  No reserva urgentes para cada jugador ni garantiza que puedan alcanzarlos.
- Se limpian estados de deslizada al cambiar de ronda.
- El servidor experimental se detiene si detecta otra version activa del juego.
- Una aparicion desactivada ya no impide crear la aparicion del juego.

Esto mejora controles concretos; no equivale a un anticheat completo.

## Direccion artistica y siguientes cortes: PROPUESTOS, NO IMPLEMENTADOS

### Mundo con identidad

Convertir la arena plana en un pequeno distrito industrial nocturno con tres
referencias faciles de recordar: central dorada, mercado verde y estacion roja.
Usar volumen, senales y siluetas en vez de cubrirlo todo de neon. Reservar el rojo
para urgencia y peligro; nunca comunicar un estado solo por color.

Dar a las puertas una funcion de orientacion: numero, nombre del destino y sello
de entrega, con una respuesta breve al completar. No bloquear al jugador con una
hoja que hoy es solo decorativa.

### Movimiento con decisiones reales

Crear dos rutas equivalentes: calle segura y atajo de habilidad. La deslizada
seguira sirviendo por velocidad; no fingir que reduce la hitbox, porque aun no lo
hace. Antes de introducir pasos bajos hay que implementar y probar esa colision.

Probar una carga fragil despues de validar contratos. La dificultad seria conservar
el paquete por una ruta segura, no anadir dano invisible al azar. Fuera del primer
corte para no mezclar mas variables de equilibrio.

### Progreso entre sesiones

Guardar reputacion y record por contrato con version de esquema, bloqueo de sesion,
reintentos y pruebas de desconexion. Anadir uniformes, colores de mochila y sellos
de entrega como recompensas visibles. No vender velocidad ni mas capacidad.

### Accesibilidad y plataformas

Ofrecer modo de movimiento reducido: sin cabeceo, sin sacudidas fuertes y con FOV
estable. Ajustar el HUD a 390x844, 844x390 y mando. Los botones del nuevo contrato
usan Activated, pero el HUD heredado NO esta validado en movil ni con mando.

## Prueba con jugadores y criterios de aceptacion

Hipotesis para una primera prueba con cinco personas; no son resultados medidos:

1. Al menos cuatro entienden donde recoger y donde entregar sin ayuda verbal.
2. Al menos cuatro logran una entrega en los primeros 30 segundos de juego activo.
3. Al menos tres pueden explicar como su contrato cambio la ruta elegida.
4. Al menos tres deciden jugar otro turno voluntariamente y saben que mejorar.
5. No hay una opcion que todos elijan porque las otras dos no merecen la pena.

Registrar tiempo hasta primera entrega, cajas y pedidos por turno, contrato elegido,
medalla, cambios de contrato, muertes y motivo para abandonar. No hace falta capturar
chat ni informacion personal. No hay telemetria nueva instalada en este prototipo.

Pruebas tecnicas pendientes: Play Solo, dos clientes, entrada a mitad de ronda,
muerte/respawn, R6 y R15, cierre de servidor, red lenta, DataStore y rendimiento
comparado con V3 en el mismo dispositivo. No publicar antes de pasarlas.

## Lo que queda fuera deliberadamente

Mundo abierto grande, mascotas, pase de batalla, recompensas aleatorias de pago,
energia que impide jugar, anuncios, combate y decenas de mecanicas inconexas.
Primero hacer divertido un turno; despues ampliar el mundo.
