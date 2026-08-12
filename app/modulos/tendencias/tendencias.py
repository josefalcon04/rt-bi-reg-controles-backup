from flask import Blueprint, render_template

from app.modulos.planta.planta_control import (
    Query_Netezza,
    Query_Netezza2
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