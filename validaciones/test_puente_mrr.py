# Cuadre del puente de MRR (P02) en sus dos versiones: churn de 3 meses y churn_sensibilidad_1m.

import pytest

PUENTES = ["puente_mrr", "puente_mrr_1m"]
MOVIMIENTOS = [
    "base_inicial", "nuevo", "expansion", "contraccion", "salida_pausa",
    "retorno_pausa", "churn", "reactivacion", "salida_pendiente",
]


@pytest.mark.parametrize("puente", PUENTES)
def test_cuadre_mensual(con, puente):
    descuadres = con.execute(f"""
        select month from {puente}
        where mrr_inicial + {" + ".join(MOVIMIENTOS)} <> mrr_final
    """).fetchall()
    assert descuadres == []


@pytest.mark.parametrize("puente", PUENTES)
def test_continuidad(con, puente):
    saltos = con.execute(f"""
        select month from (
            select month, mrr_inicial, lag(mrr_final) over (order by month) as final_anterior
            from {puente}
        )
        where final_anterior is not null and mrr_inicial <> final_anterior
    """).fetchall()
    assert saltos == []


@pytest.mark.parametrize("puente", PUENTES)
def test_mrr_final_igual_a_cliente_mes(con, puente):
    diferencias = con.execute(f"""
        select p.month
        from {puente} p
        join (select month, sum(monto_recurrente) as mrr from cliente_mes group by month) c using (month)
        where p.mrr_final <> c.mrr
    """).fetchall()
    assert diferencias == []
    meses_puente = con.execute(f"select count(*) from {puente}").fetchone()[0]
    meses_datos = con.execute("select count(distinct month) from cliente_mes").fetchone()[0]
    assert meses_puente == meses_datos


def test_mrr_final_no_depende_de_la_regla_de_churn(con):
    finales = con.execute("""
        select
            (select mrr_final from puente_mrr    where month = '2024-10'),
            (select mrr_final from puente_mrr_1m where month = '2024-10')
    """).fetchone()
    assert finales[0] is not None
    assert finales[0] == finales[1]
