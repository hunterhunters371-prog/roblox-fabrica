-- TIPO: ModuleScript
-- RUTA: Workspace > EntregaFinal > Interfaz > Config
--
-- Todos los numeros del juego en un solo sitio. El servidor requiere la
-- plantilla que vive en Workspace y el cliente requiere la copia que llega
-- al PlayerGui: son dos instancias distintas del mismo modulo, asi que aqui
-- solo puede haber constantes, nunca estado compartido.

local Config = {}

Config.NOMBRE = "ENTREGA FINAL"

-- ronda
Config.SEGUNDOS_RONDA = 60
Config.SEGUNDOS_DESCANSO = 10

-- puntuacion
Config.PUNTOS_BASE = 100
Config.BONUS_RACHA = 25
Config.RACHA_MAXIMA = 8

-- limites que aplica el servidor
Config.ENFRIAMIENTO_TOQUE = 0.35
Config.LLAMADAS_POR_SEGUNDO = 4

-- unicas acciones que el cliente puede pedir; cualquier otra se descarta
Config.ACCIONES = {
    empezar = true,
    soltar = true,
}

-- arena
Config.RADIO_ARENA = 90
Config.PUNTOS_ENTREGA = 6

-- datos
Config.CLAVE_DATASTORE = "EntregaFinal_v1"

-- colores
Config.COLOR_ACTIVO = Color3.fromRGB(80, 220, 120)
Config.COLOR_INACTIVO = Color3.fromRGB(58, 64, 76)
Config.COLOR_ALMACEN = Color3.fromRGB(240, 180, 60)

return Config
