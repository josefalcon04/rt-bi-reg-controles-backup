# ============================================================
# SERVICIO DE EMBEDDINGS
# ============================================================

import requests
import numpy as np


class EmbeddingService:

    OLLAMA_URL = "http://localhost:11434/api/embed"
    MODELO = "nomic-embed-text-v2-moe"

    def __init__(self):
        print(
            f"[EMBEDDING] Modelo configurado: {self.MODELO}"
        )

    # ========================================================
    # GENERAR EMBEDDING
    # ========================================================

    def generar(self, texto):

        if not texto:
            return None

        try:

            response = requests.post(
                self.OLLAMA_URL,
                json={
                    "model": self.MODELO,
                    "input": texto
                },
                timeout=60
            )

            response.raise_for_status()

            data = response.json()

            embeddings = data.get("embeddings")

            if not embeddings:
                print(
                    "[EMBEDDING] Ollama no devolvió embeddings"
                )
                return None

            return embeddings[0]

        except Exception as e:

            print(
                f"[ERROR EMBEDDING]: {str(e)}"
            )

            return None

    # ========================================================
    # SIMILITUD COSENO
    # ========================================================

    def similitud(self, texto_a, texto_b):

        embedding_a = self.generar(texto_a)
        embedding_b = self.generar(texto_b)

        if not embedding_a or not embedding_b:
            return 0.0

        a = np.array(
            embedding_a,
            dtype=float
        )

        b = np.array(
            embedding_b,
            dtype=float
        )

        norma_a = np.linalg.norm(a)
        norma_b = np.linalg.norm(b)

        if norma_a == 0 or norma_b == 0:
            return 0.0

        score = np.dot(a, b) / (
            norma_a * norma_b
        )

        return round(
            float(score),
            4
        )