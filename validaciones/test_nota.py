# Validaciones de docs/nota_corta.md: cada id citado existe y está aprobado, y cada cifra
# escrita junto a un id coincide con el valor del hallazgo, en el formato es-CL del tablero.
#
# Una cita es un paréntesis que contiene ids, p. ej. "(H32, H33)". Las cifras de su tramo
# (desde la cita anterior en la misma línea hasta el cierre del paréntesis) se comparan con
# los valores de los hallazgos citados.
# - Cifra con decimales, "M" o "%" que no coincide: falla.
# - Entero sin formato que no coincide (p. ej. "6" en "5 de 6"), o cifra fuera de una cita:
#   se lista como no verificable, sin fallar.
# No se tratan como cifras: fechas (2023-06), años (2022), URLs, títulos y enumeradores "(1)".

import importlib.util
import re
import warnings

import pytest
import yaml

from conftest import RAIZ

NOTA = RAIZ / "docs" / "nota_corta.md"

especificacion = importlib.util.spec_from_file_location("generar_tablero", RAIZ / "salidas" / "generar_tablero.py")
tablero = importlib.util.module_from_spec(especificacion)
especificacion.loader.exec_module(tablero)

ID = r"P\d{2}-H\d+|H\d+"
CITA = re.compile(rf"\([^()]*\b(?:{ID})\b[^()]*\)")
CIFRA = re.compile(r"[+−-]?\d{1,3}(?:\.\d{3})*(?:,\d+)?(?:\s?M\b)?%?")
NO_CIFRA = re.compile(rf"https?://\S+|\(\d\)|\b(?:{ID})\b|\bP\d{{2}}\b|\b\d{{4}}-\d{{2}}\b|\b20\d{{2}}\b")


def cargar(archivo, clave):
    datos = yaml.safe_load((RAIZ / "hallazgos" / archivo).read_text(encoding="utf-8"))
    return {h["id"]: h for h in datos.get(clave) or []}


HALLAZGOS = cargar("hallazgos.yaml", "hallazgos")
HIPOTESIS = cargar("hipotesis.yaml", "hipotesis")


@pytest.fixture(scope="module")
def nota():
    return NOTA.read_text(encoding="utf-8")


def cifras(texto):
    return [c.strip() for c in CIFRA.findall(NO_CIFRA.sub(" ", texto)) if re.search(r"\d", c)]


def formas_validas(id_hallazgo):
    """Formas es-CL en que puede escribirse el valor del hallazgo (con o sin signo)."""
    hallazgo = HALLAZGOS.get(id_hallazgo)
    if not hallazgo or hallazgo.get("valor") is None:
        return set()
    valor = float(hallazgo["valor"])
    formas = set()
    for x in (valor, abs(valor)):
        formas |= {tablero.valor_formateado({**hallazgo, "valor": x}), tablero.monto_es(x),
                   tablero.numero_es(x, 1), tablero.numero_es(x, 0)}
    return formas


def normalizar(cifra):
    return cifra.replace("-", tablero.MENOS).lstrip("+").rstrip("%").replace(" ", " ")


def revisar_cifras(nota):
    """Devuelve (verificadas, erróneas, no_verificables)."""
    verificadas, erroneas, no_verificables = [], [], []
    for linea in nota.splitlines():
        if linea.startswith("#"):
            continue
        inicio = 0
        for cita in CITA.finditer(linea):
            ids = re.findall(rf"\b(?:{ID})\b", cita.group())
            formas = set().union(*(formas_validas(i) for i in ids))
            for cifra in cifras(linea[inicio:cita.end()]):
                if normalizar(cifra) in formas:
                    verificadas.append((cifra, ids))
                elif re.search(r"[,%M]", cifra):
                    erroneas.append((cifra, ids))
                else:
                    no_verificables.append(cifra)
            inicio = cita.end()
        no_verificables += cifras(linea[inicio:])
    return verificadas, erroneas, no_verificables


def test_nota_existe():
    assert NOTA.exists(), "falta docs/nota_corta.md"


def test_ids_citados_existen_y_estan_aprobados(nota):
    citados = sorted(set(re.findall(rf"\b(?:{ID})\b", nota)))
    assert citados, "la nota no cita ningún id"
    malos = []
    for id_citado in citados:
        registro = HIPOTESIS.get(id_citado) if "-" in id_citado else HALLAZGOS.get(id_citado)
        if registro is None:
            malos.append(f"{id_citado} no existe")
        elif registro.get("estado") != "aprobado":
            malos.append(f"{id_citado} está en {registro.get('estado')}")
    assert not malos, malos


def test_cifras_junto_a_un_id_coinciden(nota):
    verificadas, erroneas, no_verificables = revisar_cifras(nota)
    print(f"\nCifras verificadas ({len(verificadas)}):")
    for cifra, ids in verificadas:
        print(f"  {cifra}  ← {', '.join(ids)}")
    print(f"No verificables automáticamente ({len(no_verificables)}): {', '.join(no_verificables)}")
    if no_verificables:
        warnings.warn(f"Cifras de la nota no verificables automáticamente: {', '.join(no_verificables)}")
    assert verificadas, "no se verificó ninguna cifra"
    assert not erroneas, f"cifras que no coinciden con su hallazgo: {erroneas}"
