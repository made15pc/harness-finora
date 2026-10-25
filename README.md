# Harness Finora

Harness de análisis para Finora (SaaS): responde preguntas de negocio con trazabilidad, desde los datos originales hasta cada cifra reportada. Cada cifra sale de una consulta SQL, se recalcula en las validaciones y solo se publica si fue aprobada.

- **Tablero:** https://made15pc.github.io/harness-finora/
- **Nota corta:** [docs/nota_corta.md](docs/nota_corta.md)

## Requisitos

- Python 3.12+
- `pip install duckdb pandas pyyaml pytest plotly`

## Cómo correrlo

```
python ejecutar.py
```

Ejecuta la limpieza, las consultas y las validaciones. Si una validación falla, el proceso se detiene. Si todas pasan, genera el tablero (`docs/index.html`) y lo valida.

## Estructura

| Carpeta | Contenido |
|---|---|
| `datos/originales/` | Fuentes crudas (solo lectura) |
| `datos/tablas/` | Tablas limpias generadas |
| `reglas/` | Definiciones de métricas (`definiciones.yaml`) y lectura de fuentes (`fuentes.yaml`) |
| `sql/` | Limpieza (`1_limpieza.sql`), ciclo de vida (`2_cliente_mes.sql`) y consultas por pregunta (`sql/preguntas/`) |
| `preguntas/` | Preguntas de negocio, plantilla y revisiones |
| `hallazgos/` | Hallazgos (hecho / inferencia) e hipótesis con veredicto |
| `validaciones/` | Pruebas de calidad y consistencia (pytest) |
| `salidas/` | Generador del tablero |
| `docs/` | Tablero publicado y nota corta |
| `.claude/agents/` | Agentes revisor y constructor del tablero |

Las reglas de trabajo están en `CLAUDE.md`.

## Ciclo de una pregunta nueva

1. **Registrar:** copiar `preguntas/_plantilla.md` a `preguntas/PXX_<tema>.md` y completarla.
2. **Definir:** si falta una métrica, proponerla en `reglas/definiciones.yaml` y esperar aprobación humana.
3. **Hipótesis:** registrarlas en `hallazgos/hipotesis.yaml` (estado `borrador`, con `si_es_cierta` y `prueba`) antes de calcular.
4. **Plan:** completar el plan de análisis de la pregunta y esperar aprobación.
5. **Calcular:** escribir `sql/preguntas/PXX_<tema>.sql` y correr `python ejecutar.py`.
6. **Hallazgos:** registrar los hechos con su consulta y las inferencias con `basada_en`, y proponer veredictos con evidencia.
7. **Revisión:** el agente `revisor` intenta refutar cada veredicto; se guardan sus objeciones y la respuesta.
8. **Aprobación:** una persona aprueba; solo lo aprobado llega al tablero.
