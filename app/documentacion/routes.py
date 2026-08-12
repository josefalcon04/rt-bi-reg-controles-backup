from flask import Blueprint, render_template, request, redirect, url_for
import os
import markdown
import datetime
import re


documentacion_bp = Blueprint(
    'documentacion',
    __name__,
    template_folder='templates'
)


# =========================================================
# CARPETA DE DOCUMENTOS
# =========================================================

# routes.py está en:
# app/documentacion/routes.py
#
# Subimos:
# documentacion -> app
# app -> proyecto
#
# Y desde proyecto entramos a:
# data/documentacion/documentos

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '..',
        '..'
    )
)

DOCS_FOLDER = os.path.join(
     os.path.dirname(__file__),
    'templates',
    'documentos'
)


# Asegurar que la carpeta exista
os.makedirs(DOCS_FOLDER, exist_ok=True)


# =========================================================
# LIMPIAR CONTENIDO
# =========================================================

def limpiar_contenido(texto):

    texto = texto.replace('\r\n', '\n')
    texto = texto.replace('\r', '\n')
    texto = texto.strip()

    # Quita espacios en líneas vacías
    texto = re.sub(r'[ \t]+\n', '\n', texto)

    # Reemplaza 3 o más saltos de línea por solo 2
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    return texto


# =========================================================
# LISTAR DOCUMENTOS
# =========================================================

@documentacion_bp.route('/documentacion')
def listar():

    archivos = [
        f for f in os.listdir(DOCS_FOLDER)
        if f.endswith('.md')
    ]

    documentos = []

    for f in archivos:

        ruta = os.path.join(DOCS_FOLDER, f)

        fecha_mod = datetime.datetime.fromtimestamp(
            os.path.getmtime(ruta)
        )

        documentos.append({
            'nombre': f,
            'descripcion': 'Sin descripción',
            'fecha_modificacion': fecha_mod
        })

    # Ordenar por fecha de modificación
    documentos.sort(
        key=lambda x: x['fecha_modificacion']
    )

    # Convertir datetime a texto
    for doc in documentos:

        doc['fecha_modificacion'] = (
            doc['fecha_modificacion']
            .strftime('%Y-%m-%d %H:%M:%S')
        )

    return render_template(
        'listar_doc.html',
        documentos=documentos
    )


# =========================================================
# CREAR DOCUMENTO
# =========================================================

@documentacion_bp.route('/documentacion/crear')
def crear():

    return render_template(
        'crear_doc.html'
    )


# =========================================================
# GUARDAR DOCUMENTO
# =========================================================

@documentacion_bp.route(
    '/documentacion/guardar',
    methods=['POST']
)
def guardar():

    titulo = request.form['titulo'].strip()

    contenido = limpiar_contenido(
        request.form['contenido']
    )

    if not titulo:
        return "⚠️ El título no puede estar vacío.", 400

    nombre_archivo = (
        titulo.replace(" ", "_") + ".md"
    )

    ruta = os.path.join(
        DOCS_FOLDER,
        nombre_archivo
    )

    with open(
        ruta,
        'w',
        encoding='utf-8'
    ) as f:

        f.write(contenido)

    return redirect(
        url_for('documentacion.listar')
    )


# =========================================================
# VER DOCUMENTO
# =========================================================

@documentacion_bp.route(
    '/documentacion/ver/<nombre>'
)
def ver(nombre):

    ruta = os.path.join(
        DOCS_FOLDER,
        nombre
    )

    if not os.path.exists(ruta):

        return (
            "❌ Documento no encontrado.",
            404
        )

    with open(
        ruta,
        'r',
        encoding='utf-8'
    ) as f:

        contenido_md = f.read()

    contenido_html = markdown.markdown(
        contenido_md
    )

    return render_template(
        'ver_doc.html',
        titulo=nombre,
        contenido=contenido_html
    )


# =========================================================
# EDITAR DOCUMENTO
# =========================================================

@documentacion_bp.route(
    '/documentacion/editar/<nombre>',
    methods=['GET', 'POST']
)
def editar(nombre):

    ruta = os.path.join(
        DOCS_FOLDER,
        nombre
    )

    if not os.path.exists(ruta):

        return (
            "❌ Documento no encontrado.",
            404
        )

    # ---------------------------------------------
    # POST -> Guardar cambios
    # ---------------------------------------------

    if request.method == 'POST':

        contenido = limpiar_contenido(
            request.form['contenido']
        )

        with open(
            ruta,
            'w',
            encoding='utf-8'
        ) as f:

            f.write(contenido)

        return redirect(
            url_for('documentacion.listar')
        )

    # ---------------------------------------------
    # GET -> Mostrar editor
    # ---------------------------------------------

    with open(
        ruta,
        'r',
        encoding='utf-8'
    ) as f:

        contenido = limpiar_contenido(
            f.read()
        )

    return render_template(
        'crear_doc.html',
        titulo=nombre,
        contenido=contenido,
        modo='editar'
    )


# =========================================================
# ELIMINAR DOCUMENTO
# =========================================================

@documentacion_bp.route(
    '/documentacion/eliminar/<nombre>',
    methods=['POST']
)
def eliminar(nombre):

    ruta = os.path.join(
        DOCS_FOLDER,
        nombre
    )

    if os.path.exists(ruta):

        os.remove(ruta)

        return redirect(
            url_for('documentacion.listar')
        )

    return (
        "❌ Documento no encontrado.",
        404
    )