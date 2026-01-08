from flask import Blueprint, render_template, request, redirect, url_for
import os
import markdown
import datetime

documentacion_bp = Blueprint('documentacion', __name__, template_folder='templates')

# Carpeta donde se guardarán los archivos .md
DOCS_FOLDER = os.path.join(os.path.dirname(__file__), 'templates', 'documentos')

# Asegurar que la carpeta exista
if not os.path.exists(DOCS_FOLDER):
    os.makedirs(DOCS_FOLDER)

# ---------------- Listar documentos ----------------
@documentacion_bp.route('/documentacion')
def listar():
    archivos = [f for f in os.listdir(DOCS_FOLDER) if f.endswith('.md')]
    
    documentos = []
    for f in archivos:
        ruta = os.path.join(DOCS_FOLDER, f)
        fecha_mod = datetime.datetime.fromtimestamp(os.path.getmtime(ruta))
        documentos.append({
            'nombre': f,
            'descripcion': 'Sin descripción',  # puedes personalizar
            'fecha_modificacion': fecha_mod  # guardamos datetime, no string aún
        })
    
    # Ordenar por fecha de modificación de menor a mayor
    documentos.sort(key=lambda x: x['fecha_modificacion'])

    # Convertimos datetime a string para la plantilla
    for doc in documentos:
        doc['fecha_modificacion'] = doc['fecha_modificacion'].strftime('%Y-%m-%d %H:%M:%S')

    return render_template('listar_doc.html', documentos=documentos)

# ---------------- Crear documento ----------------
@documentacion_bp.route('/documentacion/crear')
def crear():
    return render_template('crear_doc.html')

# ---------------- Guardar documento ----------------
@documentacion_bp.route('/documentacion/guardar', methods=['POST'])
def guardar():
    titulo = request.form['titulo'].strip()
    contenido = request.form['contenido']

    if not titulo:
        return "⚠️ El título no puede estar vacío.", 400

    nombre_archivo = titulo.replace(" ", "_") + ".md"
    ruta = os.path.join(DOCS_FOLDER, nombre_archivo)

    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(contenido)

    return redirect(url_for('documentacion.listar'))

# ---------------- Ver documento ----------------
@documentacion_bp.route('/documentacion/ver/<nombre>')
def ver(nombre):
    ruta = os.path.join(DOCS_FOLDER, nombre)
    if not os.path.exists(ruta):
        return "❌ Documento no encontrado.", 404

    with open(ruta, 'r', encoding='utf-8') as f:
        contenido_md = f.read()

    contenido_html = markdown.markdown(contenido_md)

    return render_template('ver_doc.html', titulo=nombre, contenido=contenido_html)

# ---------------- Editar documento ----------------
@documentacion_bp.route('/documentacion/editar/<nombre>', methods=['GET', 'POST'])
def editar(nombre):
    ruta = os.path.join(DOCS_FOLDER, nombre)
    if not os.path.exists(ruta):
        return "❌ Documento no encontrado.", 404

    if request.method == 'POST':
        # Guardar cambios
        contenido = request.form['contenido']
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)
        return redirect(url_for('documentacion.listar'))

    # GET -> Mostrar contenido en editor
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()

    # Enviamos 'modo' para que la plantilla sepa que estamos editando
    return render_template(
        'crear_doc.html',
        titulo=nombre,
        contenido=contenido,
        modo='editar'  # <-- NUEVO
    )


# ---------------- Eliminar documento ----------------
@documentacion_bp.route('/documentacion/eliminar/<nombre>', methods=['POST'])
def eliminar(nombre):
    ruta = os.path.join(DOCS_FOLDER, nombre)
    if os.path.exists(ruta):
        os.remove(ruta)
        return redirect(url_for('documentacion.listar'))
    return "❌ Documento no encontrado.", 404
