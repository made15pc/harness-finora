-- Ciclo de vida del cliente: una fila por cliente y mes.
-- Sigue el bloque A de reglas/definiciones.yaml. Toda la lógica con funciones de ventana.
--
-- Hueco: racha de meses consecutivos en 0 después del primer pago.
-- Cada pago abre un "tramo" (el pago y los meses en 0 que lo siguen); el hueco
-- de un tramo es lo que viene después de su pago.

create or replace table cliente_mes as
with base as (
    select
        t.ID,
        t.month,
        t.amount,
        i.Industria,
        t.amount > 0                                                           as paga,
        lag(t.amount) over (partition by t.ID order by t.month)                as monto_mes_anterior,
        min(case when t.amount > 0 then t.month end) over (partition by t.ID)  as cohorte,
        max(case when t.amount > 0 then t.month end) over (partition by t.ID)  as ultimo_pago
    from transacciones t
    left join industria i using (ID)
),

tramos as (
    select
        *,
        cohorte in ('2022-01', '2022-02')                                        as es_base_inicial,
        month < cohorte or cohorte is null                                       as es_antes_de_alta,
        sum(case when paga then 1 else 0 end) over (partition by ID order by month) as tramo
    from base
),

huecos as (
    select
        *,
        -- largo total del hueco en 0 del tramo
        count(*) filter (where not paga) over (partition by ID, tramo)                as largo_hueco,
        -- posición del mes dentro del hueco (1 = primer mes en 0)
        row_number() over (partition by ID, tramo order by month) - 1                 as posicion_hueco,
        -- el hueco termina en pago si hay un pago posterior
        ultimo_pago > month                                                           as hueco_cerrado
    from tramos
),

con_anterior as (
    select
        *,
        lag(largo_hueco) over (partition by ID order by month) as largo_hueco_anterior,
        lag(paga)        over (partition by ID order by month) as pago_mes_anterior,
        lead(amount)     over (partition by ID order by month) as monto_mes_siguiente
    from huecos
),

clasificado as (
select
    ID,
    month,
    amount,
    Industria,
    monto_mes_anterior,
    monto_mes_siguiente,
    cohorte,
    es_base_inicial,
    case
        when es_antes_de_alta then null
        when paga then 0
        else largo_hueco
    end as meses_en_cero,

    case
        when es_antes_de_alta                       then 'antes_de_alta'
        when paga and month = cohorte               then case when es_base_inicial then 'base_inicial' else 'nuevo' end
        when paga and pago_mes_anterior             then 'activo'
        when paga and largo_hueco_anterior <= 2     then 'retorno_pausa'
        when paga                                   then 'reactivado'
        when largo_hueco >= 3 and posicion_hueco = 1 then 'churn'
        when largo_hueco >= 3                       then 'inactivo'
        when hueco_cerrado                          then 'pausa'
        else 'pendiente'
    end as estado,

    -- churn_sensibilidad_1m: cualquier mes en 0 después de pagar es churn
    case
        when es_antes_de_alta                       then 'antes_de_alta'
        when paga and month = cohorte               then case when es_base_inicial then 'base_inicial' else 'nuevo' end
        when paga and pago_mes_anterior             then 'activo'
        when paga                                   then 'reactivado'
        when posicion_hueco = 1                     then 'churn'
        else 'inactivo'
    end as estado_1m

from con_anterior
),

-- monto_recurrente: en los meses de entrada o vuelta, si amount es k veces (k >= 2)
-- el amount del mes siguiente, el exceso es cobro_extra (atrasos o prepagos).
-- Tolerancia de 0,01 sobre el monto.
recurrente as (
    select
        *,
        case
            when estado in ('nuevo', 'base_inicial', 'retorno_pausa', 'reactivado')
             and monto_mes_siguiente > 0
             and round(amount / monto_mes_siguiente) >= 2
             and abs(amount - round(amount / monto_mes_siguiente) * monto_mes_siguiente) <= 0.01
            then monto_mes_siguiente
            else amount
        end as monto_recurrente
    from clasificado
)

select
    ID,
    month,
    amount,
    Industria,
    monto_mes_anterior,
    cohorte,
    es_base_inicial,
    meses_en_cero,
    estado,
    estado_1m,
    monto_recurrente,
    amount - monto_recurrente as cobro_extra
from recurrente
order by ID, month;
