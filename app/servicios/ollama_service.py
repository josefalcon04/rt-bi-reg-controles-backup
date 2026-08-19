# ============================================================
# SERVICIO OLLAMA
# ============================================================

import os
import requests


class OllamaService:

    def __init__(self):

        self.url = os.getenv(
            "OLLAMA_URL",
            "http://localhost:11434/api/generate"
        )

        self.modelo = os.getenv(
            "OLLAMA_MODEL",
            "qwen2.5-coder:7b"
            #"granite3.3:8b"
            #"qwen2.5-coder:3b"
        )

        self.timeout = int(
            os.getenv(
                "OLLAMA_TIMEOUT",
                "180"
            )
        )

    # ============================================================
    # LLAMAR A OLLAMA
    # ============================================================

    def llamar(
        self,
        pregunta,
        contexto="",
        system_prompt="",
        modelo=None
    ):

        # Si se especifica un modelo para esta llamada,
        # se utiliza ese modelo.
        # Si no, se mantiene el modelo principal.
        modelo_usar = modelo or self.modelo

        prompt = self._construir_prompt(
            pregunta=pregunta,
            contexto=contexto,
            system_prompt=system_prompt
        )

        print(
            f"[OLLAMA] Modelo: {modelo_usar}"
        )

        print(
            f"[OLLAMA] Prompt: {len(prompt)} caracteres"
        )

        payload = {
            "model": modelo_usar,
            "prompt": prompt,
            "stream": False
        }

        try:

            response = requests.post(
                self.url,
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()

            data = response.json()

            respuesta = data.get(
                "response",
                ""
            )

            if respuesta is None:
                respuesta = ""

            return str(
                respuesta
            ).strip()

        except requests.exceptions.Timeout:

            print(
                "[OLLAMA ERROR] Timeout esperando respuesta de Ollama"
            )

            raise Exception(
                "Ollama tardó demasiado en responder."
            )

        except requests.exceptions.ConnectionError:

            print(
                "[OLLAMA ERROR] No se pudo conectar con Ollama"
            )

            raise Exception(
                "No se pudo conectar con Ollama. "
                "Verifica que el servicio esté ejecutándose."
            )

        except requests.exceptions.HTTPError as e:

            print(
                f"[OLLAMA ERROR] Error HTTP: {e}"
            )

            raise Exception(
                f"Error HTTP de Ollama: {e}"
            )

        except Exception as e:

            print(
                f"[OLLAMA ERROR] {str(e)}"
            )

            raise

    # ============================================================
    # CONSTRUIR PROMPT
    # ============================================================

    def _construir_prompt(
        self,
        pregunta,
        contexto="",
        system_prompt=""
    ):

        partes = []

        if system_prompt:

            partes.append(
                "INSTRUCCIONES DEL SISTEMA:\n"
                + str(system_prompt).strip()
            )

        if contexto:

            partes.append(
                "CONTEXTO:\n"
                + str(contexto).strip()
            )

        partes.append(
            "PREGUNTA:\n"
            + str(pregunta).strip()
        )

        return "\n\n".join(
            partes
        )


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

ollama_service = OllamaService()