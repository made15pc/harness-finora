"""Orquesta el harness: limpieza, consultas, exportación y validaciones."""

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

    resultado = subprocess.run([sys.executable, "-m", "pytest", "validaciones", "-v"], cwd=RAIZ)
    if resultado.returncode != 0:
        print("Validaciones fallidas: proceso detenido.")
        sys.exit(resultado.returncode)
    print("Validaciones OK.")


if __name__ == "__main__":
    main()
