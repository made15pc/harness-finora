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
- Plan de análisis: (lo propone el analista; requiere aprobación)
- Límites: no hay datos de leads ni de etapas; toda conclusión sobre el funnel se infiere desde el resultado (clientes nuevos, ticket, retención, gasto).
- Revisión: (lo completa el revisor)
- Estado: registrada
