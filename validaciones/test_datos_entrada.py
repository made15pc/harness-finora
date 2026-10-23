def valor(con, sql):
    return con.execute(sql).fetchone()[0]


def test_clientes_y_meses(con):
    assert valor(con, "select count(distinct ID) from transacciones") == 1961
    assert valor(con, "select count(distinct month) from transacciones") == 34
    assert valor(con, "select min(month) from transacciones") == "2022-01"
    assert valor(con, "select max(month) from transacciones") == "2024-10"


def test_sin_duplicados_cliente_mes(con):
    duplicados = valor(con, """
        select count(*) from (
            select ID, month from transacciones
            group by 1, 2 having count(*) > 1
        )
    """)
    assert duplicados == 0


def test_todos_los_clientes_tienen_industria(con):
    sin_industria = valor(con, """
        select count(distinct t.ID)
        from transacciones t
        left join industria i using (ID)
        where i.ID is null
    """)
    assert sin_industria == 0
    assert valor(con, "select count(*) - count(distinct ID) from industria") == 0


def test_fila_vacia_de_industria_descartada(con):
    assert valor(con, "select count(*) from industria_descartadas") == 1
    assert valor(con, "select count(*) from industria where ID is null or Industria is null") == 0


def test_cifra_base_inicial_108_primeros_pagos_en_febrero(con, definiciones):
    assert "108 primeros pagos" in definiciones["base_inicial"]["motivo"]
    primeros_pagos_feb = valor(con, """
        select count(*) from (
            select ID, min(month) as primer_pago
            from transacciones
            where amount > 0
            group by ID
        )
        where primer_pago = '2022-02'
    """)
    assert primeros_pagos_feb == 108, (
        f"Los datos dan {primeros_pagos_feb} primeros pagos en 2022-02, no 108. "
        "Hay que corregir el motivo de base_inicial en reglas/definiciones.yaml, no este test."
    )
