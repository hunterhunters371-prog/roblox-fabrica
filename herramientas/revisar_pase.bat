@echo off
rem ============================================================
rem  revisar_pase.bat   circuito completo, universal (v6.0)
rem
rem  Doble clic:         procesa el .json mas reciente de la carpeta
rem  Arrastrar archivo:  procesa ese archivo en concreto
rem
rem  JSON de interfaz         -> spec_a_rbxmx.py + lint + render PNG
rem  JSON de animacion (rig)  -> spec_anim.py + vista previa GIF
rem  .rbxmx de interfaz       -> lint + render
rem  .rbxmx de animacion      -> aviso (va al Animation Editor)
rem  .rbxm  (binario)         -> leer_anim.py: MIDE la animacion y
rem                              guarda <nombre>_medida.txt
rem
rem  Los .py pueden estar junto al .bat o en la subcarpeta
rem  herramientas\ (para tener la carpeta mas ordenada).
rem
rem  TODO lo que pasa queda escrito en ultimo_resultado.txt
rem ============================================================
setlocal
cd /d "%~dp0"

if /i "%~1"=="__interno" goto :interno

rem ---------- modo normal: ejecuta el circuito y lo graba ----------
set "LOG=%~dp0ultimo_resultado.txt"
call "%~f0" __interno %* > "%LOG%" 2>&1
chcp 65001 >nul
type "%LOG%"
echo.
echo   -------------------------------------------------------
echo   Todo lo de arriba quedo guardado en ultimo_resultado.txt
echo   Si algo fallo: abre ese archivo y pegalo en el chat.
echo   -------------------------------------------------------
pause
exit /b 0

rem ---------- modo interno: el circuito de verdad ----------
:interno
shift
chcp 65001 >nul

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo   ERROR: no encuentro Python en este equipo.
    echo   Revisa que este instalado y en el PATH.
    exit /b 1
)

rem ---------- donde viven los .py: aqui o en herramientas\ ----------
set "PY=%~dp0"
if not exist "%PY%spec_anim.py" (
    if exist "%~dp0herramientas\spec_anim.py" set "PY=%~dp0herramientas\"
)

set "ENTRADA=%~1"

if not defined ENTRADA (
    for /f "delims=" %%f in ('dir /b /o-d *.json 2^>nul') do (
        if not defined ENTRADA set "ENTRADA=%%f"
    )
)

if not defined ENTRADA (
    for /f "delims=" %%f in ('dir /b /s /o-d *.json 2^>nul') do (
        if not defined ENTRADA set "ENTRADA=%%f"
    )
)

if not defined ENTRADA (
    for /f "delims=" %%f in ('dir /b /o-d *.rbxmx 2^>nul') do (
        if not defined ENTRADA set "ENTRADA=%%f"
    )
)

if not defined ENTRADA (
    for /f "delims=" %%f in ('dir /b /o-d *.rbxm 2^>nul') do (
        if not defined ENTRADA set "ENTRADA=%%f"
    )
)

if not defined ENTRADA (
    echo.
    echo   No encontre ningun .json, .rbxmx ni .rbxm en ESTA carpeta:
    echo   %CD%
    exit /b 1
)

if not exist "%ENTRADA%" (
    echo.
    echo   No existe el archivo: %ENTRADA%
    echo   Carpeta: %CD%
    exit /b 1
)

for %%f in ("%ENTRADA%") do (
    set "RUTA=%%~dpnf"
    set "EXT=%%~xf"
    set "NOMBRE=%%~nxf"
)

echo   Carpeta: %CD%
echo   Archivo: %NOMBRE%
echo   --------------------------------------------

if /i "%EXT%"==".rbxm"  goto :via_rbxm
if /i "%EXT%"==".rbxmx" goto :via_rbxmx

rem --- es JSON: elegir conversor segun el contenido
set "CONV=spec_a_rbxmx.py"
set "TIPO=interfaz"
findstr /c:"\"rig\"" "%ENTRADA%" >nul 2>&1
if not errorlevel 1 (
    set "CONV=spec_anim.py"
    set "TIPO=animacion"
)

echo   [1/3] Conversor (%TIPO%)
echo.
python "%PY%%CONV%" "%ENTRADA%"
if errorlevel 1 goto :fallo_json

if "%TIPO%"=="animacion" goto :anim_gif
goto :lint

rem ---------- .rbxm binario: MEDIR la animacion ----------
:via_rbxm
echo   [1/1] Medir animacion (leer_anim.py)
echo.
python "%PY%leer_anim.py" "%ENTRADA%" > "%RUTA%_medida.txt" 2>&1
set "RC=%ERRORLEVEL%"
type "%RUTA%_medida.txt"
if not "%RC%"=="0" goto :fallo_leer

echo.
echo   --------------------------------------------
echo   MEDIDA GUARDADA EN:
echo   %RUTA%_medida.txt
echo.
echo   Pegale ese archivo a la IA con esta linea delante:
echo   "Replica este estilo en una animacion de [lo que quieras]"
echo   --------------------------------------------
start "" notepad "%RUTA%_medida.txt"
exit /b 0

:via_rbxmx
findstr /c:"KeyframeSequence" "%ENTRADA%" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo   Este .rbxmx es una ANIMACION (KeyframeSequence), no una interfaz.
    echo   El lint y el render no aplican.
    echo   En Studio: Dummy del rig, carpeta AnimSaves, Insert from File,
    echo   Animation Editor para verla, y publicar para obtener el ID.
    exit /b 0
)

:lint
echo.
echo   [2/3] Lint
echo.
python "%PY%roblox_lint.py" "%RUTA%.rbxmx"
if errorlevel 1 goto :fallo_lint

echo.
echo   [3/3] Render a PNG
echo.
python "%PY%render_rbxmx.py" "%RUTA%.rbxmx"
if errorlevel 1 goto :fallo_render

if not exist "%RUTA%.png" goto :fallo_render

echo.
echo   --------------------------------------------
echo   TODO LIMPIO. PNG generado:
echo   %RUTA%.png
echo   --------------------------------------------
start "" "%RUTA%.png"
exit /b 0

:anim_gif
echo.
echo   [2/3] Vista previa GIF
echo.
python "%PY%ver_anim.py" "%ENTRADA%"
if not errorlevel 1 (
    if exist "%RUTA%.gif" start "" "%RUTA%.gif"
)

echo.
echo   --------------------------------------------
echo   ANIMACION LISTA: %RUTA%.rbxmx
echo   Vista previa: %RUTA%.gif (maniqui de bloques, aproximado)
echo   En Studio: Dummy del rig elegido, carpeta AnimSaves,
echo   Insert from File, Animation Editor para verla, y publicar
echo   para obtener el Animation ID.
echo   --------------------------------------------
exit /b 0

:fallo_json
echo.
echo   --------------------------------------------
echo   El JSON tiene errores. No lo arregles a mano:
echo   copia la lista de arriba y pegasela a la IA
echo   con esta linea delante:
echo.
echo   Corrige el JSON. El validador devolvio estos errores:
echo   [lista]. Devuelve el JSON completo, sin explicaciones.
echo   --------------------------------------------
exit /b 1

:fallo_leer
echo.
echo   --------------------------------------------
echo   No pude leer ese .rbxm.
echo.
echo   Causa mas comun: falta la libreria lz4. Instalala con:
echo       pip install lz4
echo.
echo   Si ya la tienes, copia lo de arriba y pegalo en el chat.
echo   --------------------------------------------
exit /b 1

:fallo_lint
echo.
echo   --------------------------------------------
echo   El lint encontro errores en el .rbxmx.
echo   Copia la lista de arriba y pegasela a la IA.
echo   --------------------------------------------
exit /b 1

:fallo_render
echo.
echo   --------------------------------------------
echo   El render fallo o no creo el PNG.
echo   Copia todo lo de arriba y pegalo en el chat.
echo   --------------------------------------------
exit /b 1
