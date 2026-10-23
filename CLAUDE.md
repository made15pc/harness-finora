# CLAUDE.md — Harness Finora

## Proyecto
Harness de análisis para Finora (SaaS). Responde preguntas de negocio con trazabilidad: cada respuesta se puede rastrear hasta la consulta y la regla que la producen.

## Reglas

1. **Datos originales intocables.** `datos/originales/` es de solo lectura. Nunca se modifica.
2. **Unidades, una sola vez.** Las conversiones de unidades se hacen únicamente en `sql/1_limpieza.sql`. Nunca en otro lugar.
3. **Métricas definidas.** Toda métrica sale de `reglas/definiciones.yaml`. No inventes definiciones: si falta una, propónla y espera aprobación humana.
4. **Cero cifras a mano.** Toda cifra viene de una consulta SQL ejecutada.
5. **Etiqueta cada afirmación** como `hecho`, `inferencia` o `hipótesis`.
6. **Sin funnel inventado.** No existen datos de funnel en las fuentes; no se fabrican.
7. **Validar tras cada cambio.** Después de cualquier cambio en `sql/` o `reglas/`, ejecutar `python ejecutar.py`. Si una validación falla, se detiene y se informa; no se "arregla" el test para que pase.
8. **Código simple.** SQL en DuckDB, Python solo para orquestar. Las columnas que vienen de los archivos fuente conservan su nombre original (ID, month, amount, Month, PaidMedia, Travel, PublicidadNoWeb, Freelance, SoftwareTools, Team, PayrollExpenses, Industria), porque así las conoce el negocio. Todo lo que crea el harness (carpetas, archivos, tablas y columnas nuevas o derivadas) va en español.
9. **Hipótesis antes de calcular.** Se registran en `hallazgos/hipotesis.yaml` con estado `borrador` y requieren aprobación humana antes de ejecutar el análisis.
10. **Hipótesis comprobables.** Cada una declara qué veríamos si fuera cierta (`si_es_cierta`) y con qué métrica o dato se prueba (`prueba`). Solo se usan métricas de `reglas/definiciones.yaml`.
11. **Veredictos con evidencia.** Veredictos posibles: `pendiente`, `apoyada`, `descartada`, `no_concluyente`, `no_evaluable`. `apoyada`, `descartada` o `no_concluyente` exigen al menos un hallazgo de tipo `hecho` en `evidencia`. `no_evaluable` exige completar `dato_faltante`.
12. **Origen declarado.** Cada hipótesis indica su origen: `caso` (la plantea el negocio), `analista` o `revisor`. No se elimina una hipótesis del caso aunque no sea evaluable.
13. **Aprobación humana.** El veredicto lo propone un agente, pero solo pasa a `aprobado` por decisión humana. Solo lo aprobado llega al informe y al tablero.
