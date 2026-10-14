from flask import Blueprint, render_template, jsonify, request

from app.modulos.planta.planta_control import (
    Query_Netezza,
    Query_Netezza2
)
from app.modulos.planta.planta_lac import (
    Query_Teradata_LAC,
    Query_Filtros_Teradata_LAC,
    preparar_datos_lac,
    dataframe_lac_a_json
)

import pandas as pd


tendencias_bp = Blueprint(
    "tendencias",
    __name__
)


@tendencias_bp.route("/tendencias_plantas")
def tendencias_plantas():

    # ==========================================
    # Obtener datos Planta Comercial
    # ==========================================

    df1 = Query_Netezza()

    # ==========================================
    # Obtener datos Planta Control BI
    # ==========================================

    df2 = Query_Netezza2()

    # Si no hay datos
    if not df1 or not df2:
        return render_template(
            "tendencias_plantas.html",
            tecnologias1=[],
            tecnologias2=[],
            estados1=[],
            estados2=[],
            periodo1=[],
            periodo2=[]
        )

    # Convertir a DataFrame
    df1 = pd.DataFrame(df1)
    df2 = pd.DataFrame(df2)

    # ==========================================
    # TECNOLOGÍAS
    # ==========================================

    tecnologias1 = df1["TECNOLOGIA"].dropna().unique().tolist()
    tecnologias1.insert(0, "TODAS")

    tecnologias2 = df2["TECNOLOGIA"].dropna().unique().tolist()
    tecnologias2.insert(0, "TODAS")

    # ==========================================
    # ESTADOS
    # ==========================================

    estados1 = df1["ESTADO"].dropna().unique().tolist()
    estados2 = df2["ESTADO"].dropna().unique().tolist()

    # ==========================================
    # PERÍODOS
    # ==========================================

    periodo1 = df1["PERIODO"].dropna().astype(str).unique().tolist()
    periodo2 = df2["PERIODO"].dropna().astype(str).unique().tolist()

    # ==========================================
    # Render
    # ==========================================

    return render_template(
        "tendencias_plantas.html",

        tecnologias1=tecnologias1,
        tecnologias2=tecnologias2,

        estados1=estados1,
        estados2=estados2,

        periodo1=periodo1,
        periodo2=periodo2
    )

@tendencias_bp.route("/tendencias_planta_lac_datos")
def tendencias_planta_lac_datos():
    """Datos para el panel de Tendencias de Planta LAC."""
    import logging
    import time
    from datetime import datetime

    inicio = time.time()
    anio = request.args.get("anio")
    departamento = request.args.get("departamento", "TODOS")

    # Primera carga: año actual + todos los departamentos.
    if not anio or str(anio).upper() == "TODOS":
        anio = str(datetime.now().year)

    logging.info("[LAC][ENDPOINT][1] REQUEST | anio=%s | departamento=%s", anio, departamento)

    try:
        filtros = Query_Filtros_Teradata_LAC()
        anios = filtros.get("anios", [])
        departamentos = filtros.get("departamentos", [])

        # Si el año actual no existe, usa el año más reciente disponible.
        if anios:
            try:
                if int(anio) not in anios:
                    anio = str(anios[0])
            except (TypeError, ValueError):
                anio = str(anios[0])

        logging.info("[LAC][ENDPOINT][2] Consultando gráfico | anio=%s | departamento=%s", anio, departamento)

        datos = Query_Teradata_LAC(
            anio=anio,
            departamento=None if str(departamento).upper() == "TODOS" else departamento
        )
        logging.info("[LAC][ENDPOINT][3] Query gráfico terminó | filas=%s", len(datos))

        df = preparar_datos_lac(datos)

        kpis = {"ultimo": None, "anterior": None, "crecimiento": None, "maximo": None, "minimo": None}
        if not df.empty:
            serie = (df.groupby("PERIODO", as_index=False)["CANTIDAD_TELEFONOS_UNICOS"]
                       .sum().sort_values("PERIODO"))
            valores = serie["CANTIDAD_TELEFONOS_UNICOS"].tolist()
            if valores:
                kpis["ultimo"] = int(valores[-1]); kpis["maximo"] = int(max(valores)); kpis["minimo"] = int(min(valores))
            if len(valores) >= 2 and valores[-2] != 0:
                kpis["anterior"] = int(valores[-2])
                kpis["crecimiento"] = round(((valores[-1]-valores[-2])/valores[-2])*100, 2)

        segundos = round(time.time()-inicio,2)
        logging.info("[LAC][ENDPOINT][4] OK | año=%s | depto=%s | filas=%s | tiempo=%ss", anio, departamento, len(df), segundos)

        return jsonify({
            "success": True,
            "datos": dataframe_lac_a_json(df),
            "anios": anios,
            "departamentos": departamentos,
            "anio_seleccionado": int(anio),
            "departamento_seleccionado": departamento,
            "total_periodos": int(df["PERIODO"].nunique()) if not df.empty else 0,
            "kpis": kpis,
            "debug": {"anio": anio, "departamento": departamento, "filas": len(df), "tiempo_segundos": segundos}
        })
    except Exception as error:
        logging.exception("[LAC][ENDPOINT][ERROR] %s", error)
        return jsonify({
            "success": False,
            "error": str(error),
            "datos": [],
            "anios": [],
            "departamentos": [],
            "total_periodos": 0,
            "kpis": {},
            "debug": {
                "anio": anio,
                "departamento": departamento,
                "mensaje": "Error en endpoint Planta LAC"
            }
        }), 500
