# Recuperar la barra de plugins o de herramientas en Studio

Fuente: documentacion oficial de Roblox, `create.roblox.com/docs/studio/ui-overview`.

## Como se llaman las cosas

- **Mezzanine**: la fila de arriba del todo con las pestanas.
- **Toolbar**: la fila de botones que aparece debajo de la pestana elegida.

Pestanas por defecto: **Home**, **Model**, **Avatar**, **UI**, **Script** y **Plugins**.
Los botones de los plugins instalados viven en la pestana **Plugins**.

## Causas por orden de probabilidad

### 1. La toolbar esta colapsada

La opcion **Collapse toolbar** esconde la fila de botones y deja solo las pestanas.
Sintoma exacto: ves los nombres de las pestanas pero ninguna herramienta debajo, y
al pasar el raton por encima de una pestana la barra asoma un momento y se va.

Arreglo: clic derecho en una zona vacia de la mezzanine o de la toolbar y desmarcar
**Collapse toolbar**.

### 2. La pestana esta oculta

Clic derecho en zona vacia de la barra y elegir **Manage tabs**. En esa ventana se
puede mostrar u ocultar cada pestana, reordenarlas, borrar pestanas personalizadas y
elegir alineacion **Center** o **Left**. Si `Plugins` esta desmarcada, se marca ahi.

### 3. Esta en modo compacto o sin etiquetas

**Compact toolbar** reduce los iconos y **Show labels** quita los textos. La barra
sigue estando, pero parece otra cosa. Ambas se cambian en el mismo menu de clic derecho.

### 4. Studio esta en modo de prueba

Durante Play o Run la barra cambia y algunas herramientas desaparecen. Parar la
prueba con Stop devuelve todo a su sitio.

### 5. El plugin no tiene boton

No todos los plugins crean boton. Algunos actuan por menu contextual del Explorer o
arrancan solos. Si el plugin escribe en la ventana Output, esta cargado aunque no lo
veas en la barra.

### 6. Pestanas personalizadas que no se recargan

Si se editaron archivos `.json` de `CustomRibbonTabs`, hay que abrir **Manage tabs** y,
en el menu de opciones de la esquina superior derecha, elegir **Reload custom tabs**.

## Ventanas que no van en la barra de plugins

Si lo que falta es Explorer, Properties, Output, Command Bar, Toolbox o Asset Manager,
estan en el menu **Window**, y las mas comunes tambien en la pestana **Home**. El
Command Bar esta ademas en la pestana **Script** y se abre con Ctrl+9.
Los plugins nuevos se instalan desde el **Toolbox**, seccion de plugins.

## Diagnostico rapido para este proyecto

El plugin puente `RobloxAgentBridge v1.9.3` escribe en la consola en cada arranque:

```
[RBX Bridge] runtime v3.4.0 en marcha (loader v2.1)
```

Si ese mensaje aparece, los plugins se estan cargando y el problema es solo de vista:
casi siempre la toolbar colapsada o la pestana oculta, es decir los casos 1 y 2.
