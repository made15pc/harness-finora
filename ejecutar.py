"""Orquesta el harness: limpieza, consultas, exportación, validaciones y tablero."""

import re
import subprocess
import sys
from pathlib import Path

import duckdb

RAIZ = Path(__file__).parent
BASE = RAIZ / "datos" / "finora.duckdb"
TABLAS = RAIZ / "datos" / "tablas"


def archivos_sql():
    archivos = [RAIZ / "sql" / "1_limpieza.sql", RAIZ / "sql" / "2_cliente_mes.sql"]
    archivos += sorted((RAIZ / "sql" / "preguntas").glob("*.sql"))
    return [a for a in archivos if a.exists()]


def main():
    BASE.unlink(missing_ok=True)
    con = duckdb.connect(str(BASE))
    con.execute(f"set file_search_path = '{RAIZ.as_posix()}'")

    for archivo in archivos_sql():
        print(f"Ejecutando {archivo.relative_to(RAIZ)}", flush=True)
        con.execute(archivo.read_text(encoding="utf-8"))

    TABLAS.mkdir(exist_ok=True)
    for (tabla,) in con.execute("select table_name from information_schema.tables order by 1").fetchall():
        destino = (TABLAS / f"{tabla}.csv").as_posix()
        con.execute(f"copy {tabla} to '{destino}' (header)")
        print(f"Exportada datos/tablas/{tabla}.csv", flush=True)
    con.close()

    # test_tablero.py se corre aparte, después de generar el tablero.
    resultado = subprocess.run(
        [sys.executable, "-m", "pytest", "validaciones", "-v", "--ignore=validaciones/test_tablero.py"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    print(resultado.stdout, end="", flush=True)
    print(resultado.stderr, end="", file=sys.stderr, flush=True)
    if resultado.returncode != 0:
        print("Validaciones fallidas: proceso detenido.")
        sys.exit(resultado.returncode)
    print("Validaciones OK.", flush=True)

    pasadas = re.search(r"(\d+) passed", resultado.stdout)
    if not pasadas:
        print("No se pudo leer el número de pruebas pasadas: proceso detenido.")
        sys.exit(1)
    pruebas = pasadas.group(1)
    tablero = subprocess.run([sys.executable, str(RAIZ / "salidas" / "generar_tablero.py"), "--pruebas", pruebas], cwd=RAIZ)
    if tablero.returncode != 0:
        print("Generación del tablero fallida: proceso detenido.")
        sys.exit(tablero.returncode)

    resultado = subprocess.run([sys.executable, "-m", "pytest", "validaciones/test_tablero.py", "-v"], cwd=RAIZ)
    if resultado.returncode != 0:
        print("Validaciones del tablero fallidas: proceso detenido.")
        sys.exit(resultado.returncode)
    print("Tablero OK.")


if __name__ == "__main__":
    main()
