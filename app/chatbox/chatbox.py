from flask import Blueprint, request, jsonify, render_template

# Crear blueprint para el chatbox
chatbox_bp = Blueprint('chatbox', __name__)

# Ruta para la página de chat
@chatbox_bp.route('/chatbox')
def chatbox_home():
    return render_template('chatbox.html')

# Ruta para procesar preguntas
@chatbox_bp.route('/chatbox/preguntar', methods=['POST'])
def preguntar():
    pregunta = request.json.get('pregunta', '')

    # Respuesta fija con saludo si el mensaje contiene "chatbox" o alguna pregunta relacionada
    if 'chatbox' in pregunta.lower():
        respuesta = "¡Hola! Gracias por visitar el chatbox. Pronto estaremos desarrollando un chatbox más completo para ti."
    else:
        respuesta = "¡Hola! Gracias por visitar el chatbox. Pronto estaremos desarrollando un chatbox más completo para ti."

    return jsonify({'respuesta': respuesta})
