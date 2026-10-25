# Finora — nota corta

**Mensaje principal (H38, inferencia):** desde 2023 la adquisición está plana en cantidad (54,2 → 55,4 clientes nuevos/mes; H32, H33) y en valor; el ticket mediano de entrada cae 12,5% (H37) en 5 de 6 industrias (H28), y ni el recorte de gasto ni la retención lo explican.
**Tablero:** https://made15pc.github.io/harness-finora/ · **Repo:** https://github.com/made15pc/harness-finora

## 1. Qué preguntas prioricé

- **P01 (CRO), principal.** Habilita la decisión más urgente: dónde intervenir para volver a crecer. Sin datos de funnel, la abordé desde el resultado: clientes nuevos, ticket inicial, retención y gasto.
- **P02 (CFO), acotada.** Construí el puente de MRR y diseñé el modelo de descuentos, sin cuantificarlo: con solo el monto cobrado, contracción y descuento no se pueden separar.

## 2. Qué supuestos hice

- **Base inicial:** los clientes con primer pago en 2022-01 o 2022-02 ya existían y no cuentan como adquisición.
- **Churn:** 3 meses seguidos en 0, fechado en el primer mes en 0. Medí la sensibilidad con una regla de 1 mes: en 2022 el churn pasa de −9,5 M a −31,8 M (H11, H14).
- **Pausa:** un hueco de 1 o 2 meses seguido de un nuevo pago no es churn.
- **monto_recurrente y cobro_extra:** separan los pagos atrasados o prepagos del ingreso recurrente.
- **Retención:** la medí como supervivencia sin churn hasta el mes N, solo cuando N ≤ 2024-08.
- **Ticket de entrada:** usé la mediana, por la asimetría de los montos.
- **Corte antes/después:** 2023-06, con comparación de promedios mensuales.
- **Escala de SM_spend:** la tomé tal como la indica el enunciado. Como el gasto supera al MRR, cito solo variaciones %: el gasto baja 39,8% (H36).

## 3. Qué información hizo falta

- Eventos de etapa del funnel con fechas de entrada y salida.
- Fuente y motion de cada lead (self-serve, entrada directa a SQL o SDR).
- Vínculo lead → cliente.
- Precio de lista y descuentos con su vigencia (bloque C).
- Gasto S&M por canal.
- Aclaración de Team frente a PayrollExpenses (posible doble conteo) y confirmación de la escala del gasto.

## 4. Qué cambiaría del modelo actual

- Medir el funnel por cohorte de entrada y por motion, en vez de calcular conversiones entre fotos del funnel.
- Usar "alcanzó etapa" para tolerar los leads que se saltan etapas.
- Separar MRR contratado, descuento y MRR neto, para que un descuento que expira no cuente como expansión.
- Definir si "cliente nuevo" es el Won del CRM o el primer pago (hoy es el primer pago).
- Mantener un único glosario versionado de métricas, como `reglas/definiciones.yaml`.

## 5. Cómo usé la IA, qué validé y cómo aseguré la calidad

- **Analista:** Claude Code registró las hipótesis antes de calcular, escribió el SQL y propuso los veredictos.
- **Revisor:** un agente independiente, de solo lectura, intentó refutar cada veredicto.
- **Tablero:** lo armó un agente constructor que solo usa hallazgos aprobados.
- **Cálculo:** todo en SQL determinista (DuckDB), sin cifras escritas a mano.
- **Validaciones:** hay 82 tests automáticos, y cada hecho se recalcula desde su consulta en cada corrida.
- **Aprobación humana:** yo aprobé las definiciones, las hipótesis y los veredictos.

**Ejemplo:** la primera lectura decía que los clientes nuevos crecían +73,3% (H34). El revisor mostró que esa cifra mezclaba la rampa de 2022 (27,2 clientes/mes; H31) con un nivel que está plano desde 2023 (H32, H33). La hipótesis del CRO pasó a no concluyente y la conclusión se corrigió antes de publicar.
