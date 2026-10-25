-- Adquisición (P01): prueba P01-H5 a P01-H8 de hallazgos/hipotesis.yaml.
-- Sigue los bloques A y D de reglas/definiciones.yaml.
-- Períodos: antes = 2022-03 a 2023-05; despues = 2023-06 a 2024-10.
-- Industria se usa solo como segmento.

create or replace temp table clientes_nuevos as
select
    ID,
    month                                                      as cohorte,
    Industria,
    monto_recurrente                                           as ticket_inicial,
    case when month < '2023-06' then 'antes' else 'despues' end as periodo
from cliente_mes
where estado = 'nuevo';

-- adquisicion_mes: una fila por mes desde 2022-03.
-- cac_3m queda vacío en 2022-03 y 2022-04: su ventana incluiría 2022-01 y 2022-02,
-- meses sin cliente_nuevo por definición (base_inicial).
create or replace table adquisicion_mes as
with por_mes as (
    select
        g.Month                                                        as month,
        g.total                                                        as gasto_sm,
        count(n.ID)                                                    as clientes_nuevos,
        coalesce(sum(n.ticket_inicial), 0)                             as ticket_inicial_total
    from gasto_sm g
    left join clientes_nuevos n on n.cohorte = g.Month
    group by g.Month, g.total
),

ventana as (
    select
        *,
        sum(gasto_sm)        over (order by month rows between 2 preceding and current row) as gasto_sm_3m,
        sum(clientes_nuevos) over (order by month rows between 2 preceding and current row) as clientes_nuevos_3m
    from por_mes
)

select
    month,
    case when month < '2023-06' then 'antes' else 'despues' end            as periodo,
    clientes_nuevos,
    ticket_inicial_total,
    gasto_sm,
    gasto_sm / nullif(clientes_nuevos, 0)                                  as cac,
    case when month >= '2022-05' then gasto_sm_3m / clientes_nuevos_3m end as cac_3m
from ventana
where month >= '2022-03'
order by month;

-- adquisicion_industria: una fila por período e Industria.
create or replace table adquisicion_industria as
select
    periodo,
    Industria,
    count(*)                                                           as clientes_nuevos,
    100.0 * count(*) / sum(count(*)) over (partition by periodo)       as participacion,
    median(ticket_inicial)                                             as ticket_inicial_mediana
from clientes_nuevos
group by periodo, Industria
order by periodo, Industria;

-- retencion_cohortes: una fila por cohorte mensual de adquisición.
-- Retenido a N meses: ningún churn entre el alta y el mes N (inclusive).
-- Vacío si el mes N supera 2024-08 (último churn de 3 meses confirmable).
create or replace table retencion_cohortes as
with primer_churn as (
    select n.ID, n.cohorte, n.periodo, min(c.month) as mes_churn
    from clientes_nuevos n
    left join cliente_mes c on c.ID = n.ID and c.estado = 'churn'
    group by n.ID, n.cohorte, n.periodo
),

meses_n as (
    select
        *,
        strftime(strptime(cohorte, '%Y-%m') + interval 3 month,  '%Y-%m') as mes_3,
        strftime(strptime(cohorte, '%Y-%m') + interval 6 month,  '%Y-%m') as mes_6,
        strftime(strptime(cohorte, '%Y-%m') + interval 12 month, '%Y-%m') as mes_12
    from primer_churn
)

select
    cohorte,
    periodo,
    count(*) as clientes,
    case when max(mes_3)  <= '2024-08' then 100.0 * count(*) filter (where mes_churn is null or mes_churn > mes_3)  / count(*) end as retencion_3m,
    case when max(mes_6)  <= '2024-08' then 100.0 * count(*) filter (where mes_churn is null or mes_churn > mes_6)  / count(*) end as retencion_6m,
    case when max(mes_12) <= '2024-08' then 100.0 * count(*) filter (where mes_churn is null or mes_churn > mes_12) / count(*) end as retencion_12m
from meses_n
group by cohorte, periodo
order by cohorte;

drop table clientes_nuevos;
