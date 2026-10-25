# Reglas 11 y 12 de CLAUDE.md sobre hallazgos/hipotesis.yaml.

import yaml

from conftest import RAIZ

VEREDICTOS_CON_EVIDENCIA = ("apoyada", "descartada", "no_concluyente")


def cargar(archivo, clave):
    datos = yaml.safe_load((RAIZ / "hallazgos" / archivo).read_text(encoding="utf-8"))
    return datos.get(clave) or []


HIPOTESIS = cargar("hipotesis.yaml", "hipotesis")
HECHOS = {h["id"] for h in cargar("hallazgos.yaml", "hallazgos") if h["tipo"] == "hecho"}


def test_ids_unicos():
    ids = [h["id"] for h in HIPOTESIS]
    assert len(ids) == len(set(ids))


def test_origen_valido():
    malas = [h["id"] for h in HIPOTESIS if h.get("origen") not in ("caso", "analista", "revisor")]
    assert malas == []


def test_veredicto_con_evidencia_de_hechos():
    malas = [
        h["id"] for h in HIPOTESIS
        if h.get("veredicto") in VEREDICTOS_CON_EVIDENCIA
        and not set(h.get("evidencia") or []) & HECHOS
    ]
    assert malas == []


def test_no_evaluable_declara_dato_faltante():
    malas = [
        h["id"] for h in HIPOTESIS
        if h.get("veredicto") == "no_evaluable" and not str(h.get("dato_faltante") or "").strip()
    ]
    assert malas == []
