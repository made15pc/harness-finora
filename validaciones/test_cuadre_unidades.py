# Cuadre entre las tablas limpias y los CSV originales.
# Los multiplicadores se leen de reglas/fuentes.yaml: el test no convierte, compara.


def valor(con, sql):
    return con.execute(sql).fetchone()[0]


def test_suma_transacciones(con, fuentes):
    multiplicador = fuentes["transacciones"]["columnas"]["amount"]["multiplicador"]
    suma_original = valor(con, """
        select sum(cast(amount as decimal(18, 6)))
        from read_csv('datos/originales/Transactions.csv', all_varchar = true, header = true)
    """)
    suma_limpia = valor(con, "select sum(amount) from transacciones")
    assert suma_limpia == suma_original * multiplicador


def test_suma_gasto_sm(con, fuentes):
    multiplicador = fuentes["gasto_sm"]["formato_gasto"]["multiplicador"]
    columnas = fuentes["gasto_sm"]["columnas_gasto"]
    suma_fila = " + ".join(f"cast(replace({c}, '$', '') as decimal(18, 3))" for c in columnas)
    suma_original = valor(con, f"""
        select sum({suma_fila})
        from read_csv('datos/originales/SM_spend.csv', all_varchar = true, header = true)
    """)
    suma_limpia = valor(con, "select sum(total) from gasto_sm")
    assert suma_limpia == suma_original * multiplicador


def test_control_manual_gasto_2022_01(con):
    # Fila 2022-01 del CSV: 1,040 + 0,120 + 0,340 + 0,100 + 0,080 + 0,240 + 0,080 = 2,00
    assert valor(con, "select total from gasto_sm where Month = '2022-01'") == 200_000_000
