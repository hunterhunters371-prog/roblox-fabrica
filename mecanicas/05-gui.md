# 05 - Interfaz de usuario

Modulo 5 del catalogo. Igual que el de animacion, se divide en dos partes:

- **Parte A: los modelos JSON de interfaz de este repositorio.** El formato que
  genera la IA para el pase de batalla y pantallas similares.
- **Parte B: interfaz en tiempo de ejecucion.** El codigo Luau que construye,
  anima y conecta la interfaz con el juego.

Si quieres **disenar** una pantalla, Parte A.
Si quieres que la pantalla **funcione**, Parte B.

---

# PARTE A - Los modelos JSON de interfaz

El contrato completo esta en `prompts/PROMPT-1-DISENO.md`. Aqui esta el resumen
operativo mas el analisis de los archivos existentes.

## A.1 Como decide el validador que es una interfaz

`herramientas/revisar_pase.bat` mira si el JSON tiene la clave `rig`:

| Tiene `rig` | Se trata como |
|---|---|
| Si | Animacion, va a `spec_anim.py` |
| No | Interfaz, va a `roblox_lint.py` y `spec_a_rbxmx.py` |

Por eso un JSON de interfaz **nunca** debe llevar la clave `rig`. Si se la
pones, el validador intentara leerlo como animacion y dara errores absurdos.

## A.2 Campos de la cabecera

| Campo | Tipo | Limite exacto |
|---|---|---|
| `temporada` | texto | Hasta 25 caracteres |
| `titulo` | texto | Hasta 28 caracteres |
| `subtitulo` | texto | Hasta 80 caracteres |
| `tiempo` | texto | Hasta 11 caracteres |
| `niveles` | lista | Entre 2 y 20 elementos |

Ningun texto del archivo puede contener los caracteres `<`, `>` ni `&`. Esos tres
rompen el XML del `.rbxmx` que se genera despues, por eso el validador los
rechaza antes.

## A.3 Campos de un nivel

| Campo | Tipo | Limite exacto |
|---|---|---|
| `gratis` | lista de premios | Entre 1 y 6 elementos |
| `premium` | lista de premios | Entre 1 y 6 elementos |

## A.4 Campos de un premio

| Campo | Tipo | Limite exacto |
|---|---|---|
| `etiqueta` | texto | Hasta 18 caracteres, en MAYUSCULAS |
| `color` | texto | Solo: `azul`, `cian`, `dorado`, `morado`, `naranja`, `rojo`, `rosa`, `verde` |
| `icono` | texto | Un solo emoji |
| `titulo` | texto | Hasta 20 caracteres |
| `desc` | texto | Hasta 55 caracteres |
| `bonus` | texto | Hasta 16 caracteres |
| `nuevo` | booleano | `true` o `false` |

La paleta de ocho colores no es decorativa: son los unicos nombres que el
conversor sabe traducir a un `Color3`. Cualquier otro nombre, incluido un color
en hexadecimal, se rechaza.

## A.5 Ejemplo minimo valido

```json
{
  "temporada": "TEMPORADA 3",
  "titulo": "RUTA CRITICA",
  "subtitulo": "Entrega antes de que el reloj llegue a cero",
  "tiempo": "18d 04h",
  "niveles": [
    {
      "gratis": [
        {
          "etiqueta": "MONEDAS",
          "color": "dorado",
          "icono": "C",
          "titulo": "250 monedas",
          "desc": "Se anaden al saldo al reclamar",
          "bonus": "+10% racha",
          "nuevo": false
        }
      ],
      "premium": [
        {
          "etiqueta": "MOCHILA",
          "color": "morado",
          "icono": "M",
          "titulo": "Mochila rapida",
          "desc": "Aumenta la capacidad de reparto",
          "bonus": "Exclusivo",
          "nuevo": true
        }
      ]
    }
  ]
}
```

En el campo `icono` va un emoji real. Aqui aparece una letra porque este
documento se mantiene en texto plano sin simbolos.

## A.6 Los archivos que ya existen

| Archivo | Que resuelve |
|---|---|
| `interfaces/pase.json` | El pase de batalla de referencia. Es la plantilla a copiar |
| `interfaces/temporada2.json` | Segunda temporada, misma estructura con otros premios |

Antes de pedir una pantalla nueva, abre `pase.json`. Es mas rapido copiar su
estructura y cambiar los textos que describir todo desde cero.

## A.7 Del JSON a Studio

```text
1. La IA devuelve un bloque JSON y nada mas
2. Guardas el archivo en interfaces/  (por ejemplo temporada3.json)
3. Arrastras el archivo encima de herramientas/revisar_pase.bat
   - no encuentra la clave "rig", asi que lo trata como interfaz
   - roblox_lint.py revisa longitudes, colores y caracteres prohibidos
   - spec_a_rbxmx.py genera temporada3.rbxmx
   - se genera tambien una vista previa PNG para revisar sin abrir Studio
4. Miras el PNG. Si el texto se corta o el color no encaja, corriges el JSON
   y repites. No toques el PNG ni el rbxmx a mano
5. En Studio:
   - clic derecho en StarterGui  >  Insert from File...
   - eliges temporada3.rbxmx
   - aparece un ScreenGui completo con todos los marcos
6. Conectas los botones con el codigo de la Parte B
```

## A.8 Errores del validador de interfaz

| Mensaje | Causa real | Solucion |
|---|---|---|
| Texto demasiado largo | Un campo pasa su limite de la tabla A.4 | Acorta el texto, no subas el limite |
| Color no permitido | Nombre fuera de la paleta de ocho | Usa uno de los ocho nombres |
| Caracter prohibido | Aparece `<`, `>` o `&` | Escribe la palabra: "y" en vez de `&` |
| Faltan niveles | Menos de 2 o mas de 20 | Ajusta la cantidad |
| Lista de premios vacia | `gratis` o `premium` sin elementos | Cada nivel necesita al menos 1 de cada |
| Demasiados premios | Mas de 6 en una lista | Reparte entre mas niveles |
| Campo obligatorio ausente | Falta `etiqueta`, `color`, `titulo`... | Anade el campo |
| Tipo incorrecto | `nuevo` como texto en vez de booleano | Usa `true` o `false` sin comillas |

Si la IA se equivoca, **pidele el JSON completo corregido**. Pegar un fragmento
a mano rompe la estructura y genera errores nuevos.

## A.9 Reglas practicas de diseno

1. **Los limites de caracteres existen por el ancho real del marco.** Un titulo
   de 20 caracteres cabe; uno de 30 se corta aunque el validador lo aceptara.
2. **La etiqueta va en mayusculas** porque el marco la dibuja pequena y en
   minusculas se lee mal.
3. **Usa `nuevo: true` con moderacion.** Si todo es nuevo, nada destaca.
4. **Reparte los colores.** Dorado para monedas, morado para exclusivos, verde
   para mejoras, rojo para cosmeticos agresivos. Mantener un codigo de color
   constante entre temporadas hace la pantalla legible de un vistazo.
5. **El campo `bonus` es el gancho.** Frases cortas del tipo "Exclusivo",
   "+10% velocidad", "Solo temporada".

---

# PARTE B - Interfaz en tiempo de ejecucion

## Indice de la Parte B

| # | Mecanica | Para que |
|---|---|---|
| 1 | ScreenGui y sus propiedades | La base de todo |
| 2 | UDim2, Scale y Offset | Que se vea igual en todas las pantallas |
| 3 | AnchorPoint | Centrar de verdad |
| 4 | Restricciones UI | Layouts sin calcular a mano |
| 5 | Area segura y muescas | Que no se tape en movil |
| 6 | Texto que se adapta | TextScaled y RichText |
| 7 | ScrollingFrame automatico | Listas largas |
| 8 | Tweens en interfaz | Animar sin animaciones |
| 9 | Botones con antirrebote | Evitar dobles clics |
| 10 | Barra de vida y de progreso | El widget mas comun |
| 11 | Enfriamiento circular | Indicador de habilidad |
| 12 | Cola de notificaciones | Avisos sin solaparse |
| 13 | Efecto maquina de escribir | Dialogos |
| 14 | Ventana modal | Confirmaciones |
| 15 | Pestanas | Menus con secciones |
| 16 | Arrastrar y soltar | Inventario |
| 17 | Cuadricula de inventario | Rejilla de objetos |
| 18 | Navegacion con mando | Consola y accesibilidad |
| 19 | ViewportFrame | Modelos 3D dentro de la interfaz |
| 20 | BillboardGui y SurfaceGui | Interfaz en el mundo |
| 21 | Ocultar la interfaz de Roblox | Pantalla limpia |
| 22 | Conectar la interfaz al servidor | Reclamar premios del pase |
| 23 | Reaccionar a datos sin sondear | Attributes y leaderstats |

---

### 1. ScreenGui y sus propiedades

- **Que es:** el contenedor que dibuja interfaz plana sobre la pantalla.
- **API implicada:** `ScreenGui.ResetOnSpawn`, `IgnoreGuiInset`, `DisplayOrder`,
  `ZIndexBehavior`, `Enabled`.

| Propiedad | Recomendado | Motivo |
|---|---|---|
| `ResetOnSpawn` | `false` | Si es true, la interfaz se recrea en cada muerte y pierdes el estado |
| `IgnoreGuiInset` | `true` para fondos a pantalla completa | Ocupa tambien la franja superior de Roblox |
| `DisplayOrder` | numero mayor para lo que va encima | Ordena entre ScreenGui distintos |
| `ZIndexBehavior` | `Sibling` | Comportamiento predecible del apilado |
| `Enabled` | alternar para mostrar u ocultar | Mas barato que destruir y recrear |

- **Donde va:** el ScreenGui en `StarterGui`; el codigo en un LocalScript dentro
  de el.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")
local jugador = Players.LocalPlayer
local playerGui = jugador:WaitForChild("PlayerGui")

local pantalla = Instance.new("ScreenGui")
pantalla.Name = "HUD"
pantalla.ResetOnSpawn = false
pantalla.IgnoreGuiInset = false
pantalla.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
pantalla.DisplayOrder = 10
pantalla.Parent = playerGui

local marco = Instance.new("Frame")
marco.Size = UDim2.fromScale(0.3, 0.08)
marco.Position = UDim2.fromScale(0.5, 0.92)
marco.AnchorPoint = Vector2.new(0.5, 0.5)
marco.BackgroundColor3 = Color3.fromRGB(24, 24, 28)
marco.BackgroundTransparency = 0.15
marco.BorderSizePixel = 0
marco.Parent = pantalla

local esquina = Instance.new("UICorner")
esquina.CornerRadius = UDim.new(0, 10)
esquina.Parent = marco
```

- **Errores frecuentes:**
  - Dejar `ResetOnSpawn` en true y no entender por que la interfaz "se reinicia
    sola". Es el error mas comun de todos.
  - Crear la interfaz en `StarterGui` desde un script y buscarla luego en
    `StarterGui`: en ejecucion vive en `PlayerGui`, no en `StarterGui`.
  - Crear ScreenGui desde el servidor: no se replica al `PlayerGui` como
    esperas.
- **Checklist sin errores:**
  - [ ] `ResetOnSpawn` en false salvo que quieras el reinicio
  - [ ] Se accede via `Players.LocalPlayer.PlayerGui`
  - [ ] La creacion ocurre en un LocalScript

---

### 2. UDim2, Scale y Offset

- **Que es:** el tipo que define tamano y posicion en interfaz.
- **Para que sirve:** que la pantalla se vea bien en un movil de 5 pulgadas y en
  un monitor de 27.

`UDim2.new(escalaX, pixelesX, escalaY, pixelesY)`

| Constructor | Que hace |
|---|---|
| `UDim2.fromScale(0.5, 0.2)` | Mitad del ancho, quinta parte del alto |
| `UDim2.fromOffset(200, 60)` | 200 por 60 pixeles fijos |
| `UDim2.new(0.5, -100, 0, 20)` | Mezcla: mitad menos 100 px |

- **Regla practica:** usa **escala** para lo que debe crecer con la pantalla
  (paneles, fondos, columnas) y **offset** para lo que debe medir siempre igual
  (iconos, bordes, separaciones pequenas).
- **Codigo listo para pegar:**

```lua
-- Panel que ocupa el 40 por ciento del ancho, pero nunca menos de 280 px
local panel = Instance.new("Frame")
panel.Size = UDim2.fromScale(0.4, 0.6)
panel.Position = UDim2.fromScale(0.5, 0.5)
panel.AnchorPoint = Vector2.new(0.5, 0.5)
panel.Parent = pantalla

local limite = Instance.new("UISizeConstraint")
limite.MinSize = Vector2.new(280, 200)
limite.MaxSize = Vector2.new(680, 900)
limite.Parent = panel
```

- **Errores frecuentes:**
  - Todo en offset: en un movil la interfaz se sale de la pantalla; en 4K se ve
    diminuta.
  - Todo en escala: los bordes y los iconos se deforman.
  - Confundir el orden de los argumentos de `UDim2.new`. Si tienes duda, usa
    `fromScale` y `fromOffset`.
- **Checklist sin errores:**
  - [ ] Los paneles usan escala
  - [ ] Los iconos y separaciones usan offset
  - [ ] Hay `UISizeConstraint` donde importa el tamano minimo
  - [ ] Probado en el emulador con un telefono y con una tablet

---

### 3. AnchorPoint

- **Que es:** el punto del elemento que se coloca en la posicion indicada.
- **Para que sirve:** centrar de verdad, anclar a esquinas, escalar desde el
  centro.

| AnchorPoint | Significado |
|---|---|
| `(0, 0)` | Esquina superior izquierda, valor por defecto |
| `(0.5, 0.5)` | Centro |
| `(1, 1)` | Esquina inferior derecha |
| `(0.5, 1)` | Centro abajo, ideal para barras inferiores |

- **Codigo listo para pegar:**

```lua
-- Centrado real, sin calcular la mitad del tamano
boton.AnchorPoint = Vector2.new(0.5, 0.5)
boton.Position = UDim2.fromScale(0.5, 0.5)

-- Anclado a la esquina inferior derecha con 20 px de margen
icono.AnchorPoint = Vector2.new(1, 1)
icono.Position = UDim2.new(1, -20, 1, -20)

-- Crecer desde el centro sin moverse
local TweenService = game:GetService("TweenService")
TweenService:Create(
    boton,
    TweenInfo.new(0.15),
    { Size = UDim2.fromScale(0.24, 0.1) }
):Play()
```

- **Errores frecuentes:**
  - Centrar con `Position = UDim2.fromScale(0.5, 0.5)` y dejar el AnchorPoint en
    `(0, 0)`: el elemento queda desplazado hacia abajo y a la derecha.
  - Animar el tamano con AnchorPoint en `(0, 0)`: el elemento crece hacia una
    esquina en vez de expandirse.
- **Checklist sin errores:**
  - [ ] Todo lo centrado tiene AnchorPoint `(0.5, 0.5)`
  - [ ] Las animaciones de tamano usan AnchorPoint centrado

---

### 4. Restricciones UI

- **Que es:** objetos que colocan y limitan a los hijos automaticamente.
- **Para que sirve:** dejar de calcular posiciones a mano.

| Objeto | Que hace |
|---|---|
| `UIListLayout` | Apila los hijos en fila o columna |
| `UIGridLayout` | Los coloca en cuadricula |
| `UIPageLayout` | Paginas deslizantes |
| `UITableLayout` | Filas y columnas de tabla |
| `UIPadding` | Margen interior |
| `UICorner` | Esquinas redondeadas |
| `UIStroke` | Contorno |
| `UIGradient` | Degradado de color |
| `UIAspectRatioConstraint` | Mantiene la proporcion |
| `UITextSizeConstraint` | Limita el tamano del texto |
| `UISizeConstraint` | Limita el tamano en pixeles |
| `UIScale` | Escala todo el subarbol |

- **Codigo listo para pegar:**

```lua
local lista = Instance.new("Frame")
lista.Size = UDim2.fromScale(0.3, 0.7)
lista.BackgroundTransparency = 1
lista.Parent = pantalla

local orden = Instance.new("UIListLayout")
orden.FillDirection = Enum.FillDirection.Vertical
orden.SortOrder = Enum.SortOrder.LayoutOrder -- no por nombre
orden.Padding = UDim.new(0, 8)
orden.HorizontalAlignment = Enum.HorizontalAlignment.Center
orden.Parent = lista

local margen = Instance.new("UIPadding")
margen.PaddingTop = UDim.new(0, 12)
margen.PaddingBottom = UDim.new(0, 12)
margen.PaddingLeft = UDim.new(0, 12)
margen.PaddingRight = UDim.new(0, 12)
margen.Parent = lista

for i = 1, 5 do
    local fila = Instance.new("TextLabel")
    fila.Size = UDim2.new(1, 0, 0, 44)
    fila.LayoutOrder = i -- lo que decide el orden
    fila.Text = "Elemento " .. i
    fila.TextScaled = true
    fila.BackgroundColor3 = Color3.fromRGB(34, 34, 40)
    fila.TextColor3 = Color3.fromRGB(235, 235, 240)
    fila.BorderSizePixel = 0
    fila.Parent = lista

    local r = Instance.new("UICorner")
    r.CornerRadius = UDim.new(0, 8)
    r.Parent = fila
end
```

- **Errores frecuentes:**
  - `SortOrder` en `Name`: los elementos se ordenan alfabeticamente y el 10 va
    antes del 2. Usa `LayoutOrder`.
  - Poner `Position` a los hijos de un `UIListLayout`: se ignora y confunde.
  - `UIListLayout` con hijos de tamano en escala vertical dentro de un
    `ScrollingFrame`: el alto se calcula mal. Usa offset para el alto de las
    filas.
- **Checklist sin errores:**
  - [ ] `SortOrder` es `LayoutOrder`
  - [ ] Cada hijo tiene su `LayoutOrder` asignado
  - [ ] No se asignan posiciones manuales dentro de un layout

---

### 5. Area segura y muescas

- **Que es:** la zona de pantalla que ningun elemento del sistema tapa.
- **Para que sirve:** que el boton importante no quede debajo de la muesca del
  telefono ni del boton de Roblox.
- **API implicada:** `GuiService:GetGuiInset()`, `ScreenGui.IgnoreGuiInset`,
  `ScreenGui.SafeAreaCompatibility`, `ScreenGui.ScreenInsets`.
- **Codigo listo para pegar:**

```lua
local GuiService = game:GetService("GuiService")

-- franja superior que ocupa la barra de Roblox
local superior, inferior = GuiService:GetGuiInset()
print("Franja superior:", superior.Y, "px")

local pantalla = Instance.new("ScreenGui")
pantalla.IgnoreGuiInset = false -- respeta la franja
pantalla.ScreenInsets = Enum.ScreenInsets.DeviceSafeInsets
pantalla.Parent = playerGui

-- Botones importantes: nunca en la esquina superior izquierda,
-- que es donde estan el menu de Roblox y el chat
local accion = Instance.new("TextButton")
accion.AnchorPoint = Vector2.new(1, 1)
accion.Position = UDim2.new(1, -24, 1, -140) -- por encima del joystick movil
accion.Size = UDim2.fromOffset(96, 96)
accion.Parent = pantalla
```

- **Errores frecuentes:**
  - Poner algo en la esquina superior izquierda: el menu de Roblox lo tapa.
  - Poner botones en la esquina inferior izquierda: el joystick virtual de movil
    esta ahi.
  - Probar solo en la ventana de Studio a resolucion de escritorio.
- **Checklist sin errores:**
  - [ ] Nada importante en la esquina superior izquierda
  - [ ] Nada importante en la esquina inferior izquierda
  - [ ] `ScreenInsets` configurado para dispositivos con muesca
  - [ ] Probado en el emulador con iPhone y con tablet

---

### 6. Texto que se adapta

- **Que es:** texto que cambia de tamano solo y admite formato.
- **API implicada:** `TextLabel.TextScaled`, `TextWrapped`, `RichText`,
  `TextTruncate`, `UITextSizeConstraint`.
- **Codigo listo para pegar:**

```lua
local titulo = Instance.new("TextLabel")
titulo.Size = UDim2.fromScale(1, 0.2)
titulo.BackgroundTransparency = 1
titulo.TextScaled = true      -- se adapta al marco
titulo.TextWrapped = true     -- salta de linea
titulo.RichText = true        -- admite etiquetas de formato
titulo.Font = Enum.Font.GothamBold
titulo.TextColor3 = Color3.fromRGB(240, 240, 245)
titulo.Text = 'Entrega <font color="rgb(255,190,80)">urgente</font> en <b>60</b> segundos'
titulo.Parent = pantalla

-- Con TextScaled activo, limita el tamano para que no se vuelva gigante
local limite = Instance.new("UITextSizeConstraint")
limite.MinTextSize = 12
limite.MaxTextSize = 34
limite.Parent = titulo

-- Cortar con puntos suspensivos en vez de encoger
local nombre = Instance.new("TextLabel")
nombre.TextScaled = false
nombre.TextSize = 18
nombre.TextTruncate = Enum.TextTruncate.AtEnd
nombre.Parent = pantalla
```

- **Errores frecuentes:**
  - `TextScaled` sin `UITextSizeConstraint`: en pantallas grandes el texto se
    vuelve enorme y desproporcionado.
  - `RichText` con texto que viene del jugador: alguien escribe una etiqueta y
    rompe el formato o inyecta contenido. **Nunca** pongas `RichText = true` en
    una etiqueta que muestre texto escrito por usuarios.
  - `TextWrapped` en false con texto largo: se sale del marco.
- **Checklist sin errores:**
  - [ ] `TextScaled` acompanado de `UITextSizeConstraint`
  - [ ] `RichText` desactivado en texto de jugadores
  - [ ] El texto largo tiene `TextWrapped` o `TextTruncate`

---

### 7. ScrollingFrame automatico

- **Que es:** un marco con desplazamiento cuyo lienzo se ajusta al contenido.
- **Para que sirve:** listas de premios, inventarios, tablas de clasificacion.
- **API implicada:** `ScrollingFrame.AutomaticCanvasSize`, `CanvasSize`,
  `ScrollBarThickness`, `ScrollingDirection`, `ElasticBehavior`.
- **Codigo listo para pegar:**

```lua
local scroll = Instance.new("ScrollingFrame")
scroll.Size = UDim2.fromScale(0.4, 0.7)
scroll.Position = UDim2.fromScale(0.5, 0.5)
scroll.AnchorPoint = Vector2.new(0.5, 0.5)
scroll.BackgroundColor3 = Color3.fromRGB(20, 20, 24)
scroll.BorderSizePixel = 0
scroll.ScrollBarThickness = 6
scroll.ScrollingDirection = Enum.ScrollingDirection.Y
scroll.AutomaticCanvasSize = Enum.AutomaticSize.Y -- clave
scroll.CanvasSize = UDim2.new()                   -- se calcula solo
scroll.Parent = pantalla

local orden = Instance.new("UIListLayout")
orden.SortOrder = Enum.SortOrder.LayoutOrder
orden.Padding = UDim.new(0, 6)
orden.Parent = scroll

local margen = Instance.new("UIPadding")
margen.PaddingTop = UDim.new(0, 8)
margen.PaddingBottom = UDim.new(0, 8)
margen.Parent = scroll

for i = 1, 40 do
    local fila = Instance.new("TextLabel")
    fila.Size = UDim2.new(1, -16, 0, 40) -- ancho relativo, ALTO EN OFFSET
    fila.LayoutOrder = i
    fila.Text = "Nivel " .. i
    fila.TextScaled = true
    fila.BackgroundColor3 = Color3.fromRGB(32, 32, 38)
    fila.TextColor3 = Color3.fromRGB(230, 230, 235)
    fila.BorderSizePixel = 0
    fila.Parent = scroll
end
```

- **Errores frecuentes:**
  - `CanvasSize` fijo y contenido mas largo: no se puede llegar al final.
  - Hijos con alto en escala dentro de un scroll con
    `AutomaticCanvasSize = Y`: el calculo se vuelve circular y el lienzo queda
    en cero. **El alto de las filas debe ir en offset.**
  - `ScrollBarThickness` en 0 y sin gesto tactil: en movil no se puede
    desplazar.
- **Checklist sin errores:**
  - [ ] `AutomaticCanvasSize` activado en el eje correcto
  - [ ] Las filas tienen alto en offset
  - [ ] Hay `UIPadding` para que la ultima fila no quede pegada al borde
  - [ ] Probado con muchos elementos y con uno solo

---

### 8. Tweens en interfaz

- **Que es:** animar propiedades de la interfaz de forma suave.
- **Para que sirve:** que la interfaz se sienta viva sin usar animaciones de
  personaje.
- **API implicada:** `TweenService:Create`, `TweenInfo`, `Tween.Completed`,
  `Cancel`.
- **Codigo listo para pegar:**

```lua
local TweenService = game:GetService("TweenService")

local ENTRADA = TweenInfo.new(0.32, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
local SALIDA = TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.In)

local tweenActivo: Tween? = nil

local function mostrar(panel: GuiObject)
    if tweenActivo then
        tweenActivo:Cancel()
    end
    panel.Visible = true
    panel.Size = UDim2.fromScale(0, 0)
    tweenActivo = TweenService:Create(panel, ENTRADA, {
        Size = UDim2.fromScale(0.45, 0.6),
    })
    tweenActivo:Play()
end

local function ocultar(panel: GuiObject)
    if tweenActivo then
        tweenActivo:Cancel()
    end
    tweenActivo = TweenService:Create(panel, SALIDA, {
        Size = UDim2.fromScale(0, 0),
    })
    tweenActivo.Completed:Connect(function(estado)
        if estado == Enum.PlaybackState.Completed then
            panel.Visible = false
        end
    end)
    tweenActivo:Play()
end
```

| Estilo | Cuando usarlo |
|---|---|
| `Quad` con `Out` | Entradas y salidas normales |
| `Back` con `Out` | Paneles que aparecen con un rebote elegante |
| `Elastic` | Recompensas, celebraciones |
| `Linear` | Barras de progreso y temporizadores |

- **Errores frecuentes:**
  - Lanzar un tween nuevo sobre la misma propiedad sin cancelar el anterior: los
    dos pelean y el elemento tiembla.
  - Poner `Visible = false` sin esperar a que acabe el tween: desaparece de
    golpe.
  - Animar `Position` de algo con AnchorPoint `(0, 0)` esperando un efecto
    centrado.
  - Duraciones de mas de 0.5 s en interfaz: se siente lenta.
- **Checklist sin errores:**
  - [ ] El tween anterior se cancela
  - [ ] `Visible = false` se aplica en `Completed`
  - [ ] Las duraciones estan por debajo de 0.5 s

---

### 9. Botones con antirrebote

- **Que es:** impedir que un boton se active varias veces seguidas.
- **Para que sirve:** evitar comprar dos veces, enviar dos remotes, duplicar
  premios.
- **API implicada:** `TextButton.Activated` no existe: se usa
  `MouseButton1Click` o `Activated` de `GuiButton`, mas `AutoButtonColor` y
  `Active`.
- **Codigo listo para pegar:**

```lua
local TweenService = game:GetService("TweenService")

local function conectarBoton(boton: GuiButton, enfriamiento: number, accion: () -> ())
    local ocupado = false

    boton.AutoButtonColor = false

    boton.MouseEnter:Connect(function()
        if ocupado then
            return
        end
        TweenService:Create(boton, TweenInfo.new(0.1), {
            BackgroundColor3 = Color3.fromRGB(70, 130, 220),
        }):Play()
    end)

    boton.MouseLeave:Connect(function()
        TweenService:Create(boton, TweenInfo.new(0.1), {
            BackgroundColor3 = Color3.fromRGB(45, 95, 175),
        }):Play()
    end)

    boton.Activated:Connect(function()
        if ocupado then
            return
        end
        ocupado = true
        boton.Active = false
        boton.BackgroundTransparency = 0.45

        local ok, err = pcall(accion)
        if not ok then
            warn("Fallo la accion del boton " .. boton.Name .. ": " .. tostring(err))
        end

        task.wait(enfriamiento)

        if boton.Parent then
            ocupado = false
            boton.Active = true
            boton.BackgroundTransparency = 0
        end
    end)
end

return conectarBoton
```

- **Errores frecuentes:**
  - Sin antirrebote: el jugador hace doble clic y envia dos peticiones. Aunque el
    servidor valide, la interfaz se ve mal.
  - `Activated` no se dispara si `Active` esta en false: recuerda restaurarlo.
  - No envolver la accion en `pcall`: si falla, el boton queda bloqueado para
    siempre.
  - Usar `MouseButton1Click`: no funciona con mando ni con toque en algunos
    casos. `Activated` cubre raton, toque y mando.
- **Checklist sin errores:**
  - [ ] Hay antirrebote y se libera siempre
  - [ ] La accion esta en `pcall`
  - [ ] Se usa `Activated`
  - [ ] El servidor tambien valida, la interfaz no es la seguridad

---

### 10. Barra de vida y de progreso

- **Que es:** el widget mas usado de todos.
- **API implicada:** `Frame.Size` con `UDim2`, `TweenService`, `Color3:Lerp`.
- **Codigo listo para pegar:**

```lua
local TweenService = game:GetService("TweenService")
local Players = game:GetService("Players")

local jugador = Players.LocalPlayer

local fondo = Instance.new("Frame")
fondo.Size = UDim2.fromOffset(260, 22)
fondo.Position = UDim2.new(0.5, 0, 1, -60)
fondo.AnchorPoint = Vector2.new(0.5, 1)
fondo.BackgroundColor3 = Color3.fromRGB(18, 18, 22)
fondo.BorderSizePixel = 0
fondo.Parent = pantalla

local r1 = Instance.new("UICorner")
r1.CornerRadius = UDim.new(1, 0)
r1.Parent = fondo

local relleno = Instance.new("Frame")
relleno.Size = UDim2.fromScale(1, 1)
relleno.BackgroundColor3 = Color3.fromRGB(70, 210, 110)
relleno.BorderSizePixel = 0
relleno.Parent = fondo

local r2 = Instance.new("UICorner")
r2.CornerRadius = UDim.new(1, 0)
r2.Parent = relleno

local texto = Instance.new("TextLabel")
texto.Size = UDim2.fromScale(1, 1)
texto.BackgroundTransparency = 1
texto.TextScaled = true
texto.Font = Enum.Font.GothamBold
texto.TextColor3 = Color3.new(1, 1, 1)
texto.ZIndex = 2
texto.Parent = fondo

local INFO = TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)

local function actualizar(actual: number, maximo: number)
    local fraccion = maximo > 0 and math.clamp(actual / maximo, 0, 1) or 0

    -- rojo cuando queda poco, verde cuando esta lleno
    local color = Color3.fromRGB(220, 60, 60):Lerp(Color3.fromRGB(70, 210, 110), fraccion)

    TweenService:Create(relleno, INFO, {
        Size = UDim2.fromScale(fraccion, 1),
        BackgroundColor3 = color,
    }):Play()

    texto.Text = math.floor(actual + 0.5) .. " / " .. math.floor(maximo + 0.5)
end

local function vigilar(personaje: Model)
    local hum = personaje:WaitForChild("Humanoid", 10) :: Humanoid?
    if not hum then
        return
    end

    actualizar(hum.Health, hum.MaxHealth)

    hum:GetPropertyChangedSignal("Health"):Connect(function()
        actualizar(hum.Health, hum.MaxHealth)
    end)
    hum:GetPropertyChangedSignal("MaxHealth"):Connect(function()
        actualizar(hum.Health, hum.MaxHealth)
    end)
end

if jugador.Character then
    vigilar(jugador.Character)
end
jugador.CharacterAdded:Connect(vigilar)
```

- **Errores frecuentes:**
  - Dividir por `MaxHealth` sin comprobar que no es cero: error de division y
    barra en `nan`.
  - No acotar la fraccion: si algo cura por encima del maximo, la barra se sale
    del marco.
  - Sondear la vida cada frame en vez de usar `GetPropertyChangedSignal`.
  - Olvidar `CharacterAdded`: la barra deja de funcionar al morir.
- **Checklist sin errores:**
  - [ ] La fraccion esta acotada entre 0 y 1
  - [ ] Se comprueba que `MaxHealth` no es cero
  - [ ] Se usa `GetPropertyChangedSignal`
  - [ ] Se reconecta en `CharacterAdded`

---

### 11. Enfriamiento circular

- **Que es:** un indicador que se vacia mientras la habilidad se recarga.
- **API implicada:** `ImageLabel` con `UIGradient` rotatorio, o dos mitades con
  `ClipsDescendants`. La via mas simple es una barra radial con `ImageLabel` y
  `ImageTransparency`.
- **Codigo listo para pegar:**

```lua
local RunService = game:GetService("RunService")

local function crearEnfriamiento(padre: Instance)
    local marco = Instance.new("Frame")
    marco.Size = UDim2.fromOffset(64, 64)
    marco.BackgroundColor3 = Color3.fromRGB(28, 28, 34)
    marco.BorderSizePixel = 0
    marco.ClipsDescendants = true
    marco.Parent = padre

    local r = Instance.new("UICorner")
    r.CornerRadius = UDim.new(0, 10)
    r.Parent = marco

    local velo = Instance.new("Frame")
    velo.Name = "Velo"
    velo.AnchorPoint = Vector2.new(0, 1)
    velo.Position = UDim2.fromScale(0, 1)
    velo.Size = UDim2.fromScale(1, 0)
    velo.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
    velo.BackgroundTransparency = 0.45
    velo.BorderSizePixel = 0
    velo.ZIndex = 3
    velo.Parent = marco

    local numero = Instance.new("TextLabel")
    numero.Size = UDim2.fromScale(1, 1)
    numero.BackgroundTransparency = 1
    numero.TextScaled = true
    numero.Font = Enum.Font.GothamBold
    numero.TextColor3 = Color3.new(1, 1, 1)
    numero.ZIndex = 4
    numero.Text = ""
    numero.Parent = marco

    local conexion: RBXScriptConnection? = nil

    local function iniciar(duracion: number)
        if conexion then
            conexion:Disconnect()
        end

        local inicio = os.clock()

        conexion = RunService.RenderStepped:Connect(function()
            local pasado = os.clock() - inicio
            local restante = duracion - pasado

            if restante <= 0 then
                velo.Size = UDim2.fromScale(1, 0)
                numero.Text = ""
                if conexion then
                    conexion:Disconnect()
                    conexion = nil
                end
                return
            end

            velo.Size = UDim2.fromScale(1, restante / duracion)
            numero.Text = string.format("%.1f", restante)
        end)
    end

    return { marco = marco, iniciar = iniciar }
end

return crearEnfriamiento
```

- **Errores frecuentes:**
  - No desconectar el bucle anterior al reiniciar el enfriamiento: dos bucles
    peleando por el mismo velo.
  - Usar `task.wait` en un bucle en vez de `RenderStepped`: el numero salta.
  - Confiar en este contador para bloquear la habilidad: es solo visual, el
    enfriamiento real vive en el servidor.
- **Checklist sin errores:**
  - [ ] El bucle anterior se desconecta
  - [ ] El bucle se desconecta al terminar
  - [ ] El servidor tiene su propio enfriamiento

---

### 12. Cola de notificaciones

- **Que es:** avisos que aparecen uno detras de otro sin solaparse.
- **API implicada:** `UIListLayout`, `TweenService`, tabla como cola.
- **Codigo listo para pegar:**

```lua
local TweenService = game:GetService("TweenService")

local contenedor = Instance.new("Frame")
contenedor.AnchorPoint = Vector2.new(1, 0)
contenedor.Position = UDim2.new(1, -20, 0, 80)
contenedor.Size = UDim2.fromOffset(300, 400)
contenedor.BackgroundTransparency = 1
contenedor.Parent = pantalla

local orden = Instance.new("UIListLayout")
orden.SortOrder = Enum.SortOrder.LayoutOrder
orden.VerticalAlignment = Enum.VerticalAlignment.Top
orden.Padding = UDim.new(0, 8)
orden.Parent = contenedor

local MAXIMO_VISIBLE = 4
local contador = 0
local activas = 0
local cola: { { texto: string, color: Color3 } } = {}

local function dibujar(texto: string, color: Color3)
    contador += 1
    activas += 1

    local aviso = Instance.new("TextLabel")
    aviso.Size = UDim2.new(1, 0, 0, 44)
    aviso.LayoutOrder = contador
    aviso.BackgroundColor3 = color
    aviso.TextColor3 = Color3.new(1, 1, 1)
    aviso.Font = Enum.Font.GothamMedium
    aviso.TextScaled = true
    aviso.Text = texto
    aviso.BorderSizePixel = 0
    aviso.BackgroundTransparency = 1
    aviso.TextTransparency = 1
    aviso.Parent = contenedor

    local r = Instance.new("UICorner")
    r.CornerRadius = UDim.new(0, 8)
    r.Parent = aviso

    TweenService:Create(aviso, TweenInfo.new(0.2), {
        BackgroundTransparency = 0.1,
        TextTransparency = 0,
    }):Play()

    task.delay(3, function()
        local salida = TweenService:Create(aviso, TweenInfo.new(0.25), {
            BackgroundTransparency = 1,
            TextTransparency = 1,
        })
        salida.Completed:Connect(function()
            aviso:Destroy()
            activas -= 1

            local siguiente = table.remove(cola, 1)
            if siguiente then
                dibujar(siguiente.texto, siguiente.color)
            end
        end)
        salida:Play()
    end)
end

local function notificar(texto: string, color: Color3?)
    local c = color or Color3.fromRGB(45, 95, 175)
    if activas >= MAXIMO_VISIBLE then
        table.insert(cola, { texto = texto, color = c })
        return
    end
    dibujar(texto, c)
end

return notificar
```

- **Errores frecuentes:**
  - Sin limite: cien notificaciones a la vez llenan la pantalla.
  - No destruir los avisos: se acumulan miles de instancias.
  - `LayoutOrder` siempre igual: el orden se vuelve aleatorio.
- **Checklist sin errores:**
  - [ ] Hay un maximo visible y una cola
  - [ ] Cada aviso se destruye al terminar
  - [ ] El `LayoutOrder` es creciente

---

### 13. Efecto maquina de escribir

- **Que es:** mostrar el texto letra a letra.
- **API implicada:** `TextLabel.MaxVisibleGraphemes`, `utf8.len`.
- **Codigo listo para pegar:**

```lua
local function escribir(etiqueta: TextLabel, texto: string, porSegundo: number)
    etiqueta.Text = texto
    etiqueta.MaxVisibleGraphemes = 0

    local total = utf8.len(texto) or #texto
    local inicio = os.clock()
    local terminado = false

    local conexion
    conexion = game:GetService("RunService").RenderStepped:Connect(function()
        if terminado or not etiqueta.Parent then
            conexion:Disconnect()
            return
        end

        local visibles = math.floor((os.clock() - inicio) * porSegundo)
        if visibles >= total then
            etiqueta.MaxVisibleGraphemes = -1 -- todo visible
            terminado = true
            conexion:Disconnect()
            return
        end

        etiqueta.MaxVisibleGraphemes = visibles
    end)

    return function()
        -- saltar el efecto
        terminado = true
        etiqueta.MaxVisibleGraphemes = -1
    end
end

return escribir
```

- **Errores frecuentes:**
  - Construir el texto con `string.sub` letra a letra: rompe los acentos y los
    emojis, porque un caracter puede ocupar varios bytes.
    `MaxVisibleGraphemes` es la forma correcta.
  - No ofrecer forma de saltar el dialogo.
  - No desconectar el bucle si la etiqueta se destruye a mitad.
- **Checklist sin errores:**
  - [ ] Se usa `MaxVisibleGraphemes`, no `string.sub`
  - [ ] Hay forma de saltar
  - [ ] El bucle se desconecta siempre

---

### 14. Ventana modal

- **Que es:** un panel que bloquea el resto de la interfaz hasta responder.
- **API implicada:** `Frame` de fondo con `Active = true`, `ZIndex`,
  `UserInputService.MouseBehavior`, `GuiService.SelectedObject`.
- **Codigo listo para pegar:**

```lua
local UserInputService = game:GetService("UserInputService")

local function confirmar(titulo: string, mensaje: string): boolean
    local velo = Instance.new("Frame")
    velo.Size = UDim2.fromScale(1, 1)
    velo.BackgroundColor3 = Color3.new(0, 0, 0)
    velo.BackgroundTransparency = 0.5
    velo.BorderSizePixel = 0
    velo.ZIndex = 100
    velo.Active = true -- bloquea los clics de lo que hay debajo
    velo.Parent = pantalla

    local panel = Instance.new("Frame")
    panel.Size = UDim2.fromOffset(360, 200)
    panel.Position = UDim2.fromScale(0.5, 0.5)
    panel.AnchorPoint = Vector2.new(0.5, 0.5)
    panel.BackgroundColor3 = Color3.fromRGB(26, 26, 32)
    panel.BorderSizePixel = 0
    panel.ZIndex = 101
    panel.Parent = velo

    local r = Instance.new("UICorner")
    r.CornerRadius = UDim.new(0, 12)
    r.Parent = panel

    local cabecera = Instance.new("TextLabel")
    cabecera.Size = UDim2.new(1, -24, 0, 40)
    cabecera.Position = UDim2.fromOffset(12, 12)
    cabecera.BackgroundTransparency = 1
    cabecera.Font = Enum.Font.GothamBold
    cabecera.TextScaled = true
    cabecera.TextColor3 = Color3.new(1, 1, 1)
    cabecera.Text = titulo
    cabecera.ZIndex = 102
    cabecera.Parent = panel

    local cuerpo = Instance.new("TextLabel")
    cuerpo.Size = UDim2.new(1, -24, 0, 70)
    cuerpo.Position = UDim2.fromOffset(12, 56)
    cuerpo.BackgroundTransparency = 1
    cuerpo.Font = Enum.Font.Gotham
    cuerpo.TextScaled = true
    cuerpo.TextWrapped = true
    cuerpo.TextColor3 = Color3.fromRGB(200, 200, 210)
    cuerpo.Text = mensaje
    cuerpo.ZIndex = 102
    cuerpo.Parent = panel

    local function crearBoton(texto: string, x: number, color: Color3)
        local b = Instance.new("TextButton")
        b.Size = UDim2.fromOffset(150, 42)
        b.Position = UDim2.fromOffset(x, 140)
        b.BackgroundColor3 = color
        b.TextColor3 = Color3.new(1, 1, 1)
        b.Font = Enum.Font.GothamBold
        b.TextScaled = true
        b.Text = texto
        b.BorderSizePixel = 0
        b.ZIndex = 102
        b.Parent = panel

        local rr = Instance.new("UICorner")
        rr.CornerRadius = UDim.new(0, 8)
        rr.Parent = b
        return b
    end

    local si = crearBoton("Confirmar", 14, Color3.fromRGB(50, 150, 90))
    local no = crearBoton("Cancelar", 190, Color3.fromRGB(120, 50, 50))

    -- libera el raton por si estaba bloqueado en primera persona
    local comportamientoPrevio = UserInputService.MouseBehavior
    UserInputService.MouseBehavior = Enum.MouseBehavior.Default

    local respuesta: boolean? = nil
    si.Activated:Connect(function()
        respuesta = true
    end)
    no.Activated:Connect(function()
        respuesta = false
    end)

    while respuesta == nil and velo.Parent do
        task.wait()
    end

    UserInputService.MouseBehavior = comportamientoPrevio
    velo:Destroy()

    return respuesta == true
end

return confirmar
```

- **Errores frecuentes:**
  - Velo sin `Active = true`: se puede hacer clic en los botones de detras.
  - No liberar el raton: en primera persona el jugador no puede pulsar nada.
  - Bucle de espera sin comprobar que el velo sigue existiendo: se cuelga si el
    jugador muere y la interfaz se reinicia.
- **Checklist sin errores:**
  - [ ] El velo tiene `Active = true` y `ZIndex` alto
  - [ ] El raton se libera y se restaura
  - [ ] El bucle de espera tiene salida

---

### 15. Pestanas

- **Que es:** un menu con secciones que se alternan.
- **API implicada:** tabla de paneles, `Visible`, `UIListLayout` horizontal.
- **Codigo listo para pegar:**

```lua
local function crearPestanas(padre: Instance, nombres: { string })
    local barra = Instance.new("Frame")
    barra.Size = UDim2.new(1, 0, 0, 44)
    barra.BackgroundTransparency = 1
    barra.Parent = padre

    local orden = Instance.new("UIListLayout")
    orden.FillDirection = Enum.FillDirection.Horizontal
    orden.SortOrder = Enum.SortOrder.LayoutOrder
    orden.Padding = UDim.new(0, 6)
    orden.Parent = barra

    local paneles: { [string]: Frame } = {}
    local botones: { [string]: TextButton } = {}

    local function seleccionar(nombre: string)
        for otro, panel in paneles do
            panel.Visible = (otro == nombre)
            botones[otro].BackgroundColor3 = (otro == nombre)
                and Color3.fromRGB(60, 120, 210)
                or Color3.fromRGB(38, 38, 46)
        end
    end

    for i, nombre in nombres do
        local boton = Instance.new("TextButton")
        boton.Size = UDim2.fromOffset(120, 40)
        boton.LayoutOrder = i
        boton.Text = nombre
        boton.Font = Enum.Font.GothamMedium
        boton.TextScaled = true
        boton.TextColor3 = Color3.new(1, 1, 1)
        boton.BorderSizePixel = 0
        boton.Parent = barra

        local r = Instance.new("UICorner")
        r.CornerRadius = UDim.new(0, 8)
        r.Parent = boton

        local panel = Instance.new("Frame")
        panel.Size = UDim2.new(1, 0, 1, -50)
        panel.Position = UDim2.fromOffset(0, 50)
        panel.BackgroundColor3 = Color3.fromRGB(22, 22, 28)
        panel.BorderSizePixel = 0
        panel.Visible = false
        panel.Parent = padre

        local r2 = Instance.new("UICorner")
        r2.CornerRadius = UDim.new(0, 10)
        r2.Parent = panel

        paneles[nombre] = panel
        botones[nombre] = boton

        boton.Activated:Connect(function()
            seleccionar(nombre)
        end)
    end

    if nombres[1] then
        seleccionar(nombres[1])
    end

    return { paneles = paneles, seleccionar = seleccionar }
end

return crearPestanas
```

- **Errores frecuentes:**
  - Destruir y recrear el contenido de la pestana en cada cambio: lento y se
    pierde el estado. Usa `Visible`.
  - No marcar visualmente la pestana activa.
  - No seleccionar ninguna al abrir: pantalla en blanco.
- **Checklist sin errores:**
  - [ ] Se alterna con `Visible`, no destruyendo
  - [ ] La pestana activa se distingue
  - [ ] Hay una seleccionada al abrir

---

### 16. Arrastrar y soltar

- **Que es:** mover un elemento con el dedo o el raton y soltarlo en una casilla.
- **API implicada:** `GuiObject.InputBegan`, `InputChanged`, `InputEnded`,
  `UserInputService`, `GuiObject.AbsolutePosition`, `AbsoluteSize`.
- **Codigo listo para pegar:**

```lua
local UserInputService = game:GetService("UserInputService")

local function hacerArrastrable(objeto: GuiObject, casillas: { GuiObject }, alSoltar: (GuiObject?) -> ())
    local arrastrando = false
    local desplazamiento = Vector2.zero
    local posicionOriginal = objeto.Position
    local padreOriginal = objeto.Parent
    local zOriginal = objeto.ZIndex

    local function dentroDe(casilla: GuiObject, punto: Vector2): boolean
        local p = casilla.AbsolutePosition
        local s = casilla.AbsoluteSize
        return punto.X >= p.X and punto.X <= p.X + s.X
            and punto.Y >= p.Y and punto.Y <= p.Y + s.Y
    end

    objeto.InputBegan:Connect(function(input)
        if input.UserInputType ~= Enum.UserInputType.MouseButton1
            and input.UserInputType ~= Enum.UserInputType.Touch
        then
            return
        end

        arrastrando = true
        posicionOriginal = objeto.Position
        padreOriginal = objeto.Parent
        objeto.ZIndex = 200

        local punto = Vector2.new(input.Position.X, input.Position.Y)
        desplazamiento = punto - objeto.AbsolutePosition
    end)

    UserInputService.InputChanged:Connect(function(input)
        if not arrastrando then
            return
        end
        if input.UserInputType ~= Enum.UserInputType.MouseMovement
            and input.UserInputType ~= Enum.UserInputType.Touch
        then
            return
        end

        local punto = Vector2.new(input.Position.X, input.Position.Y) - desplazamiento
        objeto.Position = UDim2.fromOffset(punto.X, punto.Y)
    end)

    UserInputService.InputEnded:Connect(function(input)
        if not arrastrando then
            return
        end
        if input.UserInputType ~= Enum.UserInputType.MouseButton1
            and input.UserInputType ~= Enum.UserInputType.Touch
        then
            return
        end

        arrastrando = false
        objeto.ZIndex = zOriginal

        local punto = Vector2.new(input.Position.X, input.Position.Y)
        local destino: GuiObject? = nil
        for _, casilla in casillas do
            if dentroDe(casilla, punto) then
                destino = casilla
                break
            end
        end

        if destino then
            objeto.Parent = destino
            objeto.Position = UDim2.fromScale(0, 0)
        else
            objeto.Parent = padreOriginal
            objeto.Position = posicionOriginal
        end

        alSoltar(destino)
    end)
end

return hacerArrastrable
```

- **Errores frecuentes:**
  - Usar solo `MouseButton1`: no funciona en movil. Hay que aceptar `Touch`.
  - No devolver el objeto a su sitio si se suelta fuera: queda flotando.
  - No subir el `ZIndex` al arrastrar: el objeto pasa por detras de los demas.
  - Aplicar el cambio de inventario solo en el cliente: el servidor debe
    confirmar el movimiento.
- **Checklist sin errores:**
  - [ ] Se aceptan raton y toque
  - [ ] Si se suelta fuera, vuelve a su posicion
  - [ ] El `ZIndex` se sube y se restaura
  - [ ] El servidor valida el cambio real

---

### 17. Cuadricula de inventario

- **Que es:** una rejilla de casillas que se rellenan con objetos.
- **API implicada:** `UIGridLayout`, `CellSize`, `CellPadding`,
  `UIAspectRatioConstraint`.
- **Codigo listo para pegar:**

```lua
local function crearRejilla(padre: Instance, filas: number, columnas: number)
    local marco = Instance.new("Frame")
    marco.Size = UDim2.fromScale(0.5, 0.6)
    marco.Position = UDim2.fromScale(0.5, 0.5)
    marco.AnchorPoint = Vector2.new(0.5, 0.5)
    marco.BackgroundColor3 = Color3.fromRGB(20, 20, 26)
    marco.BorderSizePixel = 0
    marco.Parent = padre

    local proporcion = Instance.new("UIAspectRatioConstraint")
    proporcion.AspectRatio = columnas / filas
    proporcion.Parent = marco

    local rejilla = Instance.new("UIGridLayout")
    rejilla.CellSize = UDim2.fromScale(1 / columnas - 0.012, 1 / filas - 0.012)
    rejilla.CellPadding = UDim2.fromScale(0.012, 0.012)
    rejilla.SortOrder = Enum.SortOrder.LayoutOrder
    rejilla.Parent = marco

    local margen = Instance.new("UIPadding")
    margen.PaddingTop = UDim.new(0, 8)
    margen.PaddingLeft = UDim.new(0, 8)
    margen.Parent = marco

    local casillas: { Frame } = {}

    for i = 1, filas * columnas do
        local casilla = Instance.new("Frame")
        casilla.Name = "Casilla" .. i
        casilla.LayoutOrder = i
        casilla.BackgroundColor3 = Color3.fromRGB(34, 34, 42)
        casilla.BorderSizePixel = 0
        casilla.Parent = marco

        local r = Instance.new("UICorner")
        r.CornerRadius = UDim.new(0, 6)
        r.Parent = casilla

        table.insert(casillas, casilla)
    end

    return marco, casillas
end

return crearRejilla
```

- **Errores frecuentes:**
  - `CellSize` en escala sin `UIAspectRatioConstraint`: las casillas se
    deforman a rectangulos raros al cambiar la ventana.
  - No sumar el `CellPadding` al calcular el tamano: la ultima columna se sale.
  - Crear las casillas en cada apertura del inventario: crealas una vez y
    reutilizalas.
- **Checklist sin errores:**
  - [ ] Hay `UIAspectRatioConstraint` para que las casillas sean cuadradas
  - [ ] El padding esta descontado del `CellSize`
  - [ ] Las casillas se crean una sola vez

---

### 18. Navegacion con mando

- **Que es:** poder recorrer la interfaz con la cruceta y el joystick.
- **Para que sirve:** consola, y tambien accesibilidad en PC.
- **API implicada:** `GuiObject.Selectable`, `NextSelectionUp`,
  `NextSelectionDown`, `NextSelectionLeft`, `NextSelectionRight`,
  `GuiService.SelectedObject`, `GuiService:Select`.
- **Codigo listo para pegar:**

```lua
local GuiService = game:GetService("GuiService")

local function encadenarVertical(botones: { GuiButton })
    for i, boton in botones do
        boton.Selectable = true
        boton.SelectionImageObject = nil -- puedes poner un marco propio

        local anterior = botones[i - 1]
        local siguiente = botones[i + 1]

        boton.NextSelectionUp = anterior or botones[#botones]
        boton.NextSelectionDown = siguiente or botones[1]
    end
end

local function abrirMenu(panel: Frame, primerBoton: GuiButton, botones: { GuiButton })
    encadenarVertical(botones)
    panel.Visible = true
    GuiService.SelectedObject = primerBoton -- el mando entra en el menu
end

local function cerrarMenu(panel: Frame)
    panel.Visible = false
    GuiService.SelectedObject = nil -- devuelve el control al juego
end

return { abrir = abrirMenu, cerrar = cerrarMenu }
```

- **Errores frecuentes:**
  - Dejar `GuiService.SelectedObject` apuntando a un boton de un panel oculto:
    el mando queda atrapado y el jugador no puede moverse.
  - No poner `Selectable = true`: el mando no ve el boton.
  - No cerrar el ciclo de navegacion: al llegar al ultimo boton no se puede
    seguir.
- **Checklist sin errores:**
  - [ ] `SelectedObject` se limpia al cerrar
  - [ ] Todos los botones navegables son `Selectable`
  - [ ] La navegacion es circular
  - [ ] Probado con un mando real o con el emulador

---

### 19. ViewportFrame

- **Que es:** una ventana que muestra objetos 3D dentro de la interfaz.
- **Para que sirve:** previsualizar una skin, un arma, el personaje en la
  tienda.
- **API implicada:** `ViewportFrame`, `CurrentCamera`, `WorldModel`.
- **Codigo listo para pegar:**

```lua
local RunService = game:GetService("RunService")

local function crearVisor(padre: Instance, modeloOriginal: Model)
    local visor = Instance.new("ViewportFrame")
    visor.Size = UDim2.fromOffset(220, 220)
    visor.BackgroundColor3 = Color3.fromRGB(18, 18, 24)
    visor.BorderSizePixel = 0
    visor.Ambient = Color3.fromRGB(190, 190, 190)
    visor.LightColor = Color3.fromRGB(255, 255, 255)
    visor.Parent = padre

    local mundo = Instance.new("WorldModel")
    mundo.Parent = visor

    local copia = modeloOriginal:Clone()
    for _, d in copia:GetDescendants() do
        if d:IsA("BasePart") then
            d.Anchored = true
            d.CanCollide = false
        end
    end
    copia.Parent = mundo

    local camara = Instance.new("Camera")
    camara.FieldOfView = 40
    camara.Parent = visor
    visor.CurrentCamera = camara

    local centro, tamano = copia:GetBoundingBox()
    local distancia = math.max(tamano.X, tamano.Y, tamano.Z) * 2.2

    local angulo = 0
    local conexion = RunService.RenderStepped:Connect(function(dt)
        if not visor.Parent then
            return
        end
        angulo += dt * 0.6
        local posicion = centro.Position + Vector3.new(
            math.sin(angulo) * distancia,
            tamano.Y * 0.35,
            math.cos(angulo) * distancia
        )
        camara.CFrame = CFrame.lookAt(posicion, centro.Position)
    end)

    visor.Destroying:Connect(function()
        conexion:Disconnect()
    end)

    return visor
end

return crearVisor
```

- **Errores frecuentes:**
  - Olvidar `visor.CurrentCamera`: el visor sale negro. Es el fallo numero uno.
  - Poner el modelo directamente en el ViewportFrame sin `WorldModel`: no hay
    fisica ni animacion posible.
  - Partes sin anclar: caen fuera de la vista.
  - No desconectar el bucle al destruir el visor.
- **Checklist sin errores:**
  - [ ] `CurrentCamera` asignado
  - [ ] El modelo esta dentro de un `WorldModel`
  - [ ] Todas las partes estan ancladas
  - [ ] El bucle se desconecta en `Destroying`

---

### 20. BillboardGui y SurfaceGui

- **Que es:** interfaz colocada en el mundo 3D.
- **Para que sirve:** nombres sobre la cabeza, indicadores de objetivo, carteles,
  pantallas de maquinas.

| Objeto | Comportamiento |
|---|---|
| `BillboardGui` | Siempre mira a la camara. Para nombres e iconos |
| `SurfaceGui` | Pegada a una cara de una parte. Para carteles y pantallas |

- **Codigo listo para pegar:**

```lua
local function crearEtiquetaSobreCabeza(personaje: Model, texto: string)
    local cabeza = personaje:FindFirstChild("Head") :: BasePart?
    if not cabeza then
        return nil
    end

    local cartel = Instance.new("BillboardGui")
    cartel.Name = "Etiqueta"
    cartel.Size = UDim2.fromOffset(200, 40)
    cartel.StudsOffsetWorldSpace = Vector3.new(0, 2.6, 0)
    cartel.AlwaysOnTop = false
    cartel.MaxDistance = 90     -- deja de dibujarse de lejos
    cartel.LightInfluence = 0
    cartel.Parent = cabeza

    local etiqueta = Instance.new("TextLabel")
    etiqueta.Size = UDim2.fromScale(1, 1)
    etiqueta.BackgroundTransparency = 1
    etiqueta.Font = Enum.Font.GothamBold
    etiqueta.TextScaled = true
    etiqueta.TextColor3 = Color3.new(1, 1, 1)
    etiqueta.RichText = false -- texto de jugador, nunca RichText
    etiqueta.Text = texto
    etiqueta.Parent = cartel

    local contorno = Instance.new("UIStroke")
    contorno.Thickness = 2
    contorno.Color = Color3.new(0, 0, 0)
    contorno.Parent = etiqueta

    return cartel
end

return crearEtiquetaSobreCabeza
```

- **Errores frecuentes:**
  - `MaxDistance` sin ajustar: cien etiquetas dibujandose a la vez hunden el
    rendimiento.
  - `AlwaysOnTop = true` en todo: los nombres se ven atravesando paredes.
  - `SurfaceGui` con `Face` equivocada: la interfaz esta en la cara de atras y
    parece que no funciona.
  - `RichText = true` con nombres de jugadores.
- **Checklist sin errores:**
  - [ ] `MaxDistance` limitado
  - [ ] `AlwaysOnTop` solo donde hace falta
  - [ ] La `Face` del SurfaceGui es la correcta
  - [ ] `RichText` desactivado en texto de jugadores

---

### 21. Ocultar la interfaz de Roblox

- **Que es:** desactivar los elementos nativos: chat, lista de jugadores,
  mochila, emotes.
- **Para que sirve:** pantallas de carga, cinematicas, interfaz propia.
- **API implicada:** `StarterGui:SetCoreGuiEnabled`, `SetCore`.
- **Codigo listo para pegar:**

```lua
local StarterGui = game:GetService("StarterGui")

local function ocultarTodo()
    local ok = false
    repeat
        ok = pcall(function()
            StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.All, false)
        end)
        if not ok then
            task.wait(0.1)
        end
    until ok
end

local function mostrarSoloLoNecesario()
    pcall(function()
        StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.All, true)
        StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, false)
        StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.PlayerList, false)
        StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.EmotesMenu, false)
        StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Chat, true)
    end)
end

return { ocultar = ocultarTodo, restaurar = mostrarSoloLoNecesario }
```

- **Errores frecuentes:**
  - Llamarlo demasiado pronto: la interfaz nativa aun no existe y lanza error.
    Por eso va en `pcall` con reintento.
  - Ocultar el chat y no ofrecer alternativa: los jugadores se quejan.
  - Ocultar `All` y olvidar restaurarlo tras la cinematica.
- **Checklist sin errores:**
  - [ ] Envuelto en `pcall`
  - [ ] Se restaura lo que se oculta temporalmente
  - [ ] Corre en un LocalScript

---

### 22. Conectar la interfaz al servidor

- **Que es:** el patron para que un boton produzca un cambio real y seguro.
- **Para que sirve:** reclamar premios del pase, comprar en la tienda, equipar.
- **API implicada:** `RemoteFunction` para peticiones con respuesta,
  `RemoteEvent` para avisos.
- **Codigo listo para pegar:**

```lua
-- Script: ServerScriptService/PaseServidor
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local remotes = ReplicatedStorage:WaitForChild("Remotes")
local reclamar = remotes:WaitForChild("ReclamarPremio") :: RemoteFunction

local NIVEL_MAXIMO = 20
local ultimaPeticion: { [Player]: number } = {}

reclamar.OnServerInvoke = function(jugador: Player, nivel, tipo)
    -- 1. limitar la frecuencia
    local ahora = os.clock()
    if ahora - (ultimaPeticion[jugador] or 0) < 0.4 then
        return { ok = false, motivo = "Demasiado rapido" }
    end
    ultimaPeticion[jugador] = ahora

    -- 2. validar tipos
    if typeof(nivel) ~= "number" or nivel ~= math.floor(nivel) then
        return { ok = false, motivo = "Nivel invalido" }
    end
    if nivel < 1 or nivel > NIVEL_MAXIMO then
        return { ok = false, motivo = "Nivel fuera de rango" }
    end
    if tipo ~= "gratis" and tipo ~= "premium" then
        return { ok = false, motivo = "Tipo invalido" }
    end

    -- 3. validar el estado real del jugador (datos del servidor)
    local nivelActual = jugador:GetAttribute("NivelPase") or 0
    if nivel > nivelActual then
        return { ok = false, motivo = "Nivel no alcanzado" }
    end
    if tipo == "premium" and not jugador:GetAttribute("TienePremium") then
        return { ok = false, motivo = "Requiere pase premium" }
    end

    -- 4. evitar reclamar dos veces
    local clave = "Reclamado_" .. tipo .. "_" .. nivel
    if jugador:GetAttribute(clave) then
        return { ok = false, motivo = "Ya reclamado" }
    end
    jugador:SetAttribute(clave, true)

    -- 5. entregar
    -- entregarPremio(jugador, nivel, tipo)

    return { ok = true }
end

Players.PlayerRemoving:Connect(function(jugador)
    ultimaPeticion[jugador] = nil
end)
```

```lua
-- LocalScript dentro del ScreenGui del pase
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local remotes = ReplicatedStorage:WaitForChild("Remotes")
local reclamar = remotes:WaitForChild("ReclamarPremio") :: RemoteFunction

local function pedirPremio(boton: GuiButton, nivel: number, tipo: string)
    boton.Active = false

    local ok, respuesta = pcall(function()
        return reclamar:InvokeServer(nivel, tipo)
    end)

    boton.Active = true

    if not ok then
        warn("Error de red al reclamar: " .. tostring(respuesta))
        return
    end
    if not respuesta or not respuesta.ok then
        -- notificar(respuesta and respuesta.motivo or "No se pudo reclamar")
        return
    end

    boton.Text = "RECLAMADO"
    boton.Active = false
end

return pedirPremio
```

- **Errores frecuentes:**
  - Mandar el premio desde el cliente: el jugador se da a si mismo todo el pase.
  - `InvokeServer` sin `pcall`: si el servidor lanza un error, el cliente se
    rompe.
  - No marcar el premio como reclamado antes de entregarlo: dos peticiones
    simultaneas duplican la recompensa.
  - Guardar el estado del pase solo en atributos sin persistirlo: se pierde al
    salir. Ver `mecanicas/06-datos-red.md`.
- **Checklist sin errores:**
  - [ ] El servidor valida tipo, rango, propiedad y duplicado
  - [ ] `InvokeServer` esta en `pcall`
  - [ ] Se marca como reclamado antes de entregar
  - [ ] Hay limite de frecuencia por jugador

---

### 23. Reaccionar a datos sin sondear

- **Que es:** actualizar la interfaz solo cuando el dato cambia.
- **Para que sirve:** rendimiento y codigo mas simple.
- **API implicada:** `Instance:GetAttributeChangedSignal`,
  `GetPropertyChangedSignal`, `IntValue.Changed`, `leaderstats`.
- **Codigo listo para pegar:**

```lua
local Players = game:GetService("Players")
local jugador = Players.LocalPlayer

-- Via atributos: lo mas simple para datos del propio jugador
local function seguirAtributo(nombre: string, etiqueta: TextLabel, formato: string)
    local function refrescar()
        local valor = jugador:GetAttribute(nombre) or 0
        etiqueta.Text = string.format(formato, valor)
    end

    refrescar()
    jugador:GetAttributeChangedSignal(nombre):Connect(refrescar)
end

-- Via leaderstats: para lo que debe salir en la lista de jugadores
local function seguirLeaderstat(nombre: string, etiqueta: TextLabel)
    local stats = jugador:WaitForChild("leaderstats", 20)
    if not stats then
        return
    end

    local valor = stats:WaitForChild(nombre, 10)
    if not valor or not valor:IsA("ValueBase") then
        return
    end

    local function refrescar()
        etiqueta.Text = tostring(valor.Value)
    end

    refrescar()
    valor:GetPropertyChangedSignal("Value"):Connect(refrescar)
end

return { atributo = seguirAtributo, leaderstat = seguirLeaderstat }
```

- **Errores frecuentes:**
  - Leer el valor cada frame con `RenderStepped`: gasto inutil.
  - Usar `WaitForChild` sin timeout: si el objeto nunca llega, el script se
    queda colgado y no avisa hasta 5 segundos despues con un aviso poco claro.
  - Escribir en el atributo desde el cliente esperando que el servidor lo vea:
    los atributos escritos por el cliente no se replican al servidor.
- **Checklist sin errores:**
  - [ ] Se usan senales de cambio, no sondeo
  - [ ] Todos los `WaitForChild` tienen timeout
  - [ ] El cliente solo lee, el servidor escribe

---

## Por que no aparece mi GUI

| # | Comprobacion | Sintoma tipico |
|---|---|---|
| 1 | El ScreenGui esta en `PlayerGui`, no en `StarterGui` en ejecucion | El script no encuentra nada |
| 2 | `Enabled` en true y `Visible` en true en toda la cadena de padres | Existe pero no se ve |
| 3 | `Size` distinto de cero | Ocupa 0 pixeles |
| 4 | `BackgroundTransparency` no esta en 1 sin nada dentro | Marco invisible |
| 5 | El elemento no esta fuera de la pantalla | `Position` con escala mayor que 1 |
| 6 | `ZIndex` suficiente y `ZIndexBehavior` coherente | Tapado por otro panel |
| 7 | El padre no tiene `ClipsDescendants` recortandolo | Se ve la mitad |
| 8 | `ResetOnSpawn` no lo esta borrando al morir | Desaparece al reaparecer |
| 9 | El LocalScript esta en un sitio que corre en cliente | El script nunca se ejecuta |
| 10 | No hay un `SetCoreGuiEnabled(All, false)` de otro script | Todo desaparece de golpe |
| 11 | El `ViewportFrame` tiene `CurrentCamera` | Cuadro negro |
| 12 | En `ScrollingFrame`, el `CanvasSize` permite ver el contenido | Lista vacia o cortada |

---

## Checklist maestro de interfaz

- [ ] El JSON de interfaz pasa `revisar_pase.bat` y su PNG se ve correcto
- [ ] `ResetOnSpawn` en false donde debe
- [ ] Los paneles usan escala y los iconos offset
- [ ] Lo centrado tiene AnchorPoint `(0.5, 0.5)`
- [ ] `SortOrder` es `LayoutOrder` en todos los layouts
- [ ] Nada importante en las esquinas que Roblox ocupa
- [ ] `TextScaled` acompanado de `UITextSizeConstraint`
- [ ] `RichText` desactivado en texto escrito por jugadores
- [ ] Los botones tienen antirrebote y el servidor valida igual
- [ ] Los tweens anteriores se cancelan antes de lanzar otro
- [ ] Todas las conexiones y bucles se desconectan
- [ ] Probado en el emulador con telefono, tablet y escritorio
- [ ] Probado con mando si el juego lo soporta
- [ ] Probado tras morir y reaparecer

---

## Siguiente paso

Persistir lo que muestra la interfaz en `mecanicas/06-datos-red.md`. Los sistemas
que la alimentan en `mecanicas/08-sistemas.md`. Errores concretos en
`mecanicas/09-errores-y-checklist.md`.
