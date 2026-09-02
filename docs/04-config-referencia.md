# Referencia de Config.lua

Estilo del archivo: `Config.CLAVE = valor`. 132 lineas, 3966 bytes.
Cambiar cualquiera de estos numeros SI altera el juego. Las claves de puertas y
animaciones son las unicas puramente esteticas.

## Identidad y ritmo de ronda

| Clave | Valor |
| --- | --- |
| `NOMBRE` | "ENTREGA FINAL" |
| `LEMA` | "TRES PEDIDOS. UNA ESPALDA. NOVENTA SEGUNDOS." |
| `SEGUNDOS_RONDA` | 90 |
| `SEGUNDOS_DESCANSO` | 12 |
| `SEGUNDOS_INTRO` | 7 |
| `SEGUNDOS_RITMO` | 20 |
| `SUBIDA_RITMO` | 0.18 |
| `RECORTE_RITMO` | 4 |

## Movimiento

| Clave | Valor |
| --- | --- |
| `VELOCIDAD_BASE` | 18 |
| `VELOCIDAD_CARRERA` | 31 |
| `PENALIZACION_POR_CAJA` | 2.6 |
| `SALTO_BASE` | 50 |
| `PENALIZACION_SALTO` | 4 |
| `VELOCIDAD_DESLIZADA` | 44 |
| `SEGUNDOS_DESLIZADA` | 0.75 |
| `COSTE_DESLIZADA` | 22 |
| `ENFRIAMIENTO_DESLIZADA` | 1.6 |

Velocidad real = base o carrera, menos `PENALIZACION_POR_CAJA` por caja cargada.
Con 3 cajas corriendo: 31 - 3 x 2.6 = 23.2. Este numero sirve de comprobacion.

## Camara y animacion

| Clave | Valor |
| --- | --- |
| `CAMPO_VISION` | 70 |
| `CAMPO_VISION_CARRERA` | 87 |
| `CAMPO_VISION_DESLIZADA` | 97 |
| `CABECEO` | 0.85 |
| `LADEO_MAXIMO` | 4.5 |
| `LADEO_DESLIZADA` | 7 |
| `INCLINACION_CUERPO` | -9 |
| `VELOCIDAD_ANIMACION_CARRERA` | 1.3 |
| `VELOCIDAD_ANIMACION_DESLIZADA` | 1.6 |
| `CARPETA_ANIMACIONES` | "Animaciones" |
| `PISTAS_PROPIAS` | { "Caminar", "Correr", "Deslizada" } |
| `MEZCLA_ANIMACION` | 0.15 |

## Puertas animadas (solo aspecto)

| Clave | Valor |
| --- | --- |
| `PUERTA_ANCHO` | 16 |
| `PUERTA_ALTO` | 12 |
| `PUERTA_PUNTO_ANCHO` | 8 |
| `PUERTA_PUNTO_ALTO` | 7 |
| `PUERTA_GROSOR` | 0.55 |
| `PUERTA_DISTANCIA_ABRE` | 26 |
| `PUERTA_VELOCIDAD` | 5.5 |

## Resistencia, carga y puntos

| Clave | Valor |
| --- | --- |
| `RESISTENCIA_MAXIMA` | 100 |
| `GASTO_CARRERA` | 27 |
| `RECUPERACION` | 19 |
| `MINIMO_PARA_CORRER` | 12 |
| `CAJAS_MAXIMAS` | 3 |
| `PUNTOS_POR_CAJA` | 60 |
| `BONUS_LOTE` | 45 |
| `PEDIDOS_ACTIVOS` | 3 |
| `PUNTOS_ENTREGA` | 8 |
| `SEGUNDOS_PEDIDO` | 27 |
| `SEGUNDOS_PEDIDO_URGENTE` | 15 |
| `PROBABILIDAD_URGENTE` | 0.24 |
| `MULTIPLICADOR_URGENTE` | 3 |
| `SEGUNDOS_COMBO` | 12 |
| `COMBO_MAXIMO` | 6 |
| `BONUS_COMBO` | 0.25 |

## Tecnicos

| Clave | Valor |
| --- | --- |
| `ENFRIAMIENTO_TOQUE` | 0.3 |
| `LLAMADAS_POR_SEGUNDO` | 6 |
| `MARGEN_VELOCIDAD` | 1.7 |
| `AVISOS_ANTES_DE_CORREGIR` | 3 |
| `ACCIONES` | empezar, soltar, correr, andar, deslizar |
| `RADIO_ARENA` | 110 |
| `CLAVE_DATASTORE` | "EntregaFinalV3_1" |

## Colores (RGB)

`COLOR_SUELO 38,42,52` · `COLOR_MURO 58,64,78` · `COLOR_CARRIL 72,80,98`
`COLOR_ALMACEN 240,180,60` · `COLOR_ACTIVO 80,220,120` · `COLOR_URGENTE 240,92,92`
`COLOR_INACTIVO 58,64,76` · `COLOR_FAROLA 150,200,255` · `COLOR_CAJA 214,158,70`
`COLOR_NEON 110,231,255` · `COLOR_ORO 255,208,92` · `COLOR_MAGENTA 232,106,214`
`COLOR_PANEL 16,18,28`

## Sonidos

`switch3.wav`, `electronicpingshort.wav`, `clickfast.wav`, `unsheath.wav`,
`bass.wav`, `switch.wav`
