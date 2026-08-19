# ==============================================================
# TEST DASHBOARD - FLUJO INTERACTIVO
# Simula una conversación real del Chatbox
# ==============================================================

import os
import sys
import traceback

# --------------------------------------------------------------
# PATH DEL PROYECTO
# --------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# --------------------------------------------------------------
# IMPORTAR AGENTE
# --------------------------------------------------------------
try:
    from app.agentes.agente_dashboard import AgenteDashboard
except Exception as e:
    print("\n[ERROR] No se pudo importar AgenteDashboard")
    print(str(e))
    traceback.print_exc()
    sys.exit(1)


# ==============================================================
# CONFIGURACIÓN DE PRUEBA
# ==============================================================

CONSULTA = """
Hazme un dashboard de la tabla DBI_PUBLIC.PLT_MTC_202607
"""


# ==============================================================
# MAIN
# ==============================================================

def main():

    print("=" * 70)
    print(" PRUEBA DASHBOARD - FLUJO COMPLETO INTERACTIVO")
    print("=" * 70)

    print("\n[TEST] Inicializando AgenteDashboard...")

    try:
        agente = AgenteDashboard()
    except Exception as e:
        print("\n[ERROR] No se pudo inicializar el agente")
        print(str(e))
        traceback.print_exc()
        return

    print("[TEST] AgenteDashboard inicializado correctamente")

    # ----------------------------------------------------------
    # PASO 1
    # ----------------------------------------------------------

    print("\n")
    print("=" * 70)
    print(" PASO 1 - CONSULTA DEL USUARIO")
    print("=" * 70)

    print("\n[CHATBOX -> AGENTE]")
    print(CONSULTA.strip())

    try:

        resultado = agente.procesar(CONSULTA)

    except Exception as e:

        print("\n[ERROR] Error procesando la consulta")
        print(str(e))
        traceback.print_exc()
        return

    # ----------------------------------------------------------
    # MOSTRAR RESPUESTA
    # ----------------------------------------------------------

    print("\n")
    print("=" * 70)
    print(" RESPUESTA DEL AGENTE")
    print("=" * 70)

    if isinstance(resultado, dict):

        print("\nEstado:")
        print(resultado.get("estado"))

        print("\nAgente:")
        print(resultado.get("agente"))

        print("\nRespuesta:")
        print(resultado.get("respuesta", ""))

    else:

        print(resultado)

    # ----------------------------------------------------------
    # VERIFICAR SI YA GENERÓ DASHBOARD
    # ----------------------------------------------------------

    if isinstance(resultado, dict):

        url = resultado.get("url")

        if url:

            print("\n")
            print("=" * 70)
            print(" DASHBOARD GENERADO")
            print("=" * 70)

            print(f"\nURL:")
            print(url)

            print("\n[OK] El agente ya generó el dashboard.")
            return

    # ----------------------------------------------------------
    # PASO 2 - ELECCIÓN DEL USUARIO
    # ----------------------------------------------------------

    print("\n")
    print("=" * 70)
    print(" ELECCIÓN DEL DASHBOARD")
    print("=" * 70)

    print("\nEscribe la opción que deseas construir.")

    while True:

        opcion = input("\n[CHATBOX] Opción (1 / 2 / 3): ").strip()

        if opcion in ("1", "2", "3"):
            break

        print("[ERROR] Debes ingresar solamente 1, 2 o 3.")

    # ----------------------------------------------------------
    # SIMULAR SEGUNDA INTERACCIÓN DEL CHATBOX
    # ----------------------------------------------------------

    consulta_opcion = opcion

    print("\n")
    print("=" * 70)
    print(" PASO 2 - ELECCIÓN DEL USUARIO")
    print("=" * 70)

    print(f"\n[CHATBOX -> AGENTE]")
    print(consulta_opcion)

    try:

        resultado_final = agente.procesar(consulta_opcion)

    except Exception as e:

        print("\n[ERROR] Error procesando la opción")
        print(str(e))
        traceback.print_exc()
        return

    # ----------------------------------------------------------
    # RESULTADO FINAL
    # ----------------------------------------------------------

    print("\n")
    print("=" * 70)
    print(" RESULTADO FINAL")
    print("=" * 70)

    if isinstance(resultado_final, dict):

        print("\nEstado:")
        print(resultado_final.get("estado"))

        print("\nAgente:")
        print(resultado_final.get("agente"))

        print("\nMotor:")
        print(resultado_final.get("motor"))

        print("\nFuente:")
        print(resultado_final.get("referencia"))

        print("\nOpción:")
        print(resultado_final.get("opcion"))

        print("\nRespuesta:")
        print(resultado_final.get("respuesta", ""))

        # ------------------------------------------------------
        # URL
        # ------------------------------------------------------

        url = resultado_final.get("url")

        if url:

            print("\n")
            print("=" * 70)
            print(" HTML GENERADO CORRECTAMENTE")
            print("=" * 70)

            print(f"\nURL:")
            print(url)

            # --------------------------------------------------
            # VALIDAR ARCHIVO FÍSICO
            # --------------------------------------------------

            archivo = resultado_final.get("resultado", {}).get("archivo")

            if archivo:

                ruta_archivo = archivo

                if not os.path.isabs(ruta_archivo):
                    ruta_archivo = os.path.join(BASE_DIR, ruta_archivo)

                print("\nArchivo físico:")
                print(ruta_archivo)

                if os.path.exists(ruta_archivo):

                    tamano = os.path.getsize(ruta_archivo)

                    print(f"\nTamaño HTML: {tamano:,} bytes")

                    print("\n[OK] EL FLUJO COMPLETO TERMINÓ CORRECTAMENTE")

                else:

                    print("\n[ADVERTENCIA]")
                    print("El agente devolvió una URL pero el archivo")
                    print("no fue encontrado físicamente.")

            else:

                print("\n[ADVERTENCIA]")
                print("Se generó URL pero no se encontró la ruta física.")

        else:

            print("\n")
            print("=" * 70)
            print(" NO SE GENERÓ HTML")
            print("=" * 70)

            print("\nLa respuesta final fue:")

            print(resultado_final)

    else:

        print(resultado_final)


# ==============================================================
# EJECUCIÓN
# ==============================================================

if __name__ == "__main__":
    main()