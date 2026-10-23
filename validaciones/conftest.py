from pathlib import Path

import duckdb
import pytest
import yaml

RAIZ = Path(__file__).parents[1]


@pytest.fixture(scope="session")
def con():
    conexion = duckdb.connect(str(RAIZ / "datos" / "finora.duckdb"), read_only=True)
    conexion.execute(f"set file_search_path = '{RAIZ.as_posix()}'")
    yield conexion
    conexion.close()


@pytest.fixture(scope="session")
def fuentes():
    return yaml.safe_load((RAIZ / "reglas" / "fuentes.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def definiciones():
    datos = yaml.safe_load((RAIZ / "reglas" / "definiciones.yaml").read_text(encoding="utf-8"))
    return {d["nombre"]: d for d in datos["definiciones"]}
