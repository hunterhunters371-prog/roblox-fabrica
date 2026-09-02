# Interfaz: medidas, fallos y falsos positivos

Pantalla de referencia de la auditoria: 1619 x 793, con `IgnoreGuiInset = true`.

## Fallos reales corregidos

| Fallo | Antes | Despues |
| --- | --- | --- |
| El panel Objetivo se solapaba con la fila de botones | panel 520x110 y botones 150x36 pisandose | panel 520x118 en y=-176, botones 150x44 en y=-8, solape 0 y hueco de 6 px |
| El texto del ritmo se cortaba | caja 150x18 | caja 250x20, `TextFits=true` con "RITMO x1.18   MEJOR 8647" |
| Botones planos y de area corta | sin borde, 36 px de alto | borde 2.4 px con transparencia 0.12, 44 px de alto |

## Medidas vigentes del HUD

```
Objetivo      [549,559]  520x118
Correr        [655,683]  150x44     (fila de botones, desplazamientos -237 -79 79 237)
Ritmo                    250x20
Brujula       [549,523]  520x34
Barra         [529,-44]  560x92
Pedidos       [18,222]   268x232
Clasificacion [1355,238] 246x200
Aviso         [459,56]   700x30
Fondo y Efectos a pantalla completa (z=1 y z=20)
```

## Falsos positivos: no son fallos

1. Posiciones negativas cerca de -58: es la convencion de `IgnoreGuiInset=true`.
   El area visible va de -58 a 735 en esa pantalla.
2. Elementos `Linea*` en posiciones extranas: son lineas de velocidad animadas.
3. `TAM0 Relleno en FondoCombo`: el relleno del combo vale 0 cuando no hay combo.
4. `BandaSuperior[0,-154]` y `BandaInferior[0,735]`: es el letterbox de la intro,
   ya retraido fuera de pantalla.

De 22 avisos de la auditoria numerica, solo 3 eran fallos reales.

## Metodo de auditoria recomendado

Con el juego en marcha, recorrer `PlayerGui.Interfaz:GetDescendants()` y para cada
`GuiObject` leer `AbsolutePosition`, `AbsoluteSize`, `Visible` y, en los textos,
`TextFits`. Comparar rectangulos dos a dos para detectar solapes y comprobar que
todo cae dentro del area visible. Hacerlo antes de dar por bueno cualquier cambio.
