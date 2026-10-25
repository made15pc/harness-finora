-- Puente de MRR (P02): una fila por mes desde 2022-01.
-- Sigue el bloque B de reglas/definiciones.yaml. Solo usa monto_recurrente, nunca amount.
-- puente_mrr usa estado (churn de 3 meses); puente_mrr_1m usa estado_1m (churn_sensibilidad_1m).
-- cobro_extra es informativo: no entra en el cuadre.

create or replace temp table movimientos_mrr as
with por_regla as (
    select 'churn_3m' as regla, ID, month, estado, monto_recurrente, cobro_extra from cliente_mes
    union all
    select 'churn_1m' as regla, ID, month, estado_1m, monto_recurrente, cobro_extra from cliente_mes
),

con_anterior as (
    select
        *,
        coalesce(lag(monto_recurrente) over (partition by regla, ID order by month), 0) as monto_recurrente_anterior
    from por_regla
)

select
    regla,
    month,
    sum(case when estado = 'base_inicial'  then monto_recurrente else 0 end)                              as base_inicial,
    sum(case when estado = 'nuevo'         then monto_recurrente else 0 end)                              as nuevo,
    sum(case when estado = 'activo' and monto_recurrente > monto_recurrente_anterior
             then monto_recurrente - monto_recurrente_anterior else 0 end)                                as expansion,
    sum(case when estado = 'activo' and monto_recurrente < monto_recurrente_anterior
             then monto_recurrente - monto_recurrente_anterior else 0 end)                                as contraccion,
    sum(case when estado = 'pausa'         then -monto_recurrente_anterior else 0 end)                    as salida_pausa,
    sum(case when estado = 'retorno_pausa' then monto_recurrente else 0 end)                              as retorno_pausa,
    sum(case when estado = 'churn'         then -monto_recurrente_anterior else 0 end)                    as churn,
    sum(case when estado = 'reactivado'    then monto_recurrente else 0 end)                              as reactivacion,
    sum(case when estado = 'pendiente'     then -monto_recurrente_anterior else 0 end)                    as salida_pendiente,
    sum(monto_recurrente)                                                                                 as mrr_final,
    sum(cobro_extra)                                                                                      as cobro_extra
from con_anterior
group by regla, month;

create or replace table puente_mrr as
select
    month,
    coalesce(lag(mrr_final) over (order by month), 0) as mrr_inicial,
    base_inicial, nuevo, expansion, contraccion, salida_pausa, retorno_pausa,
    churn, reactivacion, salida_pendiente, mrr_final, cobro_extra
from movimientos_mrr
where regla = 'churn_3m'
order by month;

create or replace table puente_mrr_1m as
select
    month,
    coalesce(lag(mrr_final) over (order by month), 0) as mrr_inicial,
    base_inicial, nuevo, expansion, contraccion, salida_pausa, retorno_pausa,
    churn, reactivacion, salida_pendiente, mrr_final, cobro_extra
from movimientos_mrr
where regla = 'churn_1m'
order by month;

drop table movimientos_mrr;
