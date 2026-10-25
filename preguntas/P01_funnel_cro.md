# P01 — "Estamos generando más leads, pero no estamos vendiendo más. ¿Dónde y por qué estamos perdiendo crecimiento?"

- Quién pregunta: CRO
- Qué decisión habilita: dónde intervenir en el funnel (capacidad SDR, calificación de leads, proceso post-SQL, inversión por canal) y cómo operarlo de forma recurrente.
- Subpreguntas:
  1. ¿Cómo definirías y medirías el funnel si no todos los clientes lo recorren igual (self-serve, entrada directa a SQL, estancamientos de semanas)?
  2. ¿Dónde y en qué segmentos se concentra la pérdida de crecimiento? ¿Qué métricas propondrías que hoy no existen?
  3. ¿Qué hipótesis explicarían el fenómeno (demanda, calidad, velocidad de atención, conversión post-SQL) y qué datos usarías para validar o descartar cada una?
  4. ¿Qué solución analítica construirías para que el CRO opere el funnel de forma recurrente, y qué decisiones le permitiría tomar?
- Definiciones que usa:
  - Bloque A (A_ciclo_de_vida): antes_de_alta, base_inicial, cliente_nuevo, activo, pausa, retorno_pausa, churn, inactivo, reactivacion, pendiente, churn_sensibilidad_1m.
  - Bloque B (B_mrr): monto_recurrente (vía ticket_inicial del bloque D).
  - Bloque D (D_eficiencia_comercial): gasto_sm, cac, cac_3m, ticket_inicial, retencion_cohorte.
  - Bloque E (E_funnel_comercial, diseño): lead, etapas, motion_entrada, alcanzo_etapa, conversion_cohorte, tiempo_en_etapa, estancado, speed_to_lead, win_rate, costo_por_won.
- Datos disponibles: Transactions, SM_spend, Industry.
- Datos que faltan: Tabla de eventos de etapa (lead_id, etapa, fecha_entrada, fecha_salida, fuente, motion, SDR/AE asignado) y vínculo lead_id → cliente_id.
- Hipótesis: ver hallazgos/hipotesis.yaml (se formulan antes de calcular)
- Plan de análisis: (propuesto por el analista; aprobado por Madeley el 2026-10-25)
  - Períodos: antes = 2022-03 a 2023-05; despues = 2023-06 a 2024-10. Se comparan promedios mensuales.
  - Solo se prueban P01-H5 a P01-H8; P01-H1 a P01-H4 son no_evaluable (requieren el bloque E).
  - Tablas en `sql/preguntas/P01_adquisicion.sql`:
    1. `adquisicion_mes`: una fila por mes (2022-03 a 2024-10) con período, clientes nuevos, suma de ticket_inicial, gasto_sm, cac y cac_3m. Prueba P01-H5 y P01-H6.
    2. `adquisicion_industria`: una fila por período e Industria con clientes nuevos, participación en el período y mediana de ticket_inicial. Prueba P01-H7.
    3. `retencion_cohortes`: una fila por cohorte mensual de adquisición con período, clientes y retencion_cohorte a 3, 6 y 12 meses (vacía si el mes N supera 2024-08). Prueba P01-H8.
- Límites:
  - No hay datos de leads ni de etapas; toda conclusión sobre el funnel se infiere desde el resultado (clientes nuevos, ticket, retención, gasto).
  - Si los clientes nuevos crecen "al mismo ritmo que los leads" no es evaluable sin datos de leads (definición lead, en diseño).
  - cac y cac_3m incluyen clientes self-serve; no se puede separar la adquisición asistida por ventas (motion_entrada, en diseño).
  - La escala de SM_spend (× 100.000.000) debe confirmarse con el negocio: el gasto_sm mensual supera al MRR. Mientras tanto, de gasto y CAC se citan solo variaciones %.
- Revisión: (lo completa el revisor)
- Estado: en_analisis
