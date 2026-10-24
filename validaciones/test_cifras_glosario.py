# Cifras citadas en los motivos de reglas/definiciones.yaml.
# Un hueco cerrado termina en retorno_pausa o reactivado; su largo es meses_en_cero del mes anterior.

MENSAJE = "corregir el motivo en definiciones.yaml, no el test"

HUECOS_CERRADOS = """
    select largo from (
        select estado, lag(meses_en_cero) over (partition by ID order by month) as largo
        from cliente_mes
    )
    where estado in ('retorno_pausa', 'reactivado')
"""


def contar(con, condicion):
    return con.execute(f"select count(*) from ({HUECOS_CERRADOS}) where {condicion}").fetchone()[0]


def porcentaje(parte, total):
    return f"{parte / total * 100:.1f}".replace(".", ",") + "%"


def test_468_huecos_cerrados(con, definiciones):
    total = contar(con, "true")
    assert "468 huecos" in definiciones["churn"]["motivo"], MENSAJE
    assert total == 468, f"Los datos dan {total} huecos cerrados, no 468: {MENSAJE}"


def test_330_huecos_de_1_mes(con, definiciones):
    total = contar(con, "true")
    un_mes = contar(con, "largo = 1")
    assert un_mes == 330, f"Los datos dan {un_mes} huecos de 1 mes, no 330: {MENSAJE}"
    assert porcentaje(un_mes, total) in definiciones["pausa"]["motivo"], (
        f"El porcentaje real es {porcentaje(un_mes, total)}: {MENSAJE}"
    )


def test_392_huecos_de_1_o_2_meses(con, definiciones):
    total = contar(con, "true")
    corto = contar(con, "largo <= 2")
    assert corto == 392, f"Los datos dan {corto} huecos de 1 o 2 meses, no 392: {MENSAJE}"
    assert porcentaje(corto, total) in definiciones["churn"]["motivo"], (
        f"El porcentaje real es {porcentaje(corto, total)}: {MENSAJE}"
    )


# Cifras del motivo de monto_recurrente.
CASOS_COBRO_EXTRA = """
    select estado, lag(meses_en_cero) over (partition by ID order by month) as largo, cobro_extra
    from cliente_mes
"""


def casos_cobro_extra(con, condicion="true"):
    return con.execute(
        f"select count(*) from ({CASOS_COBRO_EXTRA}) where cobro_extra > 0 and {condicion}"
    ).fetchone()[0]


def test_293_casos_de_cobro_extra(con, definiciones):
    assert "En 293 meses" in definiciones["monto_recurrente"]["motivo"], MENSAJE
    total = casos_cobro_extra(con)
    assert total == 293, f"Los datos dan {total} casos de cobro extra, no 293: {MENSAJE}"


def test_casos_de_cobro_extra_por_estado(con, definiciones):
    esperados = {"base_inicial": 51, "nuevo": 88, "retorno_pausa": 140, "reactivado": 14}
    motivo = definiciones["monto_recurrente"]["motivo"]
    for estado, esperado in esperados.items():
        assert f"{esperado} {estado}" in motivo, MENSAJE
        real = casos_cobro_extra(con, f"estado = '{estado}'")
        assert real == esperado, f"{estado}: los datos dan {real}, no {esperado}: {MENSAJE}"


def test_casos_de_retorno_pausa_por_largo_del_hueco(con):
    un_mes = casos_cobro_extra(con, "estado = 'retorno_pausa' and largo = 1")
    dos_meses = casos_cobro_extra(con, "estado = 'retorno_pausa' and largo = 2")
    assert un_mes == 116, f"Los datos dan {un_mes} tras hueco de 1 mes, no 116: {MENSAJE}"
    assert dos_meses == 24, f"Los datos dan {dos_meses} tras hueco de 2 meses, no 24: {MENSAJE}"


def test_cobro_extra_es_1_43_por_ciento_del_amount(con, definiciones):
    extra, total = con.execute("select sum(cobro_extra), sum(amount) from cliente_mes").fetchone()
    real = f"{extra / total * 100:.2f}".replace(".", ",") + "%"
    assert real == "1,43%", f"El cobro extra es {real} del amount, no 1,43%: {MENSAJE}"
    assert real in definiciones["monto_recurrente"]["motivo"], MENSAJE
