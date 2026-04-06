import os
import re
from docx import Document
import textract


class DocumentacionService:

    def __init__(self):

        self.docs_path = os.path.join(
            os.getcwd(),
            "documentacion",
            "templates",
            "documentos"
        )

        # extensiones soportadas
        self.allowed_ext = {
            ".md",
            ".docx",
            ".doc",
            ".txt"
        }

    # =========================
    # 📄 LEER DOCX
    # =========================
    def leer_docx(self, ruta):

        doc = Document(ruta)

        return "\n".join(
            p.text
            for p in doc.paragraphs
            if p.text.strip()
        )

    # =========================
    # 📄 LEER OTROS WORD (.doc)
    # =========================
    def leer_doc_legacy(self, ruta):

        # usa textract para formatos antiguos
        texto = textract.process(ruta)

        return texto.decode("utf-8", errors="ignore")

    # =========================
    # 📄 LECTURA UNIFICADA
    # =========================
    def leer_archivo(self, ruta):

        ext = os.path.splitext(ruta)[1].lower()

        if ext == ".md":
            with open(ruta, "r", encoding="utf-8") as f:
                return f.read()

        if ext == ".docx":
            return self.leer_docx(ruta)

        if ext == ".doc":
            return self.leer_doc_legacy(ruta)

        if ext == ".txt":
            with open(ruta, "r", encoding="utf-8") as f:
                return f.read()

        return ""

    # =========================
    # 🔎 BUSCAR DOCUMENTOS
    # =========================
    def buscar(self, pregunta):

        if not os.path.exists(self.docs_path):
            return None

        palabras = re.findall(r"\w+", pregunta.lower())

        mejor_doc = None
        mejor_score = 0

        for archivo in os.listdir(self.docs_path):

            if archivo.startswith("~$"):
                continue

            ext = os.path.splitext(archivo)[1].lower()

            if ext not in self.allowed_ext:
                continue

            ruta = os.path.join(self.docs_path, archivo)

            ext = os.path.splitext(archivo)[1].lower()

            if ext not in self.allowed_ext:
                continue

            contenido = self.leer_archivo(ruta)

            texto = (archivo.lower() + " " + contenido.lower())

            score = 0

            for palabra in palabras:
                if palabra in texto:
                    score += 1

            if score > mejor_score:

                mejor_score = score
                mejor_doc = {
                    "archivo": archivo,
                    "contenido": contenido
                }

        return mejor_doc