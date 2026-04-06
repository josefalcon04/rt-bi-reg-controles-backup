import json
import os
import io
import pandas as pd

from flask import Blueprint, render_template, request, redirect, send_file, jsonify
from datetime import datetime
from openpyxl.styles import Border, Side

# -------------------------
# BLUEPRINT
# -------------------------
pases_bp = Blueprint('pases', __name__)

# -------------------------
# DATA
# -------------------------
DATA_DIR = os.path.join('data')
DATA_FILE = os.path.join(DATA_DIR, 'pases_data.json')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

COLUMNAS_ORDENADAS = [
    'id', 'fecha_sistema', 'fecha',
    'proceso', 'name_proceso', 'cti', 'tinkuy',
    'documentacion', 'link_sharepoint', 'tipo',
    'desarrolladorbi', 'liderintegratel', 'responsablepap'
]

# -------------------------
# UTILIDADES
# -------------------------
def generar_nuevo_id(lista_pases):
    max_id = 0
    for p in lista_pases:
        if 'id' in p and str(p['id']).startswith('PaseReg-'):
            try:
                num = int(p['id'].split('-')[1])
                max_id = max(max_id, num)
            except:
                pass
    return f"PaseReg-{max_id + 1:06d}"


def cargar_datos():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []


def guardar_datos(datos):
    with open(DATA_FILE, 'w') as f:
        json.dump(datos, f, indent=4)


def generar_url_jira(codigo):
    if codigo and codigo != 'DEFAULT':
        return f"https://integratelperu.atlassian.net/browse/{codigo}"
    return "#"

# -------------------------
# RUTAS
# -------------------------
@pases_bp.route('/pases')
def listar_pases():
    return render_template(
        "pases.html",
        lista_pases=cargar_datos(),
        generar_url=generar_url_jira,
        enumerate=enumerate
    )


@pases_bp.route('/pases/form', defaults={'index': -1})
@pases_bp.route('/pases/form/<int:index>')
def abrir_formulario(index):
    lista_pases = cargar_datos()
    pase = lista_pases[index] if index != -1 else None
    return render_template("pases_form.html", pase=pase, index=index)

# -------------------------
# GUARDAR (SPA READY)
# -------------------------
@pases_bp.route('/pases/guardar', methods=['POST'])
def guardar():
    print("================================")
    print("ENTRO A GUARDAR")
    print(request.form)
    print("================================")
    try:
        idx = request.form.get("index")
        idx = int(idx) if idx not in [None, ""] else -1

        lista = cargar_datos()

        nuevo = {
            "id": request.form.get("id") or generar_nuevo_id(lista),
            "fecha_sistema": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fecha": request.form.get("fecha"),
            "proceso": request.form.get("proceso"),
            "name_proceso": request.form.get("name_proceso"),
            "cti": request.form.get("cti"),
            "tinkuy": request.form.get("tinkuy"),
            "documentacion": request.form.get("documentacion"),
            "link_sharepoint": request.form.get("link_sharepoint"),
            "tipo": request.form.get("tipo"),
            "desarrolladorbi": request.form.get("desarrolladorbi"),
            "liderintegratel": request.form.get("liderintegratel"),
            "responsablepap": request.form.get("responsablepap")
        }

        if idx == -1:
            lista.append(nuevo)
        else:
            lista[idx] = nuevo

        guardar_datos(lista)

        return jsonify({"ok": True})

    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500

# -------------------------
# ELIMINAR (SPA READY)
# -------------------------
@pases_bp.route(
    '/pases/eliminar/<string:pase_id>',
    methods=['POST'],
    endpoint='eliminar_pase_unico'
)
def eliminar_pase(pase_id):
    try:
        lista = cargar_datos()

        nueva_lista = [
            p for p in lista
            if p.get('id') != pase_id
        ]

        if len(nueva_lista) == len(lista):
            return jsonify({
                "ok": False,
                "message": "Pase no encontrado"
            }), 404

        guardar_datos(nueva_lista)

        return jsonify({
            "ok": True,
            "message": "Eliminado con éxito"
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "message": str(e)
        }), 500
    

# -------------------------
# IMPORTAR
# -------------------------
@pases_bp.route('/pases/importar', methods=['POST'])
def importar():
    file = request.files['file']
    if not file or file.filename == '':
        return redirect('/pases')

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file, sep=None, engine='python')
        else:
            df = pd.read_excel(file, engine='openpyxl')

        df.columns = df.columns.str.strip()

        def clean(v):
            return str(v).strip() if pd.notna(v) else ""

        lista = cargar_datos()

        for _, row in df.iterrows():
            item = {
                "id": clean(row.get('id')) or generar_nuevo_id(lista),
                "fecha_sistema": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fecha": clean(row.get('fecha')),
                "proceso": clean(row.get('proceso')),
                "name_proceso": clean(row.get('name_proceso')),
                "cti": clean(row.get('cti')),
                "tinkuy": clean(row.get('tinkuy')),
                "documentacion": clean(row.get('documentacion')),
                "link_sharepoint": clean(row.get('link_sharepoint')),
                "tipo": clean(row.get('tipo')),
                "desarrolladorbi": clean(row.get('desarrolladorbi')),
                "liderintegratel": clean(row.get('liderintegratel')),
                "responsablepap": clean(row.get('responsablepap'))
            }

            found = False
            for i, e in enumerate(lista):
                if e.get("id") == item["id"]:
                    lista[i] = item
                    found = True
                    break

            if not found:
                lista.append(item)

        guardar_datos(lista)

    except Exception as e:
        print("Error importación:", e)

    return redirect('/pases')


# -------------------------
# EXPORT CSV
# -------------------------
@pases_bp.route('/pases/exportar/csv')
def exportar_csv():
    df = pd.DataFrame(cargar_datos())
    df = df.reindex(columns=COLUMNAS_ORDENADAS).fillna("")

    output = io.BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)

    return send_file(output, mimetype='text/csv', as_attachment=True,
                     download_name="pases.csv")


# -------------------------
# EXPORT EXCEL
# -------------------------
@pases_bp.route('/pases/exportar/excel')
def exportar_excel():
    df = pd.DataFrame(cargar_datos())
    df = df.reindex(columns=COLUMNAS_ORDENADAS).fillna("")

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Pases')

        ws = writer.sheets['Pases']

        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        for col in ws.columns:
            max_len = 0
            col_letter = col[0].column_letter

            for cell in col:
                cell.border = border
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))

            ws.column_dimensions[col_letter].width = max_len + 2

    output.seek(0)

    return send_file(output,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name="pases.xlsx")
