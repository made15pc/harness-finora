-- Limpieza de datos/originales/ según reglas/fuentes.yaml.
-- Único lugar donde se convierten unidades (CLAUDE.md, regla 2).
-- Se lee todo como texto y se convierte de forma explícita.
-- Las columnas de origen conservan su nombre, con el valor ya limpio (CLAUDE.md, regla 8).

-- ── transacciones ─────────────────────────────────────────────────────
-- month "M/D/YYYY" (último día del mes) → "YYYY-MM"
-- amount × 10.000 = monto real
create or replace table transacciones as
select
    cast(ID as integer)                                             as ID,
    strftime(strptime(month, '%m/%d/%Y'), '%Y-%m')                  as month,
    cast(cast(amount as decimal(18, 6)) * 10000 as decimal(18, 2))  as amount
from read_csv('datos/originales/Transactions.csv', all_varchar = true, header = true)
order by ID, month;

-- ── gasto_sm ──────────────────────────────────────────────────────────
-- Valores "$1.040" → quitar "$", el punto es separador decimal.
-- valor × 100.000.000 = monto real. Negativos (reversos): se conservan y se marcan.
create or replace macro a_monto_sm(valor) as
    cast(cast(replace(valor, '$', '') as decimal(18, 3)) * 100000000 as decimal(18, 2));

create or replace table gasto_sm as
with convertido as (
    select
        Month,
        a_monto_sm(PaidMedia)        as PaidMedia,
        a_monto_sm(Travel)           as Travel,
        a_monto_sm(PublicidadNoWeb)  as PublicidadNoWeb,
        a_monto_sm(Freelance)        as Freelance,
        a_monto_sm(SoftwareTools)    as SoftwareTools,
        a_monto_sm(Team)             as Team,
        a_monto_sm(PayrollExpenses)  as PayrollExpenses
    from read_csv('datos/originales/SM_spend.csv', all_varchar = true, header = true)
)
select
    *,
    PaidMedia + Travel + PublicidadNoWeb + Freelance
        + SoftwareTools + Team + PayrollExpenses             as total,
    least(PaidMedia, Travel, PublicidadNoWeb, Freelance,
          SoftwareTools, Team, PayrollExpenses) < 0          as tiene_negativo
from convertido
order by Month;

drop macro a_monto_sm;

-- ── industria ─────────────────────────────────────────────────────────
-- ID "Cliente N" → entero N. Filas vacías: se descartan y se reportan.
create or replace table industria_cruda as
select ID, Industria
from read_csv('datos/originales/Industry.csv', all_varchar = true, header = true);

create or replace table industria_descartadas as
select *
from industria_cruda
where nullif(trim(ID), '') is null or nullif(trim(Industria), '') is null;

create or replace table industria as
select
    cast(regexp_extract(ID, 'Cliente (\d+)', 1) as integer) as ID,
    trim(Industria)                                          as Industria
from industria_cruda
where nullif(trim(ID), '') is not null and nullif(trim(Industria), '') is not null
order by ID;

drop table industria_cruda;
