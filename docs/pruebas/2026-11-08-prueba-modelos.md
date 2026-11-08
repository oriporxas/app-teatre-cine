# Prueba de los tres modelos de IA (8/11/2026)

Para elegir con datos qué modelo de Claude clasifica la cartelera. Mismas
instrucciones, mismos criterios (`docs/clasificacion.md`) y mismas
actividades para todos:

- **A) Las 55 respuestas de Uri** de la prueba de magia
  (`2026-11-08-respuestas-uri.json`).
- **B) 40 casos difíciles para las reglas**: dudosos, musicales, danza,
  clown, cuentacuentos… Se eligieron al azar, pero siempre los mismos
  (`pipeline/comparar_modelos.py`). Aquí no hay una respuesta «oficial»:
  se compara lo que **publicaría la app** con cada modelo, tomando como
  referencia el modelo más potente (Opus 5.5, esfuerzo medio), y se
  revisaron a mano los casos en que no coinciden.

Cada modelo se probó con dos niveles de «esfuerzo» (cuánto piensa antes de
responder): bajo y medio. En total, 6 configuraciones. La prueba completa
costó **1,33 $**. Los resultados en bruto, para repetir la comparación con
otros criterios o modelos, están en `2026-11-08-prueba-modelos-resultados.json`.

Nota: la lista tenía 95 actividades, pero 2 estaban repetidas. Por eso se
clasificaron 93.

## 1. Resultados

| Modelo y esfuerzo | Respuestas de Uri (55) | Magia sí/no (55) | Casos difíciles: publica lo mismo que Opus (40) | Coste de la prueba | Por 1000 actividades | Tiempo |
|---|---|---|---|---|---|---|
| Haiku 5.5 · bajo | 55 | 55 | 37 | 0,012 $ | 0,13 $ | 55 s |
| Haiku 5.5 · medio | 54 | 55 | 37 | 0,016 $ | 0,17 $ | 94 s |
| Sonnet 5.5 · bajo | 54 | 55 | 39 | 0,207 $ | 2,23 $ | 84 s |
| Sonnet 5.5 · medio | **55** | **55** | **39** | 0,198 $ | 2,13 $ | 84 s |
| Opus 5.5 · bajo | 54 | 55 | 40 | 0,401 $ | 4,31 $ | 78 s |
| Opus 5.5 · medio | 54 | 55 | (referencia) | 0,494 $ | 5,31 $ | 130 s |
| *Reglas actuales (gratis)* | *55* | *55* | *37* | — | — | — |

Cómo se cuentan los aciertos:

- **«Respuestas de Uri»**: coincide exactamente con lo que dijo Uri
  (principal / tema / no).
- **«Magia sí/no»**: lo que cambia en la app, es decir, si sale o no al buscar
  magia.

Los fallos de la primera columna no cambian nada en la app. Son
taller de neurociencia «Magic brains» (Uri: magia como tema; modelo: nada
que ver con la magia) y «L'aventura del mag Martí» (al revés).

**Todos aciertan la magia al 100 %**, también el tipo de magia (de cerca,
general, mentalismo). La prueba de magia ya no distingue entre modelos: las
reglas actuales también sacan 55 de 55. La diferencia está en los casos
difíciles.

## 2. Casos difíciles: dónde se equivocan

Diferencias en lo que publicaría la app:

| Actividad | Haiku | Sonnet | Opus | Correcto |
|---|---|---|---|---|
| «L'aniversari del petit ós» (dice «Conte contes», para bebés) | teatro (seguro al 85 %) con esfuerzo bajo | no sale (cuentacuentos) | no sale | no sale: es un cuentacuentos |
| «L'aniversari del petit Os» (misma artista, sin descripción) | teatro (70–80 %) | dudoso (40–45 %): no sale | dudoso: no sale | no sale: es el mismo cuentacuentos |
| «El Concurshow de Revival +» (concurso en un teatro) | teatro | teatro (60 %) | dudoso (55 %): no sale | discutible |
| Festival «Clàssics» (artes contemporáneas y pensamiento) | festival de teatro / sin disciplina | festival de teatro | festival de teatro | discutible |

Los demás desacuerdos (talleres de baile o de guitarra, coros) no cambian
nada en la app: ningún modelo los publica.

**Lo más importante:** cuando Haiku se equivoca, está muy seguro (85 %).
Por eso la idea inicial no funciona: Haiku clasifica todo y solo lo dudoso
sube a un modelo superior, pero los fallos de Haiku no parecen dudosos y no
subirían nunca. En los casos difíciles, Haiku acierta lo mismo que las
reglas gratuitas.

Sonnet y Opus sí **saben cuándo no saben**: dan una confianza baja a lo que
no está claro y eso no se publica (umbral 0,6). Así se cumple el principio
de precisión: mejor no enseñar algo que enseñarlo mal clasificado.

## 3. Coste en Barcelona

Supuestos:

- La primera vez la IA lee 1712 actividades (las que las reglas no descartan
  de entrada).
- Después, solo lo nuevo o cambiado. Se calculan 150 al día como mucho, unas
  4500 al mes; probablemente serán menos.
- Cada decisión se guarda y no se vuelve a pagar.
- Con el trabajo por lotes (Batch), Anthropic cobra la mitad.

| Opción | Primera vez | Al mes (normal) | Al mes (por lotes) |
|---|---|---|---|
| Solo Haiku 5.5 | 0,29 $ | 0,8 $ | 0,4 $ |
| Solo Sonnet 5.5 | 3,7 $ | 9,6 $ | 4,8 $ |
| **Sonnet 5.5 + Opus 5.5 revisa lo dudoso (≈ 1 de cada 10)** | **4,6 $** | **12 $** | **6 $** |
| Solo Opus 5.5 | 9,1 $ | 24 $ | 12 $ |

Las cifras mensuales son el máximo esperado. Con menos novedades al día, el
coste baja en proporción.

## 4. Recomendación (pendiente de Uri)

**Sonnet 5.5 (esfuerzo medio) clasifica. Opus 5.5 revisa solo lo que Sonnet
marca como dudoso (confianza menor que 0,7).**

- Con los datos de la prueba, esta combinación da el mismo resultado que
  Opus en todo (40 de 40 casos difíciles), a la mitad de precio.
- Mantiene la idea de que lo dudoso sube a un modelo superior. Simplemente,
  el que hace el primer trabajo es Sonnet en lugar de Haiku, porque Haiku no
  avisa cuando duda.
- Haiku queda para tareas sencillas en las que no hay que interpretar,
  como extraer datos ya escritos. La traducción al castellano se probará
  aparte, con el mismo método.
- Para crecer a otras ciudades, el coste es de unos 6–12 $ al mes por ciudad
  del tamaño de Barcelona. Cuando haya muchas ciudades, se repetirá la prueba
  por si un modelo más barato ya es suficiente.

Ajuste aplicado en `ajustes/ia.toml`. Volver a medir así:

```
python -m pipeline.comparar_modelos docs/pruebas/<fecha>-prueba-modelos.md
```

Esto necesita la clave de la IA. Precios usados, por millón de tokens
(entrada / salida):

- Haiku 5.5: 0,10 / 0,50 $
- Sonnet 5.5: 2 / 10 $
- Opus 5.5: 4 / 20 $

Leer de la caché de instrucciones cuesta el 10 % y escribir en ella, el
125 %.
