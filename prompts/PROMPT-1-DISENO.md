# PROMPT 1 · DISEÑO (universal)

Este es el PRIMER prompt. Se pega a cualquier IA (DeepSeek, Qwen, ChatGPT,
Gemini...) junto con tu idea, ANTES de generar nada. La IA responde con un
plan, no con código. Cuando el plan te guste, usas el PROMPT 2
(PROMPT-IAS.md) para que la IA genere el JSON.

Copia desde la línea de guiones hasta el final.

---

Actúa como diseñador de interfaces para Roblox. NO escribas código ni JSON
todavía: tu trabajo es convertir mi idea en un plan claro que yo revisaré.

MI IDEA: [escribe aquí lo que quieres para tu juego]

Haz esto, en este orden:

1. CONFIRMA: repite mi idea en una línea, con tus palabras, para verificar
   que la entendiste.

2. CLASIFICA: dime si es un pase de batalla u otra cosa (tienda, inventario,
   menú, HUD...).

3A. SI ES UN PASE DE BATALLA, rellena esta ficha respetando los límites
    (son duros; si los pasas, la validación fallará después):

    - temporada:   nombre corto, máx 25 caracteres. Ej: "TEMPORADA 2 - NEON"
    - titulo:      máx 28 caracteres. Ej: "PASE NEON"
    - resaltado:   una palabra o frase que aparezca en el título
                   (se pinta de otro color). Ej: "NEON"
    - subtitulo:   máx 80 caracteres
    - tiempo:      máx 11 caracteres. Ej: "12d 08:42"
    - niveles:     de 2 a 20
    - nivel:       nivel actual del jugador, entre 1 y "niveles"
    - xp:          XP actual del jugador, menor que xpPorNivel
    - xpPorNivel:  XP que cuesta subir un nivel
    - gratis:      de 1 a 6 premios
    - premium:     de 1 a 6 premios

    Cada premio lleva:
    - etiqueta: máx 18 caracteres, en MAYÚSCULAS. Ej: "FRÁGIL", "LEGENDARIO"
    - color:    SOLO uno de esta lista: azul, cian, dorado, morado,
                naranja, rojo, rosa, verde
    - icono:    UN emoji. Ej: 📦 ⚡ 💎 👑
    - titulo:   máx 20 caracteres
    - desc:     máx 55 caracteres, una sola frase
    - bonus:    opcional, máx 16 caracteres. Ej: "x1.5", "+500 XP"
    - nuevo:    true o false (muestra la etiqueta NUEVO)

3B. SI NO ES UN PASE DE BATALLA:
    - Describe las pantallas y elementos que harían falta.
    - Separa qué datos cambian (el contenido) de qué es fijo (la lógica).
    - Termina con la frase "Esta interfaz necesita un conversor nuevo" y
      un resumen de máximo 10 líneas que yo pueda llevar a mi asistente
      de programación para construirlo.

REGLAS:
- Nada de etiquetas ni de los símbolos < > & en los textos.
- Si mi idea es vaga, hazme MÁXIMO 3 preguntas antes de proponer el plan.
- No generes el JSON aquí. Cuando yo confirme el plan, te pegaré las
  instrucciones de generación y entonces sí.

---

## El sistema completo, para referencia

1. Pegas PROMPT 1 + tu idea  →  la IA devuelve el plan
2. Lo revisas y pides cambios ("más niveles", "otro color"...)
3. Confirmas el plan y pegas PROMPT-IAS.md (PROMPT 2)  →  la IA genera el JSON
4. Guardas el JSON en la carpeta  →  doble clic a revisar_pase.bat
5. Si hay errores: se los pegas a la IA y vuelves al paso 3.
   Si no hay: ves el PNG y, si te gusta, lo importas a Studio.
