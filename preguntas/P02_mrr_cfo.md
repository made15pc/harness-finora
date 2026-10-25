# P02 — "¿Qué está pasando con el negocio subyacente y cuánto revenue estamos dejando de capturar por decisiones comerciales?"

- Quién pregunta: CFO
- Qué decisión habilita: separar crecimiento real de efectos comerciales (descuentos) y medir su costo.
- Subpreguntas:
  1. Si un cliente pagaba 100 y ahora paga 80, ¿contrajo 20 o recibió un descuento?
  2. ¿Qué pasa si su suscripción creció de 100 a 130, pero tiene un descuento de 30 y sigue pagando 100?
  3. ¿Y cuando desaparezca el descuento, eso cuenta como expansión?
- Definiciones que usa:
  - Bloque A (A_ciclo_de_vida): antes_de_alta, base_inicial, cliente_nuevo, activo, pausa, retorno_pausa, churn, inactivo, reactivacion, pendiente, churn_sensibilidad_1m.
  - Bloque B (B_mrr): mrr, expansion, contraccion, monto_recurrente, cobro_extra.
  - Bloque C (C_descuentos, diseño): mrr_contratado, descuento, mrr_neto, descuento_expirado, revenue_no_capturado.
- Datos disponibles: Transactions.
- Datos que faltan: Precio de lista o plan por cliente-mes, y registro de descuentos con fecha de inicio y fin.
- Hipótesis: ver hallazgos/hipotesis.yaml (se formulan antes de calcular)
- Plan de análisis: (lo propone el analista; requiere aprobación)
- Límites: con monto cobrado únicamente, descuento y contracción no se pueden separar.
- Revisión: (lo completa el revisor)
- Estado: revisada
