# Harness Finora

Harness de análisis para Finora (SaaS): responde preguntas de negocio con trazabilidad, desde los datos originales hasta cada cifra reportada.

## Requisitos

- Python 3.12+
- `pip install duckdb pandas pyyaml pytest plotly`

## Cómo correrlo

```
python ejecutar.py
```

Ejecuta la limpieza, las consultas y las validaciones. Si una validación falla, el proceso se detiene.

## Estructura

| Carpeta | Contenido |
|---|---|
| `datos/originales/` | Fuentes crudas (solo lectura) |
| `datos/tablas/` | Tablas limpias generadas |
| `reglas/` | Definiciones de métricas (`definiciones.yaml`) |
| `sql/` | Limpieza (`1_limpieza.sql`) y consultas por pregunta (`sql/preguntas/`) |
| `preguntas/` | Preguntas de negocio |
| `hallazgos/` | Respuestas etiquetadas (hecho / inferencia / hipótesis) |
| `validaciones/` | Pruebas de calidad y consistencia |
| `salidas/` | Resultados y gráficos |

Las reglas de trabajo están en `CLAUDE.md`.
