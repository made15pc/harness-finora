"""Genera docs/index.html: tablero autocontenido a partir de datos/tablas/*.csv y hallazgos/*.yaml.

Reglas (ver .claude/agents/constructor-tablero.md):
- Cero cifras a mano: toda cifra sale de un CSV o del valor de un hallazgo aprobado.
- Un marcador {Hxx} se reemplaza por la afirmación del hallazgo con su valor en formato es-CL.
- Si un marcador o una cita apunta a algo que no existe o no está aprobado, el script falla.

Uso: python salidas/generar_tablero.py --pruebas N
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

RAIZ = Path(__file__).parents[1]
TABLAS = RAIZ / "datos" / "tablas"
DESTINO = RAIZ / "docs" / "index.html"
PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"
MARCADOR = re.compile(r"\{(H\d+)\}")
MENOS = "−"


# ── Carga ────────────────────────────────────────────────────────────────

def leer_yaml(ruta):
    return yaml.safe_load((RAIZ / ruta).read_text(encoding="utf-8"))


def leer_csv(nombre):
    return pd.read_csv(TABLAS / f"{nombre}.csv", dtype={"month": str, "Month": str, "cohorte": str})


HALLAZGOS = {h["id"]: h for h in leer_yaml("hallazgos/hallazgos.yaml")["hallazgos"]}
HIPOTESIS = {h["id"]: h for h in leer_yaml("hallazgos/hipotesis.yaml")["hipotesis"]}
DEFINICIONES = {d["nombre"]: d for d in leer_yaml("reglas/definiciones.yaml")["definiciones"]}
FUENTES = leer_yaml("reglas/fuentes.yaml")


class ErrorTablero(Exception):
    pass


def hallazgo_aprobado(id_hallazgo):
    hallazgo = HALLAZGOS.get(id_hallazgo)
    if hallazgo is None:
        raise ErrorTablero(f"El hallazgo {id_hallazgo} no existe en hallazgos/hallazgos.yaml.")
    if hallazgo.get("estado") != "aprobado":
        raise ErrorTablero(f"El hallazgo {id_hallazgo} no está aprobado (estado: {hallazgo.get('estado')}).")
    return hallazgo


def hipotesis_aprobada(id_hipotesis):
    hipotesis = HIPOTESIS.get(id_hipotesis)
    if hipotesis is None:
        raise ErrorTablero(f"La hipótesis {id_hipotesis} no existe en hallazgos/hipotesis.yaml.")
    if hipotesis.get("estado") != "aprobado":
        raise ErrorTablero(f"La hipótesis {id_hipotesis} no está aprobada (estado: {hipotesis.get('estado')}).")
    return hipotesis


def comprobar_cita(id_citado):
    if id_citado in HALLAZGOS or re.fullmatch(r"H\d+", id_citado):
        hallazgo_aprobado(id_citado)
    else:
        hipotesis_aprobada(id_citado)
    return id_citado


# ── Formato es-CL ────────────────────────────────────────────────────────

def con_signo_menos(texto):
    return texto.replace("-", MENOS)


def numero_es(x, decimales=0):
    texto = f"{x:,.{decimales}f}"
    texto = texto.replace(",", "_").replace(".", ",").replace("_", ".")
    return con_signo_menos(texto)


def monto_es(x):
    """Montos: millones como '97,0 M'; bajo un millón, con miles."""
    if abs(x) >= 1_000_000:
        return f"{numero_es(x / 1_000_000, 1)} M"
    return numero_es(x, 0 if float(x).is_integer() else 1)


def porcentaje_es(x, signo=False):
    texto = numero_es(x, 1) + "%"
    return ("+" + texto) if signo and x > 0 else texto


def valor_formateado(hallazgo):
    valor = float(hallazgo["valor"])
    if "{valor}%" in hallazgo["afirmacion"]:
        return numero_es(valor, 1)
    if abs(valor) >= 1_000_000 or float(valor).is_integer():
        return monto_es(valor)
    return numero_es(valor, 1)


def valor_de(id_hallazgo):
    """Solo la cifra del hallazgo, formateada (para KPI y títulos)."""
    hallazgo = hallazgo_aprobado(id_hallazgo)
    if hallazgo.get("valor") is None:
        raise ErrorTablero(f"El hallazgo {id_hallazgo} no tiene valor.")
    return valor_formateado(hallazgo)


def variacion_de(id_hallazgo):
    """Cifra de un hallazgo de variación %, con signo explícito."""
    hallazgo = hallazgo_aprobado(id_hallazgo)
    return porcentaje_es(float(hallazgo["valor"]), signo=True)


def afirmacion_de(id_hallazgo):
    hallazgo = hallazgo_aprobado(id_hallazgo)
    afirmacion = " ".join(str(hallazgo["afirmacion"]).split())
    if "{valor}" in afirmacion:
        afirmacion = afirmacion.replace("{valor}", valor_formateado(hallazgo))
    return afirmacion


def etiqueta(tipo, ids):
    return f'<span class="etiqueta etiqueta-{html.escape(tipo)}">{html.escape(tipo)} · {html.escape(", ".join(ids))}</span>'


def texto(plantilla):
    """Escapa la plantilla y reemplaza cada {Hxx} por su afirmación etiquetada."""
    def reemplazo(coincidencia):
        id_hallazgo = coincidencia.group(1)
        hallazgo = hallazgo_aprobado(id_hallazgo)
        return f"{html.escape(afirmacion_de(id_hallazgo))} {etiqueta(hallazgo['tipo'], [id_hallazgo])}"
    return MARCADOR.sub(reemplazo, html.escape(plantilla))


def chips_ids(ids):
    partes = []
    for id_citado in ids:
        comprobar_cita(id_citado)
        titulo = afirmacion_de(id_citado) if id_citado in HALLAZGOS else HIPOTESIS[id_citado]["hipotesis"]
        partes.append(f'<span class="id" title="{html.escape(titulo)}">{html.escape(id_citado)}</span>')
    return " ".join(partes)


# ── Datos derivados de los CSV ───────────────────────────────────────────

ADQUISICION_MES = leer_csv("adquisicion_mes")
ADQUISICION_INDUSTRIA = leer_csv("adquisicion_industria")
RETENCION = leer_csv("retencion_cohortes")
PUENTE = leer_csv("puente_mrr")
PUENTE_1M = leer_csv("puente_mrr_1m")
GASTO = leer_csv("gasto_sm")
DESCARTADAS = leer_csv("industria_descartadas")
CLIENTE_MES = leer_csv("cliente_mes")

MES_CORTE = ADQUISICION_MES.loc[ADQUISICION_MES["periodo"] == "despues", "month"].min()
ULTIMO_MES = PUENTE["month"].max()
MOVIMIENTOS = ["nuevo", "expansion", "contraccion", "salida_pausa", "retorno_pausa",
               "churn", "reactivacion", "salida_pendiente"]


def por_anio(puente, columnas):
    tabla = puente.assign(anio=puente["month"].str[:4])
    suma = tabla.groupby("anio")[columnas].sum()
    meses = tabla.groupby("anio")["month"].count()
    return suma, meses


def nombre_anio(anio, meses):
    return anio if meses == 12 else f"{anio} ({meses} meses)"


# ── Gráficos (especificación Plotly; colores como "var:--token") ─────────

def eje_base(titulo=""):
    return {"title": {"text": titulo, "font": {"size": 12}}, "gridcolor": "var:--rejilla",
            "linecolor": "var:--eje", "zerolinecolor": "var:--eje", "automargin": True}


def layout_base(**extra):
    layout = {
        "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "system-ui, -apple-system, 'Segoe UI', sans-serif", "size": 12, "color": "var:--tinta-2"},
        "separators": ",.", "margin": {"l": 8, "r": 8, "t": 8, "b": 8},
        "legend": {"orientation": "h", "x": 0, "y": 1.02, "yanchor": "bottom"},
        "hoverlabel": {"bgcolor": "var:--superficie", "bordercolor": "var:--borde", "font": {"color": "var:--tinta-1"}},
        "barcornerradius": 4, "bargap": 0.25, "bargroupgap": 0.08,
        "xaxis": eje_base(), "yaxis": eje_base(),
    }
    layout.update(extra)
    return layout


def tabla_datos(columnas, filas):
    return {"columnas": columnas, "filas": filas}


def grafico_adquisicion():
    df = ADQUISICION_MES
    meses = df["month"].tolist()
    posicion_corte = meses.index(MES_CORTE) - 0.5
    trazas = [
        {"type": "bar", "name": "Clientes nuevos", "x": meses, "y": df["clientes_nuevos"].tolist(),
         "xaxis": "x", "yaxis": "y", "marker": {"color": "var:--serie-1"},
         "customdata": [numero_es(v) for v in df["clientes_nuevos"]],
         "hovertemplate": "%{x}<br>Clientes nuevos: %{customdata}<extra></extra>"},
        {"type": "bar", "name": "gasto_sm (millones)", "x": meses, "y": (df["gasto_sm"] / 1_000_000).tolist(),
         "xaxis": "x", "yaxis": "y2", "marker": {"color": "var:--serie-2"},
         "customdata": [monto_es(v) for v in df["gasto_sm"]],
         "hovertemplate": "%{x}<br>gasto_sm: %{customdata}<extra></extra>"},
    ]
    layout = layout_base(
        height=440, showlegend=True, hovermode="x",
        xaxis={**eje_base(), "anchor": "y2", "type": "category", "tickangle": -45, "nticks": 12},
        yaxis={**eje_base("Clientes nuevos"), "domain": [0.56, 1]},
        yaxis2={**eje_base("gasto_sm (millones)"), "domain": [0, 0.44]},
        shapes=[{"type": "line", "xref": "x", "yref": "paper", "x0": posicion_corte, "x1": posicion_corte,
                 "y0": 0, "y1": 1, "line": {"color": "var:--tinta-2", "width": 1.5, "dash": "dot"}}],
        annotations=[{"xref": "x", "yref": "paper", "x": posicion_corte, "y": 1, "xanchor": "left",
                      "yanchor": "top", "text": f" desde {MES_CORTE}", "showarrow": False,
                      "font": {"color": "var:--tinta-2", "size": 11}}],
    )
    filas = [[m, numero_es(c), monto_es(g)] for m, c, g in zip(meses, df["clientes_nuevos"], df["gasto_sm"])]
    return {
        "id": "g-adquisicion",
        "titulo": f"Desde {MES_CORTE}: clientes nuevos por mes {variacion_de('H34')} y gasto S&M {variacion_de('H36')}",
        "bajada": texto("{H32} {H33} La escala de SM_spend está pendiente de confirmar: lea la forma del gasto, no su nivel."),
        "fuente": "datos/tablas/adquisicion_mes.csv · " + chips_ids(["H34", "H36", "H32", "H33"]),
        "trazas": trazas, "layout": layout,
        "tabla": tabla_datos(["Mes", "Clientes nuevos", "gasto_sm"], filas),
    }


def grafico_industria():
    df = ADQUISICION_INDUSTRIA.pivot(index="Industria", columns="periodo", values="ticket_inicial_mediana")
    df = df.sort_values("antes", ascending=False)
    industrias = df.index.tolist()
    trazas = []
    for periodo, nombre, color in [("antes", f"Antes de {MES_CORTE}", "var:--neutro"),
                                   ("despues", f"Desde {MES_CORTE}", "var:--serie-1")]:
        trazas.append({"type": "bar", "name": nombre, "x": industrias, "y": df[periodo].tolist(),
                       "marker": {"color": color},
                       "customdata": [monto_es(v) for v in df[periodo]],
                       "hovertemplate": "%{x}<br>" + nombre + ": %{customdata}<extra></extra>"})
    layout = layout_base(height=360, barmode="group", xaxis={**eje_base(), "type": "category"},
                         yaxis={**eje_base("Mediana de ticket_inicial"), "tickformat": ",.0f"})
    filas = [[i, monto_es(df.loc[i, "antes"]), monto_es(df.loc[i, "despues"])] for i in industrias]
    return {
        "id": "g-industria",
        "titulo": f"El ticket inicial mediano baja en {valor_de('H28')} de {len(industrias)} industrias desde {MES_CORTE}",
        "bajada": texto("{H24} {H25} {H37}"),
        "fuente": "datos/tablas/adquisicion_industria.csv · " + chips_ids(["H28", "H24", "H25", "H37"]),
        "trazas": trazas, "layout": layout,
        "tabla": tabla_datos(["Industria", f"Antes de {MES_CORTE}", f"Desde {MES_CORTE}"], filas),
    }


def grafico_retencion():
    df = RETENCION
    cohortes = df["cohorte"].tolist()
    trazas = []
    for columna, nombre, color, guion in [("retencion_3m", "Retención a 3 meses", "var:--serie-1", "solid"),
                                          ("retencion_6m", "Retención a 6 meses", "var:--serie-2", "dash")]:
        valores = [None if pd.isna(v) else v for v in df[columna]]
        trazas.append({"type": "scatter", "mode": "lines+markers", "name": nombre, "x": cohortes, "y": valores,
                       "line": {"color": color, "width": 2, "dash": guion}, "marker": {"size": 8, "color": color},
                       "connectgaps": False,
                       "customdata": ["" if v is None else porcentaje_es(v) for v in valores],
                       "hovertemplate": nombre + ": %{customdata}<extra></extra>"})
    layout = layout_base(height=360, hovermode="x unified",
                         xaxis={**eje_base("Cohorte (mes de alta)"), "type": "category", "tickangle": -45, "nticks": 12},
                         yaxis={**eje_base("% sin churn"), "ticksuffix": "%"})
    filas = [[c, "" if pd.isna(a) else porcentaje_es(a), "" if pd.isna(b) else porcentaje_es(b)]
             for c, a, b in zip(cohortes, df["retencion_3m"], df["retencion_6m"])]
    return {
        "id": "g-retencion",
        "titulo": f"Las cohortes desde {MES_CORTE} no se pierden antes: retención a 6 meses {valor_de('H29')}% → {valor_de('H30')}%",
        "bajada": texto("{H29} {H30} Las cohortes sin dato son las que aún no cumplen el plazo con churn confirmable."),
        "fuente": "datos/tablas/retencion_cohortes.csv · " + chips_ids(["H29", "H30", "P01-H8"]),
        "trazas": trazas, "layout": layout,
        "tabla": tabla_datos(["Cohorte", "Retención 3 meses", "Retención 6 meses"], filas),
    }


def grafico_puente():
    suma, meses = por_anio(PUENTE, MOVIMIENTOS)
    colores = ["var:--serie-1", "var:--serie-2", "var:--serie-3"]
    trazas = []
    for i, anio in enumerate(suma.index):
        nombre = nombre_anio(anio, meses[anio])
        valores = suma.loc[anio, MOVIMIENTOS]
        trazas.append({"type": "bar", "name": nombre, "x": MOVIMIENTOS, "y": (valores / 1_000_000).tolist(),
                       "marker": {"color": colores[i % len(colores)]},
                       "customdata": [monto_es(v) for v in valores],
                       "hovertemplate": "%{x}<br>" + nombre + ": %{customdata}<extra></extra>"})
    layout = layout_base(height=400, barmode="group",
                         xaxis={**eje_base(), "type": "category", "tickangle": -30},
                         yaxis={**eje_base("MRR (millones)"), "tickformat": ",.0f"})
    filas = [[m] + [monto_es(suma.loc[a, m]) for a in suma.index] for m in MOVIMIENTOS]
    return {
        "id": "g-puente",
        "titulo": f"El MRR llega a {valor_de('H01')} en {ULTIMO_MES}: movimientos del puente por año",
        "bajada": texto("{H01} Valores positivos suman MRR; negativos lo restan."),
        "fuente": "datos/tablas/puente_mrr.csv (suma anual) · " + chips_ids(["H01"]),
        "trazas": trazas, "layout": layout,
        "tabla": tabla_datos(["Movimiento"] + [nombre_anio(a, meses[a]) for a in suma.index], filas),
    }


def grafico_churn_reglas():
    suma_3m, meses = por_anio(PUENTE, ["churn"])
    suma_1m, _ = por_anio(PUENTE_1M, ["churn"])
    anios = [nombre_anio(a, meses[a]) for a in suma_3m.index]
    trazas = []
    for serie, nombre, color in [(suma_3m["churn"], "churn (regla de 3 meses)", "var:--serie-1"),
                                 (suma_1m["churn"], "churn_sensibilidad_1m (regla de 1 mes)", "var:--serie-2")]:
        trazas.append({"type": "bar", "name": nombre, "x": anios, "y": (serie / 1_000_000).tolist(),
                       "marker": {"color": color}, "customdata": [monto_es(v) for v in serie],
                       "hovertemplate": "%{x}<br>" + nombre + ": %{customdata}<extra></extra>"})
    layout = layout_base(height=340, barmode="group", xaxis={**eje_base(), "type": "category"},
                         yaxis={**eje_base("MRR (millones)"), "tickformat": ",.0f"})
    filas = [[n, monto_es(a), monto_es(b)] for n, a, b in zip(anios, suma_3m["churn"], suma_1m["churn"])]
    return {
        "id": "g-churn",
        "titulo": f"El churn depende de la regla: en 2022 pasa de {valor_de('H11')} (3 meses) a {valor_de('H14')} (1 mes)",
        "bajada": texto("{H03} {H15} {H04} {H05}"),
        "fuente": "datos/tablas/puente_mrr.csv y puente_mrr_1m.csv · " + chips_ids(["H11", "H14", "H03", "H15", "H04", "H05"]),
        "trazas": trazas, "layout": layout,
        "tabla": tabla_datos(["Año", "Churn 3 meses", "Churn 1 mes"], filas),
    }


def grafico_contraccion_churn():
    columnas = ["contraccion", "churn", "salida_pendiente"]
    suma, meses = por_anio(PUENTE, columnas)
    anios = [nombre_anio(a, meses[a]) for a in suma.index]
    trazas = []
    for columna, nombre, color in [("contraccion", "contraccion", "var:--serie-1"),
                                   ("churn", "churn (3 meses)", "var:--serie-2"),
                                   ("salida_pendiente", "salida_pendiente", "var:--serie-3")]:
        trazas.append({"type": "bar", "name": nombre, "x": anios, "y": (suma[columna] / 1_000_000).tolist(),
                       "marker": {"color": color}, "customdata": [monto_es(v) for v in suma[columna]],
                       "hovertemplate": "%{x}<br>" + nombre + ": %{customdata}<extra></extra>"})
    layout = layout_base(height=340, barmode="group", xaxis={**eje_base(), "type": "category"},
                         yaxis={**eje_base("MRR (millones)"), "tickformat": ",.0f"})
    filas = [[n] + [monto_es(suma.loc[a, c]) for c in columnas] for n, a in zip(anios, suma.index)]
    return {
        "id": "g-contraccion",
        "titulo": "Con churn de 3 meses, la contracción supera al churn en 2022 y 2023; 2024 no es concluyente",
        "bajada": texto("{H09} {H02} {H10} {H06}"),
        "fuente": "datos/tablas/puente_mrr.csv (suma anual) · " + chips_ids(["H08", "H09", "H02", "H10", "H06"]),
        "trazas": trazas, "layout": layout,
        "tabla": tabla_datos(["Año", "contraccion", "churn (3 meses)", "salida_pendiente"], filas),
    }


# ── Bloques HTML ─────────────────────────────────────────────────────────

def html_grafico(g):
    cabecera = "".join(f"<th>{html.escape(c)}</th>" for c in g["tabla"]["columnas"])
    filas = "".join("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in fila) + "</tr>"
                    for fila in g["tabla"]["filas"])
    return f"""
    <figure class="tarjeta grafico">
      <h3>{html.escape(g['titulo'])}</h3>
      <p class="bajada">{g['bajada']}</p>
      <div class="lienzo" id="{g['id']}" role="img" aria-label="{html.escape(g['titulo'])}"></div>
      <details><summary>Ver datos</summary>
        <div class="tabla-scroll"><table><thead><tr>{cabecera}</tr></thead><tbody>{filas}</tbody></table></div>
      </details>
      <figcaption>Fuente: {g['fuente']}</figcaption>
    </figure>"""


def kpi(valor, rotulo, plantilla, ids):
    return f"""
      <div class="kpi">
        <div class="kpi-rotulo">{html.escape(rotulo)}</div>
        <div class="kpi-valor">{html.escape(valor)}</div>
        <p class="kpi-nota">{texto(plantilla)}</p>
      </div>"""


def pestana_resumen():
    principal = hallazgo_aprobado("H38")
    anio = ULTIMO_MES[:4]
    meses_anio = (PUENTE["month"].str[:4] == anio).sum()
    kpis = "".join([
        kpi(valor_de("H01"), f"MRR {ULTIMO_MES}", "{H01}", ["H01"]),
        kpi(valor_de("H33"), f"Clientes nuevos por mes, {nombre_anio(anio, meses_anio)}", "{H33}", ["H33"]),
        kpi(f"{valor_de('H24')} → {valor_de('H25')}", "Mediana de ticket inicial, antes → después",
            "{H37}", ["H24", "H25", "H37"]),
        kpi(variacion_de("H36"), "Variación del gasto S&M mensual", "{H36}", ["H36"]),
    ])
    decisiones = [
        ("Poner el foco en el ticket de entrada, no solo en el volumen: la cantidad de clientes nuevos se sostiene "
         "y el ticket mediano baja. Revisar precios, descuentos y planes de entrada. {H37} {H28}",
         ["H38", "H37", "H28", "P01-H5", "P01-H7"]),
        ("No atribuir el estancamiento al recorte de gasto S&M ni a una peor retención de las cohortes nuevas: "
         "ambas hipótesis quedaron descartadas. {H36} {H30}",
         ["P01-H6", "P01-H8", "H36", "H30"]),
        ("Conseguir los datos de funnel para evaluar demanda, calidad de leads, velocidad de atención y conversión "
         "post-SQL. Dato a pedir: " + HIPOTESIS["P01-H1"]["dato_faltante"],
         ["P01-H1", "P01-H2", "P01-H3", "P01-H4"]),
        ("Conseguir el precio de lista para separar descuento de contracción y medir el revenue no capturado. "
         "Dato a pedir: " + HIPOTESIS["P02-H1"]["dato_faltante"],
         ["P02-H1", "H08"]),
        ("Confirmar con el negocio la escala de SM_spend antes de leer niveles de gasto o CAC. Nota del veredicto de P01-H6: "
         + HIPOTESIS["P01-H6"]["nota_veredicto"],
         ["P01-H6"]),
    ]
    puntos = "".join(f"<li>{texto(t)} <span class='cita'>{etiqueta('inferencia', ids)}</span></li>"
                     for t, ids in decisiones)
    for _, ids in decisiones:
        for id_citado in ids:
            comprobar_cita(id_citado)
    return f"""
    <section class="tarjeta mensaje">
      <div class="mensaje-rotulo">Mensaje principal {etiqueta(principal['tipo'], ['H38'])}</div>
      <p class="mensaje-texto">{html.escape(afirmacion_de('H38'))}</p>
      <p class="mensaje-base">Basada en: {chips_ids(principal['basada_en'])}</p>
    </section>
    <section class="kpis">{kpis}</section>
    <section class="tarjeta">
      <h2>Qué decidir (CRO)</h2>
      <ol class="decisiones">{puntos}</ol>
    </section>"""


def pestana_adquisicion(graficos):
    return "".join(html_grafico(graficos[i]) for i in ["g-adquisicion", "g-industria", "g-retencion"])


def pestana_hipotesis():
    clases = {"apoyada": "bien", "descartada": "critico", "no_concluyente": "aviso",
              "no_evaluable": "neutro", "pendiente": "neutro"}
    filas = []
    for id_hipotesis, h in HIPOTESIS.items():
        if h.get("estado") != "aprobado":
            continue
        veredicto = h["veredicto"]
        evidencia = chips_ids(h.get("evidencia") or []) or "—"
        filas.append(f"""
        <tr>
          <td class="nowrap"><strong>{html.escape(id_hipotesis)}</strong></td>
          <td>{html.escape(h['hipotesis'])}</td>
          <td>{html.escape(h['origen'])}</td>
          <td><span class="chip chip-{clases.get(veredicto, 'neutro')}">{html.escape(veredicto.replace('_', ' '))}</span></td>
          <td>{html.escape(h.get('nota_veredicto') or '—')}</td>
          <td class="ids">{evidencia}</td>
          <td>{html.escape(h.get('dato_faltante') or '—')}</td>
        </tr>""")
    return f"""
    <section class="tarjeta">
      <h2>Hipótesis aprobadas y su veredicto</h2>
      <p class="bajada">Solo hipótesis con estado aprobado. Pase el cursor sobre un id de evidencia para ver la afirmación.</p>
      <div class="tabla-scroll">
        <table class="tabla-hipotesis">
          <thead><tr><th>id</th><th>Hipótesis</th><th>Origen</th><th>Veredicto</th><th>Nota</th><th>Evidencia</th><th>Dato faltante</th></tr></thead>
          <tbody>{''.join(filas)}</tbody>
        </table>
      </div>
    </section>"""


def pestana_mrr(graficos):
    nota = f"""
    <section class="tarjeta nota">
      <h2>Cómo leer el MRR</h2>
      <ul>
        <li><strong>Contracción y descuento no se separan.</strong> {html.escape(DEFINICIONES['contraccion']['advertencia'])}
            Para separarlos falta el bloque C (diseño): {html.escape(DEFINICIONES['descuento']['dato_faltante'])}</li>
        <li><strong>2024 es no concluyente</strong> por churn truncado. {texto('{H08}')}</li>
      </ul>
    </section>"""
    return nota + "".join(html_grafico(graficos[i]) for i in ["g-puente", "g-churn", "g-contraccion"])


def limites_de(ruta):
    """Lee la sección '- Límites:' de una pregunta (línea y sub-viñetas)."""
    lineas = (RAIZ / ruta).read_text(encoding="utf-8").splitlines()
    resultado, dentro = [], False
    for linea in lineas:
        if linea.startswith("- Límites:"):
            dentro = True
            resto = linea.removeprefix("- Límites:").strip()
            if resto:
                resultado.append(resto)
            continue
        if dentro:
            if linea.startswith("  - "):
                resultado.append(linea.strip()[2:])
            else:
                break
    return resultado


def pestana_datos():
    # Conteos desde los CSV
    clientes_base = CLIENTE_MES.loc[CLIENTE_MES["es_base_inicial"], "ID"].nunique()
    meses_cobro_extra = int((CLIENTE_MES["cobro_extra"] > 0).sum())
    participacion_extra = 100 * CLIENTE_MES["cobro_extra"].sum() / CLIENTE_MES["amount"].sum()
    filas_descartadas = len(DESCARTADAS)
    meses_negativos = int(GASTO["tiene_negativo"].sum())
    gasto_vs_mrr = GASTO.merge(PUENTE[["month", "mrr_final"]], left_on="Month", right_on="month")
    meses_gasto_sobre_mrr = int((gasto_vs_mrr["total"] > gasto_vs_mrr["mrr_final"]).sum())
    multiplicador_sm = FUENTES["gasto_sm"]["formato_gasto"]["multiplicador"]
    accion_negativos = FUENTES["gasto_sm"]["negativos"]["accion"].replace("_", " ")
    accion_vacias = FUENTES["industrias"]["filas_vacias"]["accion"].replace("_", " ")
    estados_cliente = CLIENTE_MES["estado"].value_counts()

    def d(nombre, campo):
        return html.escape(DEFINICIONES[nombre].get(campo, ""))

    inconsistencias = [
        ("Base inicial (clientes que ya existían al empezar los datos)",
         f"{d('base_inicial', 'motivo')} Supuesto: {d('base_inicial', 'supuesto')}",
         f"{d('base_inicial', 'regla')} Clientes en base_inicial: <strong>{numero_es(clientes_base)}</strong>.",
         "sql/2_cliente_mes.sql"),
        ("Pausas frente a churn",
         f"{d('pausa', 'motivo')} {d('churn', 'motivo')}",
         f"Pausa: {d('pausa', 'regla')} Churn: {d('churn', 'regla')} Pendiente: {d('pendiente', 'regla')} "
         f"Meses en pausa: <strong>{numero_es(estados_cliente.get('pausa', 0))}</strong>; meses pendientes: "
         f"<strong>{numero_es(estados_cliente.get('pendiente', 0))}</strong>. Advertencia: {d('churn', 'advertencia')}",
         "sql/2_cliente_mes.sql"),
        ("Cobros acumulados en meses de entrada o vuelta (cobro_extra)",
         d("monto_recurrente", "motivo"),
         f"monto_recurrente: {d('monto_recurrente', 'regla')} cobro_extra = {d('cobro_extra', 'regla')} "
         f"Meses con cobro_extra &gt; 0: <strong>{numero_es(meses_cobro_extra)}</strong> "
         f"({porcentaje_es(participacion_extra)} del amount total). Advertencia: {d('monto_recurrente', 'advertencia')}",
         "sql/2_cliente_mes.sql"),
        ("Fila vacía en Industry.csv",
         "Hay filas sin ID ni Industria en el archivo de origen.",
         f"Acción: {html.escape(accion_vacias)}. Filas descartadas: <strong>{numero_es(filas_descartadas)}</strong> "
         "(datos/tablas/industria_descartadas.csv).",
         "sql/1_limpieza.sql"),
        ("Valores negativos en PayrollExpenses",
         "Reversos en el gasto de S&M.",
         f"Acción: {html.escape(accion_negativos)} (columna tiene_negativo). Meses con algún negativo: "
         f"<strong>{numero_es(meses_negativos)}</strong>. {d('cac_3m', 'motivo')}",
         "sql/1_limpieza.sql"),
        ("Escala de SM_spend",
         f"Los valores vienen como texto con \"$\" y se multiplican por {numero_es(multiplicador_sm)}. "
         f"Con esa escala, el gasto_sm mensual supera al MRR en <strong>{numero_es(meses_gasto_sobre_mrr)}</strong> "
         f"de {numero_es(len(gasto_vs_mrr))} meses.",
         "Pendiente de confirmar con el negocio. Mientras tanto, de gasto y CAC se citan solo variaciones % (P01-H6).",
         "sql/1_limpieza.sql, reglas/fuentes.yaml"),
        ("Team frente a PayrollExpenses",
         "Ambas columnas parecen gasto de personal.",
         f"No hay tratamiento documentado en el repositorio: hoy ambas se suman en gasto_sm ({d('gasto_sm', 'regla')}). "
         "Posible doble conteo de personal, a confirmar con el negocio.",
         "sql/1_limpieza.sql"),
    ]
    filas_inc = "".join(f"<tr><td><strong>{html.escape(t)}</strong></td><td>{p}</td><td>{tr}</td>"
                        f"<td class='nowrap'><code>{html.escape(a)}</code></td></tr>"
                        for t, p, tr, a in inconsistencias)

    supuestos = []
    for nombre, definicion in DEFINICIONES.items():
        if definicion.get("estado") != "operativa":
            continue
        for campo in ("supuesto", "advertencia"):
            if definicion.get(campo):
                supuestos.append(f"<tr><td><code>{html.escape(nombre)}</code></td><td>{campo}</td>"
                                 f"<td>{html.escape(definicion[campo])}</td></tr>")

    limites = "".join(f"<li><strong>P01:</strong> {html.escape(l)}</li>" for l in limites_de("preguntas/P01_funnel_cro.md"))
    limites += "".join(f"<li><strong>P02:</strong> {html.escape(l)}</li>" for l in limites_de("preguntas/P02_mrr_cfo.md"))

    pedidos = {}
    for nombre, definicion in DEFINICIONES.items():
        if definicion.get("estado") == "diseño" and definicion["bloque"].startswith(("C_", "E_")):
            clave = (definicion["bloque"], definicion["dato_faltante"])
            pedidos.setdefault(clave, []).append(nombre)
    lista_pedidos = "".join(
        f"<li><strong>{html.escape(bloque.replace('_', ' ', 1))}:</strong> {html.escape(dato)}"
        f"<br><span class='bajada'>Habilita: {html.escape(', '.join(nombres))}</span></li>"
        for (bloque, dato), nombres in pedidos.items())

    return f"""
    <section class="tarjeta">
      <h2>Inconsistencias detectadas y su tratamiento</h2>
      <div class="tabla-scroll"><table>
        <thead><tr><th>Tema</th><th>Qué se vio</th><th>Tratamiento</th><th>Dónde</th></tr></thead>
        <tbody>{filas_inc}</tbody>
      </table></div>
    </section>
    <section class="tarjeta">
      <h2>Qué no se puede concluir</h2>
      <ul>{limites}</ul>
    </section>
    <section class="tarjeta">
      <h2>Datos a pedir</h2>
      <p class="bajada">Métricas en diseño (bloques C y E de reglas/definiciones.yaml): no se calculan hasta tener el dato.</p>
      <ul>{lista_pedidos}</ul>
    </section>
    <section class="tarjeta">
      <h2>Supuestos y advertencias del glosario</h2>
      <div class="tabla-scroll"><table>
        <thead><tr><th>Métrica</th><th>Tipo</th><th>Texto</th></tr></thead>
        <tbody>{''.join(supuestos)}</tbody>
      </table></div>
    </section>"""


def pestana_como_funciona(pruebas):
    aprobados = sum(1 for h in HALLAZGOS.values() if h.get("estado") == "aprobado")
    hip_aprobadas = sum(1 for h in HIPOTESIS.values() if h.get("estado") == "aprobado")
    operativas = sum(1 for d in DEFINICIONES.values() if d.get("estado") == "operativa")
    pasos = [
        ("Pregunta", "preguntas/PXX.md", "El negocio formula la pregunta y la decisión que habilita."),
        ("Definiciones", "reglas/definiciones.yaml", f"{numero_es(operativas)} métricas operativas; las de diseño solo como dato faltante."),
        ("SQL", "sql/", "DuckDB: limpieza (única conversión de unidades), ciclo de vida y tablas por pregunta."),
        ("Validaciones", "validaciones/", f"{numero_es(pruebas)} pruebas pasaron en la última corrida."),
        ("Hallazgos", "hallazgos/*.yaml", "Cada hecho guarda su consulta y se recalcula en las pruebas."),
        ("Revisor", "preguntas/revision_*.md", "Agente independiente que objeta veredictos e inferencias."),
        ("Aprobación", "estado: aprobado", f"Decisión humana: {numero_es(aprobados)} hallazgos y {numero_es(hip_aprobadas)} hipótesis aprobados."),
        ("Tablero", "docs/index.html", "Solo muestra lo aprobado; las cifras salen de los CSV y de los hallazgos."),
    ]
    diagrama = "".join(f"""<li class="paso"><span class="paso-num">{i}</span><strong>{html.escape(t)}</strong>
        <code>{html.escape(a)}</code><span>{html.escape(x)}</span></li>""" for i, (t, a, x) in enumerate(pasos, 1))

    campos = []
    for linea in (RAIZ / "preguntas" / "_plantilla.md").read_text(encoding="utf-8").splitlines():
        if linea.startswith("- "):
            nombre, _, ayuda = linea[2:].partition(":")
            campos.append(f"<li><strong>{html.escape(nombre)}</strong>{(': ' + html.escape(ayuda.strip())) if ayuda.strip() else ''}</li>")
    return f"""
    <section class="tarjeta">
      <h2>De la pregunta al tablero</h2>
      <ol class="diagrama">{diagrama}</ol>
    </section>
    <section class="tarjeta">
      <h2>Validaciones</h2>
      <p>La última corrida de <code>python ejecutar.py</code> pasó <strong>{numero_es(pruebas)}</strong> pruebas
         (datos de entrada, cuadre de unidades, definiciones, cifras del glosario, puente de MRR, hallazgos e hipótesis).
         Después de generar esta página, <code>validaciones/test_tablero.py</code> comprueba que no queden marcadores
         sin reemplazar ni ids en borrador.</p>
    </section>
    <section class="tarjeta">
      <h2>Cómo entra una pregunta nueva</h2>
      <p>Se copia <code>preguntas/_plantilla.md</code> y se completan sus campos:</p>
      <ul>{''.join(campos)}</ul>
      <p class="bajada">Luego: hipótesis en borrador en hallazgos/hipotesis.yaml → aprobación humana del plan → SQL en
         sql/preguntas/ → hallazgos con su consulta → revisor → aprobación → tablero.</p>
    </section>"""


# ── Página ───────────────────────────────────────────────────────────────

CSS = """
:root {
  color-scheme: light;
  --plano: #f9f9f7; --superficie: #fcfcfb; --tinta-1: #0b0b0b; --tinta-2: #52514e; --tinta-3: #898781;
  --rejilla: #e1e0d9; --eje: #c3c2b7; --borde: rgba(11,11,11,0.10);
  --serie-1: #2a78d6; --serie-2: #eb6834; --serie-3: #1baf7a; --neutro: #b5b3ab;
  --bien: #0ca30c; --aviso: #fab219; --critico: #d03b3b; --chip-neutro: #e1e0d9;
  --acento-suave: #cde2fb;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --plano: #0d0d0d; --superficie: #1a1a19; --tinta-1: #f0efec; --tinta-2: #c3c2b7; --tinta-3: #898781;
    --rejilla: #2c2c2a; --eje: #383835; --borde: rgba(255,255,255,0.10);
    --serie-1: #3987e5; --serie-2: #d95926; --serie-3: #199e70; --neutro: #6b6a64;
    --chip-neutro: #383835; --acento-suave: #184f95;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --plano: #0d0d0d; --superficie: #1a1a19; --tinta-1: #f0efec; --tinta-2: #c3c2b7; --tinta-3: #898781;
  --rejilla: #2c2c2a; --eje: #383835; --borde: rgba(255,255,255,0.10);
  --serie-1: #3987e5; --serie-2: #d95926; --serie-3: #199e70; --neutro: #6b6a64;
  --chip-neutro: #383835; --acento-suave: #184f95;
}
* { box-sizing: border-box; }
html, body { margin: 0; }
body { background: var(--plano); color: var(--tinta-1); font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
.contenedor { max-width: 1120px; margin: 0 auto; padding: 16px; }
header h1 { font-size: 1.4rem; margin: 8px 0 2px; }
header p { margin: 0; color: var(--tinta-2); }
nav { display: flex; flex-wrap: wrap; gap: 6px; margin: 16px 0; }
nav button { font: inherit; padding: 6px 12px; border-radius: 999px; border: 1px solid var(--borde);
  background: var(--superficie); color: var(--tinta-2); cursor: pointer; }
nav button[aria-selected="true"] { background: var(--tinta-1); color: var(--plano); border-color: var(--tinta-1); }
.pestana[hidden] { display: none; }
.tarjeta { background: var(--superficie); border: 1px solid var(--borde); border-radius: 12px; padding: 16px; margin: 0 0 16px; min-width: 0; }
h2 { font-size: 1.1rem; margin: 0 0 8px; }
h3 { font-size: 1rem; margin: 0 0 4px; }
.bajada, figcaption { color: var(--tinta-2); font-size: 0.85rem; margin: 0 0 8px; }
figure { margin: 0 0 16px; }
.lienzo { width: 100%; min-height: 300px; }
.mensaje { border-left: 4px solid var(--serie-1); }
.mensaje-rotulo { color: var(--tinta-2); font-size: 0.85rem; }
.mensaje-texto { font-size: 1.15rem; margin: 6px 0; }
.mensaje-base { font-size: 0.8rem; color: var(--tinta-3); margin: 0; }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 16px; }
.kpi { background: var(--superficie); border: 1px solid var(--borde); border-radius: 12px; padding: 16px; min-width: 0; }
.kpi-rotulo { color: var(--tinta-2); font-size: 0.85rem; }
.kpi-valor { font-size: 1.7rem; font-weight: 600; margin: 4px 0; }
.kpi-nota { color: var(--tinta-2); font-size: 0.8rem; margin: 0; }
.etiqueta { display: inline-block; font-size: 0.72rem; padding: 0 6px; border-radius: 4px; border: 1px solid var(--borde);
  color: var(--tinta-2); white-space: nowrap; vertical-align: 1px; }
.etiqueta-inferencia { border-style: dashed; }
.etiqueta-hecho { background: var(--acento-suave); color: var(--tinta-1); }
.decisiones li { margin-bottom: 10px; }
.id { display: inline-block; font-size: 0.75rem; padding: 0 5px; border-radius: 4px; background: var(--chip-neutro);
  color: var(--tinta-1); margin: 1px 0; cursor: help; }
.tabla-scroll { overflow-x: auto; max-width: 100%; }
table { border-collapse: collapse; width: 100%; font-size: 0.85rem; }
th, td { text-align: left; vertical-align: top; padding: 6px 8px; border-bottom: 1px solid var(--rejilla); }
th { color: var(--tinta-2); font-weight: 600; }
td { font-variant-numeric: tabular-nums; }
.tabla-hipotesis { min-width: 900px; }
.nowrap { white-space: nowrap; }
.chip { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 0.78rem; white-space: nowrap; font-weight: 600; }
.chip-bien { background: var(--bien); color: #fff; }
.chip-critico { background: var(--critico); color: #fff; }
.chip-aviso { background: var(--aviso); color: #0b0b0b; }
.chip-neutro { background: var(--chip-neutro); color: var(--tinta-1); }
details summary { cursor: pointer; color: var(--tinta-2); font-size: 0.85rem; margin: 6px 0; }
code { font-size: 0.82em; background: var(--chip-neutro); padding: 0 4px; border-radius: 4px; overflow-wrap: anywhere; }
.nota ul { margin: 0; padding-left: 20px; }
.diagrama { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px 28px; }
.paso { position: relative; border: 1px solid var(--borde); border-radius: 10px; padding: 10px; display: flex;
  flex-direction: column; gap: 4px; font-size: 0.85rem; min-width: 0; }
.paso span:last-child { color: var(--tinta-2); }
.paso-num { position: absolute; top: -10px; left: 10px; background: var(--serie-1); color: #fff; border-radius: 999px;
  width: 20px; height: 20px; font-size: 0.72rem; display: grid; place-items: center; }
.paso:not(:last-child)::after { content: "→"; position: absolute; right: -22px; top: 50%; transform: translateY(-50%); color: var(--tinta-3); }
@media (min-width: 761px) { .paso:nth-child(4n)::after { content: none; } }
@media (max-width: 760px) {
  .diagrama { grid-template-columns: 1fr; }
  .paso:not(:last-child)::after { content: "↓"; right: auto; left: 50%; top: auto; bottom: -22px; transform: none; }
  .kpi-valor { font-size: 1.6rem; }
}
"""

JS = """
const DATOS = JSON.parse(document.getElementById('datos-tablero').textContent);
const pintados = new Set();

function resolverColores(objeto, estilo) {
  if (typeof objeto === 'string') {
    return objeto.startsWith('var:') ? estilo.getPropertyValue(objeto.slice(4)).trim() : objeto;
  }
  if (Array.isArray(objeto)) return objeto.map(v => resolverColores(v, estilo));
  if (objeto && typeof objeto === 'object') {
    const copia = {};
    for (const clave in objeto) copia[clave] = resolverColores(objeto[clave], estilo);
    return copia;
  }
  return objeto;
}

function pintar(id) {
  const grafico = DATOS.graficos[id];
  const nodo = document.getElementById(id);
  if (!grafico || !nodo || typeof Plotly === 'undefined') return;
  const estilo = getComputedStyle(document.documentElement);
  Plotly.react(nodo, resolverColores(grafico.trazas, estilo), resolverColores(grafico.layout, estilo),
               {displayModeBar: false, responsive: true});
  pintados.add(id);
}

function mostrar(nombre) {
  document.querySelectorAll('nav button').forEach(b => b.setAttribute('aria-selected', b.dataset.pestana === nombre));
  document.querySelectorAll('.pestana').forEach(s => { s.hidden = s.id !== nombre; });
  document.querySelectorAll('#' + nombre + ' .lienzo').forEach(n => {
    if (pintados.has(n.id)) Plotly.Plots.resize(n); else pintar(n.id);
  });
  try { localStorage.setItem('pestana', nombre); } catch (e) {}
}

document.querySelectorAll('nav button').forEach(b => b.addEventListener('click', () => mostrar(b.dataset.pestana)));
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => pintados.forEach(pintar));
let inicial = 'resumen';
try { inicial = localStorage.getItem('pestana') || 'resumen'; } catch (e) {}
mostrar(document.getElementById(inicial) ? inicial : 'resumen');
"""


def generar(pruebas):
    graficos = {g["id"]: g for g in [grafico_adquisicion(), grafico_industria(), grafico_retencion(),
                                       grafico_puente(), grafico_churn_reglas(), grafico_contraccion_churn()]}
    pestanas = [
        ("resumen", "Resumen", pestana_resumen()),
        ("adquisicion", "Adquisición (CRO)", pestana_adquisicion(graficos)),
        ("hipotesis", "Hipótesis", pestana_hipotesis()),
        ("mrr", "MRR (CFO)", pestana_mrr(graficos)),
        ("datos", "Datos y límites", pestana_datos()),
        ("como", "Cómo funciona", pestana_como_funciona(pruebas)),
    ]
    botones = "".join(f'<button type="button" data-pestana="{c}" aria-selected="false">{html.escape(t)}</button>'
                      for c, t, _ in pestanas)
    secciones = "".join(f'<section class="pestana" id="{c}" hidden>{contenido}</section>' for c, _, contenido in pestanas)
    datos_json = json.dumps({"graficos": {k: {"trazas": g["trazas"], "layout": g["layout"]} for k, g in graficos.items()}},
                            ensure_ascii=False).replace("</", "<\\/")
    pagina = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tablero Finora</title>
<style>{CSS}</style>
<script src="{PLOTLY_CDN}" charset="utf-8"></script>
</head>
<body>
<div class="contenedor">
  <header>
    <h1>Finora · crecimiento y MRR</h1>
    <p>Datos hasta {ULTIMO_MES}. Cada afirmación lleva su etiqueta (hecho o inferencia) y el id del hallazgo aprobado del que sale.</p>
  </header>
  <nav aria-label="Pestañas">{botones}</nav>
  {secciones}
</div>
<script id="datos-tablero" type="application/json">{datos_json}</script>
<script>{JS}</script>
</body>
</html>
"""
    restos = MARCADOR.findall(pagina)
    if restos:
        raise ErrorTablero(f"Quedaron marcadores sin reemplazar: {sorted(set(restos))}")
    DESTINO.parent.mkdir(exist_ok=True)
    DESTINO.write_text(pagina, encoding="utf-8")
    print(f"Tablero generado: {DESTINO.relative_to(RAIZ).as_posix()}")


def main():
    parser = argparse.ArgumentParser(description="Genera docs/index.html")
    parser.add_argument("--pruebas", type=int, required=True, help="número de pruebas que pasaron en ejecutar.py")
    argumentos = parser.parse_args()
    try:
        generar(argumentos.pruebas)
    except ErrorTablero as error:
        print(f"Error al generar el tablero: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
