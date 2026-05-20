from flask import Flask, render_template, request, jsonify
from gpt4all import GPT4All

# Inicializar app Flask
app = Flask(__name__)

# Cargar modelo GPT4All
model = GPT4All("ggml-gpt4all-j-v1.3-groovy")  # ruta al modelo local

# Ruta principal que sirve el chatbox HTML
@app.route("/")
def home():
    return render_template("chatbox.html")

# Ruta para recibir mensajes del frontend y devolver la respuesta del modelo
@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"response": "Por favor escribe un mensaje."})

    # Generar respuesta usando GPT4All
    response = model.generate(user_input)
    return jsonify({"response": response})

# Ejecutar app
if __name__ == "__main__":
    app.run(debug=True)