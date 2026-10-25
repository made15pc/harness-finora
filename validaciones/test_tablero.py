# Validaciones de docs/index.html (lo genera salidas/generar_tablero.py desde ejecutar.py).
# Se corre aparte, después de generar el tablero: la primera pasada de pytest lo ignora.

import re

import pytest
import yaml

from conftest import RAIZ

TABLERO = RAIZ / "docs" / "index.html"


def cargar(archivo, clave):
    datos = yaml.safe_load((RAIZ / "hallazgos" / archivo).read_text(encoding="utf-8"))
    return datos.get(clave) or []


BORRADORES = [h["id"] for h in cargar("hallazgos.yaml", "hallazgos") if h.get("estado") == "borrador"]
HIPOTESIS_BORRADOR = [h["id"] for h in cargar("hipotesis.yaml", "hipotesis") if h.get("estado") == "borrador"]


@pytest.fixture(scope="module")
def pagina():
    return TABLERO.read_text(encoding="utf-8")


def test_tablero_existe():
    assert TABLERO.exists(), "falta docs/index.html: correr python ejecutar.py"


def test_sin_marcadores_sin_reemplazar(pagina):
    restos = re.findall(r"\{H\d+\}", pagina)
    assert not restos, f"marcadores sin reemplazar: {sorted(set(restos))}"


def test_no_aparecen_hallazgos_en_borrador(pagina):
    # Palabra completa: H1 no debe coincidir dentro de H10.
    presentes = [i for i in BORRADORES if re.search(rf"\b{re.escape(i)}\b", pagina)]
    assert not presentes, f"hallazgos en borrador que aparecen en el tablero: {presentes}"


def test_no_aparecen_hipotesis_en_borrador(pagina):
    # Los ids de hipótesis llevan guion (P01-H1): no deben tener letras, dígitos ni guion pegados.
    presentes = [i for i in HIPOTESIS_BORRADOR if re.search(rf"(?<![\w-]){re.escape(i)}(?![\w-])", pagina)]
    assert not presentes, f"hipótesis en borrador que aparecen en el tablero: {presentes}"
