# Trazabilidad de hallazgos/hallazgos.yaml: cada hecho se recalcula desde su consulta.
# Se carga con BaseLoader para leer valor tal como está escrito (con sus decimales).

from decimal import Decimal

import pytest
import yaml

from conftest import RAIZ


def cargar_hallazgos():
    datos = yaml.load((RAIZ / "hallazgos" / "hallazgos.yaml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    return datos.get("hallazgos") or []


HALLAZGOS = cargar_hallazgos()
HECHOS = [h for h in HALLAZGOS if h["tipo"] == "hecho"]
INFERENCIAS = [h for h in HALLAZGOS if h["tipo"] == "inferencia"]


def test_ids_unicos():
    ids = [h["id"] for h in HALLAZGOS]
    assert len(ids) == len(set(ids))


def test_tipos_validos():
    assert all(h["tipo"] in ("hecho", "inferencia") for h in HALLAZGOS)


@pytest.mark.parametrize("hallazgo", HECHOS, ids=[h["id"] for h in HECHOS])
def test_hecho_recalcula_su_valor(con, hallazgo):
    assert hallazgo.get("consulta"), "un hecho necesita consulta"
    assert "{valor}" in hallazgo["afirmacion"]
    filas = con.execute(hallazgo["consulta"]).fetchall()
    assert len(filas) == 1 and len(filas[0]) == 1, "la consulta debe devolver un solo valor"
    escrito = Decimal(hallazgo["valor"])
    calculado = Decimal(str(filas[0][0])).quantize(escrito)
    assert calculado == escrito


@pytest.mark.parametrize("hallazgo", INFERENCIAS, ids=[h["id"] for h in INFERENCIAS])
def test_inferencia_basada_en_hechos(hallazgo):
    ids_hechos = {h["id"] for h in HECHOS}
    basada_en = hallazgo.get("basada_en") or []
    assert basada_en, "una inferencia necesita basada_en"
    assert set(basada_en) <= ids_hechos
