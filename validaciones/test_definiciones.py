# Coherencia de cliente_mes con el bloque A de reglas/definiciones.yaml.


def valor(con, sql):
    return con.execute(sql).fetchone()[0]


def test_un_solo_mes_de_alta_por_cliente(con):
    clientes_mal = valor(con, """
        select count(*) from (
            select ID
            from cliente_mes
            group by ID
            having count(*) filter (where estado in ('nuevo', 'base_inicial')) <> 1
        )
    """)
    assert clientes_mal == 0


def test_base_inicial_nunca_es_nuevo(con):
    assert valor(con, "select count(*) from cliente_mes where es_base_inicial and estado = 'nuevo'") == 0


def test_ningun_nuevo_antes_de_2022_03(con):
    assert valor(con, "select count(*) from cliente_mes where estado = 'nuevo' and month < '2022-03'") == 0


def test_un_estado_por_cliente_mes(con):
    assert valor(con, "select count(*) from cliente_mes where estado is null or estado_1m is null") == 0
    duplicados = valor(con, """
        select count(*) from (
            select ID, month from cliente_mes group by 1, 2 having count(*) > 1
        )
    """)
    assert duplicados == 0
    assert valor(con, "select count(*) from cliente_mes") == valor(con, "select count(*) from transacciones")


def test_pausa_dura_1_o_2_meses_y_termina_en_retorno(con):
    assert valor(con, "select count(*) from cliente_mes where estado = 'pausa' and meses_en_cero not in (1, 2)") == 0
    mal_cerradas = valor(con, """
        select count(*) from (
            select estado, lead(estado) over (partition by ID order by month) as siguiente
            from cliente_mes
        )
        where estado = 'pausa' and siguiente not in ('pausa', 'retorno_pausa')
    """)
    assert mal_cerradas == 0


def test_reactivado_tiene_churn_previo(con):
    sin_churn = valor(con, """
        select count(*)
        from cliente_mes r
        where r.estado = 'reactivado'
          and not exists (
              select 1 from cliente_mes c
              where c.ID = r.ID and c.estado = 'churn' and c.month < r.month
          )
    """)
    assert sin_churn == 0


def test_pendiente_solo_en_los_ultimos_2_meses(con):
    fuera = valor(con, "select count(*) from cliente_mes where estado = 'pendiente' and month not in ('2024-09', '2024-10')")
    assert fuera == 0


def test_monto_recurrente_mas_cobro_extra_es_amount(con):
    assert valor(con, "select count(*) from cliente_mes where monto_recurrente + cobro_extra <> amount") == 0


def test_cobro_extra_solo_en_meses_de_entrada_o_vuelta(con):
    assert valor(con, "select count(*) from cliente_mes where cobro_extra < 0") == 0
    fuera = valor(con, """
        select count(*) from cliente_mes
        where cobro_extra <> 0
          and estado not in ('nuevo', 'base_inicial', 'retorno_pausa', 'reactivado')
    """)
    assert fuera == 0
